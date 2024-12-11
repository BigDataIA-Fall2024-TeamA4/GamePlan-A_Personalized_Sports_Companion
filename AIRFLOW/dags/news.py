from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import os
from dotenv import load_dotenv
from pinecone import Pinecone
import boto3
import json
from datetime import datetime
from typing import Any, List, Dict, Optional
import openai

# Load environment variables
load_dotenv()

# Get API keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

# RSS feed configurations
RSS_SOURCES = {
    'BBC': 'https://feeds.bbci.co.uk/sport/rss.xml',
    'Sky Sports': 'https://www.skysports.com/rss/12040',
    'Bleacher Report': 'https://bleacherreport.com/articles/feed'
}

def classify_with_openai(title: str, description: str) -> Optional[str]:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a sports news classifier. Classify the given sports news into one of these categories: Basketball, Cricket, Tennis, or Football. Consider Soccer as Football. Do not classify Rugby or any other sport. Return only the sports category as a single word."
                },
                {
                    "role": "user",
                    "content": f"Classify this sports news: Title: {title}, Description: {description}"
                }
            ],
            max_tokens=10
        )
        
        category = response.choices[0].message['content'].strip()
        
        # Validate the returned category
        if category in ["Basketball", "Cricket", "Tennis", "Football"]:
            return category
        return None  # Ignore unrelated sports
        
    except Exception as e:
        print(f"Error classifying with OpenAI: {str(e)}")
        return None

def extract_category(title: str, description: str) -> Optional[str]:
    try:
        # Use both the title and description for classification
        return classify_with_openai(title, description)
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
                category = extract_category(title, description)
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

def clean_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {key: (value if value is not None else "") for key, value in metadata.items()}

# Create embeddings and store in Pinecone
def create_embeddings(**kwargs) -> Optional[List[str]]:
   
    from sentence_transformers import SentenceTransformer
    from huggingface_hub import login
 
    try:
        # Load API keys
        HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
        PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
 
        # Validate environment variables
        if not all([PINECONE_API_KEY, PINECONE_ENVIRONMENT, HUGGING_FACE_API_KEY]):
            raise ValueError("Missing API keys or environment variables")
 
        # Initialize services
        login(token=HUGGING_FACE_API_KEY)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index('sport-news')
 
        # Load the embedding model
        model = SentenceTransformer("BAAI/bge-small-en-v1.5")
 
        # Pull articles from XCom
        articles: List[Dict[str, Any]] = kwargs['ti'].xcom_pull(task_ids='fetch_news', key='articles')
 
        if not articles:
            raise ValueError("No articles found for embedding.")
 
        embedded_ids = []
 
        for article in articles:
            try:
                # Check if the article is already in Pinecone
                existing_vectors = index.fetch(
                    ids=[
                        f"{article['link']}_category",
                        f"{article['link']}_title",
                        f"{article['link']}_description"
                    ]
                )
 
                # Skip if all three vectors already exist
                if existing_vectors and 'vectors' in existing_vectors and len(existing_vectors['vectors']) == 3:
                    print(f"Skipping existing article: {article['title']}")
                    continue
 
                # Prepare metadata
                metadata = {
                    "title": article['title'],
                    "description": article['description'],
                    "source": article['source'],
                    "category": article['category'],
                    "published_date": article['published_date'],
                    "image_link": article.get('image_link'),
                    "timestamp": article['timestamp']
                }

                cleaned_data = clean_metadata(metadata)

                # Create embeddings
                category_embedding = model.encode(article['category'])
                title_embedding = model.encode(article['title'])
                description_embedding = model.encode(article['description'])
 
                # Upsert embeddings into Pinecone
                index.upsert(
                    vectors=[
                        (f"{article['link']}_category", category_embedding.tolist(), {**cleaned_data, "type": "category"}),
                        (f"{article['link']}_title", title_embedding.tolist(), {**cleaned_data, "type": "title"}),
                        (f"{article['link']}_description", description_embedding.tolist(), {**cleaned_data, "type": "description"}),
                    ]
                )
 
                print(f"Embeddings created for {article['title']}")
 
                # Track successful embeddings
                embedded_ids.extend([
                    f"{article['link']}_category",
                    f"{article['link']}_title",
                    f"{article['link']}_description"
                ])
 
            except Exception as e:
                print(f"Error processing article '{article['title']}': {str(e)}")
 
        return embedded_ids
 
    except Exception as e:
        print(f"Critical Error in create_embeddings: {str(e)}")
        return None
       
def cleanup_old_news(**kwargs) -> Optional[int]:
    try:
        PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
 
        if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
            raise ValueError("Pinecone API Key or Environment Missing")
 
        # Initialize Pinecone client
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index('sports-news')
 
        # Current timestamp
        current_time = datetime.utcnow()
 
        # Fetch all vector metadata
        index_stats = index.describe_index_stats()
 
        if not index_stats or 'namespaces' not in index_stats:
            print("No namespaces found in Pinecone index.")
            return 0
 
        deleted_count = 0
 
        # Iterate through all namespaces
        for namespace, stats in index_stats['namespaces'].items():
            vector_ids = []
 
            # Collect all vector IDs
            for vector_id, vector_data in stats.get('vectors', {}).items():
                try:
                    metadata = vector_data['metadata']
                    news_timestamp = datetime.fromisoformat(metadata['timestamp'])
 
                    # Check if older than 2 days
                    if (current_time - news_timestamp) > timedelta(days=2):
                        vector_ids.append(vector_id)
                        print(f"Marked for deletion: {vector_id}")
 
                except Exception as e:
                    print(f"Error processing vector '{vector_id}': {str(e)}")
 
            # Delete collected vectors
            if vector_ids:
                index.delete(ids=vector_ids, namespace=namespace)
                deleted_count += len(vector_ids)
                print(f"Deleted {len(vector_ids)} vectors from namespace '{namespace}'.")
 
        print(f"Total deleted entries: {deleted_count}")
        return deleted_count
 
    except Exception as e:
        print(f"Critical Error in cleanup_old_news: {str(e)}")
        return None
 
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
   
    cleanup_task = PythonOperator(
        task_id='cleanup_old_news',
        python_callable=cleanup_old_news,
        provide_context=True
    )
 
    fetch_task >> save_raw_data_task >> embed_task >> cleanup_task
 