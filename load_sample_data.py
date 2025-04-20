import streamlit as st
import pandas as pd
import os

# This script loads the sample data files into the Streamlit app
# to demonstrate the functionality without requiring manual uploads

def main():
    # Clear any existing session state for fresh demo
    if 'uploaded_files_data' in st.session_state:
        st.session_state.uploaded_files_data = {}
    if 'domains' in st.session_state:
        st.session_state.domains = []
    if 'comparison_data' in st.session_state:
        st.session_state.comparison_data = None
    
    # Load sample data files
    sample_files = [
        "sample_data.csv",
        "sample_data_domain2.csv"
    ]
    
    from utils import validate_search_console_csv, process_search_data
    
    # Process each sample file
    for file_name in sample_files:
        if os.path.exists(file_name):
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
                    
                    st.success(f"Successfully loaded sample data for domain: {domain}")
                else:
                    st.error(f"Error processing {file_name}: {message}")
            
            except Exception as e:
                st.error(f"Error processing {file_name}: {str(e)}")
    
    # Display a message
    st.info("""
    Sample data has been automatically loaded for demonstration purposes.
    You can explore all tabs to see how the dashboard works with this sample data.
    """)

if __name__ == "__main__":
    main()