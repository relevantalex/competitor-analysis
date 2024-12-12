import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import re
import logging
import json
from urllib.parse import urlparse
import openai
from anthropic import Anthropic
from duckduckgo_search import DDGS
import csv
from io import StringIO

# Initialize session state
if 'competitors' not in st.session_state:
    st.session_state.competitors = {}
if 'industries' not in st.session_state:
    st.session_state.industries = None
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 0

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="Venture Studio Competitor Analysis",
    page_icon="🎯",
    layout="wide",
)

# Improved Custom CSS with better UI/UX
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Main theme colors - softer palette */
        :root {
            --background-color: #121212;
            --card-bg: #1E1E1E;
            --text-color: #E0E0E0;
            --accent-color: #E53935;
            --accent-light: #FF5252;
            --accent-dark: #C62828;
            --border-color: #2C2C2C;
            --input-bg: #262626;
        }

        /* Global styles */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            color: var(--text-color);
            background-color: var(--background-color);
        }

        /* Streamlit containers */
        .stApp {
            background-color: var(--background-color);
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-color) !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em !important;
        }

        /* Links with improved contrast */
        a {
            color: var(--accent-light) !important;
            text-decoration: none !important;
            transition: all 0.2s ease !important;
            opacity: 0.9 !important;
        }
        
        a:hover {
            color: var(--accent-light) !important;
            opacity: 1 !important;
            text-decoration: none !important;
        }

        /* Improved competitor cards */
        .competitor-card {
            padding: 28px;
            border-radius: 12px;
            background-color: var(--card-bg);
            margin: 24px 0;
            border-left: 3px solid var(--accent-color);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .competitor-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
        }

        .competitor-card h3 {
            margin-bottom: 16px;
            font-size: 1.3rem;
            color: var(--text-color) !important;
        }

        .competitor-card p {
            margin-bottom: 12px;
            line-height: 1.6;
        }

        /* Enhanced title container */
        .title-container {
            padding: 3rem 0;
            text-align: center;
            background: linear-gradient(135deg, #1E1E1E 0%, var(--accent-dark) 100%);
            color: white;
            border-radius: 0 0 24px 24px;
            margin-bottom: 3rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .title-container h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            letter-spacing: -0.03em;
        }

        .title-container p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        /* Improved form inputs */
        .stTextInput > div > div {
            background-color: var(--input-bg) !important;
            color: var(--text-color) !important;
            border-radius: 8px !important;
            border: 1px solid var(--border-color) !important;
            padding: 8px 12px !important;
            transition: all 0.2s ease !important;
        }

        .stTextInput > div > div:focus-within {
            border-color: var(--accent-color) !important;
            box-shadow: 0 0 0 2px rgba(229, 57, 53, 0.2) !important;
        }

        .stTextArea > div > div {
            background-color: var(--input-bg) !important;
            color: var(--text-color) !important;
            border-radius: 8px !important;
            border: 1px solid var(--border-color) !important;
            padding: 8px 12px !important;
            min-height: 100px !important;
            transition: all 0.2s ease !important;
        }

        .stTextArea > div > div:focus-within {
            border-color: var(--accent-color) !important;
            box-shadow: 0 0 0 2px rgba(229, 57, 53, 0.2) !important;
        }

/* Enhanced buttons */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-dark) 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.6rem 1.5rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
            transition: all 0.2s ease !important;
            text-transform: uppercase !important;
            font-size: 0.9rem !important;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, var(--accent-light) 0%, var(--accent-color) 100%) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(229, 57, 53, 0.2) !important;
        }

        /* Improved tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: var(--background-color);
            padding: 8px 0;
            border-bottom: 1px solid var(--border-color);
        }

        .stTabs [data-baseweb="tab"] {
            background-color: var(--card-bg) !important;
            color: var(--text-color) !important;
            border-radius: 8px !important;
            border: 1px solid var(--border-color) !important;
            padding: 12px 24px !important;
            transition: all 0.2s ease !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            border-color: var(--accent-color) !important;
            background-color: var(--input-bg) !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-dark) 100%) !important;
            color: white !important;
            border: none !important;
        }

        /* Progress bars and spinners */
        .stProgress > div > div > div > div {
            background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-dark) 100%) !important;
        }

        /* Download button */
        .stDownloadButton > button {
            background: linear-gradient(135deg, var(--accent-dark) 0%, var(--accent-color) 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.6rem 1.5rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
            transition: all 0.2s ease !important;
            text-transform: uppercase !important;
            font-size: 0.9rem !important;
        }

        .stDownloadButton > button:hover {
            background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-light) 100%) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(229, 57, 53, 0.2) !important;
        }

        /* Warning messages */
        .stAlert {
            background-color: var(--card-bg) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
        }

        /* Divider */
        hr {
            border-color: var(--border-color) !important;
            margin: 2rem 0 !important;
        }
    </style>
