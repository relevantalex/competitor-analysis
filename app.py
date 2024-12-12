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
        
        /* Modern form styling */
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
        
        /* Button styling */
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
            background-color: #C01745 !important;
            transform: translateY(-1px);
        }
        
        /* Card styling */
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
        
        /* Container styling */
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #f8fafc;
            padding: 4px;
            border-radius: 12px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #E01955 !important;
            color: white !important;
        }
        
        /* Export button styling */
        .export-button {
            background-color: white !important;
            color: #E01955 !important;
            border: 1px solid #E01955 !important;
            padding: 8px 16px;
        }
        
        .export-button:hover {
            background-color: #fdf2f2 !important;
        }
        
        /* Form container */
        .form-container {
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 24px;
        }
        
        /* Help text */
        .help-text {
            color: #64748b;
            font-size: 0.875rem;
            margin-top: 4px;
        }
        
        /* Website link styling */
        .website-link {
            color: #E01955;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        
        .website-link:hover {
            text-decoration: underline;
        }
    </style>
""", unsafe_allow_html=True)

# Rest of your AI Provider and helper functions remain the same...

def main():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Modern form layout
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)
    
    if submitted and startup_name and pitch:
        with st.spinner("Analyzing industries..."):
            st.session_state.industries = identify_industries(pitch)
            st.session_state.competitors = {}
            st.rerun()

    if st.session_state.industries:
        # Create tabs with export button
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            tab_titles = st.session_state.industries
            tabs = st.tabs(tab_titles)
        
        with col2:
            if st.session_state.competitors:
                export_results(startup_name)
        
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

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
