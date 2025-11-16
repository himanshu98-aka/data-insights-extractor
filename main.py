import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from gemini_api import get_api_keys, generate_with_failover

# Page config
st.set_page_config(
    page_title="AI Data Insights Generator",
    layout="wide",
    page_icon="📊"
)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'insights' not in st.session_state:
    st.session_state.insights = None

# Title
st.title("📊 AI Dataset Insights Generator")
st.markdown("Upload your dataset and get instant AI-powered insights with customizable visualizations")

# Sidebar
st.sidebar.header("📁 Upload Dataset")
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV or Excel file",
    type=['csv', 'xlsx', 'xls'],
    help="Supported formats: CSV, Excel"
)

# API Key Status
api_keys = get_api_keys()
if api_keys:
    st.sidebar.success(f"✅ {len(api_keys)} API key(s) configured")
else:
    st.sidebar.warning("⚠️ No API keys found. AI Insights will not work.")

# Load data
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        
        st.sidebar.success(f"✅ Loaded {len(st.session_state.df)} rows")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")

# Main content
if st.session_state.df is not None:
    df = st.session_state.df
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🎨 Visualizations", "🤖 AI Insights", "📊 Custom Analysis"])
    
    # Tab 1: Overview
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
        
        # Data preview
        st.subheader("📋 Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Column info
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Column Information")
            col_info = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes.values,
                'Non-Null': df.count().values,
                'Null': df.isnull().sum().values
            })
            st.dataframe(col_info, use_container_width=True)
        
        with col2:
            st.subheader("📈 Statistical Summary")
            st.dataframe(df.describe(), use_container_width=True)
    
    # Tab 2: Visualizations
    with tab2:
        st.subheader("🎨 Create Custom Visualizations")
        
        # Chart type selector
        chart_type = st.selectbox(
            "Select Chart Type",
            ["Bar Chart", "Line Chart", "Scatter Plot", "Histogram", "Box Plot", 
             "Pie Chart", "Heatmap", "Area Chart", "Violin Plot", "Sunburst Chart"]
        )
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        all_cols = df.columns.tolist()
        
        col1, col2 = st.columns(2)
        
        # Chart configurations
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
        
        elif chart_type == "Area Chart":
            with col1:
                x_axis = st.selectbox("X-axis", all_cols)
            with col2:
                y_axis = st.selectbox("Y-axis", numeric_cols)
            
            color = st.selectbox("Color by (optional)", [None] + all_cols)
            fig = px.area(df, x=x_axis, y=y_axis, color=color,
                         title=f"{y_axis} over {x_axis}")
        
        elif chart_type == "Violin Plot":
            with col1:
                y_axis = st.selectbox("Y-axis (numeric)", numeric_cols)
            with col2:
                x_axis = st.selectbox("Group by (optional)", [None] + all_cols)
            
            fig = px.violin(df, y=y_axis, x=x_axis, title=f"Violin Plot of {y_axis}")
        
        elif chart_type == "Sunburst Chart":
            path_cols = st.multiselect("Path (hierarchy)", all_cols, max_selections=3)
            values = st.selectbox("Values", numeric_cols)
            
            if path_cols:
                fig = px.sunburst(df, path=path_cols, values=values,
                                title="Hierarchical Data View")
            else:
                fig = None
                st.warning("Please select at least one path column")
        
        # Display chart
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            
            # Customization options
            with st.expander("⚙️ Chart Customization"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    width = st.slider("Width", 400, 1400, 800)
                with col2:
                    height = st.slider("Height", 300, 800, 500)
                with col3:
                    theme = st.selectbox("Theme", ["plotly", "plotly_white", "plotly_dark"])
                
                fig.update_layout(width=width, height=height, template=theme)
                st.plotly_chart(fig, use_container_width=False)
    
    # Tab 3: AI Insights with Failover
    with tab3:
        st.subheader("🤖 AI-Powered Insights")
        
        if api_keys:
            if st.button("🔍 Generate AI Insights", type="primary"):
                with st.spinner("Analyzing your data with AI (using failover keys if needed)..."):
                    # Prepare data summary
                    data_summary = f"""
Dataset Overview:
- Total rows: {len(df)}
- Total columns: {len(df.columns)}
- Columns: {', '.join(df.columns.tolist())}

Sample Data:
{df.head(5).to_string()}

Statistical Summary:
{df.describe().to_string()}

Missing Values:
{df.isnull().sum().to_string()}
"""
                    
                    prompt = f"""
Analyze this dataset and provide comprehensive insights:

{data_summary}

Please provide:
1. Key findings and patterns
2. Data quality assessment
3. Interesting correlations or trends
4. Potential insights for decision-making
5. Recommendations for further analysis
6. Any anomalies or outliers detected

Format your response in clear sections with bullet points.
"""
                    
                    # Use the failover function
                    insights = generate_with_failover(prompt)
                    
                    if not insights.startswith("ERROR:"):
                        st.session_state.insights = insights
                    else:
                        st.error(insights)
            
            if st.session_state.insights:
                st.markdown(st.session_state.insights)
                
                # Download insights
                st.download_button(
                    "📥 Download Insights",
                    st.session_state.insights,
                    file_name="ai_insights.txt",
                    mime="text/plain"
                )
        else:
            st.warning("⚠️ Please configure GEMINI_API_KEY_1 (and optionally GEMINI_API_KEY_2) in secrets or .env file")
    
    # Tab 4: Custom Analysis
    with tab4:
        st.subheader("📊 Custom Data Analysis")
        
        analysis_type = st.selectbox(
            "Select Analysis Type",
            ["Filter Data", "Group By Analysis", "Pivot Table", "Export Data"]
        )
        
        if analysis_type == "Filter Data":
            st.markdown("#### Filter Your Data")
            
            filter_col = st.selectbox("Select column to filter", all_cols)
            
            if df[filter_col].dtype in ['object', 'category']:
                unique_values = df[filter_col].unique()
                selected_values = st.multiselect("Select values", unique_values)
                if selected_values:
                    filtered_df = df[df[filter_col].isin(selected_values)]
                else:
                    filtered_df = df
            else:
                min_val = float(df[filter_col].min())
                max_val = float(df[filter_col].max())
                range_values = st.slider("Select range", min_val, max_val, (min_val, max_val))
                filtered_df = df[(df[filter_col] >= range_values[0]) & (df[filter_col] <= range_values[1])]
            
            st.dataframe(filtered_df, use_container_width=True)
            st.info(f"Filtered data: {len(filtered_df)} rows")
        
        elif analysis_type == "Group By Analysis":
            st.markdown("#### Group By Analysis")
            
            group_col = st.selectbox("Group by column", all_cols)
            agg_col = st.selectbox("Aggregate column", numeric_cols)
            agg_func = st.selectbox("Aggregation function", ["mean", "sum", "count", "min", "max", "median"])
            
            grouped = df.groupby(group_col)[agg_col].agg(agg_func).reset_index()
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.dataframe(grouped, use_container_width=True)
            with col2:
                fig = px.bar(grouped, x=group_col, y=agg_col,
                           title=f"{agg_func.capitalize()} of {agg_col} by {group_col}")
                st.plotly_chart(fig)
        
        elif analysis_type == "Pivot Table":
            st.markdown("#### Create Pivot Table")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                index_col = st.selectbox("Index (rows)", all_cols)
            with col2:
                columns_col = st.selectbox("Columns", all_cols)
            with col3:
                values_col = st.selectbox("Values", numeric_cols)
            
            agg_func = st.selectbox("Aggregation", ["mean", "sum", "count"])
            
            pivot = pd.pivot_table(df, values=values_col, index=index_col, 
                                 columns=columns_col, aggfunc=agg_func)
            
            st.dataframe(pivot, use_container_width=True)
        
        elif analysis_type == "Export Data":
            st.markdown("#### Export Your Data")
            
            export_format = st.radio("Select format", ["CSV", "Excel", "JSON"])
            
            if export_format == "CSV":
                csv = df.to_csv(index=False)
                st.download_button("📥 Download CSV", csv, "data.csv", "text/csv")
            elif export_format == "Excel":
                from io import BytesIO
                buffer = BytesIO()
                df.to_excel(buffer, index=False)
                st.download_button("📥 Download Excel", buffer, "data.xlsx", 
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            elif export_format == "JSON":
                json_str = df.to_json(orient='records')
                st.download_button("📥 Download JSON", json_str, "data.json", "application/json")

else:
    # Welcome screen
    st.info("👈 Please upload a dataset to get started")
    
    st.markdown("### ✨ Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📊 Data Overview**
        - Automatic data profiling
        - Statistical summaries
        - Missing value detection
        """)
    
    with col2:
        st.markdown("""
        **🎨 Visualizations**
        - 10+ chart types
        - Interactive plots
        - Full customization
        """)
    
    with col3:
        st.markdown("""
        **🤖 AI Insights**
        - Powered by Gemini AI
        - Failover API keys
        - Smart recommendations
        """)