""", unsafe_allow_html=True)

class AIProvider:
    def __init__(self):
        self.provider = st.secrets.get("api_settings", {}).get("ai_provider", "openai")
        
        if self.provider == "openai":
            openai.api_key = st.secrets["api_keys"]["openai_api_key"]
            self.model = "gpt-4-turbo-preview"
        else:
            self.anthropic = Anthropic(api_key=st.secrets["api_keys"]["anthropic_api_key"])
            self.model = "claude-3-opus-20240229"

    def generate_response(self, prompt: str) -> str:
        try:
            if self.provider == "openai":
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a startup and industry analysis expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                return response.choices[0].message.content
            else:
                message = self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.7,
                    system="You are a startup and industry analysis expert.",
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content

        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            raise

@st.cache_data(ttl=3600)
def identify_industries(pitch: str) -> List[str]:
    """Identify potential industries based on the pitch using AI"""
    ai = AIProvider()
    prompt = f"""Based on this pitch: "{pitch}"
    Identify exactly 3 specific, relevant industries or market segments.
    Format your response as a JSON array with exactly 3 strings.
    Make each industry name specific and descriptive.
    Example: ["AI-Powered Security Analytics", "Retail Technology Solutions", "Computer Vision SaaS"]"""

    try:
        response = ai.generate_response(prompt)
        # Clean the response to ensure it's valid JSON
        cleaned_response = response.strip()
        if not cleaned_response.startswith('['):
            cleaned_response = cleaned_response[cleaned_response.find('['):]
        if not cleaned_response.endswith(']'):
            cleaned_response = cleaned_response[:cleaned_response.rfind(']')+1]
        
        industries = json.loads(cleaned_response)
        return industries[:3]
    except Exception as e:
        logger.error(f"Industry identification failed: {str(e)}")
        return ["Technology Solutions", "Software Services", "Digital Innovation"]

def find_competitors(industry: str, pitch: str) -> List[Dict]:
    """Find competitors using AI and web search"""
    ai = AIProvider()
    
    try:
        # First, generate a focused search query
        search_prompt = f"""For a startup in {industry} with this pitch: "{pitch}"
        Create a search query to find direct competitors.
        Return only the search query text, nothing else."""

        search_query = ai.generate_response(search_prompt).strip().strip('"')
        
        # Perform the search
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=10))
            
            # Analyze the results with AI
            analysis_prompt = f"""Analyze these competitors in {industry}:
            {json.dumps(results)}
            
            Identify the top 3 most relevant direct competitors.
            Return a JSON array with exactly 3 companies, each containing:
            {{
                "name": "Company Name",
                "website": "company website",
                "description": "2-sentence description",
                "differentiator": "key unique selling point"
            }}
            
            Return ONLY the JSON array, no other text."""

            competitor_analysis = ai.generate_response(analysis_prompt)
            # Clean the response to ensure it's valid JSON
            cleaned_analysis = competitor_analysis.strip()
            if not cleaned_analysis.startswith('['):
                cleaned_analysis = cleaned_analysis[cleaned_analysis.find('['):]
            if not cleaned_analysis.endswith(']'):
                cleaned_analysis = cleaned_analysis[:cleaned_analysis.rfind(']')+1]
            
            competitors = json.loads(cleaned_analysis)
            
            # Clean URLs
            for comp in competitors:
                if comp.get('website'):
                    parsed_url = urlparse(comp['website'])
                    domain = parsed_url.netloc if parsed_url.netloc else parsed_url.path
                    if not domain.startswith('www.'):
                        domain = f"www.{domain}"
                    comp['website'] = f"https://{domain}"
            
            return competitors[:3]
            
    except Exception as e:
        logger.error(f"Competitor search failed: {str(e)}")
        st.error(f"Error finding competitors: {str(e)}")
        return []

def export_results(startup_name: str):
    """Export analysis results to CSV"""
    if not st.session_state.competitors:
        st.warning("No analysis results to export yet.")
        return
        
    csv_data = []
    headers = ['Industry', 'Competitor', 'Website', 'Description', 'Key Differentiator']
    
    for industry, competitors in st.session_state.competitors.items():
        for comp in competitors:
            csv_data.append([
                industry,
                comp['name'],
                comp['website'],
                comp['description'],
                comp['differentiator']
            ])
    
    # Create CSV string
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(csv_data)
    
    # Create download button
    st.download_button(
        label="📥 Export Analysis",
        data=output.getvalue(),
        file_name=f"{startup_name}_competitor_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv'
    )

def main():
    st.markdown("""
        <div class="title-container">
            <h1>Venture Studio Competitor Analysis</h1>
            <p>Powered by AI for accurate market insights</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Input section
    with st.form("analysis_form"):
        startup_name = st.text_input(
            "Startup Name",
            help="Enter your startup's name"
        )
        
        pitch = st.text_area(
            "One-Sentence Pitch",
            help="Describe what your startup does in one sentence",
            max_chars=200
        )
        
        submitted = st.form_submit_button("Analyze")
    
    if submitted and startup_name and pitch:
        with st.spinner("Analyzing industries..."):
            st.session_state.industries = identify_industries(pitch)
            st.session_state.competitors = {}
            st.rerun()

    # Show analysis if industries are identified
    if st.session_state.industries:
        # Create tabs
        tab_titles = st.session_state.industries
        tabs = st.tabs(tab_titles)
        
        # Handle tab content
        for i, tab in enumerate(tabs):
            with tab:
                industry = st.session_state.industries[i]
                
                # Load competitors if not already loaded
                if industry not in st.session_state.competitors:
                    with st.spinner(f"Analyzing competitors in {industry}..."):
                        competitors = find_competitors(industry, pitch)
                        st.session_state.competitors[industry] = competitors
                
                # Display competitors
                if industry in st.session_state.competitors:
                    for comp in st.session_state.competitors[industry]:
                        st.markdown(f"""
                        <div class="competitor-card">
                            <h3>{comp['name']}</h3>
                            <p><strong>Website:</strong> <a href="{comp['website']}" target="_blank">{comp['website']}</a></p>
                            <p><strong>Description:</strong> {comp['description']}</p>
                            <p><strong>Key Differentiator:</strong> {comp['differentiator']}</p>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Show export button if we have results
        if st.session_state.competitors:
            st.markdown("---")
            export_results(startup_name)

if __name__ == "__main__":
    main()
