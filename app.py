import streamlit as st
import os
import openai
import anthropic
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
import json
from typing import List, Dict, Any
import base64

# Set page configuration FIRST
st.set_page_config(
    page_title="Relevant Venture Studio Competitor Analysis",
    page_icon="📊",
    layout="wide"
)

# Configure API clients
if not all(key in st.secrets for key in ["openai_api_key", "anthropic_api_key", "brave_api_key"]):
    st.error("⚠️ Missing required API keys in Streamlit secrets")
    st.info("""
    Please add the following keys in your Streamlit Cloud settings:
    - `openai_api_key` (for GPT-4)
    - `anthropic_api_key` (for Claude)
    - `brave_api_key` (for web search)
    
    You can set these in your Streamlit Cloud dashboard under:
    App -> Settings -> Secrets
    """)
    st.stop()

openai.api_key = st.secrets["openai_api_key"]
claude = anthropic.Client(api_key=st.secrets["anthropic_api_key"])
BRAVE_API_KEY = st.secrets["brave_api_key"]
AI_MODEL = st.secrets.get("ai_model", "gpt-4")  # Default to GPT-4 if not specified

# Custom CSS with Poppins font
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif !important;
        }
        
        .stButton>button {
            background-color: #4CAF50 !important;
            color: white !important;
            font-family: 'Poppins', sans-serif !important;
        }
        
        .competitor-card {
            padding: 20px;
            border-radius: 10px;
            background-color: #f8f9fa;
            margin: 10px 0;
            border-left: 5px solid #4CAF50;
        }
        
        .header-image {
            width: 100%;
            margin-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

def get_industry_analysis(pitch: str, model: str = "gpt-4") -> List[str]:
    """Use AI to analyze the pitch and identify potential industries"""
    if model == "gpt-4":
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert in industry analysis and market research."},
                {"role": "user", "content": f"""Based on this pitch, identify the top 3 most relevant industries 
                that this startup could be categorized in. Only return the industry names separated by '|':
                Pitch: {pitch}"""}
            ],
            temperature=0.7
        )
        industries = response.choices[0].message.content.split("|")
    else:
        response = claude.messages.create(
            model="claude-3-opus-20240229",
            messages=[{
                "role": "user",
                "content": f"""Based on this pitch, identify the top 3 most relevant industries 
                that this startup could be categorized in. Only return the industry names separated by '|':
                Pitch: {pitch}"""
            }]
        )
        industries = response.first_response.text.split("|")
    
    return [industry.strip() for industry in industries]

def analyze_competitors(industry: str, startup_name: str, pitch: str, model: str = "gpt-4") -> List[Dict[str, Any]]:
    """Use AI to analyze competitors based on web search results"""
    
    # First, get competitor information from Brave Search
    headers = {
        'X-Subscription-Token': BRAVE_API_KEY,
        'Accept': 'application/json',
    }
    
    params = {
        'q': f"top companies {industry} {startup_name} competitors",
        'count': '30'
    }
    
    results = []
    try:
        response = requests.get(
            'https://api.search.brave.com/res/v1/web/search',
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            search_results = data.get('web', {}).get('results', [])
            
            # Use AI to analyze the search results
            if model == "gpt-4":
                analysis_prompt = f"""Based on these search results about competitors in {industry}, identify the top 3 most relevant 
                competitors for a startup with this pitch: {pitch}

                For each competitor, provide:
                1. Company name
                2. Website URL
                3. Brief description of their offering
                4. Key differentiators

                Format the response as JSON with this structure:
                {{
                    "competitors": [
                        {{
                            "name": "Company Name",
                            "website": "URL",
                            "description": "Brief description",
                            "differentiators": ["diff1", "diff2"]
                        }}
                    ]
                }}

                Search results:
                {json.dumps(search_results, indent=2)}"""
                
                response = openai.ChatCompletion.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are an expert in competitive analysis."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    temperature=0.7
                )
                competitors = json.loads(response.choices[0].message.content)["competitors"]
            
            else:  # Claude
                analysis_prompt = f"""Based on these search results about competitors in {industry}, identify the top 3 most relevant 
                competitors for a startup with this pitch: {pitch}

                For each competitor, provide:
                1. Company name
                2. Website URL
                3. Brief description of their offering
                4. Key differentiators

                Format the response as JSON with this structure:
                {{
                    "competitors": [
                        {{
                            "name": "Company Name",
                            "website": "URL",
                            "description": "Brief description",
                            "differentiators": ["diff1", "diff2"]
                        }}
                    ]
                }}

                Search results:
                {json.dumps(search_results, indent=2)}"""
                
                response = claude.messages.create(
                    model="claude-3-opus-20240229",
                    messages=[{
                        "role": "user",
                        "content": analysis_prompt
                    }]
                )
                competitors = json.loads(response.first_response.text)["competitors"]
            
            return competitors
            
    except Exception as e:
        st.error(f"Error analyzing competitors: {str(e)}")
        return []

