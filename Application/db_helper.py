import json
import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Snowflake connection details
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE')
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE')
SNOWFLAKE_SCHEMA = os.getenv('SNOWFLAKE_SCHEMA')

def get_snowflake_connection():
    return snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA
    )

def fetch_user_profile(username):
    """Fetch user interests and expertise level from Snowflake."""
    conn = get_snowflake_connection()
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT interests, expertise_level
        FROM users
        WHERE username = '{username}'
        """
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            # Parse the JSON array (interests)
            interests_json = result[0]  # JSON array as string
            interests = json.loads(interests_json)  # Convert JSON string to Python list
            expertise_level = result[1]
            return interests, expertise_level
        else:
            return None, None
    finally:
        conn.close()
