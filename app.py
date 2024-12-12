import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import json
from anthropic import Anthropic
from duckduckgo_search import DDGS
import csv
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page configuration with wider layout
st.set_page_config(
    page_title="Venture Studio Competitor Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern UI styling with your brand color
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Main container and text styles */
        .main {
            font-family: 'Inter', sans-serif !important;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif !important;
            font-weight: 600;
        }
        
        /* Header image and title styling */
        .header-container {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            background: linear-gradient(to right, #E01955, #ff4081);
            padding: 2rem;
            border-radius: 12px;
            color: white;
        }
        
        .header-image {
            max-width: 200px;
            margin-right: 2rem;
        }
        
        /* Form styling */
        .form-container {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        
        /* Input fields styling */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            padding: 12px;
            background: white;
            font-family: 'Inter', sans-serif;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #E01955 !important;
            color: white !important;
            padding: 12px 24px;
            border-radius: 8px;
            border: none;
            font-weight: 500;
            width: 100%;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            background-color: #C01745 !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* Competitor card styling */
        .competitor-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #E01955;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }
        
        .competitor-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Tab styling */
        .stTabs {
            background: white;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Export button styling */
        .export-button {
            background-color: white !important;
            color: #E01955 !important;
            border: 1px solid #E01955 !important;
            margin-top: 1rem;
        }
        
        /* Website link styling */
        .website-link {
            color: #E01955;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            transition: all 0.2s ease;
        }
        
        .website-link:hover {
            text-decoration: underline;
            opacity: 0.9;
        }
        
        /* Add divider styling */
        .divider {
            height: 1px;
            background: #e2e8f0;
            margin: 1rem 0;
        }
        
        /* Help icon styling */
        .help-icon {
            color: #94a3b8;
            margin-left: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Header with logo
st.markdown("""
    <div class="header-container">
        <img src="https://drive.google.com/uc?id=1JmN239NqwH1KOJJUWtjcr7dU6zn1Auh4" 
             alt="Company Logo" 
             class="header-image">
        <h1>Venture Studio Competitor Analysis</h1>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'competitors' not in st.session_state:
    st.session_state.competitors = {}
if 'industries' not in st.session_state:
    st.session_state.industries = None

# Form container
st.markdown('<div class="form-container">', unsafe_allow_html=True)
with st.form("analysis_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        startup_name = st.text_input(
            "Startup Name",
            help="Enter your startup's name",
            placeholder="e.g., TechVision AI"
        )
        
        region = st.selectbox(
            "Target Region",
            options=["Worldwide", "North America", "Europe", "Asia Pacific", 
                    "Latin America", "Middle East & Africa"],
            help="Select your primary target market"
        )
    
    with col2:
        pitch = st.text_area(
            "One-Sentence Pitch",
            help="Describe what your startup does in one sentence",
            placeholder="e.g., AI-powered analytics platform for retail optimization",
            max_chars=200
        )
    
    submitted = st.form_submit_button("Analyze Market")
st.markdown('</div>', unsafe_allow_html=True)

# Rest of your existing logic for competitors analysis...
# [Previous competitor analysis code remains the same]

def display_competitor_card(competitor):
    st.markdown(f"""
        <div class="competitor-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; font-size: 1.25rem;">{competitor['name']}</h3>
                <a href="{competitor['website']}" target="_blank" class="website-link">
                    Visit Website
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" 
                         stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <line x1="10" y1="14" x2="21" y2="3"></line>
                    </svg>
                </a>
            </div>
            <div class="divider"></div>
            <div style="margin-bottom: 1rem;">
                <h4 style="margin-bottom: 0.5rem;">Description</h4>
                <p style="color: #64748b; margin: 0;">{competitor['description']}</p>
            </div>
            <div class="divider"></div>
            <div>
                <h4 style="margin-bottom: 0.5rem;">Key Differentiator</h4>
                <p style="color: #64748b; margin: 0;">{competitor['differentiator']}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Display results in tabs
if st.session_state.industries:
    tabs = st.tabs(st.session_state.industries)
    
    for i, tab in enumerate(tabs):
        with tab:
            industry = st.session_state.industries[i]
            if industry in st.session_state.competitors:
                for competitor in st.session_state.competitors[industry]:
                    display_competitor_card(competitor)

# Export functionality
if st.session_state.competitors:
    st.markdown('<div style="display: flex; justify-content: center;">', unsafe_allow_html=True)
    export_results(startup_name)
    st.markdown('</div>', unsafe_allow_html=True)
