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
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from fastapi import Query
 
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
 
CRICKET_API_KEY = os.getenv('CRICKET_API_KEY')
BASKETBALL_API_KEY= os.getenv('BASKETBALL_API_KEY')
TENNIS_API_KEY= os.getenv('TENNIS_API_KEY')
FOOTBALL_API_KEY= os.getenv('FOOTBALL_API_KEY')
 
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
 
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
 
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index('sport-news')
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
 
class ForgotPasswordRequest(BaseModel):
    email: str
 
class PasswordReset(BaseModel):
    token: str
    new_password: str
 
# Send Reset Email Function
def send_reset_email(email, reset_link):
    try:
        # Email message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Password Reset Request"
        message["From"] = EMAIL_USER
        message["To"] = email
 
        text = f"Please click the link below to reset your password:\n{reset_link}"
        html = f"<p>Please click the link below to reset your password:</p><a href='{reset_link}'>{reset_link}</a>"
        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))
 
        # Send email
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, email, message.as_string())
 
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
       
def fetch_user_interests(username):
    """Fetch user interests from Snowflake."""
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT INTERESTS FROM USERS WHERE USERNAME = '{username}'")
    result = cursor.fetchone()
    conn.close()
 
    if result and result[0]:
        try:
            return json.loads(result[0])  # Ensure it's parsed correctly
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            return []
    return []
 
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
        conn = get_snowflake_connection()
        cursor = conn.cursor()
 
        # Check username and password
        query = f"""
        SELECT FIRST_NAME, EMAIL, INTERESTS
        FROM USERS
        WHERE USERNAME = '{user.username}' AND PASSWORD = '{user.password}'
        """
        cursor.execute(query)
        result = cursor.fetchone()
 
        cursor.close()
        conn.close()
 
        if not result:
            raise HTTPException(status_code=400, detail="Invalid credentials!")
 
        # Decode interests from Snowflake's JSON storage
        user_interests = json.loads(result[2]) if result[2] else []
 
        # Fetch personalized feed from Pinecone
        personalized_feed = query_pinecone_latest_news(user_interests)
 
        # Return user data and personalized feed
        return {
            "first_name": result[0],
            "email": result[1],
            "interests": user_interests,
            "personalized_feed": personalized_feed,
        }
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
 
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
 
def query_pinecone_latest_news(user_interests, hours_back=24):
    news_feed = []
 
    latest_time_filter = datetime.utcnow() - timedelta(hours=hours_back)
    latest_time_epoch = int(latest_time_filter.timestamp())  
    for interest in user_interests:
       
        query_embedding = model.encode(interest).tolist()
 
        try:
            search_results = index.query(
                vector=query_embedding,            
                top_k=5,                          
                include_metadata=True,            
                filter={
                    "type": {"$eq": "category"},  
                    "timestamp": {"$gte": latest_time_epoch}  
                }
            )
 
            # Process search results
            for result in search_results["matches"]:
                metadata = result["metadata"]
 
               
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
 
    # Sort results by timestamp
    news_feed.sort(key=lambda x: x["timestamp"], reverse=True)
 
    return news_feed
 
@app.post("/personalized_news")
async def get_personalized_news(data: dict):
    try:
        user_interests = data.get("interests", [])
        if not user_interests:
            return {"news": []}
 
        news_feed = []
        seen_ids = set()  
 
        for interest in user_interests:
            query_embedding = model.encode(interest).tolist()
            search_results = index.query(
                vector=query_embedding,
                top_k=5,  
                include_metadata=True,
                filter={"type": {"$eq": "category"}}
            )
 
            for result in search_results.get("matches", []):
                metadata = result.get("metadata", {})
                base_link = result["id"].split("_")[0]  
 
                if base_link in seen_ids:
                    continue  
                seen_ids.add(base_link)  
 
                default_image = "https://img.freepik.com/premium-vector/unavailable-movie-icon-no-video-bad-record-symbol_883533-383.jpg?w=360"
       
                if {"title", "description", "category"} <= metadata.keys():
                    news_feed.append({
                        "title": metadata["title"],
                        "description": metadata["description"],
                        "link": base_link,
                        "image_link": metadata.get("image_link", "") or default_image,
                        "category": metadata["category"],
                        "published_date": metadata.get("published_date", "Unknown"),
                        "source": metadata.get("source", "Unknown"),
                    })
 
       
        news_feed.sort(key=lambda x: x.get("published_date", ""), reverse=True)
        return {"news": news_feed[:10]}  # Limit to top 10
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
 
 
@app.post("/search_news")
async def search_news(data: dict):
    try:
        query = data.get("query", "").lower()
        if not query:
            return {"rag_results": [], "web_results": []}
 
        # Query Pinecone (RAG)
        query_embedding = model.encode(query).tolist()
        pinecone_results = index.query(
            vector=query_embedding,
            top_k=3,  
            include_metadata=True
        )
 
        # Process Pinecone results
        rag_results = []
        seen_ids = set()
 
        for result in pinecone_results.get("matches", []):
            metadata = result.get("metadata", {})
            base_link = result["id"].split("_")[0]  # Extract base ID
 
            if base_link in seen_ids:
                continue  # Skip duplicates
            seen_ids.add(base_link)
 
            rag_results.append({
                "title": metadata.get("title", "Unknown Title"),
                "description": metadata.get("description", "No Description Available."),
                "link": base_link,
                "image_link": metadata.get("image_link", "https://img.freepik.com/premium-vector/unavailable-movie-icon-no-video-bad-record-symbol_883533-383.jpg?w=360"),
                "category": metadata.get("category", "Uncategorized"),
                "published_date": metadata.get("published_date", "Unknown"),
                "source": metadata.get("source", "Unknown"),
            })
 
        if "sports" not in query:
            query += " sports"
 
        # Query SERP API (Web Search)
        serp_api_url = "https://serpapi.com/search.json"
        params = {
            "engine": "google",
            "q": query,
            "api_key": os.getenv("SERP_API_KEY"),
            "gl": "us",
            "hl": "en"
        }
        serp_response = requests.get(serp_api_url, params=params)
        serp_results = serp_response.json()
 
        #print("SERP API Full Response:", serp_response.json())
 
        # Extract relevant sections from SERP API response
        organic_results = serp_results.get("organic_results", [])
        top_stories = serp_results.get("top_stories", [])
 
        # Combine the results
        web_results = []
 
        for result in organic_results + top_stories:
            title = result.get("title", "Unknown Title")
            link = result.get("link", "")
            snippet = result.get("snippet", "No Description Available.")
            image_link = result.get("thumbnail", "https://t3.ftcdn.net/jpg/05/88/70/78/360_F_588707867_pjpsqF5zUNMV1I2g8a3tQAYqinAxFkQp.jpg")
            source = result.get("source", "Unknown Source")
 
            if title and link and link not in seen_ids:
                web_results.append({
                    "title": title,
                    "description": snippet,
                    "link": link,
                    "image_link": image_link,
                    "source": source,
                    "published_date": result.get("date", "Unknown")
                })
                seen_ids.add(link)
 
        # Return combined results
        return {"rag_results": rag_results, "web_results": web_results}
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
 
