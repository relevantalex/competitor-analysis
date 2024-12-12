import streamlit as st

# Set page configuration FIRST
st.set_page_config(
    page_title="Relevant Venture Studio Competitor Analysis",
    page_icon="📊",
    layout="wide"
)

import pandas as pd
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import json

# Download required NLTK data
@st.cache_resource
def download_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('punkt')
        nltk.download('stopwords')

download_nltk_data()

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
        
        .industry-button {
            width: 100%;
            margin: 5px 0;
            padding: 10px;
        }
        
        .sentiment-box {
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
            background-color: #f8f9fa;
        }
        
        .article-date {
            color: #666;
            font-size: 0.9em;
        }
    </style>
""", unsafe_allow_html=True)

def identify_industries(startup_name, pitch):
    """Identify potential industries based on startup name and pitch"""
    # Combine startup name and pitch
    text = f"{startup_name} {pitch}".lower()
    
    # Define industry keywords
    industry_keywords = {
        "AI and Machine Learning": ["ai", "machine learning", "artificial intelligence", "ml", "deep learning", "neural", "automation"],
        "Financial Technology": ["fintech", "banking", "payment", "finance", "insurance", "lending", "crypto"],
        "Healthcare Technology": ["health", "medical", "healthcare", "biotech", "wellness", "diagnosis", "clinical"],
        "E-commerce": ["ecommerce", "retail", "shopping", "marketplace", "commerce", "store", "shop"],
        "Enterprise Software": ["saas", "enterprise", "business software", "b2b", "cloud", "workflow"],
        "Education Technology": ["edtech", "education", "learning", "teaching", "school", "student", "training"],
        "Cybersecurity": ["security", "cyber", "privacy", "encryption", "protection", "firewall"],
        "Clean Technology": ["cleantech", "renewable", "sustainability", "green", "energy", "environmental"],
        "Internet of Things": ["iot", "connected devices", "smart home", "sensors", "hardware"],
        "Mobile Applications": ["mobile", "app", "android", "ios", "smartphone", "tablets"]
    }
    
    # Score each industry based on keyword matches
    industry_scores = {}
    for industry, keywords in industry_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            industry_scores[industry] = score
    
    # Return top 3 industries
    top_industries = sorted(industry_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    return [industry for industry, _ in top_industries] if top_industries else ["Technology", "Software", "Consumer"]

def get_sentiment_emoji(sentiment_score):
    """Return emoji and description based on sentiment score"""
    if sentiment_score >= 0.5:
        return "🤩", "Very Positive"
    elif sentiment_score > 0:
        return "😊", "Positive"
    elif sentiment_score == 0:
        return "😐", "Neutral"
    elif sentiment_score > -0.5:
        return "😕", "Negative"
    else:
        return "😢", "Very Negative"

def clean_html(text):
    """Clean HTML tags and format text"""
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text(separator=' ').strip()

[... Previous functions remain the same ...]

def analyze_industry(startup_name, pitch, time_period, industry, api_key):
    """Analyze competitors for a specific industry"""
    search_query = f"{startup_name} {pitch} {industry}"
    df = brave_search(search_query, time_period, api_key)
    
    if not df.empty:
        df['description'] = df['description'].apply(clean_html)
        return df
    return pd.DataFrame()

def display_sentiment_explanation(sentiment_score):
    """Display sentiment score with emoji and explanation"""
    emoji, sentiment_text = get_sentiment_emoji(sentiment_score)
    
    st.markdown(f"""
    <div class="sentiment-box">
        <h3>{emoji} Sentiment Score: {sentiment_score:.2f}</h3>
        <p>This article has a <strong>{sentiment_text}</strong> tone</p>
        <p>Sentiment scores range from -1 (very negative) to +1 (very positive):</p>
        <ul>
            <li>🤩 0.5 to 1.0: Very Positive</li>
            <li>😊 0.0 to 0.5: Positive</li>
            <li>😐 0.0: Neutral</li>
            <li>😕 -0.5 to 0.0: Negative</li>
            <li>😢 -1.0 to -0.5: Very Negative</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.title("Relevant Venture Studio Competitor Analysis")
    
    # Check for Brave API key in secrets
    if 'brave_api_key' not in st.secrets:
        st.error("Please add your Brave API key to the Streamlit secrets with the key 'brave_api_key'")
        st.info("To add your API key, go to your Streamlit app settings and add it under 'Secrets' with the key 'brave_api_key'")
        return
    
    # Input section
    col1, col2 = st.columns(2)
    
    with col1:
        startup_name = st.text_input("Enter Startup Name")
        pitch = st.text_area("Enter Pitch or One-Sentence Description")
    
    with col2:
        time_period = st.selectbox(
            "Select Time Period",
            ["Last Month", "Last 3 Months", "Last 6 Months", "Last Year", "Any Time"]
        )
    
    if startup_name and pitch:
        # Identify industries
        industries = identify_industries(startup_name, pitch)
        
        st.subheader("Select Industry for Analysis")
        st.write("Based on your input, we've identified these relevant industries:")
        
        # Create columns for industry buttons
        cols = st.columns(3)
        selected_industry = None
        
        # Display industry buttons
        for i, industry in enumerate(industries):
            with cols[i]:
                if st.button(f"📊 {industry}", key=f"industry_{i}", use_container_width=True):
                    selected_industry = industry
        
        if selected_industry:
            with st.spinner(f"Analyzing {selected_industry} industry..."):
                df = analyze_industry(startup_name, pitch, time_period, selected_industry, st.secrets["brave_api_key"])
                
                if not df.empty:
                    st.subheader(f"Competitor Analysis Results - {selected_industry}")
                    
                    # Display visualizations
                    fig_sentiment, fig_wordfreq, sentiment_trend, avg_sentiment = analyze_competitors(df)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(fig_sentiment, use_container_width=True)
                    with col2:
                        st.plotly_chart(fig_wordfreq, use_container_width=True)
                    
                    # Display sentiment summary with emoji
                    st.subheader("Market Sentiment Summary")
                    emoji, sentiment_text = get_sentiment_emoji(avg_sentiment)
                    st.markdown(f"### Overall Market Sentiment: {emoji} {sentiment_text}")
                    display_sentiment_explanation(avg_sentiment)
                    
                    # Display news articles
                    st.subheader("Recent News and Developments")
                    for _, row in df.iterrows():
                        with st.expander(f"{row['title']} - {row['date'].strftime('%B %Y')}"):
                            st.write(row['description'])
                            emoji, _ = get_sentiment_emoji(row['sentiment'])
                            st.write(f"Sentiment: {emoji} {row['sentiment']:.2f}")
                            st.write(f"Source: {row['link']}")
                else:
                    st.warning(f"No relevant competitor information found for {selected_industry} industry in the specified time period.")
    else:
        st.info("Please enter your startup name and pitch to begin the analysis.")

if __name__ == "__main__":
    main()
