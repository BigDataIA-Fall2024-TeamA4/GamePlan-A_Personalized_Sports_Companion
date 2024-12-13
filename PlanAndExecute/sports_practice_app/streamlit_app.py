import streamlit as st
import requests

# Set the title of the Streamlit app
st.title("Sports Practice App")

# Input field for user interests (multiple selection)
user_interests = st.multiselect("Select your sports interests:", ["Basketball", "Football", "Tennis", "Cricket"])

# Input field for user location
user_location = st.text_input("Enter your location (e.g., 'Boston, MA')")

# Input field for difficulty level
difficulty_level = st.selectbox("Select difficulty level:", ["Beginner", "Intermediate", "Advanced"])

# Function to fetch default videos based on user interests and difficulty level
def fetch_default_videos(interests, level):
    videos = []
    for interest in interests:
        response = requests.get(f"http://localhost:8000/default_videos/{interest.lower()}?level={level.lower()}")
        if response.status_code == 200:
            videos.extend(response.json()["youtube_results"])
        else:
            st.error(f"Error fetching default videos for {interest}.")
    return videos

# Function to fetch nearby facilities based on user interests and location
def fetch_nearby_facilities(interests, location):
    facilities = []
    for interest in interests:
        response = requests.get(f"http://localhost:8000/nearby_facilities/{interest.lower()}?location={location}")
        if response.status_code == 200:
            facilities.extend(response.json()["location_results"])
        else:
            st.error(f"Error fetching facilities for {interest}.")
    return facilities

# Load default videos for the selected sports and difficulty level
if user_interests and difficulty_level:
    default_videos = fetch_default_videos(user_interests, difficulty_level)
    st.subheader(f"Default Videos for {', '.join(user_interests)} at {difficulty_level} Level:")
    if default_videos:
        for video in default_videos:
            # Display the thumbnail and title with a link
            col1, col2 = st.columns([1, 3])  # Create two columns
            with col1:
                st.image(video['thumbnail_url'], width=120)  # Display the thumbnail
            with col2:
                st.write(f"- **Title:** {video['title']}")
                st.write(f"  - **URL:** [Watch here]({video['url']})")
    else:
        st.write("No default videos found.")

# Button to fetch nearby facilities
if st.button("Find Nearby Facilities"):
    if user_location:
        nearby_facilities = fetch_nearby_facilities(user_interests, user_location)
        st.subheader("Nearby Facilities:")
        if nearby_facilities:
            for facility in nearby_facilities:
                st.write(f"- **Name:** {facility['name']}")
                st.write(f"  - **Address:** {facility['address']}")
                st.write(f"  - **Maps Link:** [View on Google Maps]({facility['maps_url']})")  # Display the Maps link
        else:
            st.write("No facilities found.")
    else:
        st.warning("Please enter your location.")

# Button to submit the query for facilities and practice videos
if st.button("Submit Query"):
    # Additional functionality can be added here for future use
    st.warning("This feature is not yet implemented.")