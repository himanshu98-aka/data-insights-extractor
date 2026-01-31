import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from gemini_api import get_api_keys, generate_with_failover

# Page config set karne ke liye 
img = "logo/logo.png" 
st.set_page_config(
    page_title="Data Insights Generator",
    layout="wide",
    page_icon=img
)

# Session state initialize kar rahe hai taaki data reload na ho
if 'df' not in st.session_state:
    st.session_state.df = None
if 'insights' not in st.session_state:
    st.session_state.insights = None

# Main Title
st.title("Dataset Insights Generator")
st.markdown("Upload your dataset and get instant AI-powered insights.")

# Sidebar's upload options
st.sidebar.header(" Upload Dataset")
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV or Excel file",
    type=['csv', 'xlsx', 'xls'],
    help="Supported formats: CSV, Excel"
)

# API Key check karne ke liye 
api_keys = get_api_keys()
if api_keys:
    st.sidebar.success(f" {len(api_keys)} API key(s) connected")
else:
    st.sidebar.warning(" No API keys found. AI features will not work.")

# Data load karne ka logic
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        
        st.sidebar.success(f" Loaded {len(st.session_state.df)} rows")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")

# Agar data hai to dashboard dikhane ka logic 
if st.session_state.df is not None:
    df = st.session_state.df
    
    # Tabs create kane ke liye
    tab1, tab2, tab3 = st.tabs([" Overview", " Visualizations", " AI Insights"])
    
    # Tab 1: Basic Info
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Rows", len(df))
        with col2:
            st.metric("Total Columns", len(df.columns))
        with col3:
            st.metric("Numeric Columns", len(df.select_dtypes(include=['number']).columns))
        with col4:
            st.metric("Missing Values", df.isnull().sum().sum())
        
        st.markdown("---")
        
        # Data ka preview
        st.subheader(" Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Column ki details
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("ℹ Column Information")
            col_info = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes.values,
                'Non-Null': df.count().values,
                'Null': df.isnull().sum().values
            })
            st.dataframe(col_info, use_container_width=True)
        
        with col2:
            st.subheader(" Statistical Summary")
            st.dataframe(df.describe(), use_container_width=True)
    
    # Tab 2: Custom Visualizations tab starts here 
    with tab2:
        st.subheader(" Create Custom Visualizations")
        
        # Chart selection
        chart_type = st.selectbox(
            "Select Chart Type",
            ["Bar Chart", "Line Chart", "Scatter Plot", "Histogram", "Box Plot", 
             "Pie Chart", "Heatmap", "Area Chart"]
        )
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        all_cols = df.columns.tolist()
        
        col1, col2 = st.columns(2)
        
        # Chart logic starts from here 
        if chart_type == "Bar Chart":
            with col1:
                x_axis = st.selectbox("X-axis", all_cols)
            with col2:
                y_axis = st.selectbox("Y-axis", numeric_cols)
            
            color = st.selectbox("Color by (optional)", [None] + all_cols)
            fig = px.bar(df, x=x_axis, y=y_axis, color=color, title=f"{y_axis} by {x_axis}")
        
        elif chart_type == "Line Chart":
            with col1:
                x_axis = st.selectbox("X-axis", all_cols)
            with col2:
                y_axis = st.selectbox("Y-axis", numeric_cols)
            
            color = st.selectbox("Color by (optional)", [None] + all_cols)
            fig = px.line(df, x=x_axis, y=y_axis, color=color, title=f"{y_axis} over {x_axis}")
        
        elif chart_type == "Scatter Plot":
            with col1:
                x_axis = st.selectbox("X-axis", numeric_cols)
            with col2:
                y_axis = st.selectbox("Y-axis", numeric_cols)
            
            col3, col4 = st.columns(2)
            with col3:
                size = st.selectbox("Size by (optional)", [None] + numeric_cols)
            with col4:
                color = st.selectbox("Color by (optional)", [None] + all_cols)
            
            fig = px.scatter(df, x=x_axis, y=y_axis, size=size, color=color,
                           title=f"{y_axis} vs {x_axis}")
        
        elif chart_type == "Histogram":
            with col1:
                column = st.selectbox("Column", numeric_cols)
            with col2:
                bins = st.slider("Number of bins", 10, 100, 30)
            
            color = st.selectbox("Color by (optional)", [None] + all_cols)
            fig = px.histogram(df, x=column, nbins=bins, color=color,
                             title=f"Distribution of {column}")
        
        elif chart_type == "Box Plot":
            with col1:
                y_axis = st.selectbox("Y-axis (numeric)", numeric_cols)
            with col2:
                x_axis = st.selectbox("Group by (optional)", [None] + all_cols)
            
            fig = px.box(df, y=y_axis, x=x_axis, title=f"Box Plot of {y_axis}")
        
        elif chart_type == "Pie Chart":
            with col1:
                names = st.selectbox("Categories", all_cols)
            with col2:
                values = st.selectbox("Values", numeric_cols)
            
            fig = px.pie(df, names=names, values=values, title=f"{values} by {names}")
        
        elif chart_type == "Heatmap":
            correlation = df[numeric_cols].corr()
            fig = px.imshow(correlation, title="Correlation Heatmap",
                          color_continuous_scale='RdBu_r')
        
        # Chart display karne ke liye
        if 'fig' in locals() and fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # Tab 3: AI wala part
    with tab3:
        st.subheader("AI-Powered Insights")
        
        if api_keys:
            if st.button(" Generate AI Insights", type="primary"):
                with st.spinner("Analyzing your data with AI..."):
                    # Data context preparne ke liye < prompt create ke liye chat gpt use kiya hai >
                    data_context = f"""
Shape: {df.shape}
Head:
{df.head().to_string()}
Stats:
{df.describe().to_string()}
"""
                    # Prompt construct kar rahe hai
                    prompt = f"""

Analyze the following dataset and extract maximum possible insights.

Dataset Summary:
{data_context}

Instructions for response:
- Use ONLY short bullet points
- Do NOT write paragraphs
- Keep each point concise (1–2 lines max)
- Be specific and data-driven

Provide insights under these sections:

1. Key Findings & Patterns
   - Major observations
   - Notable distributions
   - Frequent values or dominant categories

2. Data Quality Assessment
   - Missing values (severity & impact)
   - Data consistency issues
   - Potential data leakage or redundancy

3. Correlations & Relationships
   - Strong positive/negative correlations
   - Unexpected relationships
   - Features with predictive potential

4. Trends & Variations
   - Increasing/decreasing trends
   - Seasonal or grouped variations
   - High-variance vs low-variance features

5. Anomalies & Outliers
   - Columns with extreme values
   - Possible data entry errors
   - Rare or unusual observations

6. Decision-Making Insights
   - Actionable business/real-world insights
   - High-impact features
   - Risk indicators or opportunity signals

7. Recommendations for Further Analysis
   - Feature engineering ideas
   - Additional visualizations to create
   - Advanced analysis or modeling suggestions

Return insights strictly as bullet points under each section.
"""
                    
                    # Failover function < heart of this project takes 2 weeks to solve >
                    insights = generate_with_failover(prompt)
                    
                    if not insights.startswith("ERROR:"):
                        st.session_state.insights = insights
                    else:
                        st.error(insights)
            
            if st.session_state.insights:
                st.markdown(st.session_state.insights)
                
                # Download insights
                st.download_button(
                    " Download Insights",
                    st.session_state.insights,
                    file_name="ai_insights.txt",
                    mime="text/plain"
                )
        else:
            st.warning("⚠️ Please configure API Keys in secrets or .env file.")
    
else:
    # Welcome screen
    st.info(" Please upload a dataset to get started")
    
    st.markdown("###  Features")
    st.markdown("""
    - **Data Overview**: Automatic data profiling and statistics
    - **Visualizations**: Create custom charts and plots
    - **AI Insights**: Get intelligent insights using Gemini AI
    """)
