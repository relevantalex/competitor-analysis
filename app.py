import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="Venture Studio Competitor Analysis",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

@st.cache_resource
def initialize_nltk():
    """Initialize NLTK resources safely"""
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except Exception as e:
            logger.error(f"Failed to download NLTK data: {e}")
            st.error("Failed to initialize text analysis tools. Please try again later.")
            return False
    return True

# Custom CSS with modern styling
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }
        
        .stButton>button {
            background-color: #4CAF50 !important;
            color: white !important;
            font-family: 'Inter', sans-serif !important;
            border-radius: 8px !important;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
        }
        
        .competitor-card {
            padding: 24px;
            border-radius: 12px;
            background-color: #ffffff;
            margin: 16px 0;
            border-left: 5px solid #4CAF50;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        
        .sentiment-box {
            padding: 24px;
            border-radius: 12px;
            margin: 16px 0;
            background-color: #ffffff;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

def validate_api_key() -> bool:
    """Validate the presence of the Brave API key"""
    if 'brave_api_key' not in st.secrets:
        st.error("Missing Brave API key in secrets.")
        st.info("Add your API key to Streamlit secrets with key 'brave_api_key'")
        return False
    return True

@st.cache_data(ttl=3600)
def brave_search(query: str, time_period: str, api_key: str) -> pd.DataFrame:
    """
    Perform a search using Brave's API with improved error handling
    """
    headers = {
        'X-Subscription-Token': api_key,
        'Accept': 'application/json',
    }
    
    params = {
        'q': query,
        'count': '20',
        'time_range': get_brave_time_range(time_period)
    }
    
    try:
        with st.spinner('Searching for competitor data...'):
            response = requests.get(
                'https://api.search.brave.com/res/v1/web/search',
                headers=headers,
                params=params,
                timeout=10
            )
            
        response.raise_for_status()
        data = response.json()
        
        results = []
        for result in data.get('web', {}).get('results', []):
            results.append({
                'title': result.get('title', ''),
                'description': result.get('description', ''),
                'link': result.get('url', ''),
                'date': datetime.now(),
                'sentiment': get_sentiment(f"{result.get('title', '')} {result.get('description', '')}")
            })
            
        return pd.DataFrame(results)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Brave API request failed: {str(e)}")
        st.error("Failed to fetch competitor data. Please try again later.")
        return pd.DataFrame()

@st.cache_data
def get_sentiment(text: str) -> float:
    """Calculate sentiment score for text"""
    try:
        analysis = TextBlob(clean_text(text))
        return analysis.sentiment.polarity
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {str(e)}")
        return 0.0

def main():
    st.title("Venture Studio Competitor Analysis")
    
    if not validate_api_key() or not initialize_nltk():
        return
    
    # Input section with improved validation
    with st.form("analysis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            startup_name = st.text_input(
                "Startup Name",
                help="Enter your startup's name"
            )
            
        with col2:
            time_period = st.selectbox(
                "Time Period",
                ["Last Month", "Last 3 Months", "Last 6 Months", "Last Year"]
            )
            
        pitch = st.text_area(
            "Pitch or Description",
            help="Enter a brief description of your startup"
        )
        
        submitted = st.form_submit_button("Analyze")
        
    if submitted and startup_name and pitch:
        # Store search in history
        st.session_state.search_history.append({
            'startup': startup_name,
            'timestamp': datetime.now()
        })
        
        # Perform analysis
        try:
            with st.spinner('Analyzing competitors...'):
                df = brave_search(
                    f"{startup_name} {pitch}",
                    time_period,
                    st.secrets["brave_api_key"]
                )
                
                if not df.empty:
                    display_analysis_results(df, startup_name)
                else:
                    st.warning("No competitor data found. Try adjusting your search terms.")
                    
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            st.error("An error occurred during analysis. Please try again.")
            
    # Display search history
    if st.session_state.search_history:
        with st.expander("Recent Searches"):
            for search in reversed(st.session_state.search_history[-5:]):
                st.text(f"{search['startup']} - {search['timestamp'].strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()
