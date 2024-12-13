import streamlit as st
import requests
from dotenv import load_dotenv
import os
import json
from datetime import datetime
 
# Load environment variables
load_dotenv()
 
# Fetch the FastAPI URL from environment variables
FASTAPI_URL = os.getenv('FASTAPI_URL')
 
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
 
st.set_page_config(layout="wide")
 
if "interests" not in st.session_state:
    st.session_state.interests = []
 
if "expertise_level" not in st.session_state:
    st.session_state.expertise_level = "Beginner"  # Set a default value
 
if "username" not in st.session_state:
    st.session_state["username"] = None
 
preferences_response = requests.get(
    f"{FASTAPI_URL}/get_preferences", params={"username": st.session_state['username']}
)

if st.session_state.get("username"):
    preferences_response = requests.get(
        f"{FASTAPI_URL}/get_preferences", params={"username": st.session_state['username']}
    )
    if preferences_response.status_code == 200:
        st.session_state['preferences'] = preferences_response.json().get('preferences', {})
    else:
        st.session_state['preferences'] = {}
else:
    st.session_state['preferences'] = {}

if not st.session_state.get('username'):
    st.info(" Please Signup or Login!")

if "personalized_feed" not in st.session_state:
    response = requests.post(f"{FASTAPI_URL}/personalized_news", json={
        "interests": st.session_state["interests"]
    })
    if response.status_code == 200:
        st.session_state["personalized_feed"] = response.json().get("news", [])
    else:
        st.error("Failed to fetch personalized news.")


# Function to create a sign-up form
def sign_up():
    ''' Sign up form with validations '''
    with st.form(key='signup', clear_on_submit=True):
        st.subheader('Sign Up')
        email = st.text_input('Email', placeholder='Enter Your Email!')
        username = st.text_input('Username', placeholder='Enter Your Username!')
        password1 = st.text_input('Password', placeholder='Enter Your Password!', type='password')
        password2 = st.text_input('Confirm Password', placeholder='Confirm Your Password!', type='password')
       
        first_name = st.text_input('First Name', placeholder='Enter Your First Name!')
        last_name = st.text_input('Last Name', placeholder='Enter Your Last Name!')
       
        interests = st.multiselect(
            'Interests',
            options=["Soccer", "Basketball", "Cricket", "Tennis", "American Football"],
            help="Select one or more sports interests!"
        )
        interests_json = json.dumps(interests)
 
        selected_expertise = st.select_slider(
            'Select Expertise Level',
            options= ("Beginner", "Intermediate", "Advanced", "Professional"),
            help="Select your expertise level."
        )
 
        submit_button = st.form_submit_button('Sign Up')
 
        if submit_button:
            if not (any(c.isupper() for c in password1) and
                    any(c.isdigit() for c in password1) and
                    any(c in "!@#$%^&*()_+" for c in password1) and
                    len(password1) >= 8):
                st.error("Password should contain at least 1 uppercase letter, 1 special character, 1 numerical character, and be at least 8 characters long!")
            elif password1 != password2:
                st.error("Password and Confirm Password do not match!")
            else:
                data = {
                    "email": email,
                    "username": username,
                    "password": password1,
                    "first_name": first_name,
                    "last_name": last_name,
                    "interests": interests_json,
                    "expertise_level": selected_expertise
                }
               
                response = requests.post(f"{FASTAPI_URL}/register", json=data)
               
                if response.status_code == 200:
                    # Automatically log in the user after successful registration
                    login_data = {
                        "username": username,
                        "password": password1
                    }
                    login_response = requests.post(f"{FASTAPI_URL}/login", json=login_data)
                   
                    if login_response.status_code == 200:
                        user_data = login_response.json()
                        st.session_state["access_token"] = user_data.get("access_token")
                        st.session_state["first_name"] = user_data.get("first_name")
                        st.session_state["email"] = user_data.get("email")
                        st.session_state["username"] = username
                        st.session_state["password"] = password1
                        st.session_state["interests"] = user_data.get("interests")
                        st.session_state["expertise_level"] = user_data.get("expertise_level")
                        st.success("Registration successful!")
                        st.rerun()
                else:
                    st.error("Username already exists!")
 
