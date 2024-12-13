import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import os

from youtube import YouTubeAPI
from maps import GoogleMapsAPI
from planner import TaskPlanner

# Load environment variables from .env file
load_dotenv()

# Now you can access your API keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Initialize FastAPI app
app = FastAPI()

# Initialize APIs and Planner
youtube_api = YouTubeAPI(YOUTUBE_API_KEY)
maps_api = GoogleMapsAPI(GOOGLE_MAPS_API_KEY)
task_planner = TaskPlanner()

class QueryRequest(BaseModel):
    query: str
    user_location: Optional[str] = None

class QueryResponse(BaseModel):
    youtube_results: List[Dict[str, str]]
    location_results: List[Dict[str, str]]

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query and return relevant results"""
    try:
        # Log the incoming query
        print(f"Received query: {request.query}")

        # Create a plan based on the user query
        plan = task_planner.create_plan(request.query)
        print(f"Generated Plan: {plan}")  # Debugging line

        youtube_results = []
        location_results = []

        # Execute tasks based on the plan
        for task in plan:
            if task["task_name"] == "YouTube" and task["should_execute"]:
                print(f"Searching YouTube for: {task['search_query']}")  # Debugging line
                youtube_results = youtube_api.search_videos(task["search_query"])
                print(f"YouTube Results: {youtube_results}")  # Debugging line
            elif task["task_name"] == "Maps" and task["should_execute"]:
                print(f"Searching Maps for: {task['search_query']}")  # Debugging line
                location_results = maps_api.get_location(task["search_query"])
                print(f"Location Results: {location_results}")  # Debugging line

        return {
            "youtube_results": [video.dict() for video in youtube_results],
            "location_results": [location.dict() for location in location_results],
        }

    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Log the error
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/default_videos/{user_interest}", response_model=QueryResponse)
async def get_default_videos(user_interest: str, level: str):
    """Get default YouTube videos based on user interest and difficulty level."""
    try:
        # Construct the search query based on interest and level
        search_query = f"{user_interest} tutorials {level}"
        youtube_results = youtube_api.search_videos(search_query)
        
        return {
            "youtube_results": [video.dict() for video in youtube_results],
            "location_results": []  # No location results for this endpoint
        }
    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Log the error
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/nearby_facilities/{user_interest}", response_model=QueryResponse)
async def get_nearby_facilities(user_interest: str, location: str):
    """Get nearby facilities based on user interest and location."""
    try:
        # Construct the search query for facilities
        search_query = f"{user_interest} facilities near {location}"
        location_results = maps_api.get_location(search_query)
        
        return {
            "youtube_results": [],  # No YouTube results for this endpoint
            "location_results": [location.dict() for location in location_results]
        }
    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Log the error
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)