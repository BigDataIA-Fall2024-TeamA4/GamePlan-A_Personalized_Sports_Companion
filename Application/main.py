from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
import snowflake.connector
import os
from dotenv import load_dotenv
from fastapi.responses import Response
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import time

load_dotenv()

# Fetching environment variables
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE')
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE')
SNOWFLAKE_SCHEMA = os.getenv('SNOWFLAKE_SCHEMA')
SECRET_KEY = os.getenv("SECRET_KEY") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index('sports-news')
model = SentenceTransformer("BAAI/bge-small-en-v1.5")

# Snowflake connection
def get_snowflake_connection():
    return snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA
    )

# Helper: Generate JWT Token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Helper: Verify JWT Token
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class User(BaseModel):
    email: str
    username: str
    password: str
    first_name: str
    last_name: str
    interests: str
    expertise_level: str

class UserLogin(BaseModel):
    username: str
    password: str


def fetch_user_interests(username):
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT INTERESTS FROM USERS WHERE USERNAME = '{username}'")
    result = cursor.fetchone()
    conn.close()
    #print(f"Fetched Interests for {username}: {result}")
    return result[0] if result else []


# Endpoint for user registration
@app.post("/register")
async def register_user(user: User):
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute(f"SELECT * FROM USERS WHERE USERNAME = '{user.username}'")
        result = cursor.fetchone()
        if result:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="Username already exists!")

        # Use a SELECT statement for PARSE_JSON
        query = f"""
            INSERT INTO USERS (EMAIL, USERNAME, PASSWORD, FIRST_NAME, LAST_NAME, INTERESTS, EXPERTISE_LEVEL)
            SELECT
                '{user.email}',
                '{user.username}',
                '{user.password}',
                '{user.first_name}',
                '{user.last_name}',
                PARSE_JSON('{user.interests}'),
                '{user.expertise_level}'
        """
        cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "User registered successfully!"}

    except Exception as e:
        return {"error": str(e)}

# Endpoint for user login
@app.post("/login")
async def login_user(user: UserLogin):
    try:
        # Connect to Snowflake
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # Check username and password
        cursor.execute(
            f"SELECT FIRST_NAME, EMAIL, INTERESTS FROM USERS WHERE USERNAME = '{user.username}' AND PASSWORD = '{user.password}'"
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            raise HTTPException(status_code=400, detail="Invalid credentials!")

        # Fetch user interests
        user_interests = fetch_user_interests(user.username)

        # Fetch latest news from Pinecone
        personalized_feed = query_pinecone_latest_news(user_interests)

        return {
            "first_name": result[0],
            "email": result[1],
            "interests": result[2],
            "personalized_feed": personalized_feed,
        }

    except Exception as e:
        #print(f"Error in /login endpoint: {e}")  # Log the error to the console
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.put("/update_password")
async def update_user_password(data: dict):
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        query = f"""
            UPDATE USERS
            SET PASSWORD = '{data['new_password']}'
            WHERE USERNAME = '{data['username']}'
        """
        cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Password updated successfully!"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@app.put("/update_interests")
async def update_user_interests(data: dict):
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        query = f"""
            UPDATE USERS
            SET INTERESTS = PARSE_JSON('{data['interests']}')
            WHERE USERNAME = '{data['username']}'
        """
        cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Interests updated successfully!"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@app.put("/update_expertise")
async def update_user_expertise(data: dict):
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        query = f"""
            UPDATE USERS
            SET EXPERTISE_LEVEL = '{data['expertise_level']}'
            WHERE USERNAME = '{data['username']}'
        """
        cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Expertise level updated successfully!"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

# Query Pinecone for latest news based on interests
def query_pinecone_latest_news(user_interests, hours_back=24):
    news_feed = []

    # Calculate the latest time filter in epoch seconds
    latest_time_filter = datetime.utcnow() - timedelta(hours=hours_back)
    latest_time_epoch = int(latest_time_filter.timestamp())  # Convert to epoch time

    for interest in user_interests:
        # Encode interest as a query vector
        query_embedding = model.encode(interest).tolist()

        try:
            # Search only category embeddings using metadata filtering
            search_results = index.query(
                vector=query_embedding,             # Encoded interest vector
                top_k=5,                           # Number of results
                include_metadata=True,             # Include metadata
                filter={
                    "type": {"$eq": "category"},   # Ensure only category embeddings are matched
                    "timestamp": {"$gte": latest_time_epoch}  # Filter by recent timestamps
                }
            )

            # Process search results
            for result in search_results["matches"]:
                metadata = result["metadata"]

                # Add to feed only if essential fields exist
                if {"title", "description", "link", "category", "timestamp"} <= metadata.keys():
                    news_feed.append({
                        "title": metadata["title"],
                        "description": metadata["description"],
                        "link": metadata["link"],
                        "image_link": metadata.get("image_link", ""),
                        "category": metadata["category"],
                        "timestamp": metadata["timestamp"]
                    })

        except Exception as e:
            print(f"Error querying Pinecone for {interest}: {str(e)}")

    # Sort results by timestamp (most recent first)
    news_feed.sort(key=lambda x: x["timestamp"], reverse=True)

    return news_feed

@app.get("/all_news")
def get_all_news():
    try:
        response = index.query(
            vector=[0] * 384,  # Dummy vector
            top_k=100,  # Adjust this as needed
            include_metadata=True
        )
        news_feed = {}
        
        for match in response["matches"]:
            metadata = match["metadata"]
            # Extract the link without the suffix (_category, _title, _description)
            original_link = match["id"].split("_")[0]
            
            # Deduplicate based on the original link
            if original_link not in news_feed:
                news_feed[original_link] = {
                    "title": metadata["title"],
                    "description": metadata["description"],
                    "link": original_link,  # Use the deduplicated link
                    "image_link": metadata.get("image_link", ""),
                    "category": metadata["category"],
                    "timestamp": metadata["timestamp"],
                    "source": metadata.get("source", "Unknown"),
                    "published_date": metadata.get("published_date", "Unknown")
                }
        
        # Return deduplicated list
        return {"news": list(news_feed.values())}
    except Exception as e:
        return {"error": str(e)}

                    
# Example protected endpoint
@app.get("/protected-endpoint")
async def protected_endpoint(token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    return {"message": f"Hello, {username}. This is a protected endpoint!"}

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI application!"}

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)