# Function for login
def login():
    with st.form(key="login_form"):
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
 
        if submit_button:
            response = requests.post(f"{FASTAPI_URL}/login", json={"username": username, "password": password})
 
            if response.status_code == 200:
                user_data = response.json()
               
                # Store session state
                st.session_state["logged_in"] = True
                st.session_state["first_name"] = user_data["first_name"]
                st.session_state["email"] = user_data["email"]
                st.session_state["username"] = username
                st.session_state["personalized_feed"] = user_data["personalized_feed"]
                st.session_state["interests"] = user_data["interests"]  # Correct session assignment
 
                st.success(f"Welcome back, {user_data['first_name']}!")
                st.rerun()  # Reload the main page
            else:
                st.error("Invalid username or password!")
 
# Navigation menu for login/signup
def menu_login():
    ''' Navigation menu for login/signup '''
    st.title("GamePlan : A Personalized Sports Companion")
   
    # Horizontal menu for navigation
    menu_option = st.selectbox(
        "Select Option",
        ["Login", "Sign Up"],
        index=0,
        help="Select between Login or Sign Up to proceed!"
    )
   
    if menu_option == "Sign Up":
        sign_up()
    elif menu_option == "Login":
        login()
 
def update_password(username, new_password):
    response = requests.put(f"{FASTAPI_URL}/update_password", json={
        "username": username,
        "new_password": new_password
    })
    if response.status_code != 200:
        st.sidebar.error("Failed to update password. Please try again.")
 
def update_interests(username, interests_json):
    response = requests.put(f"{FASTAPI_URL}/update_interests", json={
        "username": username,
        "interests": interests_json
    })
    if response.status_code != 200:
        st.sidebar.error("Failed to update interests. Please try again.")
 
def update_expertise(username, expertise_level):
    response = requests.put(f"{FASTAPI_URL}/update_expertise", json={
        "username": username,
        "expertise_level": expertise_level
    })
    if response.status_code != 200:
        st.sidebar.error("Failed to update expertise level. Please try again.")
 
def logout():
    st.session_state.clear()  
    st.rerun()
   
