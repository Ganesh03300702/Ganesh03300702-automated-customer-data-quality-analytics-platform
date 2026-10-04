# Automated Customer Data Quality & Analytics Platform

A reusable Streamlit application for structured CSV/XLSX data quality, profiling, validation, SQL analysis and reporting.

## Features
- CSV and XLSX upload
- Dynamic column normalization; no fixed engineering/customer schema
- Dataset profiling and semantic column detection
- Missing-value and duplicate detection
- Applicable email, phone, date, age and numeric checks
- Valid / Invalid / Review Required classification
- SQLite SQL layer
- Quality dashboard and analytics
- Excel and CSV report downloads

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit deployment
1. Create a GitHub repository named `automated-customer-data-quality-analytics-platform`.
2. Upload all project files, keeping `app.py`, `requirements.txt`, and the `utils` folder.
3. In Streamlit Community Cloud, deploy the repository and select `app.py` as the main file.

## Scope
The application is designed for structured tabular CSV/XLSX data. It applies generic and semantically applicable quality checks; custom business rules still need to be configured for a specific organization.
