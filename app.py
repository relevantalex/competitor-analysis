import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import json
from anthropic import Anthropic
import csv
from io import StringIO
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="Competitor Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern UI styling
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Global styles */
        .main {
            background: linear-gradient(to bottom right, #f3f4f6, #ffffff);
            padding: 2rem;
        }
        
        /* Container */
        .content-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        /* Form styling */
        .form-container {
            background: white;
            padding: 2rem;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
        }
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {
            border-radius: 0.5rem;
            border: 1px solid #e5e7eb;
            padding: 0.75rem;
            font-size: 0.875rem;
            background: white;
        }
        
        /* Button styling - Removing green */
        .stButton > button {
            width: 100%;
            background-color: #E01955 !important;
            color: white !important;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem !important;
            border: none !important;
            font-weight: 500;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            background-color: #C01745 !important;
            transform: translateY(-1px);
        }

        /* Override Streamlit's default green button color */
        .stButton > button[kind="primary"] {
            background-color: #E01955 !important;
            border-color: #E01955 !important;
        }
        
        /* Override any other potential green buttons */
        button[data-baseweb="button"] {
            background-color: #E01955 !important;
            border-color: #E01955 !important;
        }
        
        /* Remove green focus outline */
        .stButton > button:focus {
            box-shadow: 0 0 0 0.2rem rgba(224, 25, 85, 0.25) !important;
        }
        
        /* Competitor card */
        .competitor-card {
            background: white;
            border-radius: 0.75rem;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        }
        
        .competitor-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .card-header {
            background: #E01955;
            padding: 1.25rem;
            color: white;
        }
        
        .company-name {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0;
            color: white;
        }
        
        .company-industry {
            font-size: 0.875rem;
            opacity: 0.9;
            margin-top: 0.25rem;
        }
        
        .card-content {
            padding: 1.25rem;
        }
        
        .description-text {
            font-size: 0.875rem;
            color: #4b5563;
            margin-bottom: 1rem;
            line-height: 1.5;
        }
        
        /* Form field styling */
        .stTextInput > div:hover,
        .stTextArea > div:hover,
        .stMultiSelect > div:hover {
            border-color: #E01955 !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stMultiSelect > div:focus {
            border-color: #E01955 !important;
            box-shadow: 0 0 0 1px #E01955 !important;
        }

        /* Form icons (dropdown and clear) */
        .stTextInput [data-baseweb="icon"],
        .stSelectbox [data-baseweb="icon"],
        .stMultiSelect [data-baseweb="icon"] {
            color: #000000 !important;
        }

        /* Multiselect chips */
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #E01955 !important;
            color: white !important;
        }
        
        .stMultiSelect [data-baseweb="tag"]:hover {
            background-color: #C01745 !important;
        }

        /* Analyze Market button and line */
        .stButton > button {
            width: 100%;
            background-color: #E01955 !important;
            color: white !important;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem !important;
            border: none !important;
            font-weight: 500;
            font-size: 0.875rem;
            transition: all 0.2s ease;
            border-bottom: 2px solid #E01955 !important;
        }
        
        .stButton > button:hover {
            background-color: #C01745 !important;
            transform: translateY(-1px);
            border-bottom-color: #C01745 !important;
        }
        
        /* Override any remaining focus/selection colors */
        *:focus {
            outline-color: #E01955 !important;
        }
        
        *::selection {
            background-color: rgba(224, 25, 85, 0.2) !important;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 4px;
            margin: 4px;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #E01955 !important;
            color: white !important;
            border-color: #E01955 !important;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background-color: rgba(224, 25, 85, 0.1) !important;
            color: #E01955 !important;
        }
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            padding: 0.5rem;
            border-radius: 0.5rem;
            background: #f3f4f6;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 0.375rem;
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
            border: 1px solid #e5e7eb;
            background: white;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: #E01955 !important;
            color: white !important;
            border-color: #E01955 !important;
        }
        
        /* Export button */
        .export-button {
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 1rem;
            border: 1px solid #E01955;
            border-radius: 0.375rem;
            color: #E01955;
            text-decoration: none;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        }
        
        .export-button:hover {
            background: #E01955;
            color: white;
        }
        
        .website-link {
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 1rem;
            border: 1px solid #E01955;
            border-radius: 0.375rem;
            color: #E01955;
            text-decoration: none;
            font-size: 0.875rem;
            transition: all 0.2s ease;
            margin-top: 1rem;
        }
        
        .website-link:hover {
            background: #E01955;
            color: white;
        }
        
        /* Title styling */
        .page-title {
            font-size: 2rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 2rem;
            color: #1f2937;
        }
        
        /* Help text */
        .help-text {
            font-size: 0.75rem;
            color: #6b7280;
            margin-top: 0.25rem;
        }

        /* Fix textarea copy-paste */
        .stTextArea textarea {
            resize: vertical !important;
            min-height: 100px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Mock data
MOCK_COMPETITORS = [
    {
        "id": "1",
        "name": "ERC Hospitality Systems",
        "website": "https://www.erconline.com",
        "description": "ERC Hospitality Systems is a Georgia-based POS reseller and technology provider with nearly four decades of experience in restaurant technology. They have served over 15,000 restaurants with technology solutions.",
        "keyDifferentiator": "Long-standing industry experience and a wide customer base.",
        "industry": "Restaurant Management Solutions",
        "logo": "/api/placeholder/80/80"
    },
    {
        "id": "2",
        "name": "Coram",
        "website": "https://www.coram.ai",
        "description": "Coram offers next-generation cloud-based software for upgrading physical security infrastructure to modern cloud-based systems. It supports easy integration with existing IP cameras and centralizes monitoring on the cloud.",
        "keyDifferentiator": "Focus on cloud-based integration and open platform compatibility.",
        "industry": "Hospitality Security Systems",
        "logo": "/api/placeholder/80/80"
    },
    {
        "id": "3",
        "name": "FoodTech Analytics",
        "website": "https://www.foodtechanalytics.com",
        "description": "FoodTech Analytics provides advanced data analysis tools for restaurants and food service businesses. Their platform offers insights on menu optimization, customer preferences, and operational efficiency.",
        "keyDifferentiator": "AI-driven predictive analytics for food service industry.",
        "industry": "Food Service Analytics",
        "logo": "/api/placeholder/80/80"
    }
]

def export_to_csv(data):
    df = pd.DataFrame(data)
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="competitor_analysis.csv" class="export-button">📥 Download Analysis (CSV)</a>'
    return href

def main():
    st.markdown('<h1 class="page-title">Competitor Analysis Tool</h1>', unsafe_allow_html=True)

    # Form section - Changed to vertical layout
    with st.form("analysis_form"):
        startup_name = st.text_input(
            "Startup Name",
            help="Enter your startup's name",
            placeholder="e.g., TechVision AI"
        )
        
        pitch = st.text_area(
            "One-Sentence Pitch",
            help="Describe your startup in one sentence",
            placeholder="e.g., AI-powered analytics platform for retail optimization"
        )
        
        # Changed to multiselect for regions
        region = st.multiselect(
            "Target Region",
            ["Worldwide", "North America", "Europe", "Asia"],
            default=["Worldwide"],
            help="Select your target market regions (you can select multiple)"
        )
        
        submitted = st.form_submit_button("Analyze Market")

    if submitted and startup_name and pitch:
        # Industry filter with multiselect
        available_industries = list(set(comp["industry"] for comp in MOCK_COMPETITORS))
        selected_industries = st.multiselect(
            "Filter by Industry",
            available_industries,
            default=available_industries,
            help="Select industries to filter (you can select multiple)"
        )

        # Display filtered competitors in two columns
        col1, col2 = st.columns(2)
        
        # Filter competitors
        filtered_competitors = [
            comp for comp in MOCK_COMPETITORS 
            if comp["industry"] in (selected_industries if selected_industries else available_industries)
        ]
        
        # Display competitors in two columns
        for i, competitor in enumerate(filtered_competitors):
            with col1 if i % 2 == 0 else col2:
                st.markdown(f"""
                    <div class="competitor-card">
                        <div class="card-header">
                            <h2 class="company-name">{competitor['name']}</h2>
                            <p class="company-industry">{competitor['industry']}</p>
                        </div>
                        <div class="card-content">
                            <p class="description-text">{competitor['description']}</p>
                            <div>
                                <h3 style="font-size: 0.875rem; font-weight: 600; margin-bottom: 0.5rem;">Key Differentiator</h3>
                                <p class="description-text" style="margin-bottom: 1rem;">{competitor['keyDifferentiator']}</p>
                            </div>
                            <a href="{competitor['website']}" target="_blank" class="website-link">
                                Visit Website
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" 
                                     fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" 
                                     stroke-linejoin="round" style="margin-left: 0.5rem;">
                                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                    <polyline points="15 3 21 3 21 9"></polyline>
                                    <line x1="10" y1="14" x2="21" y2="3"></line>
                                </svg>
                            </a>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        # Display competitors
        for competitor in filtered_competitors:
            st.markdown(f"""
                <div class="competitor-card">
                    <div class="card-header">
                        <h2 class="company-name">{competitor['name']}</h2>
                        <p class="company-industry">{competitor['industry']}</p>
                    </div>
                    <div class="card-content">
                        <p class="description-text">{competitor['description']}</p>
                        <div>
                            <h3 style="font-size: 0.875rem; font-weight: 600; margin-bottom: 0.5rem;">Key Differentiator</h3>
                            <p class="description-text" style="margin-bottom: 1rem;">{competitor['keyDifferentiator']}</p>
                        </div>
                        <a href="{competitor['website']}" target="_blank" class="website-link">
                            Visit Website
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" 
                                 fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" 
                                 stroke-linejoin="round" style="margin-left: 0.5rem;">
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                <polyline points="15 3 21 3 21 9"></polyline>
                                <line x1="10" y1="14" x2="21" y2="3"></line>
                            </svg>
                        </a>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # Export button
        if filtered_competitors:
            st.markdown(export_to_csv(filtered_competitors), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