def update_profile():
    st.sidebar.subheader("Update Profile")
   
    if st.sidebar.button("Logout"):
        logout()
 
    # Display email (non-editable)
    st.sidebar.text(f"Email: {st.session_state.get('email', 'N/A')}")
 
    # Initialize default session state variables if not present
    st.session_state.setdefault("password", "")
    st.session_state.setdefault("interests", [])
    st.session_state.setdefault("expertise_level", "Beginner")
   
    # Update password
    new_password = st.sidebar.text_input("New Password", type="password")
    confirm_password = st.sidebar.text_input("Confirm New Password", type="password")
   
    # Update interests
    interests = st.sidebar.multiselect(
        'Update Interests',
        options=["Basketball", "Cricket", "Tennis", "Football"],
        default=st.session_state["interests"],
        help="Select one or more sports interests!"
    )
   
    # Add expertise level update
    expertise_level = st.sidebar.select_slider(
        'Update Expertise Level',
        options=["Beginner", "Intermediate", "Advanced", "Professional"],
        value=st.session_state["expertise_level"],
        help="Select your expertise level."
    )
   
    if st.sidebar.button("Update Profile"):
        password_updated = False
        interests_updated = False
        expertise_updated = False
 
        # Handle password update if new password is entered
        if new_password:
            if new_password == st.session_state["password"]:
                st.sidebar.error("New password must be different from the current password.")
            elif new_password != confirm_password:
                st.sidebar.error("New password and confirmation do not match.")
            elif not (any(c.isupper() for c in new_password) and
                      any(c.isdigit() for c in new_password) and
                      any(c in "!@#$%^&*()_+" for c in new_password) and
                      len(new_password) >= 8):
                st.sidebar.error("Password should contain at least 1 uppercase letter, 1 special character, 1 numerical character, and be at least 8 characters long!")
            else:
                update_password(st.session_state["username"], new_password)
                st.session_state["password"] = new_password
                password_updated = True
 
        # Handle interests update if interests have changed
        current_interests = set(st.session_state["interests"])
        new_interests = set(interests)
        if current_interests != new_interests:
            interests_json = json.dumps(list(new_interests))
            update_interests(st.session_state["username"], interests_json)
            st.session_state["interests"] = list(new_interests)
            interests_updated = True
           
            # Call the personalized news function to refresh the news feed
            response = requests.post(f"{FASTAPI_URL}/personalized_news", json={"interests": list(new_interests)})
            if response.status_code == 200:
                st.session_state["personalized_feed"] = response.json().get("news", [])
                st.sidebar.success("Interests updated and personalized news refreshed!")
            else:
                st.sidebar.error("Failed to refresh personalized news.")
 
        # Handle expertise level update if changed
        if expertise_level != st.session_state["expertise_level"]:
            update_expertise(st.session_state["username"], expertise_level)
            st.session_state["expertise_level"] = expertise_level
            expertise_updated = True
       
        # Show success messages based on what was updated
        if password_updated:
            st.sidebar.success("Password updated successfully!")
        if interests_updated:
            st.sidebar.success("Interests updated successfully!")
        if expertise_updated:
            st.sidebar.success("Expertise level updated successfully!")
 
        if not (password_updated or interests_updated or expertise_updated):
            st.sidebar.warning("No changes were made.")
 
def display_search_results(search_response):
    rag_results = search_response.get("rag_results", [])
    web_results = search_response.get("web_results", [])
 
    if rag_results:
        display_news(rag_results, "Top Results:","search")
    else:
        st.info("No relevant results found from RAG (Pinecone).")
 
    if web_results:
        display_news(web_results, "Results Retrieved from Web Search:","web")
    else:
        st.info("No relevant results found from Web Search.")
 
def update_preference(news_id, preference):
    response = requests.post(
        f"{FASTAPI_URL}/like_news",
        json={
            "username": st.session_state["username"],
            "news_id": news_id,
            "preference": preference,
        }
    )

    if response.status_code == 200:
        # Update session state after successful update
        st.session_state['preferences'][news_id] = preference
        #st.success("Your preference has been saved!")

        # Refresh personalized feed
        response = requests.post(f"{FASTAPI_URL}/personalized_news", json={
            "interests": st.session_state["interests"]
        })
        if response.status_code == 200:
            st.session_state["personalized_feed"] = response.json().get("news", [])
        else:
            st.error("Failed to refresh personalized news.")
    else:
        st.error("Failed to update preference.")
 
