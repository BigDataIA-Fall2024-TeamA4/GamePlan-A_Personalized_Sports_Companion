from typing import List
from pydantic import BaseModel
import requests

class Location(BaseModel):
    """Model for location search results."""
    name: str
    address: str
    maps_url: str

class GoogleMapsAPI:
    def __init__(self, api_key: str):
        """Initialize the Google Maps API client with the provided API key.

        Args:
            api_key (str): Google Maps API key.
        """
        self.api_key = api_key

    def get_location(self, query: str) -> List[Location]:
        """Get locations based on a query.

        Args:
            query (str): Search query (e.g., "basketball facilities near Boston").

        Returns:
            List[Location]: List of location results.
        """
        response = requests.get(
            f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={self.api_key}"
        )

        if response.status_code == 200:
            locations = []
            for result in response.json().get("results", []):
                location = Location(
                    name=result["name"],
                    address=result.get("formatted_address", "Address not available"),
                    maps_url=f"https://www.google.com/maps/place/?q=place_id:{result['place_id']}"
                )
                locations.append(location)
            return locations
        else:
            print(f"Error fetching locations: {response.status_code}")
            return []
