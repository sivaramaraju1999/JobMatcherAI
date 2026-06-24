# pyrefly: ignore [missing-import]
from jobspy import scrape_jobs
import pandas as pd

df = scrape_jobs(
    site_name=["linkedin", "indeed"],
    search_term="software engineer",
    location="Remote",
    results_wanted=3
)
print("Columns:")
print(df.columns.tolist())
if not df.empty:
    print("First row data:")
    for col in df.columns:
        print(f"{col}: {df.iloc[0][col]}")
