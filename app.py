import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="Venture Studio Competitor Analysis",
    page_icon="📊",
    layout="wide",
)

# Define regions
REGIONS = {
    "Worldwide": "Global market analysis",
    "North America": ["United States", "Canada"],
    "Europe": ["European Union", "United Kingdom", "Switzerland"],
    "Asia Pacific": ["China", "Japan", "South Korea", "Singapore"],
    "Latin America": ["Brazil", "Mexico", "Argentina"],
    "Middle East & Africa": ["UAE", "Saudi Arabia", "South Africa"],
}

# Modern UI styling
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Header styling */
        .header-container {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            background: linear-gradient(to right, #E01955, #C01745);
            padding: 2rem;
            border-radius: 12px;
            color: white;
        }
        
        .header-image {
            max-width: 200px;
            margin-right: 2rem;
        }
        
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            padding: 12px;
            background: white;
        }
        
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            padding: 12px;
            background: white;
        }
        
        .stSelectbox > div > div {
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            padding: 2px;
            background: white;
        }
        
        .stButton>button {
            width: 100%;
            background-color: #E01955 !important;
            color: white !important;
            padding: 12px 24px;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton>button:hover {
            background-color: #B01535 !important;
            transform: translateY(-1px);
        }
        
        .competitor-card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin: 16px 0;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #E01955;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .competitor-card:hover {
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transform: translateY(-2px);
            transition: all 0.2s ease;
        }
        
        .website-link {
            color: #E01955;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        
        .website-link:hover {
            color: #B01535;
            text-decoration: underline;
        }
    </style>
""", unsafe_allow_html=True)

# Header with logo
st.markdown("""
    <div class="header-container">
        <h1>Relevant Venture Studio Competitor Analysis</h1>
    </div>
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
            st.error("Failed to generate AI response. Please check your API settings.")
            return ""

def identify_industries(pitch: str) -> List[str]:
    ai = AIProvider()
    prompt = f"""Based on this pitch: "{pitch}"
    Identify exactly 3 specific, relevant industries or market segments.
    Format your response as a JSON array with exactly 3 strings.
    Make each industry name specific and descriptive.
    Example: ["AI-Powered Security Analytics", "Retail Technology Solutions", "Computer Vision SaaS"]"""

    try:
        response = ai.generate_response(prompt)
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
    ai = AIProvider()
    
    try:
        search_prompt = f"""For a startup in {industry} with this pitch: "{pitch}"
        Create a search query to find direct competitors.
        Return only the search query text, nothing else."""

        search_query = ai.generate_response(search_prompt).strip().strip('"')
        
        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, max_results=10))
            
            analysis_prompt = f"""Analyze these competitors in {industry}:
            {json.dumps(results)}
            
            Identify the top 3 most relevant direct competitors.
            Return a JSON array with exactly 3 companies, each containing:
            {{
                "name": "Company Name",
                "website": "company website",
                "description": "2-sentence description",
                "differentiator": "key unique selling point"
            }}"""

            competitor_analysis = ai.generate_response(analysis_prompt)
            cleaned_analysis = competitor_analysis.strip()
            if not cleaned_analysis.startswith('['):
                cleaned_analysis = cleaned_analysis[cleaned_analysis.find('['):]
            if not cleaned_analysis.endswith(']'):
                cleaned_analysis = cleaned_analysis[:cleaned_analysis.rfind(']')+1]
            
            competitors = json.loads(cleaned_analysis)
            return competitors[:3]
            
    except Exception as e:
        logger.error(f"Competitor search failed: {str(e)}")
        st.error(f"Error finding competitors: {str(e)}")
        return []

def export_results(startup_name: str):
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
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(csv_data)
    
    st.download_button(
        label="📥 Export Analysis",
        data=output.getvalue(),
        file_name=f"{startup_name}_competitor_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
        key='export-button',
        help="Download the complete analysis as a CSV file"
    )

def main():
    with st.form("analysis_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            startup_name = st.text_input(
                "Startup Name",
                help="Enter your startup's name",
                placeholder="e.g., TechVision AI"
            )
            
            region = st.selectbox(
                "Target Region",
                options=list(REGIONS.keys()),
                help="Select your target market region"
            )
        
        with col2:
            pitch = st.text_area(
                "One-Sentence Pitch",
                help="Describe what your startup does in one sentence",
                max_chars=200,
                placeholder="e.g., AI-powered analytics platform for retail optimization"
            )
        
        submitted = st.form_submit_button("Analyze Market")
    
    if submitted and startup_name and pitch:
        with st.spinner("Analyzing industries..."):
            st.session_state.industries = identify_industries(pitch)
            st.session_state.competitors = {}
            st.rerun()

    if st.session_state.industries:
        tabs = st.tabs(st.session_state.industries)
        
        for i, tab in enumerate(tabs):
            with tab:
                industry = st.session_state.industries[i]
                
                if industry not in st.session_state.competitors:
                    with st.spinner(f"Analyzing competitors in {industry}..."):
                        competitors = find_competitors(industry, pitch)
                        st.session_state.competitors[industry] = competitors
                
                if industry in st.session_state.competitors:
                    for comp in st.session_state.competitors[industry]:
                        st.markdown(f"""
                        <div class="competitor-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                                <h3 style="margin: 0; font-size: 1.25rem; font-weight: 600;">{comp['name']}</h3>
                                <a href="{comp['website']}" target="_blank" class="website-link">
                                    Visit Website
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                        <polyline points="15 3 21 3 21 9"></polyline>
                                        <line x1="10" y1="14" x2="21" y2="3"></line>
                                    </svg>
                                </a>
                            </div>
                            <div style="margin-bottom: 16px;">
                                <h4 style="font-weight: 600; margin-bottom: 4px;">Description</h4>
                                <p style="color: #64748b; margin: 0;">{comp['description']}</p>
                            </div>
                            <div>
                                <h4 style="font-weight: 600; margin-bottom: 4px;">Key Differentiator</h4>
                                <p style="color: #64748b; margin: 0;">{comp['differentiator']}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        if st.session_state.competitors:
            export_results(startup_name)

if __name__ == "__main__":
    main()
