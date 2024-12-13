from typing import Dict, Any, List
from youtube import YouTubeAPI
from maps import GoogleMapsAPI
import logging

class Tasks:
    def __init__(self, youtube_api: YouTubeAPI, maps_api: GoogleMapsAPI):
        """Initialize the Tasks class with API clients.

        Args:
            youtube_api (YouTubeAPI): An instance of the YouTubeAPI class.
            maps_api (GoogleMapsAPI): An instance of the GoogleMapsAPI class.
        """
        self.youtube_api = youtube_api
        self.maps_api = maps_api

    async def execute_youtube_task(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Execute the YouTube search task.

        Args:
            query (str): The query to search for videos.
            max_results (int, optional): Number of videos to fetch. Defaults to 5.

        Returns:
            Dict[str, Any]: A dictionary containing YouTube video results.
        """
        videos = self.youtube_api.search_videos(query=query, max_results=max_results)
        return {"videos": [video.dict() for video in videos]}

    async def execute_maps_task(self, query: str, location: str, radius: int = 5000) -> Dict[str, Any]:
        """Execute the Google Maps search task.

        Args:
            query (str): The query to search for locations.
            location (str): The center of the search as "latitude,longitude".
            radius (int, optional): Search radius in meters. Defaults to 5000.

        Returns:
            Dict[str, Any]: A dictionary containing location results.
        """
        locations = self.maps_api.get_location(query=query, location=location, radius=radius)
        return {"locations": [location.dict() for location in locations]}

    async def execute_tasks(self, plan: List[Dict[str, Any]], user_location: str) -> Dict[str, Any]:
        """Execute the tasks based on the provided plan.

        Args:
            plan (List[Dict[str, Any]]): A list of tasks to execute.
            user_location (str): The user's location for map-related tasks.

        Returns:
            Dict[str, Any]: A dictionary containing results from executed tasks.
        """
        results = {
            "youtube": {"videos": []},
            "maps": {"locations": []}
        }

        for task in plan:
            logging.info(f"Executing task: {task}")  # Log the task being executed
            if task["task_name"] == "YouTube" and task["should_execute"]:
                youtube_results = await self.execute_youtube_task(task["search_query"])
                results["youtube"]["videos"].extend(youtube_results["videos"])
            elif task["task_name"] == "Maps" and task["should_execute"]:
                maps_results = await self.execute_maps_task(task["search_query"], user_location)
                results["maps"]["locations"].extend(maps_results["locations"])

        return results
