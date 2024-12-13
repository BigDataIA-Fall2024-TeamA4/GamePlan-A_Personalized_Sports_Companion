import requests

def fetch_nearby_facilities(sport, location, api_key):
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{sport} practice facilities",
        "location": location,
        "radius": 5000,  # Radius in meters
        "key": api_key
    }
    response = requests.get(url, params=params).json()
    return [
        {"name": result["name"], "address": result["formatted_address"]}
        for result in response.get("results", [])
    ]
