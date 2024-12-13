from typing import List
from pydantic import BaseModel
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class YouTubeVideo(BaseModel):
    """Model for YouTube video results."""
    title: str
    video_id: str
    url: str
    thumbnail_url: str
    description: str
    channel_title: str

class YouTubeAPI:
    def __init__(self, api_key: str):
        """Initialize the YouTube API client."""
        self.api_key = api_key
        self.youtube = build("youtube", "v3", developerKey=api_key)

    def search_videos(self, query: str, max_results: int = 5) -> List[YouTubeVideo]:
        """Search for YouTube videos based on a query."""
        try:
            request = self.youtube.search().list(
                q=query,
                part="snippet",
                type="video",
                maxResults=max_results
            )
            response = request.execute()

            videos = []
            for item in response.get("items", []):
                video = YouTubeVideo(
                    title=item["snippet"]["title"],
                    video_id=item["id"]["videoId"],
                    url=f'https://www.youtube.com/watch?v={item["id"]["videoId"]}',  # Constructing the URL
                    thumbnail_url=item["snippet"]["thumbnails"]["medium"]["url"],
                    description=item["snippet"]["description"],
                    channel_title=item["snippet"]["channelTitle"]
                )
                videos.append(video)

            return videos

        except HttpError as e:
            print(f"HTTP error occurred: {e.resp.status} - {e.content}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

