# AI Overview Click Analytics Dashboard

This Streamlit dashboard helps you analyze and compare AI Overview Clicks from Google Search Console data. It provides insights on how AI Overview affects your website's organic search traffic.

## Features

- **Upload & Analyze Data**: Upload Google Search Console CSV files and view key metrics
- **Keyword Analysis**: Analyze specific keywords across different domains
- **Domain/URL Analysis**: Analyze specific domains or URL paths
- **Comparison Analytics**: Compare metrics across different domains

## How to Use

1. Export your Google Search Console data as CSV (must include query, clicks, impressions, CTR, position columns)
2. Upload the CSV files to the dashboard
3. Explore the various tabs to gain insights into your AI Overview metrics

## Local Setup

To run the dashboard locally:

```bash
pip install streamlit pandas numpy plotly trafilatura
streamlit run app.py
```

## Deployment

This app can be deployed on Streamlit Cloud or similar platforms.

## Sample Data

The repository includes sample data files that demonstrate how the dashboard works:
- sample_data.csv (example.com)
- sample_data_domain2.csv (cookingsite.com)