@app.get("/all_news")
async def get_all_news():
    try:
       
        search_results = index.query(
            vector=[0] * 384,  
            top_k=100,  
            include_metadata=True
        )
 
        news_feed = []
        seen_ids = set()  # Set to track unique base IDs
 
        for result in search_results.get("matches", []):
            metadata = result.get("metadata", {})
            base_link = result["id"].split("_")[0]  # Extract base ID
 
            if base_link in seen_ids:
                continue  # Skip duplicate entries
            seen_ids.add(base_link)  # Add to the seen set
       
            if {"title", "description", "category"} <= metadata.keys():
                news_feed.append({
                    "title": metadata["title"],
                    "description": metadata["description"],
                    "link": base_link,
                    "image_link": metadata.get("image_link", "https://img.freepik.com/premium-vector/unavailable-movie-icon-no-video-bad-record-symbol_883533-383.jpg?w=360"),
                    "category": metadata["category"],
                    "published_date": metadata.get("published_date", "Unknown"),
                    "source": metadata.get("source", "Unknown"),
                })
 
        # Return results
        return {"news": news_feed}
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
 
@app.post("/forgot_password")
async def forgot_password(request: ForgotPasswordRequest):
    email = request.email
 
    # Log email received
    print(f"Received email for password reset: {email}")
 
    # Check if email exists in Snowflake
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT USERNAME FROM USERS WHERE EMAIL = '{email}'")
    result = cursor.fetchone()
 
    if not result:
        raise HTTPException(status_code=404, detail="Email not found")
       
 
    username = result[0]
 
    # Generate reset token
    reset_token = jwt.encode({"sub": username, "exp": datetime.utcnow() + timedelta(hours=1)}, SECRET_KEY, algorithm=ALGORITHM)
 
    # Generate reset link
    reset_link = f"http://localhost:8501/reset_password?token={reset_token}"
 
    # Send email and handle responses
    if send_reset_email(email, reset_link):
        return {"message": "Password reset email sent successfully."}
    else:
        raise HTTPException(status_code=500, detail="Failed to send reset email.")
 
# Endpoint: Reset Password
@app.post("/reset_password")
async def reset_password(data: PasswordReset):
    try:
        # Decode token
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
 
        if not username:
            raise HTTPException(status_code=400, detail="Invalid token")
 
        # Update password in Snowflake
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE USERS SET PASSWORD = '{data.new_password}' WHERE USERNAME = '{username}'")
        conn.commit()
 
        return {"message": "Password reset successfully."}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset token has expired.")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
 
@app.get("/matches/")
def get_matches(username: str = Query(...)):
    try:
        # Fetch user interests from Snowflake
        user_interests = fetch_user_interests(username)
        if not user_interests:
            raise HTTPException(status_code=404, detail=f"No interests found for user: {username}")
 
        results = {}
        for sport in user_interests:
            sport = sport.lower()
            if sport == "tennis":
                url = "https://api.api-tennis.com/tennis/"
                params = {
                    "method": "get_fixtures",
                    "APIkey": TENNIS_API_KEY,
                    "date_start": datetime.now().strftime("%Y-%m-%d"),
                    "date_stop": datetime.now().strftime("%Y-%m-%d")
                }
                response = requests.get(url, params=params)
                response.raise_for_status()
                results["tennis"] = response.json()
 
            elif sport == "football":
                url = "http://api.football-data.org/v4/matches"
                headers = {"X-Auth-Token": FOOTBALL_API_KEY}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                results["football"] = response.json()
 
            elif sport == "cricket":
                url = "https://api.cricapi.com/v1/matches"
                params = {
                    "apikey": CRICKET_API_KEY,
                    "offset": 0
                }
                response = requests.get(url, params=params)
                response.raise_for_status()
                results["cricket"] = response.json()
 
            elif sport == "basketball":
                url = "https://v1.basketball.api-sports.io/games"
                headers = {
                    'x-rapidapi-host': "v1.basketball.api-sports.io",
                    'x-rapidapi-key': BASKETBALL_API_KEY
                }
                params = {"date": datetime.now().strftime("%Y-%m-%d")}
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                results["basketball"] = response.json()
 
            else:
                results[sport] = {"error": f"{sport} is not a valid sport type"}
       
        return results
 
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error while fetching matches: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
             
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
 
 