def get_market_insights(industry: str, competitors: List[Dict[str, Any]], model: str = "gpt-4") -> str:
    """Get AI-generated market insights based on competitor analysis"""
    if model == "gpt-4":
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert in market analysis and business strategy."},
                {"role": "user", "content": f"""Based on these competitors in the {industry} industry, provide strategic insights 
                about market opportunities and positioning:
                {json.dumps(competitors, indent=2)}
                
                Focus on:
                1. Market gaps
                2. Underserved segments
                3. Potential differentiators
                4. Strategic recommendations
                
                Format your response with Markdown headings and bullet points."""}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    else:
        response = claude.messages.create(
            model="claude-3-opus-20240229",
            messages=[{
                "role": "user",
                "content": f"""Based on these competitors in the {industry} industry, provide strategic insights 
                about market opportunities and positioning:
                {json.dumps(competitors, indent=2)}
                
                Focus on:
                1. Market gaps
                2. Underserved segments
                3. Potential differentiators
                4. Strategic recommendations
                
                Format your response with Markdown headings and bullet points."""
            }]
        )
        return response.first_response.text

def display_competitor_card(competitor):
    """Display a competitor card with company information"""
    st.markdown(f"""
    <div class="competitor-card">
        <h3>{competitor['name']}</h3>
        <p><strong>Website:</strong> <a href="{competitor['website']}" target="_blank">{competitor['website']}</a></p>
        <p><strong>Description:</strong> {competitor['description']}</p>
        <p><strong>Key Differentiators:</strong></p>
        <ul>
            {''.join([f"<li>{diff}</li>" for diff in competitor['differentiators']])}
        </ul>
    </div>
    """, unsafe_allow_html=True)

def load_header_image():
    """Load and display the header image"""
    image_url = "https://drive.usercontent.google.com/download?id=15BCFR1gw399ILx8wAmVEUQn9rvvumc8C"
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            encoded_image = base64.b64encode(response.content).decode()
            st.markdown(f"""
                <img src="data:image/png;base64,{encoded_image}" class="header-image">
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error("Error loading header image")

def main():
    # Display header image
    load_header_image()
    
    st.title("Relevant Venture Studio Competitor Analysis")
    
    # Check for required API keys
    required_keys = ['openai_api_key', 'anthropic_api_key', 'brave_api_key', 'ai_model']
    missing_keys = [key for key in required_keys if key not in st.secrets["api_keys"]]
    
    if missing_keys:
        st.error(f"Missing required API keys: {', '.join(missing_keys)}")
        st.info("Please add the missing API keys to your Streamlit secrets.")
        return
    
    # Input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        startup_name = st.text_input("Enter Startup Name")
        pitch = st.text_area("Enter Pitch or One-Sentence Description")
    
    with col2:
        model_info = """
        ### AI Model Selection
        - **GPT-4 Turbo**: Latest model with enhanced analysis capabilities
        - **Claude 3 Opus**: Advanced analysis with longer context window
        """
        st.markdown(model_info)
        selected_model = st.radio("Select AI Model", 
                                ["gpt-4", "claude"], 
                                index=0 if AI_MODEL == "gpt-4" else 1)
    
    if startup_name and pitch:
        with st.spinner("Analyzing your startup and identifying relevant industries..."):
            industries = get_industry_analysis(pitch, selected_model)
            
            st.subheader("🎯 Select Industry for Detailed Analysis")
            st.write("Based on your pitch, we've identified these relevant industries:")
            
            # Create columns for industry buttons
            cols = st.columns(3)
            selected_industry = None
            
            # Display industry buttons
            for i, industry in enumerate(industries):
                with cols[i]:
                    if st.button(f"📊 {industry}", key=f"industry_{i}", use_container_width=True):
                        selected_industry = industry
        
        if selected_industry:
            st.subheader(f"🔍 Competitor Analysis: {selected_industry}")
            
            with st.spinner("Analyzing competitors and market landscape..."):
                # Get competitor analysis
                competitors = analyze_competitors(selected_industry, startup_name, pitch, selected_model)
                
                if competitors:
                    # Display top competitors first
                    st.write("### 🏢 Top Competitors")
                    for competitor in competitors:
                        display_competitor_card(competitor)
                    
                    # Get and display market insights
                    st.write("### 💡 Market Insights and Opportunities")
                    insights = get_market_insights(selected_industry, competitors, selected_model)
                    st.markdown(insights)
                    
                    # Additional resources
                    st.write("### 📚 Additional Resources")
                    st.write("""
                    - **Industry Reports**: Check out reports from Gartner, Forrester, or IDC
                    - **Market Research**: Visit CB Insights or Crunchbase for more competitor data
                    - **News & Trends**: Follow industry news on TechCrunch or relevant trade publications
                    """)
                else:
                    st.warning("No competitor information found. Try adjusting your search criteria or selecting a different industry.")

if __name__ == "__main__":
    main()
