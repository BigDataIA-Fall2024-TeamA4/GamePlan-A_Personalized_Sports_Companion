import streamlit as st
import requests
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Fetch the FastAPI URL from environment variables
FASTAPI_URL = os.getenv('FASTAPI_URL')

if "interests" not in st.session_state:
    st.session_state.interests = []

if "expertise_level" not in st.session_state:
    st.session_state.expertise_level = "Beginner"  # Set a default value

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
                st.success(f"Welcome back, {user_data['first_name']}!")

                # Store session variables
                st.session_state["logged_in"] = True
                st.session_state["first_name"] = user_data["first_name"]
                st.session_state["email"] = user_data["email"]
                st.session_state["username"] = username
                st.session_state["personalized_feed"] = user_data["personalized_feed"]

                # Redirect to the main page
                st.rerun()  # Forces the app to refresh and load the main page
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

def update_profile():
    st.sidebar.subheader("Update Profile")
    
    # Display email (non-editable)
    st.sidebar.text(f"Email: {st.session_state['email']}")
    
    # Update password
    new_password = st.sidebar.text_input("New Password", type="password")
    confirm_password = st.sidebar.text_input("Confirm New Password", type="password")
    
    # Update interests
    interests = st.sidebar.multiselect(
        'Update Interests',
        options=["Basketball", "Cricket", "Tennis", "Football"],
        default=st.session_state.interests,
        help="Select one or more sports interests!"
    )
    
    # Add expertise level update
    expertise_level = st.sidebar.select_slider(
        'Update Expertise Level',
        options=["Beginner", "Intermediate", "Advanced", "Professional"],
        value=st.session_state.expertise_level,
        help="Select your expertise level."
    )
    
    if st.sidebar.button("Update Profile"):
        password_updated = False
        interests_updated = False
        expertise_updated = False
        
        # Handle password update if new password is entered
        if new_password:
            if new_password == st.session_state['password']:
                st.sidebar.error("New password must be different from the current password.")
            elif new_password != confirm_password:
                st.sidebar.error("New password and confirmation do not match.")
            elif not (any(c.isupper() for c in new_password) and 
                      any(c.isdigit() for c in new_password) and 
                      any(c in "!@#$%^&*()_+" for c in new_password) and 
                      len(new_password) >= 8):
                st.sidebar.error("Password should contain at least 1 uppercase letter, 1 special character, 1 numerical character, and be at least 8 characters long!")
            else:
                update_password(st.session_state['username'], new_password)
                st.session_state['password'] = new_password
                password_updated = True

        # Handle interests update if interests have changed
        current_interests = set(st.session_state['interests'] if isinstance(st.session_state['interests'], list) else json.loads(st.session_state['interests']))
        new_interests = set(interests)
        if current_interests != new_interests:
            interests_json = json.dumps(list(new_interests))
            update_interests(st.session_state['username'], interests_json)
            st.session_state['interests'] = interests_json  # Store as JSON string
            interests_updated = True
            # Refresh the feed after updating interests
            login_response = requests.post(f"{FASTAPI_URL}/login", 
                                           json={"username": st.session_state['username'], 
                                                 "password": st.session_state['password']})
            if login_response.status_code == 200:
                st.session_state["personalized_feed"] = login_response.json()["personalized_feed"]
                st.rerun()
            
        # Handle expertise level update if changed
        if expertise_level != st.session_state['expertise_level']:
            update_expertise(st.session_state['username'], expertise_level)
            st.session_state['expertise_level'] = expertise_level
            expertise_updated = True
        
        # Show success messages based on what was updated
        if password_updated and interests_updated and expertise_updated:
            st.sidebar.success("Profile updated successfully!")
        elif password_updated and interests_updated:
            st.sidebar.success("Password and interests updated successfully!")
        elif password_updated and expertise_updated:
            st.sidebar.success("Password and expertise level updated successfully!")
        elif interests_updated and expertise_updated:
            st.sidebar.success("Interests and expertise level updated successfully!")
        elif password_updated:
            st.sidebar.success("Password updated successfully!")
        elif interests_updated:
            st.sidebar.success("Interests updated successfully!")
        elif expertise_updated:
            st.sidebar.success("Expertise level updated successfully!")

def display_news(news_feed, title):
    st.subheader(title)
    # Check if the news_feed is a dictionary
    if isinstance(news_feed, dict):
        news_feed = news_feed.get("news", [])  # Adjust this key based on the actual data structure

    # Check if it's now a list
    if not isinstance(news_feed, list):
        st.error("News feed is not in the expected format. Please check the API response.")
        return

    # Iterate through the list of news articles
    for article in news_feed:
        if isinstance(article, dict):  # Ensure each article is a dictionary
            st.markdown(
                f"""
                <div style="border: 1px solid #ddd; border-radius: 8px; padding: 10px; margin-bottom: 20px; background-color: #f9f9f9;">
                    <img src="{article.get('image_link', '')}" alt="{article.get('title', 'Image')}" style="width:100%; border-radius: 8px;" />
                    <div style="padding: 10px 0;">
                        <span style="background-color: #0056b3; color: white; padding: 3px 8px; font-size: 12px; border-radius: 3px;">{article.get('category', 'Uncategorized')}</span>
                        <h4><a href="{article.get('link', '#')}" target="_blank" style="color: #0056b3; text-decoration: none;">{article.get('title', 'Untitled')}</a></h4>
                        <p style="color: black;">{article.get('description', 'No description available.')}</p>
                        <small style="color: black;">Published: {article.get('published_date', 'Unknown')} | Source: {article.get('source', 'Unknown')}</small>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning("Invalid article format. Skipping...")

# Main page after login
def main_page():
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.title("GamePlan: Personalized Sports News")
        login()
        return

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

    tabs = st.tabs(["Fixtures", "Feed", "Skill Upgrades"])

    with tabs[1]:
        st.subheader("News Feed")

        # Fetch all news from FastAPI
        if "all_news" not in st.session_state:
            response = requests.get(f"{FASTAPI_URL}/all_news")
            if response.status_code == 200:
                try:
                    all_news = response.json()
                    st.session_state["all_news"] = all_news  # Cache the news articles
                    #st.write("Debug: Response from /all_news", all_news)
                    display_news(st.session_state["all_news"], "All News")
                except Exception as e:
                    st.error(f"Error parsing news data: {e}")
            else:
                st.error("Failed to fetch today's news. Please try again later.")
        else:
            display_news(st.session_state["all_news"], "All News")

# Main navigation
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    main_page()  # Show the homepage with tabs if the user is logged in
else:
    menu_login() 