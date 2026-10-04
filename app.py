import io
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

from utils.quality_engine import process_dataframe

st.set_page_config(page_title="Automated Customer Data Quality & Analytics Platform", page_icon="📊", layout="wide")

st.title("AUTOMATED CUSTOMER DATA QUALITY & ANALYTICS PLATFORM")
st.caption("Upload CSV/XLSX → Profile → Clean → Validate → Classify → Store in SQL → Analyze → Download")

@st.cache_data(show_spinner=False)
def read_file(file_bytes, filename):
    bio = io.BytesIO(file_bytes)
    if filename.lower().endswith(".csv"):
        return pd.read_csv(bio)
    return pd.read_excel(bio)

uploaded = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if not uploaded:
    st.info("Upload any structured tabular dataset to begin. Unknown columns are retained; applicable generic quality checks are applied automatically.")
    st.stop()

try:
    df = read_file(uploaded.getvalue(), uploaded.name)
    if df.empty:
        st.error("The uploaded file contains no rows.")
        st.stop()
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

result = process_dataframe(df)
profile = result["profile"]
quality = result["quality"]
classified = result["data"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df):,}")
c2.metric("Columns", f"{len(df.columns):,}")
c3.metric("Missing Cells", f"{quality['missing_cells']:,}")
c4.metric("Duplicate Rows", f"{quality['duplicate_rows']:,}")

st.subheader("Dataset Profile")
st.dataframe(profile, use_container_width=True, height=280)

st.subheader("Data Quality Summary")
q1, q2, q3 = st.columns(3)
q1.metric("Valid", f"{quality['valid_records']:,}")
q2.metric("Invalid", f"{quality['invalid_records']:,}")
q3.metric("Review Required", f"{quality['review_records']:,}")

st.write("**Detected checks:** " + (", ".join(quality["checks_applied"]) if quality["checks_applied"] else "Generic profiling only"))

st.subheader("Quality Results")
st.dataframe(classified.head(1000), use_container_width=True, height=360)

st.subheader("Analytics")
a, b = st.columns(2)
with a:
    st.write("Classification")
    st.bar_chart(classified["classification"].value_counts())
with b:
    st.write("Missing Values by Column")
    missing = classified.drop(columns=["classification", "quality_issues"], errors="ignore").isna().sum().sort_values(ascending=False)
    st.bar_chart(missing.head(15))

st.subheader("SQL Data Layer")
conn = sqlite3.connect(":memory:")
classified.to_sql("processed_data", conn, index=False, if_exists="replace")
sql_summary = pd.read_sql_query("SELECT classification, COUNT(*) AS records FROM processed_data GROUP BY classification", conn)
st.dataframe(sql_summary, use_container_width=True)
conn.close()

st.subheader("Download Reports")
report = io.BytesIO()
with pd.ExcelWriter(report, engine="openpyxl") as writer:
    classified.to_excel(writer, sheet_name="All Records", index=False)
    classified[classified["classification"] == "Valid"].to_excel(writer, sheet_name="Valid Records", index=False)
    classified[classified["classification"] == "Invalid"].to_excel(writer, sheet_name="Invalid Records", index=False)
    classified[classified["classification"] == "Review Required"].to_excel(writer, sheet_name="Review Required", index=False)
    profile.to_excel(writer, sheet_name="Profile", index=False)
    sql_summary.to_excel(writer, sheet_name="SQL Summary", index=False)

st.download_button("Download Excel Quality Report", report.getvalue(), file_name="data_quality_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.download_button("Download Processed CSV", classified.to_csv(index=False).encode("utf-8"), file_name="processed_data.csv", mime="text/csv")
st.caption(f"Processed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
