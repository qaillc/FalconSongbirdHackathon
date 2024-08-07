import streamlit as st
from dotenv import load_dotenv
import os

# Set the page configuration to wide layout
# st.set_page_config(layout="wide")

# Load environment variables from .env file
load_dotenv()

def get_ai71_api_key():
    return os.getenv("AI71_API_KEY")