def display_news(news_feed, title,tab_key):
    st.subheader(title)
 
    # Validate news_feed format
    if isinstance(news_feed, dict):
        news_feed = news_feed.get("news", [])
 
    if not isinstance(news_feed, list):
        st.error("News feed is not in the expected format.")
        return
 
    # Create a grid layout with 4 columns
    num_articles = len(news_feed)
    cols_per_row = 4
   
    for idx in range(0, num_articles, cols_per_row):
        cols = st.columns(cols_per_row)
 
        # Populate articles in each column
        for col, article in zip(cols, news_feed[idx:idx+cols_per_row]):
            if isinstance(article, dict):  
                news_id = article.get("link", "unknown")  # Use 'link' as the unique ID
                current_preference = st.session_state['preferences'].get(news_id, -1)
               
                default_image = "https://img.freepik.com/premium-vector/unavailable-movie-icon-no-video-bad-record-symbol_883533-383.jpg?w=360"
                image_link = article.get('image_link') or default_image
               
                if not image_link.startswith("http"):  # Ensure it's a valid link
                    image_link = default_image
 
                with col:
                    # News Content
                    st.markdown(
                        f"""
                        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 10px; background-color: #f9f9f9; height: 450px; width: 330px; overflow: hidden; margin: 10px;">
                            <img src="{image_link}" alt="{article.get('title', 'Image')}" style="width:100%; height:200px; object-fit:cover; border-radius: 8px;" />
                            <h4 style="margin-top:10px; height: 70px; overflow: hidden; text-overflow: ellipsis;">
                                <a href="{article.get('link', '#')}" target="_blank" style="color: #0056b3; text-decoration: none;">
                                    {article.get('title', 'Untitled')}
                                </a>
                            </h4>
                            <p style="color: black; font-size: 14px; line-height: 1.6; height: 70px; overflow: hidden; text-overflow: ellipsis;">
                                {article.get('description', 'No description available.')}
                            </p>
                            <div style="margin-top: 10px; font-size: 12px; color: #0056b3; font-weight: bold;">
                                Category: {article.get('category', 'Uncategorized')}
                            </div>
                            <small style="color: gray;">
                                Published: {article.get('published_date', 'Unknown')} | Source: {article.get('source', 'Unknown')}
                            </small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
 
                    # Like/Dislike Buttons with Dynamic Highlight
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("👍", key=f"{tab_key}_like_{news_id}_{idx}", help="Like", disabled=(current_preference == 1)):
                            update_preference(news_id, 1)
        
                    with col2:
                        if st.button("👎", key=f"{tab_key}_dislike_{news_id}_{idx}", help="Dislike", disabled=(current_preference == 0)):
                            update_preference(news_id, 0)
  
def fetch_sport_data():
    """Fetch fixtures for the user's interests."""
    try:
        response = requests.get(f"{FASTAPI_URL}/matches/?username={st.session_state['username']}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch sports data")
            return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

from datetime import datetime

def display_fixtures(data, selected_sport):
    st.sidebar.subheader("Fixtures Filter Options")

    # Filter options
    filter_options = ["All", "Latest Update", "Completed", "Upcoming"]
    selected_filter = st.sidebar.radio("Select Filter:", filter_options, index=0)

    st.subheader(f"{selected_sport.capitalize()} Matches")

    if "error" in data:
        st.warning(data["error"])
    else:
        cols = st.columns(3)  # Adjust number of columns for layout
        matches = []

        # Parse matches based on selected sport
        if selected_sport == "football":
            matches = data.get("matches", [])
        elif selected_sport == "basketball":
            matches = data.get("response", [])
        elif selected_sport == "tennis":
            matches = data.get("results", [])
        elif selected_sport == "cricket":
            matches = data.get("data", [])

        if not matches:
            st.write(f"No {selected_sport.capitalize()} matches found.")
            return

        # Helper function to parse dates
        def parse_date(match, key="utcDate"):
            date_str = match.get(key, match.get("date", match.get("event_date", "Unknown")))
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                return datetime.min

        # Filter matches based on selected filter
        def filter_matches(match):
            status = match.get("status", "")
            if isinstance(status, dict):
                status = status.get("long", "").lower()
            else:
                status = str(status).lower()
            if selected_filter == "Latest Update":
                return status in ["live", "in progress"]
            elif selected_filter == "Completed":
                return status in ["game finished", "completed", "ended"]
            elif selected_filter == "Upcoming":
                return status in ["not started", "timed"]
            elif selected_filter == "All":
                return True
            return False

        # Sort and filter matches
        matches = [match for match in matches if filter_matches(match)]
        matches = sorted(matches, key=lambda match: parse_date(match), reverse=False)  # Change `reverse` as needed

        if not matches:
            st.write(f"No {selected_sport.capitalize()} matches found for the selected filter.")
            return

        for i, match in enumerate(matches):
            with cols[i % len(cols)]:
                with st.container():
                    # Extract team and match details
                    if selected_sport == "football":
                        home_team = match.get("homeTeam", {}).get("name", "Unknown")
                        away_team = match.get("awayTeam", {}).get("name", "Unknown")
                        home_logo = match.get("homeTeam", {}).get("crest", "")
                        away_logo = match.get("awayTeam", {}).get("crest", "")
                        match_date = parse_date(match).strftime("%Y-%m-%d %H:%M")
                        competition = match.get("competition", {}).get("name", "Unknown")
                        status = match.get("status", "Scheduled")
                        if isinstance(status, dict):
                            match_status = status.get("long", "Scheduled")
                        else:
                            match_status = str(status).capitalize()

                    elif selected_sport == "basketball":
                        home_team = match.get("teams", {}).get("home", {}).get("name", "Unknown")
                        away_team = match.get("teams", {}).get("away", {}).get("name", "Unknown")
                        home_logo = match.get("teams", {}).get("home", {}).get("logo", "")
                        away_logo = match.get("teams", {}).get("away", {}).get("logo", "")
                        home_score = match.get("scores", {}).get("home", {}).get("total", "-")
                        away_score = match.get("scores", {}).get("away", {}).get("total", "-")
                        match_date = match.get("date", "Unknown")
                        match_status = match.get("status", {}).get("long", "Unknown")

                    elif selected_sport == "tennis":
                        home_team = match.get("player1", {}).get("name", "Unknown")
                        away_team = match.get("player2", {}).get("name", "Unknown")
                        home_logo = match.get("event_first_player_logo", "")
                        away_logo = match.get("event_second_player_logo", "")
                        match_date = parse_date(match, "event_date").strftime("%Y-%m-%d %H:%M")
                        tournament = match.get("tournament", {}).get("name", "Unknown")
                        surface = match.get("tournament", {}).get("surface", "Unknown")

                    elif selected_sport == "cricket":
                        home_team, away_team = match.get("teams", ["Unknown", "Unknown"])
                        home_logo, away_logo = "", ""  # Cricket API might not have team logos
                        match_date = match.get("date", "Unknown")
                        venue = match.get("venue", "Unknown")
                        match_type = match.get("matchType", "Unknown")
                        match_status = match.get("status", "Unknown")

                    # Default logo
                    default_logo = "https://cdn-icons-png.flaticon.com/512/6855/6855128.png"
                    home_logo = home_logo if home_logo.startswith("http") else default_logo
                    away_logo = away_logo if away_logo.startswith("http") else default_logo

                    # Render match details
                    st.markdown(
                        f"""
                        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; background-color: #fff;">
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                                <div style="text-align: center;">
                                    <img src="{home_logo}" alt="{home_team}" style="height: 80px; width: 80px; border-radius: 5px;" />
                                    <p style="margin: 5px 0; font-weight: bold;">{home_team}</p>
                                </div>
                                <div style="font-size: 20px; font-weight: bold;">vs</div>
                                <div style="text-align: center;">
                                    <img src="{away_logo}" alt="{away_team}" style="height: 80px; width: 80px; border-radius: 5px;" />
                                    <p style="margin: 5px 0; font-weight: bold;">{away_team}</p>
                                </div>
                            </div>
                            <div style="text-align: center; color: #666;">
                                <p><b>Date:</b> {match_date}</p>
                                <p><b>Status:</b> {match_status}</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# Main page after login
def main_page():
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.title("GamePlan: Personalized Sports News")
        login()
        return
   
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            background-color: #f9f9f9 !important;
        }
   
        /* General text elements */
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
        [data-testid="stSidebar"] .stTextInput label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] .stSlider label,
        [data-testid="stSidebar"] .stSlider p {
            color: black !important;
        }
   
        /* Input fields */
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] .stTextInput input[type="text"],
        [data-testid="stSidebar"] .stTextInput input[type="email"] {
            color: black !important;
            background-color: white !important;
        }
   
        /* Slider specific styles */
        [data-testid="stSidebar"] .stSlider [data-testid="stThumbValue"] {
            color: black !important;
        }
   
        [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div {
            color: black !important;
        }
   
        /* Email field highlight */
        [data-testid="stSidebar"] .stTextInput input {
            border: 2px solid #4CAF50 !important;
            border-radius: 4px !important;
            padding: 4px 8px !important;
        }
   
        /* Ensure all text elements in sidebar are black */
        [data-testid="stSidebar"] * {
            color: black !important;
        }
 
        div[data-testid="stHorizontalBlock"] button {
            font-size: 24px; /* Increase font size */
            font-weight: bold; /* Make text bold */
            color: red; /* Change text color */
            padding: 10px 20px; /* Add padding for spacing */
        }

        div[data-testid="stHorizontalBlock"] button[data-selected="true"] {
            font-size: 28px; /* Larger font size for active tab */
            font-weight: bold;
            color: white; /* Change active text color */
            background-color: red; /* Highlight active tab */
            border-radius: 10px; /* Rounded corners for active tab */
        }

        div[data-testid="stHorizontalBlock"] button:hover {
            color: white;
            background-color: red; /* Match hover styling */
            border-radius: 10px; /* Rounded corners on hover */
        }
 
        </style>
        """,
        unsafe_allow_html=True
        )
 
    update_profile()
 
    st.markdown(
        """
        <style>
        body, .stApp {
            background-color: #E6E6FA;
            color: black;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
 
    tabs = st.tabs(["Personalized News","Feed", "Fixtures", "Skill Upgrades"])
 
    with tabs[1]:
        # Search input field
        search_query = st.text_input("Search for news by title or description:", placeholder="Enter keywords or phrases...")
   
        if search_query:
            # Query the FastAPI /search_news endpoint
            response = requests.post(f"{FASTAPI_URL}/search_news", json={"query": search_query})
           
            if response.status_code == 200:
                search_results = response.json()
                display_search_results(search_results)
            else:
                st.error("Failed to fetch search results. Please try again later.")
        else:
            # Fetch all news if no search query is provided
            if "all_news" not in st.session_state:
                response = requests.get(f"{FASTAPI_URL}/all_news")
                if response.status_code == 200:
                    try:
                        all_news = response.json()
                        st.session_state["all_news"] = all_news  # Cache the news articles
                        display_news(st.session_state["all_news"], "All News","all_news")
                    except Exception as e:
                        st.error(f"Error parsing news data: {e}")
                else:
                    st.error("Failed to fetch today's news. Please try again later.")
            else:
                display_news(st.session_state["all_news"], "All News","all_news")
 
 
    with tabs[0]:
        try:
            # Fetch user interests from FastAPI (already in session state)
            user_interests = st.session_state.get("interests", [])
            #st.write("Interests in session state:", st.session_state.get("interests"))
            if not user_interests:
                st.warning("No interests found. Please update your profile to select interests.")
                return
 
            # Query Pinecone for personalized news
            response = requests.post(f"{FASTAPI_URL}/personalized_news", json={"interests": user_interests})
            if response.status_code == 200:
                personalized_news = response.json()
                display_news(personalized_news, "Personalized News","personalized")
            else:
                st.error("Failed to fetch personalized news. Please try again later.")
        except Exception as e:
            st.error(f"Error fetching personalized news: {e}")
   
    with tabs[2]:
        fixtures_data = fetch_sport_data()
        if fixtures_data:
            selected_sport = st.selectbox("Select a sport", list(fixtures_data.keys()))
            data = fixtures_data[selected_sport]
            display_fixtures(data, selected_sport)
  
# Main navigation
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    main_page()  # Show the homepage with tabs if the user is logged in
else:
    menu_login()
 