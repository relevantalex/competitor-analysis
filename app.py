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
    "Oceania": ["Australia", "New Zealand"]
}

# Custom CSS with updated brand color
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }
        
        .stButton>button {
            background-color: #E01955 !important;
            color: white !important;
            font-family: 'Inter', sans-serif !important;
            border-radius: 10px !important;
            transition: all 0.3s ease;
            height: 48px !important;
            font-size: 16px !important;
            border: none !important;
            padding: 0 24px !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(224, 25, 85, 0.2);
        }
        
        .competitor-card {
            padding: 24px;
            border-radius: 20px !important;
            background-color: #ffffff;
            margin: 16px 0;
            border-left: 5px solid #E01955;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        
        .competitor-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        }
        
        .banner-container {
            margin: -4rem -4rem 2rem -4rem;
            padding: 0;
            position: relative;
        }
        
        .banner-container img {
            width: 100%;
            height: auto;
            border-radius: 0 0 20px 20px;
        }
        
        .banner-overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 2rem;
            background: linear-gradient(to bottom, rgba(0,0,0,0), rgba(0,0,0,0.7));
            border-radius: 0 0 20px 20px;
        }
        
        .banner-overlay h1 {
            color: white;
            margin: 0;
            font-size: 2.5rem;
            font-weight: 600;
        }
        
        .banner-overlay p {
            color: rgba(255,255,255,0.9);
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
        }
        
        /* Style the form container */
        .stForm {
            background-color: white;
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        
        /* Style the tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-radius: 20px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 8px 16px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #E01955 !important;
            color: white !important;
        }
        
        /* Style the select boxes */
        .stSelectbox [data-baseweb="select"] {
            border-radius: 10px;
        }
        
        /* Add spacing between sections */
        .section-spacing {
            margin: 2rem 0;
        }
        
        /* Style the export button */
        .stDownloadButton>button {
            background-color: #2E3192 !important;
            margin-top: 2rem;
        }
        
    </style>
""", unsafe_allow_html=True)

[... REST OF THE CODE REMAINS THE SAME UNTIL THE MAIN FUNCTION ...]

def main():
    # Banner with overlay
    st.markdown("""
        <div class="banner-container">
            <img src="https://drive.google.com/uc?id=1JmN239NqwH1KOJJUWtjcr7dU6zn1Auh4" alt="Banner">
            <div class="banner-overlay">
                <h1>Venture Studio Competitor Analysis</h1>
                <p>Powered by AI for accurate market insights</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Input section with modern styling
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
        
        submitted = st.form_submit_button("Analyze Market", use_container_width=True)
    
    if submitted and startup_name and pitch:
        with st.spinner("Analyzing industries..."):
            st.session_state.industries = identify_industries(pitch)
            st.session_state.competitors = {}
            st.rerun()

    # Show analysis if industries are identified
    if st.session_state.industries:
        st.markdown("<div class='section-spacing'></div>", unsafe_allow_html=True)
        
        # Create tabs
        tab_titles = st.session_state.industries
        tabs = st.tabs(tab_titles)
        
        # Handle tab content
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
