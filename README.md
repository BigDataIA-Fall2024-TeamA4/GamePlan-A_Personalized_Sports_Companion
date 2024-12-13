# GamePlan-A_Personalized_Sports_Companion


## Project Overview

Gameplan: A Personalized Sports Companion is an innovative platform designed to offer users a tailored sports experience. The application allows users to register, select their sporting interests, and specify their expertise level, ensuring a highly personalized journey. Through advanced data processing techniques, the platform aggregates relevant sports news, real-time fixtures, and skill-building resources. A sophisticated search functionality powered by a Retrieval-Augmented Generation (RAG) system ensures users receive the most accurate and contextually relevant responses. With seamless integration of external data sources and real-time updates, users are provided with up-to-date fixtures and recommendations. The entire system is containerized for efficient deployment and scalability, making it a robust solution for sports enthusiasts seeking personalized content.

[![Codelabs](https://img.shields.io/badge/Codelabs-blue)](https://codelabs-preview.appspot.com/?file_id=https://docs.google.com/document/d/13bIFU6uHJsi0LIQrMZbMpwrMkvKQmYtk9Br9EjyJgJA/edit?tab=t.0#4)

Youtube Video : https://youtu.be/Bpwil7IP0kI


**WE ATTEST THAT WE HAVEN'T USED ANY OTHER STUDENTS' WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK**


## Goal and Expected Outcome

**Goal:** The goal is to build a comprehensive, personalized sports companion application that helps users stay informed, improve their skills, and find local sports opportunities based on their interests and expertise. The application should provide a seamless experience with real-time sports news, fixtures, skill upgrade recommendations, and personalized user interactions. The key focus is on dynamic user engagement, sports news filtering, and relevant recommendations for skill enhancement.

**Final Outcome:**

- **Fully Functional FastAPI and Streamlit Application:** An interactive user interface built with Streamlit, where users can register, login, and manage their interests and expertise level.
A backend powered by FastAPI that handles authentication, sports news fetching, fixtures display, and skill upgrade recommendations.

- **Personalized Sports News Feed:** Personalized news articles fetched from multiple sources (BBC Sport, SkySports, Bleacher Report), filtered based on user interests, and displayed in a dynamic, user-friendly format.

- **Real-Time Sports Fixtures:** Integration with APIs for cricket, football, tennis, and basketball fixtures to provide up-to-date match schedules based on the user’s sporting interests.

- **Skill Upgrade Recommendations:** A recommendation engine that suggests relevant YouTube tutorials and nearby sports facilities using user data (sporting interest and expertise level), powered by Langchain for the planning and execution agent.

- **Incremental Data Handling and Search Functionality:** Implementation of RAG (Retrieval-Augmented Generation) for contextual querying, using Pinecone for fast search and response generation, enhanced with web search capabilities via the OpenAI and SERP API.

- **Cloud Deployment and Dockerization:** The entire application will be containerized using Docker, deployed on GCP Cloud, and made publicly accessible to users.

## Architecture Diagram

![Team4 drawio](https://github.com/user-attachments/assets/532f4ff2-73fe-4de0-bcd2-930020622e74)




## Technologies Used

![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-FF4E00?logo=python&logoColor=white) : Used for web scraping, extracting articles from RSS feeds of BBC Sport, SkySports, and Bleacher Report.

![Airflow](https://img.shields.io/badge/Airflow-017E6B?logo=apache-airflow&logoColor=white) : Used for orchestrating and automating the scraping, data processing, and storage workflows.

![Amazon S3](https://img.shields.io/badge/Amazon%20S3-569A31?logo=amazonaws&logoColor=white) : Stores raw scraped data (articles) and other assets, providing scalable and durable storage.

![Pinecone](https://img.shields.io/badge/Pinecone-00B8D9?logo=pinecone&logoColor=white) : Stores vector embeddings of scraped articles to enable fast similarity searches in the RAG (Retrieval-Augmented Generation) system.

![OpenAI](https://img.shields.io/badge/OpenAI-111111?logo=openai&logoColor=white) : Used for generating responses when a user query does not find relevant information in the fetched data, part of the RAG search process. Open AI model gpt-3.5-turbo used for categorization

![SERP API](https://img.shields.io/badge/SERP%20API-FF5722?logo=searchengineland&logoColor=white) : Used as a web search agent to retrieve additional data when the RAG search does not find relevant results.

![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white) : Powers the backend API, handling user requests for sports news, fixtures, and skill recommendations.


![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white) : Handles the frontend, displaying the UI for users to interact with sports news, fixtures, and skill upgrade recommendations.


![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white) : Containerised the application, ensuring a consistent and portable environment for deployment.

![GCP](https://img.shields.io/badge/GCP-4285F4?logo=google-cloud&logoColor=white) : Hosts the containerized application, providing scalable infrastructure for deployment and management.

![Snowflake](https://img.shields.io/badge/Snowflake-004F9C?logo=snowflake&logoColor=white) : Storing User Data

![HuggingFace](https://img.shields.io/badge/HuggingFace-FF2D20?logo=huggingface&logoColor=white) : SentenceTransformer("BAAI/bge-small-en-v1.5") used for generating Embeddings



## Prerequisites

Python Knowledge

Hugging Face Embedding Models Research

Snowflake Account Setup

S3 Account Setup

Airflow Setup

Docker Desktop

GCP Account Setup

### Environment Variables

Create a `.env` file with the following variables:

### API Keys

```bash
PINECONE_API_KEY=your_pinecone_key
OPENAI_API_KEY=your_openai_key
SERPAPI_KEY=your_serpapi_key
YOUTUBE_API_KEY=your_youtube_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
CRICKET_API_KEY=your_chosen_cricket_website_api_key
FOOTBALL_API_KEY=your_chosen_football_website_api_key
BASKETBALL_API_KEY=your_chosen_basketball_website_api_key
TENNIS_API_KEY=your_chosen_tennis_website_api_key
```

### Database

```bash
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=your_index_name
SNOWFLAKE_ACCOUNT=your_snowflake_account_name
SNOWFLAKE_USER=your_snowflake_username
SNOWFLAKE_PASSWORD=your_snowflake_password
SNOWFLAKE_DATABASE=your_snowflake_database
SNOWFLAKE_SCHEMA=your_snowflake_schema
SNOWFLAKE_WAREHOUSE=your_snowflake_warehouse_name
```




## Contribution

| Contributor         | Percentage | Tasks                                                                                                                                                                                                 |
|---------------------|------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Vaishnavi Veerkumar** | 40%        | Data extraction from rss feed, Webscraping for additional metadata related to news, Pinecone and S3 setup, Raw data storage in S3, Embedding storage in Pinecone, Airflow DAG,UI and backend for personalized news, search news and all news |
| **Sriram Venkatesh**   | 30%        |  Contributed to creating a Planning Agent for fetching related Youtube Videos and NEarby facilities, Beautification of UI |
| **Siddharth Pawar**     | 30%        | Login & SignUp setup on Fast API & Streamlit, Storing User interests and expertise level in Snowflake, API calls fetching and response formatting via FastAPI and Streamlit, Contributed to the implementation of RAG and Web Search agent for Sports Feed, Documentation : Codelabs, ReadME and Architecture Diagram |

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
