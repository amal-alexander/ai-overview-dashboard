import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import os.path
from utils import validate_search_console_csv, process_search_data, compare_domains

# Page configuration
st.set_page_config(
    page_title="AI Overview Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# App title and description
st.title("AI Overview Click Analytics Dashboard")
st.markdown("""
    This dashboard helps you analyze and compare AI Overview Clicks from Google Search Console data.
    Upload your Search Console CSV files, analyze individual keywords, or compare domains and pages.
""")

# Initialize session state variables
if 'uploaded_files_data' not in st.session_state:
    st.session_state.uploaded_files_data = {}
if 'domains' not in st.session_state:
    st.session_state.domains = []
if 'comparison_data' not in st.session_state:
    st.session_state.comparison_data = None
    
# Auto-load sample data if available and no data is uploaded yet
if not st.session_state.uploaded_files_data:
    sample_files = ["sample_data.csv", "sample_data_domain2.csv"]
    all_exist = all(os.path.exists(file) for file in sample_files)
    
    if all_exist:
        with st.spinner("Loading sample data for demonstration..."):
            for file_name in sample_files:
                try:
                    # Read the file
                    df = pd.read_csv(file_name)
                    
                    # Validate and process
                    is_valid, message = validate_search_console_csv(df)
                    
                    if is_valid:
                        # Process the data
                        domain, processed_data = process_search_data(df)
                        
                        if domain not in st.session_state.domains:
                            st.session_state.domains.append(domain)
                        
                        # Store the processed data
                        st.session_state.uploaded_files_data[file_name] = {
                            'domain': domain,
                            'data': processed_data
                        }
                
                except Exception as e:
                    st.error(f"Error loading sample data: {str(e)}")
            
            if st.session_state.uploaded_files_data:
                st.success("Sample data loaded for demonstration purposes.")

# Create tabs for different functionalities
tab1, tab2, tab3, tab4 = st.tabs([
    "Upload & Analyze Data", 
    "Keyword Analysis", 
    "Domain/URL Analysis", 
    "Comparison Analytics"
])

# Tab 1: Upload & Analyze Data
with tab1:
    st.header("Upload Search Console Data")
    st.markdown("""
        Upload CSV files exported from Google Search Console. The files should contain:
        - Query data
        - Clicks, Impressions, CTR, Position metrics
        - AI Overview click data
    """)
    
    uploaded_files = st.file_uploader(
        "Upload Search Console CSV files",
        type=['csv'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Process each file
            file_content = uploaded_file.read()
            
            try:
                # Validate and process the file
                df = pd.read_csv(io.BytesIO(file_content))
                
                # Check if it's a valid Search Console export
                is_valid, message = validate_search_console_csv(df)
                
                if is_valid:
                    # Process the data
                    domain, processed_data = process_search_data(df)
                    
                    if domain not in st.session_state.domains:
                        st.session_state.domains.append(domain)
                    
                    # Store the processed data
                    st.session_state.uploaded_files_data[uploaded_file.name] = {
                        'domain': domain,
                        'data': processed_data
                    }
                    
                    st.success(f"Successfully processed {uploaded_file.name} for domain: {domain}")
                else:
                    st.error(f"Error processing {uploaded_file.name}: {message}")
            
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
    
    # Display data summaries if available
    if st.session_state.uploaded_files_data:
        st.header("Data Overview")
        
        # Select file to analyze
        file_names = list(st.session_state.uploaded_files_data.keys())
        selected_file = st.selectbox("Select file to analyze:", file_names)
        
        if selected_file:
            data = st.session_state.uploaded_files_data[selected_file]
            df = data['data']
            domain = data['domain']
            
            # Display metrics
            st.subheader(f"Domain: {domain}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Queries", len(df))
            with col2:
                st.metric("Total Clicks", int(df['clicks'].sum()))
            with col3:
                st.metric("AI Overview Clicks", int(df['ai_overview_clicks'].sum()))
            with col4:
                if df['clicks'].sum() > 0:
                    ai_click_percentage = (df['ai_overview_clicks'].sum() / df['clicks'].sum()) * 100
                    st.metric("AI Overview %", f"{ai_click_percentage:.2f}%")
                else:
                    st.metric("AI Overview %", "N/A")
            
            # Top queries affected by AI Overview
            st.subheader("Top Queries Affected by AI Overview")
            top_ai_queries = df.sort_values('ai_overview_clicks', ascending=False).head(10)
            
            if not top_ai_queries.empty:
                # Create a horizontal bar chart
                fig = px.bar(
                    top_ai_queries,
                    x='ai_overview_clicks',
                    y='query',
                    orientation='h',
                    title="Top Queries by AI Overview Clicks",
                    labels={'ai_overview_clicks': 'AI Overview Clicks', 'query': 'Query'},
                    color='ai_overview_percentage',
                    color_continuous_scale='Reds',
                )
                
                fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
                
                # Display data table with more details
                display_df = top_ai_queries[['query', 'clicks', 'impressions', 'ai_overview_clicks', 'ai_overview_percentage', 'position']]
                display_df = display_df.rename(columns={
                    'query': 'Query',
                    'clicks': 'Clicks',
                    'impressions': 'Impressions',
                    'ai_overview_clicks': 'AI Overview Clicks',
                    'ai_overview_percentage': 'AI Overview %',
                    'position': 'Position'
                })
                
                # Format the percentages
                display_df['AI Overview %'] = display_df['AI Overview %'].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("No AI Overview clicks data found in this dataset.")

# Tab 2: Keyword Analysis
with tab2:
    st.header("Single Keyword Analysis")
    
    # Check if we have any data uploaded
    if not st.session_state.uploaded_files_data:
        st.warning("Please upload Search Console data files first in the 'Upload & Analyze Data' tab.")
    else:
        # Input field for keyword
        keyword = st.text_input("Enter a keyword to analyze:")
        
        if keyword:
            # Find this keyword across all uploaded files
            keyword_data = []
            
            for file_name, data in st.session_state.uploaded_files_data.items():
                df = data['data']
                domain = data['domain']
                
                # Find rows matching the keyword (case insensitive)
                matches = df[df['query'].str.lower() == keyword.lower()]
                
                if not matches.empty:
                    for _, row in matches.iterrows():
                        keyword_data.append({
                            'Domain': domain,
                            'Clicks': row['clicks'],
                            'Impressions': row['impressions'],
                            'AI Overview Clicks': row['ai_overview_clicks'],
                            'AI Overview %': f"{row['ai_overview_percentage']:.2f}%",
                            'Position': row['position'],
                            'CTR': f"{row['ctr']}%"
                        })
            
            if keyword_data:
                st.subheader(f"Results for: '{keyword}'")
                
                # Convert to DataFrame for display
                keyword_df = pd.DataFrame(keyword_data)
                st.dataframe(keyword_df, use_container_width=True)
                
                # Create comparison visualization
                if len(keyword_data) > 1:
                    st.subheader("Domain Comparison for this Keyword")
                    
                    fig = px.bar(
                        keyword_df,
                        x='Domain',
                        y='AI Overview Clicks',
                        title=f"AI Overview Clicks Comparison for '{keyword}'",
                        color='Domain'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Position vs AI Overview visualization
                if len(keyword_data) > 0:
                    # Convert percentage string to float
                    keyword_df['AI Overview % (numeric)'] = keyword_df['AI Overview %'].str.rstrip('%').astype(float)
                    
                    fig = px.scatter(
                        keyword_df,
                        x='Position',
                        y='AI Overview % (numeric)',
                        size='Clicks',
                        color='Domain',
                        hover_data=['Impressions', 'CTR'],
                        labels={'AI Overview % (numeric)': 'AI Overview %'},
                        title=f"Position vs AI Overview % for '{keyword}'"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No data found for the keyword '{keyword}' in the uploaded files.")

# Tab 3: Domain/URL Analysis
with tab3:
    st.header("Domain & Page Analysis")
    
    if not st.session_state.uploaded_files_data:
        st.warning("Please upload Search Console data files first in the 'Upload & Analyze Data' tab.")
    else:
        # Domain selection
        domain_options = ["All Domains"] + st.session_state.domains
        selected_domain = st.selectbox("Select Domain:", domain_options)
        
        # URL path input
        url_path = st.text_input("Enter URL path to analyze (leave empty for domain-level analysis):", "")
        
        if selected_domain:
            # Filter data based on domain selection
            if selected_domain == "All Domains":
                # Use all data
                all_data = []
                for file_data in st.session_state.uploaded_files_data.values():
                    all_data.append(file_data['data'])
                
                if all_data:
                    combined_df = pd.concat(all_data, ignore_index=True)
                else:
                    combined_df = pd.DataFrame()
            else:
                # Filter for selected domain
                domain_data = []
                for file_data in st.session_state.uploaded_files_data.values():
                    if file_data['domain'] == selected_domain:
                        domain_data.append(file_data['data'])
                
                if domain_data:
                    combined_df = pd.concat(domain_data, ignore_index=True)
                else:
                    combined_df = pd.DataFrame()
            
            # Further filter based on URL path if provided
            if url_path and not combined_df.empty and 'page' in combined_df.columns:
                combined_df = combined_df[combined_df['page'].str.contains(url_path, case=False, na=False)]
            
            if not combined_df.empty:
                # Display metrics
                st.subheader("AI Overview Metrics")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Queries", len(combined_df))
                with col2:
                    st.metric("Total Clicks", int(combined_df['clicks'].sum()))
                with col3:
                    st.metric("AI Overview Clicks", int(combined_df['ai_overview_clicks'].sum()))
                with col4:
                    if combined_df['clicks'].sum() > 0:
                        ai_click_percentage = (combined_df['ai_overview_clicks'].sum() / combined_df['clicks'].sum()) * 100
                        st.metric("AI Overview %", f"{ai_click_percentage:.2f}%")
                    else:
                        st.metric("AI Overview %", "N/A")
                
                # Time series analysis if date column exists
                if 'date' in combined_df.columns:
                    st.subheader("AI Overview Trend")
                    
                    # Group by date
                    date_df = combined_df.groupby('date').agg({
                        'clicks': 'sum',
                        'impressions': 'sum',
                        'ai_overview_clicks': 'sum'
                    }).reset_index()
                    
                    # Calculate AI Overview percentage
                    date_df['ai_overview_percentage'] = (date_df['ai_overview_clicks'] / date_df['clicks'] * 100).fillna(0)
                    
                    # Create time series chart
                    fig = px.line(
                        date_df,
                        x='date',
                        y=['clicks', 'ai_overview_clicks'],
                        title="AI Overview Clicks vs Total Clicks Over Time",
                        labels={'value': 'Count', 'date': 'Date', 'variable': 'Metric'},
                        color_discrete_map={'clicks': 'blue', 'ai_overview_clicks': 'red'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # AI Overview percentage trend
                    fig2 = px.line(
                        date_df,
                        x='date',
                        y='ai_overview_percentage',
                        title="AI Overview Percentage Over Time",
                        labels={'ai_overview_percentage': 'AI Overview %', 'date': 'Date'}
                    )
                    fig2.update_traces(line_color='red')
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Page level analysis if page column exists
                if 'page' in combined_df.columns and selected_domain != "All Domains":
                    st.subheader("Top Pages Affected by AI Overview")
                    
                    # Group by page
                    page_df = combined_df.groupby('page').agg({
                        'clicks': 'sum',
                        'impressions': 'sum',
                        'ai_overview_clicks': 'sum',
                    }).reset_index()
                    
                    # Calculate AI Overview percentage
                    page_df['ai_overview_percentage'] = (page_df['ai_overview_clicks'] / page_df['clicks'] * 100).fillna(0)
                    
                    # Sort by AI Overview clicks
                    top_pages = page_df.sort_values('ai_overview_clicks', ascending=False).head(10)
                    
                    if not top_pages.empty:
                        # Create bar chart
                        fig = px.bar(
                            top_pages,
                            x='ai_overview_clicks',
                            y='page',
                            orientation='h',
                            title="Top Pages by AI Overview Clicks",
                            labels={'ai_overview_clicks': 'AI Overview Clicks', 'page': 'Page'},
                            color='ai_overview_percentage',
                            color_continuous_scale='Reds',
                        )
                        
                        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display data table
                        display_df = top_pages[['page', 'clicks', 'impressions', 'ai_overview_clicks', 'ai_overview_percentage']]
                        display_df = display_df.rename(columns={
                            'page': 'Page',
                            'clicks': 'Clicks',
                            'impressions': 'Impressions',
                            'ai_overview_clicks': 'AI Overview Clicks',
                            'ai_overview_percentage': 'AI Overview %'
                        })
                        
                        # Format percentages
                        display_df['AI Overview %'] = display_df['AI Overview %'].apply(lambda x: f"{x:.2f}%")
                        
                        st.dataframe(display_df, use_container_width=True)
            else:
                if url_path:
                    st.info(f"No data found for URL path containing '{url_path}'.")
                else:
                    st.info(f"No data available for the selected domain.")

# Tab 4: Comparison Analytics
with tab4:
    st.header("Compare Domains and Pages")
    
    if len(st.session_state.domains) < 2:
        st.warning("Please upload data for at least two domains to enable comparison.")
    else:
        st.subheader("Domain Comparison")
        
        # Select domains to compare
        selected_domains = st.multiselect(
            "Select domains to compare:",
            options=st.session_state.domains,
            default=st.session_state.domains[:2] if len(st.session_state.domains) >= 2 else st.session_state.domains
        )
        
        if len(selected_domains) >= 2:
            # Generate comparison data
            comparison_data = compare_domains(st.session_state.uploaded_files_data, selected_domains)
            
            if comparison_data:
                # Create overall metrics comparison
                st.subheader("Overall Metrics Comparison")
                
                # Metrics table
                metrics_df = pd.DataFrame(comparison_data['overall_metrics'])
                st.dataframe(metrics_df, use_container_width=True)
                
                # Visualization of AI Overview metrics
                st.subheader("AI Overview Impact Comparison")
                
                # Create comparison bar chart
                fig = px.bar(
                    metrics_df,
                    x='Domain',
                    y=['Total Clicks', 'AI Overview Clicks'],
                    barmode='group',
                    title="Clicks vs AI Overview Clicks by Domain",
                    labels={'value': 'Count', 'variable': 'Metric'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # AI Overview percentage comparison
                fig2 = px.bar(
                    metrics_df,
                    x='Domain',
                    y='AI Overview %',
                    title="AI Overview Percentage by Domain",
                    labels={'AI Overview %': 'Percentage'},
                    color='Domain'
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                # Common queries analysis
                if 'common_queries' in comparison_data and comparison_data['common_queries']:
                    st.subheader("Common Queries Analysis")
                    
                    common_queries_df = pd.DataFrame(comparison_data['common_queries'])
                    st.dataframe(common_queries_df, use_container_width=True)
                    
                    # Visualization for common queries
                    selected_query = st.selectbox(
                        "Select a query to compare across domains:",
                        options=common_queries_df['Query'].unique()
                    )
                    
                    if selected_query:
                        query_data = common_queries_df[common_queries_df['Query'] == selected_query]
                        
                        # Create visualization
                        fig = go.Figure()
                        
                        for domain in selected_domains:
                            domain_data = query_data[query_data['Domain'] == domain]
                            if not domain_data.empty:
                                fig.add_trace(go.Bar(
                                    name=f"{domain} - Total Clicks",
                                    x=[domain],
                                    y=domain_data['Clicks'],
                                    marker_color='blue',
                                    opacity=0.7
                                ))
                                
                                fig.add_trace(go.Bar(
                                    name=f"{domain} - AI Overview Clicks",
                                    x=[domain],
                                    y=domain_data['AI Overview Clicks'],
                                    marker_color='red',
                                    opacity=0.7
                                ))
                        
                        fig.update_layout(
                            title=f"Comparison for Query: '{selected_query}'",
                            barmode='group',
                            xaxis_title="Domain",
                            yaxis_title="Clicks"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Position comparison
                        fig2 = px.bar(
                            query_data,
                            x='Domain',
                            y='Position',
                            title=f"Position Comparison for Query: '{selected_query}'",
                            labels={'Position': 'Average Position (lower is better)'},
                            color='Domain'
                        )
                        
                        # Invert y-axis so lower positions (better rankings) are on top
                        fig2.update_layout(yaxis={'autorange': 'reversed'})
                        
                        st.plotly_chart(fig2, use_container_width=True)
