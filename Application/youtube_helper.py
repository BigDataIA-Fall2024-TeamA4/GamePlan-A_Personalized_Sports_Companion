def fetch_youtube_videos(sport, expertise_level, api_key):
    import requests
    search_query = f"{sport} training {expertise_level}"
    url = f"https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": search_query,  # Search for sport-specific training videos
        "type": "video",
        "key": api_key,
        "maxResults": 5,  # Limit to top 5 results
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get("items", [])
        return [
            {
                "title": video["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={video['id']['videoId']}",
            }
            for video in results
        ]
    return []
