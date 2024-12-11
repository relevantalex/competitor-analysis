import streamlit as st
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

# Set page configuration
st.set_page_config(
    page_title="Relevant Venture Studio Competitor Analysis",
    page_icon="📊",
    layout="wide"
)

# Custom CSS with Poppins font
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }
        
        .stButton>button {
            background-color: #4CAF50 !important;
            color: white !important;
            font-family: 'Poppins', sans-serif !important;
        }
        
        div[data-testid="stMarkdownContainer"] > p {
            font-family: 'Poppins', sans-serif;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_time_range(period):
    today = datetime.now()
    if period == "Last Month":
        start_date = today - relativedelta(months=1)
    elif period == "Last 3 Months":
        start_date = today - relativedelta(months=3)
    elif period == "Last 6 Months":
        start_date = today - relativedelta(months=6)
    elif period == "Last Year":
        start_date = today - relativedelta(years=1)
    else:  # Any time
        start_date = today - relativedelta(years=10)
    return start_date

@st.cache_data
def clean_text(text):
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # Remove special characters and digits
    text = re.sub(r'[^\w\s]', '', text)
    # Convert to lowercase
    text = text.lower()
    return text

@st.cache_data
def get_sentiment(text):
    analysis = TextBlob(clean_text(text))
    return analysis.sentiment.polarity

@st.cache_data(ttl=3600)
def scrape_news(query, start_date):
    # List to store results
    results = []
    
    # Google News search URL
    base_url = "https://news.google.com/rss/search"
    params = {
        'q': query,
        'hl': 'en-US',
        'gl': 'US',
        'ceid': 'US:en'
    }
    
    try:
        response = requests.get(base_url, params=params)
        soup = BeautifulSoup(response.content, 'xml')
        
        items = soup.find_all('item')
        for item in items:
            pub_date = datetime.strptime(item.pubDate.text, '%a, %d %b %Y %H:%M:%S %Z')
            if pub_date >= start_date:
                title = item.title.text
                description = item.description.text
                link = item.link.text
                
                sentiment = get_sentiment(title + " " + description)
                
                results.append({
                    'title': title,
                    'description': description,
                    'link': link,
                    'date': pub_date,
                    'sentiment': sentiment
                })
    except Exception as e:
        st.error(f"Error scraping news: {str(e)}")
    
    return pd.DataFrame(results)

@st.cache_data
def analyze_competitors(df):
    # Sentiment analysis over time
    fig_sentiment = px.line(df, x='date', y='sentiment',
                           title='Sentiment Analysis Over Time',
                           labels={'sentiment': 'Sentiment Score', 'date': 'Date'})
    fig_sentiment.update_layout(
        font_family="Poppins",
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
        font_family="Poppins",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig_sentiment, fig_wordfreq, sentiment_trend, avg_sentiment

def main():
    st.title("Relevant Venture Studio Competitor Analysis")
    
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
    
    if st.button("Analyze Competitors"):
        if startup_name and pitch:
            # Show loading spinner
            with st.spinner("Analyzing competitors..."):
                # Get date range
                start_date = get_time_range(time_period)
                
                # Create search query
                search_query = f"{startup_name} {pitch}"
                
                # Scrape and analyze data
                df = scrape_news(search_query, start_date)
                
                if not df.empty:
                    # Display results
                    st.subheader("Competitor Analysis Results")
                    
                    # Display visualizations
                    fig_sentiment, fig_wordfreq, sentiment_trend, avg_sentiment = analyze_competitors(df)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(fig_sentiment, use_container_width=True)
                    with col2:
                        st.plotly_chart(fig_wordfreq, use_container_width=True)
                    
                    # Display sentiment summary
                    st.subheader("Market Sentiment Summary")
                    st.write(f"Overall market sentiment: {sentiment_trend}")
                    st.write(f"Average sentiment score: {avg_sentiment:.2f}")
                    
                    # Display news articles
                    st.subheader("Recent News and Developments")
                    for _, row in df.iterrows():
                        with st.expander(row['title']):
                            st.write(row['description'])
                            st.write(f"Date: {row['date']}")
                            st.write(f"Sentiment: {row['sentiment']:.2f}")
                            st.write(f"Source: {row['link']}")
                else:
                    st.warning("No relevant competitor information found for the specified time period.")
        else:
            st.warning("Please enter both startup name and pitch description.")

if __name__ == "__main__":
    main()
