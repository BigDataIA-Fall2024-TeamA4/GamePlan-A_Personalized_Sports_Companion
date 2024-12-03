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
                st.session_state["email"] = user_data.get("email")
                st.session_state["username"] = username
                st.session_state["password"] = password
                st.session_state["interests"] = user_data.get("interests")
                st.session_state["expertise_level"] = user_data.get("expertise_level")
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
        options=["Soccer", "Basketball", "Cricket", "Tennis", "American Football"],
        default=json.loads(st.session_state['interests']),
        help="Select one or more sports interests!"
    )
    
    # Add expertise level update
    expertise_level = st.sidebar.select_slider(
        'Update Expertise Level',
        options=["Beginner", "Intermediate", "Advanced", "Professional"],
        value=st.session_state['expertise_level'],
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
        current_interests = set(json.loads(st.session_state['interests']))
        new_interests = set(interests)
        if current_interests != new_interests:
            interests_json = json.dumps(interests)
            update_interests(st.session_state['username'], interests_json)
            st.session_state['interests'] = interests_json
            interests_updated = True
            
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
                st.rerun()
        
        # Add Profile Update Section
        update_profile()

# Main navigation
if "access_token" not in st.session_state:
    menu_login()
else:
    main_page()