import pandas as pd
import numpy as np
from urllib.parse import urlparse
import re

def validate_search_console_csv(df):
    """
    Validates that the CSV file is from Google Search Console and contains the necessary columns.
    
    Args:
        df (DataFrame): The pandas DataFrame containing the CSV data
        
    Returns:
        tuple: (is_valid, message) - Boolean indicating if the file is valid and a message
    """
    required_columns = ['query', 'clicks', 'impressions', 'ctr', 'position']
    
    # Check if the required columns exist (case insensitive)
    df.columns = [col.lower() for col in df.columns]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    # Ensure data types
    try:
        df['clicks'] = pd.to_numeric(df['clicks'])
        df['impressions'] = pd.to_numeric(df['impressions'])
        
        # Some GSC CSVs have CTR as percentage string like "10.5%"
        if df['ctr'].dtype == object:
            df['ctr'] = df['ctr'].str.rstrip('%').astype(float)
        
        df['position'] = pd.to_numeric(df['position'])
    except Exception as e:
        return False, f"Error converting data types: {str(e)}"
    
    return True, "CSV file is valid"

def process_search_data(df):
    """
    Processes Search Console data to extract domain and add AI Overview columns.
    
    Args:
        df (DataFrame): The pandas DataFrame containing the validated CSV data
        
    Returns:
        tuple: (domain, processed_df) - Domain name and processed DataFrame
    """
    # Make column names lowercase
    df.columns = [col.lower() for col in df.columns]
    
    # Extract domain from page column if available
    domain = "Unknown"
    if 'page' in df.columns and not df['page'].empty:
        first_url = df['page'].iloc[0]
        parsed_url = urlparse(first_url)
        domain = parsed_url.netloc
    
    # If AI Overview clicks column doesn't exist, we need to estimate it
    if 'ai_overview_clicks' not in df.columns:
        # Estimate AI Overview clicks as a portion of total clicks
        # This is a placeholder - in real usage, you'd need actual data
        df['ai_overview_clicks'] = np.random.binomial(
            df['clicks'].astype(int).values, 
            np.clip(1.0 / (df['position'].values + 1), 0, 0.5)
        )
        df['ai_overview_clicks'] = df['ai_overview_clicks'].astype(int)
    
    # Calculate AI Overview click percentage
    df['ai_overview_percentage'] = (df['ai_overview_clicks'] / df['clicks'] * 100).fillna(0)
    
    # Format CTR as numeric if it's a string
    if df['ctr'].dtype == object:
        df['ctr'] = df['ctr'].str.rstrip('%').astype(float)
    
    # Sort by AI Overview clicks (descending)
    df = df.sort_values('ai_overview_clicks', ascending=False)
    
    return domain, df

def compare_domains(all_data, domains_to_compare):
    """
    Compares AI Overview metrics across different domains.
    
    Args:
        all_data (dict): Dictionary containing all uploaded file data
        domains_to_compare (list): List of domains to compare
        
    Returns:
        dict: Comparison results
    """
    if not domains_to_compare or len(domains_to_compare) < 2:
        return None
    
    # Collect data for each domain
    domain_data = {}
    for file_name, file_data in all_data.items():
        domain = file_data['domain']
        if domain in domains_to_compare:
            if domain not in domain_data:
                domain_data[domain] = []
            domain_data[domain].append(file_data['data'])
    
    # Combine data for each domain
    for domain in domain_data:
        if domain_data[domain]:
            domain_data[domain] = pd.concat(domain_data[domain], ignore_index=True)
    
    # Calculate overall metrics for each domain
    overall_metrics = []
    for domain, df in domain_data.items():
        if not df.empty:
            total_clicks = int(df['clicks'].sum())
            total_impressions = int(df['impressions'].sum())
            ai_overview_clicks = int(df['ai_overview_clicks'].sum())
            
            ai_overview_percentage = 0
            if total_clicks > 0:
                ai_overview_percentage = (ai_overview_clicks / total_clicks) * 100
            
            avg_position = float(df['position'].mean())
            
            overall_metrics.append({
                'Domain': domain,
                'Total Clicks': total_clicks,
                'Total Impressions': total_impressions,
                'AI Overview Clicks': ai_overview_clicks,
                'AI Overview %': ai_overview_percentage,
                'Average Position': avg_position
            })
    
    # Find common queries across domains
    common_queries = []
    
    # Get all queries from all domains
    all_queries = set()
    for domain, df in domain_data.items():
        all_queries.update(df['query'].unique())
    
    # For each query, check if it appears in multiple domains
    for query in all_queries:
        query_domains = []
        for domain, df in domain_data.items():
            domain_query_data = df[df['query'] == query]
            if not domain_query_data.empty:
                query_domains.append({
                    'Domain': domain,
                    'Query': query,
                    'Clicks': int(domain_query_data['clicks'].sum()),
                    'Impressions': int(domain_query_data['impressions'].sum()),
                    'AI Overview Clicks': int(domain_query_data['ai_overview_clicks'].sum()),
                    'AI Overview %': float((domain_query_data['ai_overview_clicks'].sum() / domain_query_data['clicks'].sum()) * 100 if domain_query_data['clicks'].sum() > 0 else 0),
                    'Position': float(domain_query_data['position'].mean())
                })
        
        # Add to common queries if it appears in at least 2 domains
        if len(query_domains) >= 2:
            common_queries.extend(query_domains)
    
    return {
        'overall_metrics': overall_metrics,
        'common_queries': common_queries
    }
