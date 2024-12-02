import streamlit as st
import requests
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Fetch the FastAPI URL from environment variables
FASTAPI_URL = os.getenv('FASTAPI_URL')

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
        interests_json = json.dumps(interests)  # Convert selected interests to JSON string

        # Expertise Level - Slider
        selected_expertise = st.select_slider(
            'Select Expertise Level',
            options= ("Beginner", "Intermediate", "Advanced", "Professional"),
            help="Select your expertise level."
        )

        submit_button = st.form_submit_button('Sign Up')

        if submit_button:
            # Validate password strength
            if not (any(c.isupper() for c in password1) and 
                    any(c.isdigit() for c in password1) and 
                    any(c in "!@#$%^&*()_+" for c in password1) and 
                    len(password1) >= 8):
                st.error("Password should contain at least 1 uppercase letter, 1 special character, 1 numerical character, and be at least 8 characters long!")
            elif password1 != password2:
                st.error("Password and Confirm Password do not match!")
            else:
                # Send data to FastAPI to store in Snowflake DB
                data = {
                    "email": email,
                    "username": username,
                    "password": password1,
                    "first_name": first_name,
                    "last_name": last_name,
                    "interests": interests_json,  # Pass the JSON string of interests
                    "expertise_level": selected_expertise  # Pass the selected expertise level
                }
                
                # Make the POST request to FastAPI
                response = requests.post(f"{FASTAPI_URL}/register", json=data)
                
                if response.status_code == 200:
                    st.success("Registration successful!")
                else:
                    st.error("Username already exists!")

# Function for login
def login():
    ''' Login form '''
    with st.form(key='login', clear_on_submit=True):
        st.subheader('Login')
        username = st.text_input('Username', placeholder='Enter Your Username!')
        password = st.text_input('Password', placeholder='Enter Your Password!', type='password')
        
        submit_button = st.form_submit_button('Login')
        
        if submit_button:
            # Send data to FastAPI to validate credentials
            data = {
                "username": username,
                "password": password
            }
            
            response = requests.post(f"{FASTAPI_URL}/login", json=data)
            
            if response.status_code == 200:
                user_data = response.json()  # Assuming FastAPI returns user data (e.g., first_name)
                st.session_state["access_token"] = user_data.get("access_token")
                st.session_state["first_name"] = user_data.get("first_name")
                st.success("Login successful!")
                st.rerun()  # Redirect to main page
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

# Main page after login
def main_page():
    ''' Main page layout '''
    col1, col2, col3 = st.columns([1, 2, 1])  # Adjust column widths to center the logo
    with col2:
        st.image("logo.png", width=200)
    tabs = st.tabs(["Fixtures", "Feed", "Skill Upgrades"])
    
    with tabs[0]:
        st.write("Fixtures Content Here")
    
    with tabs[1]:
        st.write("Feed Content Here")
    
    with tabs[2]:
        st.write("Skill Upgrades Content Here")

    # User Profile Section
    with st.sidebar:
        with st.expander(f"Hello {st.session_state['first_name']}"):
            if st.button("Logout"):
                st.session_state.clear()
                st.experimental_rerun()

# Main navigation
if "access_token" not in st.session_state:
    menu_login()
else:
    main_page()