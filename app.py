import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import re
import logging
from pathlib import Path
import openai
from anthropic import Anthropic
from duckduckgo_search import DDGS
import json
from urllib.parse import urlparse

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
        
        .header-image {
            margin-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

class AIProvider:
    def __init__(self):
        self.provider = st.secrets["api_settings"]["ai_provider"]
        if self.provider == "openai":
            openai.api_key = st.secrets["api_keys"]["openai_api_key"]
            self.model = st.secrets["model_settings"]["openai_model"]
        else:
            self.anthropic = Anthropic(api_key=st.secrets["api_keys"]["anthropic_api_key"])
            self.model = st.secrets["model_settings"]["anthropic_model"]

    def generate_response(self, prompt: str) -> str:
        try:
            if self.provider == "openai":
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                return response.choices[0].message.content
            else:
                message = self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.7,
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
    prompt = f"""Given this startup pitch: "{pitch}"
    Identify the top 3 most relevant industries for this startup. 
    Consider both traditional industry categories and modern technology sectors.
    Return ONLY a JSON array of 3 industry names, nothing else.
    Example: ["AI Healthcare", "Medical Devices", "Digital Therapeutics"]"""

    try:
        response = ai.generate_response(prompt)
        industries = json.loads(response)
        return industries[:3]  # Ensure we only get 3 industries
    except Exception as e:
        logger.error(f"Industry identification failed: {str(e)}")
        return ["Technology", "Software", "Digital Services"]  # Fallback industries

@st.cache_data(ttl=3600)
def find_competitors(industry: str, pitch: str) -> List[Dict]:
    """Find competitors using AI and web search"""
    ai = AIProvider()
    
    # First, use AI to understand what to search for
    search_prompt = f"""Given this startup pitch: "{pitch}" in the {industry} industry,
    generate a specific search query to find direct competitors.
    Focus on identifying companies solving similar problems.
    Return ONLY the search query, nothing else."""

    try:
        search_query = ai.generate_response(search_prompt)
        
        # Use DuckDuckGo for search (more reliable than Brave for this use case)
        competitors = []
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=10))
            
            # Use AI to analyze search results and identify real competitors
            analysis_prompt = f"""Given these search results for competitors in {industry}:
            {json.dumps(results)}
            
            Identify the top 3 most relevant direct competitors.
            For each competitor, provide:
            1. Company name
            2. Website (extract from the search results)
            3. Brief description of what they do
            4. Key differentiator
            
            Return the response as a JSON array with these exact keys:
            name, website, description, differentiator"""

            competitor_analysis = ai.generate_response(analysis_prompt)
            competitors = json.loads(competitor_analysis)
            
            # Clean and validate URLs
            for comp in competitors:
                if comp.get('website'):
                    domain = urlparse(comp['website']).netloc
                    if not domain.startswith('www.'):
                        comp['website'] = f"https://www.{domain}"
                    elif not comp['website'].startswith('http'):
                        comp['website'] = f"https://{domain}"
            
            return competitors[:3]  # Ensure we only get 3 competitors
            
    except Exception as e:
        logger.error(f"Competitor search failed: {str(e)}")
        return []

def main():
    # Display header image
    st.image("header_image.png", use_column_width=True, caption=None)
    
    st.title("Venture Studio Competitor Analysis")
    
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
                # Identify industries
                industries = identify_industries(pitch)
                
                st.subheader("🎯 Select Your Industry")
                st.write("Based on your pitch, these are the most relevant industries:")
                
                # Create columns for industry buttons
                cols = st.columns(3)
                selected_industry = None
                
                for idx, industry in enumerate(industries):
                    with cols[idx]:
                        if st.button(f"📊 {industry}", use_container_width=True):
                            selected_industry = industry
                
                # If an industry is selected, show competitor analysis
                if selected_industry:
                    with st.spinner(f"Finding competitors in {selected_industry}..."):
                        competitors = find_competitors(selected_industry, pitch)
                        
                        st.subheader("🏢 Top Competitors")
                        st.write(f"Here are your top competitors in {selected_industry}:")
                        
                        for comp in competitors:
                            st.markdown(f"""
                            <div class="competitor-card">
                                <h3>{comp['name']}</h3>
                                <p><strong>Website:</strong> <a href="{comp['website']}" target="_blank">{comp['website']}</a></p>
                                <p><strong>Description:</strong> {comp['description']}</p>
                                <p><strong>Key Differentiator:</strong> {comp['differentiator']}</p>
                            </div>
                            """, unsafe_allow_html=True)

            except Exception as e:
                logger.error(f"Analysis failed: {str(e)}")
                st.error("An error occurred during analysis. Please try again.")

if __name__ == "__main__":
    main()
