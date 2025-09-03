import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Default model settings
DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 1000

# Web search settings
MAX_SEARCH_RESULTS = 5

# Context memory settings
MAX_CONTEXT_TURNS = 3

# Streamlit app settings
APP_TITLE = "Deal Finder - AI Product Comparison Assistant"
APP_DESCRIPTION = """
Find the best deals on products, compare prices across retailers, and get AI-powered shopping recommendations.
"""
