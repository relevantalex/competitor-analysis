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

# Initialize session state for storing analysis results
if 'competitors' not in st.session_state:
    st.session_state.competitors = {}
if 'selected_industry' not in st.session_state:
    st.session_state.selected_industry = None
if 'industries' not in st.session_state:
    st.session_state.industries = None
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False

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
    layout="wide",
)

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
            height: 60px !important;
            font-size: 16px !important;
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
        
        .title-container {
            padding: 2rem 0;
            text-align: center;
            background: linear-gradient(120deg, #155799, #159957);
            color: white;
            border-radius: 0 0 20px 20px;
            margin-bottom: 2rem;
        }

        .export-button {
            background-color: #1976D2 !important;
        }
    </style>
""", unsafe_allow_html=True)

class AIProvider:
    """AI Provider class to handle different AI services"""
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
            st.error("Failed to generate AI response. Please check your API settings.")
            raise

@st.cache_data(ttl=3600)
def identify_industries(pitch: str) -> List[str]:
    """Identify potential industries based on the pitch using AI"""
    ai = AIProvider()
    prompt = f"""Analyze this startup pitch and identify the 3 most relevant industries: "{pitch}"
    Focus on specific, modern industry categories.
    Return only a JSON array of 3 industry names, no other text.
    Example format: ["FinTech - Payment Processing", "B2B SaaS", "Financial Services"]
    Make industries specific and actionable."""

    try:
        response = ai.generate_response(prompt)
        industries = json.loads(response)
        return industries[:3]
    except Exception as e:
        logger.error(f"Industry identification failed: {str(e)}")
        return ["Technology", "Software", "Digital Services"]

@st.cache_data(ttl=3600)
def find_competitors(industry: str, pitch: str) -> List[Dict]:
    """Find competitors using AI and web search"""
    ai = AIProvider()
    
    search_prompt = f"""Create a precise search query to find direct competitors based on:
    Industry: {industry}
    Pitch: "{pitch}"
    Focus on companies solving similar problems.
    Return only the search query, no other text."""

    try:
        search_query = ai.generate_response(search_prompt)
        
        competitors = []
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=10))
            
            analysis_prompt = f"""Analyze these search results and identify the 3 most relevant direct competitors in {industry}.
            Search results: {json.dumps(results)}
            
            For each competitor provide:
            - Company name (only the actual company name)
            - Website (main company website only)
            - Brief, specific description (max 2 sentences)
            - Key differentiator (one specific unique selling point)
            
            Return as JSON array with keys: name, website, description, differentiator
            Ensure websites are clean, valid URLs."""

            competitor_analysis = ai.generate_response(analysis_prompt)
            competitors = json.loads(competitor_analysis)
            
            # Clean and validate URLs
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
        return []

def export_results(data: Dict, startup_name: str):
    """Export analysis results to CSV"""
    csv_data = []
    headers = ['Industry', 'Competitor', 'Website', 'Description', 'Key Differentiator']
    
    for industry, competitors in data.items():
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
        label="📥 Export Analysis to CSV",
        data=output.getvalue(),
        file_name=f"{startup_name}_competitor_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
        key='export-button',
        help="Download the complete analysis as a CSV file"
    )

def main():
    # Custom title section with gradient background
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
        with st.spinner("Analyzing your startup..."):
            try:
                # Generate industries
                st.session_state.industries = identify_industries(pitch)
                st.session_state.analysis_done = True
                st.session_state.competitors = {}  # Reset competitors
                
                # Rerun to show the tabs
                st.rerun()
                
            except Exception as e:
                logger.error(f"Analysis failed: {str(e)}")
                st.error("An error occurred during analysis. Please check your API settings and try again.")
    
    # Show tabs if analysis is done
    if st.session_state.analysis_done and st.session_state.industries:
        # Create tabs for each industry
        tabs = st.tabs(st.session_state.industries)
        
        # Process the selected tab
        for idx, (tab, industry) in enumerate(zip(tabs, st.session_state.industries)):
            with tab:
                if industry not in st.session_state.competitors:
                    if st.button(f"Analyze {industry} Competitors", key=f"analyze_{idx}"):
                        with st.spinner(f"Finding competitors in {industry}..."):
                            competitors = find_competitors(industry, pitch)
                            st.session_state.competitors[industry] = competitors
                            st.rerun()
                
                # Show competitors if available
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
        
        # Show export button if we have any analysis results
        if st.session_state.competitors:
            st.markdown("---")
            export_results(st.session_state.competitors, startup_name)

if __name__ == "__main__":
    main()
