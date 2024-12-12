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
        
        .competitor-card {
            padding: 20px;
            border-radius: 10px;
            background-color: #f8f9fa;
            margin: 10px 0;
            border-left: 5px solid #4CAF50;
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
        
        .differentiator {
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

def get_brave_time_range(period):
    """Convert time period to Brave API format"""
    if period == "Last Month":
        return "past_month"
    elif period == "Last 3 Months":
        return "past_6_months"
    elif period == "Last 6 Months":
        return "past_6_months"
    elif period == "Last Year":
        return "past_year"
    else:
        return None

def identify_industries(startup_name, pitch):
    """Identify potential industries based on startup name and pitch"""
    text = f"{startup_name} {pitch}".lower()
    
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
    
    industry_scores = {}
    for industry, keywords in industry_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            industry_scores[industry] = score
    
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

@st.cache_data
def clean_text(text):
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[^\w\s]', '', text)
    return text.lower()

@st.cache_data
def get_sentiment(text):
    analysis = TextBlob(clean_text(text))
    return analysis.sentiment.polarity

@st.cache_data(ttl=3600)
def brave_search(query, time_period):
    """Search using Brave's API with time filtering"""
    results = []
    
    headers = {
        'X-Subscription-Token': st.secrets["brave_api_key"],
        'Accept': 'application/json',
    }

    params = {
        'q': query,
        'count': '20'
    }
    
    brave_time = get_brave_time_range(time_period)
    if brave_time:
        params['time_range'] = brave_time
    
    try:
        response = requests.get(
            'https://api.search.brave.com/res/v1/web/search',
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            
            for result in data.get('web', {}).get('results', []):
                title = result.get('title', '')
                description = result.get('description', '')
                url = result.get('url', '')
                date = datetime.now()
                
                sentiment = get_sentiment(title + " " + description)
                
                results.append({
                    'title': title,
                    'description': description,
                    'link': url,
                    'date': date,
                    'sentiment': sentiment
                })
        else:
            st.error(f"Error from Brave API: {response.status_code}")
            st.write("Response:", response.text)
            
    except Exception as e:
        st.error(f"Error searching Brave: {str(e)}")
    
    return pd.DataFrame(results)

def analyze_competitors(df):
    """Analyze competition and extract insights"""
    if df.empty:
        return None, None, 'Neutral', 0.0
    
    # Sentiment analysis over time
    fig_sentiment = px.line(df, x='date', y='sentiment',
                           title='Sentiment Analysis Over Time',
                           labels={'sentiment': 'Sentiment Score', 'date': 'Date'})
    fig_sentiment.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Aggregate sentiment statistics
    avg_sentiment = df['sentiment'].mean()
    sentiment_trend = 'Positive' if avg_sentiment > 0 else 'Negative' if avg_sentiment < 0 else 'Neutral'
    
    # Word frequency analysis
    all_text = ' '.join(df['description'].fillna(''))
    words = word_tokenize(clean_text(all_text))
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words and len(word) > 3]
    word_freq = pd.Series(words).value_counts().head(10)
    
    fig_wordfreq = px.bar(x=word_freq.index, y=word_freq.values,
                         title='Top Keywords in Competitor News',
                         labels={'x': 'Keywords', 'y': 'Frequency'})
    fig_wordfreq.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig_sentiment, fig_wordfreq, sentiment_trend, avg_sentiment

def extract_competitors(df, industry):
    """Extract and analyze competitors from the data"""
    competitors = []
    seen_domains = set()
    
    for _, row in df.iterrows():
        domain = re.sub(r'https?://', '', row['link'].split('/')[0])
        
        if domain not in seen_domains and not any(x in domain for x in ['news', 'blog', 'medium']):
            seen_domains.add(domain)
            competitors.append({
                'name': row['title'].split('-')[0].strip() if '-' in row['title'] else row['title'],
                'website': row['link'],
                'description': clean_html(row['description']),
                'sentiment': row['sentiment']
            })
    
    return competitors[:5]  # Return top 5 competitors

def suggest_differentiators(competitors, industry):
    """Generate differentiation suggestions based on competitors and industry"""
    # Basic differentiator templates by industry
    industry_differentiators = {
        "AI and Machine Learning": [
            "Focus on explainable AI and transparency",
            "Offer more user-friendly interface for non-technical users",
            "Specialize in specific industry verticals",
            "Provide better data privacy guarantees",
            "Offer hybrid AI-human solutions"
        ],
        "Financial Technology": [
            "Provide better integration with existing systems",
            "Focus on specific customer segments",
            "Offer more competitive pricing",
            "Enhance security features",
            "Provide better customer support"
        ]
    }
    
    # Get industry-specific differentiators or use generic ones
    differentiators = industry_differentiators.get(industry, [
        "Focus on superior user experience",
        "Target underserved market segments",
        "Offer more competitive pricing",
        "Provide better customer support",
        "Develop unique features"
    ])
    
    return differentiators

def display_competitor_analysis(competitors, startup_name, pitch, industry):
    """Display competitor analysis with differentiation suggestions"""
    st.subheader("🏢 Key Competitors Analysis")
    
    if not competitors:
        st.warning("No direct competitors found. Try adjusting your search criteria.")
        return
        
    for comp in competitors:
        st.markdown(f"""
        <div class="competitor-card">
            <h3>{comp['name']}</h3>
            <p><strong>Website:</strong> <a href="{comp['website']}" target="_blank">{comp['website']}</a></p>
            <p><strong>Summary:</strong> {comp['description']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Generate differentiation suggestions
    differentiators = suggest_differentiators(competitors, industry)
    
    st.subheader("💡 Differentiation Opportunities")
    st.markdown("""
    <div class="differentiator">
        <h4>Recommended Positioning Strategies:</h4>
        <ul>
    """ + '\n'.join([f"<li>{d}</li>" for d in differentiators]) + """
        </ul>
    </div>
    """, unsafe_allow_html=True)

def display_sentiment_explanation(sentiment_score):
    """Display sentiment score with emoji and explanation"""
    emoji, sentiment_text = get_sentiment_emoji(sentiment_score)
    
    st.markdown(f"""
    <div class="sentiment-box">
        <h3>{emoji} Sentiment Score: {sentiment_score:.2f}</h3>
        <p>This article has a <strong>{sentiment_text}</strong> tone</p>
        <p>Sentiment scores range from -1 (very negative) to +1 (very positive):</p>
        <ul>
            <li>🤩 0.5 to 1.0: Very Positive - Strong positive sentiment, indicating enthusiasm or high praise</li>
            <li>😊 0.0 to 0.5: Positive - Moderate positive sentiment, suggesting general approval</li>
            <li>😐 0.0: Neutral - No clear positive or negative sentiment</li>
            <li>😕 -0.5 to 0.0: Negative - Moderate negative sentiment, indicating concerns or criticism</li>
            <li>😢 -1.0 to -0.5: Very Negative - Strong negative sentiment, suggesting serious issues or problems</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.title("Relevant Venture Studio Competitor Analysis")
    
    if 'brave_api_key' not in st.secrets:
        st.error("Please add your Brave API key to the Streamlit secrets")
        st.info("Add it in your Streamlit Cloud dashboard under App -> Settings -> Secrets")
        return
    
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
        industries = identify_industries(startup_name, pitch)
        
        st.subheader("Select Industry for Analysis")
        st.write("Based on your input, we've identified these relevant industries:")
        
        cols = st.columns(3)
        selected_industry = None
        
        for i, industry in enumerate(industries):
            with cols[i]:
                if st.button(f"📊 {industry}", key=f"industry_{i}", use_container_width=True):
                    selected_industry = industry
        
        if selected_industry:
            with st.spinner(f"Analyzing {selected_industry} industry..."):
                df = brave_search(f"{startup_name} {pitch} {selected_industry}", time_period)
                
                if not df.empty:
                    st.subheader(f"Competitor Analysis Results - {selected_industry}")
                    
                    # Extract and display competitor analysis first
                    competitors = extract_competitors(df, selected_industry)
                    display_competitor_analysis(competitors, startup_name, pitch, selected_industry)
                    
                    # Display visualizations
