import streamlit as st
import requests
from dotenv import load_dotenv
import os
import json

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

if preferences_response.status_code == 200:
    st.session_state['preferences'] = preferences_response.json().get('preferences', {})
else:
    st.session_state['preferences'] = {}

if not st.session_state.get('username'):
    st.info(" Please login!")

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
    # Forgot Password Section
    st.markdown("---")
    st.markdown("**Forgot your password?**")
    if st.button("Forgot Password"):
        forgot_password()

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

def forgot_password():
    st.title("Forgot Password")
    
    # Correct text input type
    email = st.text_input("Enter your email", type="default")  
    
    if st.button("Send Reset Link"):
        # Ensure correct payload and endpoint
        payload = {"email": email}
        response = requests.post(f"{FASTAPI_URL}/forgot_password", json=payload)
        
        # Debugging logs
        st.write("Payload Sent:", payload)
        st.write("Response Status Code:", response.status_code)
        
        if response.status_code == 200:
            st.success("Password reset link sent to your email.")
        else:
            st.error(response.json().get("detail", "Error sending reset link."))



def reset_password():
    st.title("Reset Password")
    token = st.experimental_get_query_params().get("token", [""])[0]

    if not token:
        st.error("Invalid or missing reset token.")
        return

    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Reset Password"):
        if new_password != confirm_password:
            st.error("Passwords do not match.")
            return

        response = requests.post(f"{FASTAPI_URL}/reset_password", json={"token": token, "new_password": new_password})
        if response.status_code == 200:
            st.success("Password reset successful! You can now log in with your new password.")
        else:
            st.error(response.json().get("detail", "Failed to reset password."))

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
        display_news(rag_results, "Top Results:")
    else:
        st.info("No relevant results found from RAG (Pinecone).")

    if web_results:
        display_news(web_results, "Results Retrieved from Web Search:")
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
        st.success("Your preference has been saved!")
    else:
        st.error("Failed to update preference.")

def display_news(news_feed, title):
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
                        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; background-color: #f9f9f9; height: 450px; width: 330px; overflow: hidden; margin: 10px;">
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
                        like_style = "background-color: #e0ffe0; border: 2px solid green; color: green; border-radius: 5px;" if current_preference == 1 else ""
                        if st.button(
                            "👍 Like",
                            key=f"like_{news_id}_{title}",
                            help="Click to Like",
                        ):
                            update_preference(news_id, 1)  # Set preference to 'Like'

                    with col2:
                        dislike_style = "background-color: #ffe0e0; border: 2px solid red; color: red; border-radius: 5px;" if current_preference == 0 else ""
                        if st.button(
                            "👎 Dislike",
                            key=f"dislike_{news_id}_{title}",
                            help="Click to Dislike",
                        ):
                            update_preference(news_id, 0)  # Set preference to 'Dislike'

                    # Dynamic Highlighting CSS
                    st.markdown(
                        f"""
                        <style>
                        [key="like_{news_id}"] {{
                            {like_style}
                        }}
                        [key="dislike_{news_id}"] {{
                            {dislike_style}
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )


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

        /* Style the tab headers */
        [data-baseweb="tab"] button {
            font-size: 24px; /* Increase font size */
            font-weight: bold; /* Make text bold */
            color: red !important; /* Change text color to red */
            padding: 10px 20px; /* Add padding for a larger clickable area */
        }

        /* Active tab styling */
        [data-baseweb="tab"].css-1nliwu6 button {
            font-size: 24px; /* Ensure active tab font size matches */
            font-weight: bold;
            color: white !important; /* Change active text color to white */
            background-color: red !important; /* Highlight active tab with red background */
            border-radius: 10px; /* Rounded corners for active tab */
        }

        /* Hover effect for tabs */
        [data-baseweb="tab"] button:hover {
            color: white !important;
            background-color: red !important;
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
            background-color: black;
            color: white;
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
                        display_news(st.session_state["all_news"], "All News")
                    except Exception as e:
                        st.error(f"Error parsing news data: {e}")
                else:
                    st.error("Failed to fetch today's news. Please try again later.")
            else:
                display_news(st.session_state["all_news"], "All News")


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
                display_news(personalized_news, "Personalized News")
            else:
                st.error("Failed to fetch personalized news. Please try again later.")
        except Exception as e:
            st.error(f"Error fetching personalized news: {e}")
    
    with tabs[2]:
        fixtures_data = fetch_sport_data()
        if fixtures_data:
            for sport, data in fixtures_data.items():
                st.subheader(f"{sport.capitalize()} Matches")
                
                if "error" in data:
                    st.warning(data["error"])
                elif sport == "football":
                    matches = data.get("matches",[])
                    if not matches:
                        st.write("No Football matches found.")
                    for match in matches:
                        st.write(match)
                        st.write(f"**{match['homeTeam']['name']}** vs **{match['awayTeam']['name']}**")
                        st.write(f"Competition: {match['competition']['name']}")
                        st.write(f"Date: {match['utcDate']}")
                        st.divider()
                elif sport == "basketball":
                    games = data.get("response", [])
                    if not games:
                        st.write("No Basketball matches found.")
                    for game in games:
                        home_team = game.get("teams", {}).get("home", {}).get("name", "Unknown")
                        away_team = game.get("teams", {}).get("away", {}).get("name", "Unknown")

                        home_score = game.get("scores", {}).get("home", {}).get("total", "N/A")
                        away_score = game.get("scores", {}).get("away", {}).get("total", "N/A")

                        st.write(f"**{home_team}** vs **{away_team}**")
                        st.write(f"Final Score: **{home_score} - {away_score}**")
                        st.write(f"Date: {game.get('date', 'Unknown')} | Status: {game.get('status', {}).get('long', 'Unknown')}")
                        st.divider()
                elif sport == "tennis":
                    results = data.get("results", [])
                    if not results:
                        st.write("No Tennis matches found.")
                    for result in results:
                        st.write(result)
                        st.write(f"**{result['player1']['name']}** vs **{result['player2']['name']}**")
                        st.write(f"Tournament: {result['tournament']['name']} | Surface: {result['tournament']['surface']}")
                        st.write(f"Score: {result.get('score', 'Not available')}")
                        st.divider()
                elif sport == "cricket":
                    matches = data.get("data", [])
                    if not matches:
                        st.write("No Cricket matches found.")
                    for match in matches:
                        team1 = match.get("teams", [None, None])[0]
                        team2 = match.get("teams", [None, None])[1]
                        st.write(f"**{team1}** vs **{team2}**")
                        st.write(f"Venue: {match.get('venue', 'Unknown')} | Match Type: {match.get('matchType', 'Unknown')}")
                        st.write(f"Status: {match.get('status', 'Unknown')} | Date: {match.get('date', 'Unknown')}")
                        st.divider()
                else:
                    st.warning(f"No data available for {sport}.")
        else:
            st.error("Failed to fetch sports data.")

# Main navigation
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    main_page()  # Show the homepage with tabs if the user is logged in
else:
    menu_login() 