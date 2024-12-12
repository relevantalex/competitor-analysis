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
    </style>
""", unsafe_allow_html=True)

class AIProvider:
    """AI Provider class to handle different AI services"""
    def __init__(self):
        # Check which AI provider to use
        self.provider = st.secrets.get("api_settings", {}).get("ai_provider", "openai")
        
        if self.provider == "openai":
            openai.api_key = st.secrets["api_keys"]["openai_api_key"]
            # GPT-4 Turbo is the latest model as of April 2024
            self.model = "gpt-4-turbo-preview"
        else:
            self.anthropic = Anthropic(api_key=st.secrets["api_keys"]["anthropic_api_key"])
            # Claude 3 Opus is the latest model as of April 2024
            self.model = "claude-3-opus-20240229"

    async def generate_response(self, prompt: str) -> str:
        """Generate AI response with proper error handling"""
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
                industries = identify_industries(pitch)
                
                st.subheader("🎯 Select Your Industry")
                st.write("Based on your pitch, these are the most relevant industries:")
                
                cols = st.columns(3)
                selected_industry = None
                
                for idx, industry in enumerate(industries):
                    with cols[idx]:
                        if st.button(f"📊 {industry}", use_container_width=True):
                            selected_industry = industry
                
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
                st.error("An error occurred during analysis. Please check your API settings and try again.")

if __name__ == "__main__":
    main()
