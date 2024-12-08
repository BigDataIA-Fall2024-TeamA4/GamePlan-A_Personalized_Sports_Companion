from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from rapidfuzz import fuzz
import boto3
import json
from datetime import datetime
from typing import List, Optional

# Load environment variables
load_dotenv()

# Get API keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")

# RSS feed configurations
RSS_SOURCES = {
    'BBC': 'https://feeds.bbci.co.uk/sport/rss.xml',
    'Sky Sports': 'https://www.skysports.com/rss/12040',
    'Bleacher Report': 'https://bleacherreport.com/articles/feed'
}

# Keywords for categories
CATEGORY_KEYWORDS = {
    'Basketball': ['basketball', 'nba', 'dunk', 'three-pointer'],
    'Cricket': ['cricket', 'bat', 'bowl', 'wicket', 'run'],
    'Tennis': ['tennis', 'grand slam', 'wimbledon', 'serve', 'match'],
    'Football': ['football', 'soccer', 'goal', 'striker', 'defender']
}

# Extract best matching category using fuzzy matching
def extract_category_fuzzy(title: str, description: str, link: str) -> Optional[str]:
    try:
        combined_text = f"{title} {description} {link}".lower()
        best_category = None
        max_score = 0

        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                score = fuzz.partial_ratio(keyword, combined_text)
                if score > max_score and score >= 75:  
                    max_score = score
                    best_category = category

        return best_category
    except Exception as e:
        print(f"Error extracting category: {str(e)}")
        return None

# Fetch and process RSS feeds
def fetch_and_process_feeds(**kwargs) -> None:
    all_articles = []

    for source_name, url in RSS_SOURCES.items():
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'xml')

            for item in soup.find_all('item'):
                title = item.find('title').text if item.find('title') else ''
                link = item.find('link').text if item.find('link') else ''
                description = item.find('description').text if item.find('description') else ''
                pub_date = item.find('pubDate').text if item.find('pubDate') else ''

                # Extract category
                category = extract_category_fuzzy(title, description, link)
                if not category:
                    continue  # Skip if no relevant category found

                # Extract image link per source
                image_link = None
                try:
                    if source_name == 'BBC':
                        image_link = item.find('media:thumbnail')['url'] if item.find('media:thumbnail') else None

                    elif source_name == 'Sky Sports' and link:
                        article_response = requests.get(link, timeout=10)
                        article_soup = BeautifulSoup(article_response.content, 'html.parser')
                        img_tag = article_soup.find('img', class_='sdc-article-image__item')
                        image_link = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None

                    elif source_name == 'Bleacher Report':
                        image_link = item.find('image').find('link').text if item.find('image') and item.find('image').find('link') else None

                except Exception as e:
                    print(f"Error extracting image link for {source_name}: {str(e)}")

                # Store the article data
                article = {
                    'title': title,
                    'link': link,
                    'description': description,
                    'image_link': image_link,
                    'source': source_name,
                    'category': category,
                    'published_date': pub_date,
                    'timestamp': datetime.now().isoformat()
                }
                all_articles.append(article)

        except Exception as e:
            print(f"Error processing {source_name}: {str(e)}")

    kwargs['ti'].xcom_push(key='articles', value=all_articles)

def save_data_to_s3(**kwargs) -> None:

    # S3 bucket and file path
    S3_BUCKET = os.getenv("AWS_BUCKET_NAME")
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
    S3_KEY = f"sports_news_{timestamp}.json"

    # Get data from XCom
    all_articles = kwargs['ti'].xcom_pull(task_ids='fetch_news', key='articles')

    # Validate data before saving
    if not all_articles:
        raise ValueError("No articles found to save to S3!")

    # Save the data to S3
    s3_client = boto3.client('s3')
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=S3_KEY,
            Body=json.dumps(all_articles),
            ContentType='application/json'
        )
        print(f"Raw data saved to S3: {S3_BUCKET}/{S3_KEY}")
    except Exception as e:
        print(f"Error saving raw data to S3: {str(e)}")
        raise e

# Create embeddings and store in Pinecone
def create_embeddings(**kwargs) -> None:
    from sentence_transformers import SentenceTransformer
    from huggingface_hub import login

    HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")

    if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
        raise ValueError("Pinecone API Key or Environment Missing")
    if not HUGGING_FACE_API_KEY:
        raise ValueError("Hugging Face API Key Missing")

    login(token=HUGGING_FACE_API_KEY)
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index('sports-news')
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    articles = kwargs['ti'].xcom_pull(task_ids='fetch_news', key='articles')

    for article in articles:
        try:
            text_to_embed = f"{article['title']} {article['description']} {article['category']}"
            embedding = model.encode(text_to_embed)

            metadata = {
                'title': article['title'],
                'description': article['description'],
                'source': article['source'],
                'category': article['category'],
                'published_date': article['published_date'],
                'timestamp': article['timestamp']
            }

            if article['image_link']:
                metadata['image_link'] = article['image_link']

            index.upsert(
                vectors=[(article['link'], embedding.tolist(), metadata)]
            )
        except Exception as e:
            print(f"Error creating embedding for article '{article['title']}': {str(e)}")

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5)
}

# Define the DAG
with DAG(
    'sports_news',
    default_args=default_args,
    description='Fetch and process sports news every 15 minutes',
    schedule_interval=timedelta(minutes=15),
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:
    
    fetch_task = PythonOperator(
        task_id='fetch_news',
        python_callable=fetch_and_process_feeds,
        provide_context=True
    )
    
    save_raw_data_task = PythonOperator(
        task_id='save_raw_data_to_s3',
        python_callable=save_data_to_s3,
        provide_context=True
    )

    embed_task = PythonOperator(
        task_id='create_embeddings',
        python_callable=create_embeddings,
        provide_context=True
    )
    
    fetch_task >> save_raw_data_task >> embed_task
