# clean_linkedin_minimal.py

import pandas as pd
import re
import html
from bs4 import BeautifulSoup

INPUT = "data/linkedIn_job_postings.csv"
OUTPUT = "data/linkedin_cleaned.csv"

def clean_html(text: str) -> str:
    if pd.isna(text):
        return ""
    text = html.unescape(str(text))
    soup = BeautifulSoup(text, "lxml")
    text = soup.get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def main():
    print("[+] Loading dataset...")
    df = pd.read_csv(INPUT)

    # попробуем угадать названия колонок
    possible_title_cols = ["title", "job_title", "Job Title"]
    possible_desc_cols  = ["description", "job_description", "Job Description"]

    title_col = next(c for c in possible_title_cols if c in df.columns)
    desc_col  = next(c for c in possible_desc_cols if c in df.columns)

    print(f"[+] Using columns: {title_col}, {desc_col}")

    df = df[[title_col, desc_col]].copy()
    df.columns = ["title", "description"]

    print("[+] Cleaning HTML & text...")
    df["title"] = df["title"].astype(str).apply(clean_html)
    df["description"] = df["description"].astype(str).apply(clean_html)

    # убираем совсем пустое
    df = df[df["description"].str.len() > 30]

    print(f"[+] Final shape: {df.shape}")
    print("[+] Saving minimal dataset...")

    df.to_csv(OUTPUT, index=False)
    print(f"[+] Saved to {OUTPUT}")

if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("data/linkedin_cleaned.csv")

    before = len(df)
    df = df.drop_duplicates(subset=["title", "description"])
    after = len(df)

    print(f"Dropped duplicates: {before - after}")
    df.to_csv(OUTPUT, index=False)
    print(f"[+] Saved to {OUTPUT}")

