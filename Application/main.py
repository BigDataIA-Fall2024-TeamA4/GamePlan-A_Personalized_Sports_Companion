from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
import snowflake.connector
import os
from dotenv import load_dotenv

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

        # Check if username and password are correct
        cursor.execute(f"SELECT FIRST_NAME FROM USERS WHERE USERNAME = '{user.username}' AND PASSWORD = '{user.password}'")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            # Generate JWT Token
            access_token = create_access_token(data={"sub": user.username})
            return {"access_token": access_token, "token_type": "bearer", "first_name": result[0]}
        else:
            raise HTTPException(status_code=400, detail="Invalid username or password!")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

# Example protected endpoint
@app.get("/protected-endpoint")
async def protected_endpoint(token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    return {"message": f"Hello, {username}. This is a protected endpoint!"}
