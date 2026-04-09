"""
University Lead Name Finder v2
- Uses DuckDuckGo (less blocking than Google)
- Faster delays (2-4 sec instead of 8-12)
- Better name extraction
- Skips rows that already have real names
"""

import pandas as pd
import requests
import re
import time
import random
import os
from datetime import datetime

INPUT_FILE = "University Leads final done.xlsx"
OUTPUT_FILE = "leads_with_names.xlsx"
PROGRESS_FILE = "progress_v2.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

ROLE_SEARCH = {
    "Director of Research Communications": "director research communications",
    "VP of Research / Research Dean":      "vice president research OR VP research",
    "Director of Digital Learning":        "director digital learning OR educational technology",
    "Director of Digital Learning / Educational Technology": "director digital learning educational technology",
    "Head of Libraries":                   "university librarian OR dean of libraries OR head of libraries",
    "Provost":                             "provost",
    "SVP for Research & Innovation":       "senior vice president research",
}

def get_saved_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return int(f.read().strip())
    return 0

def save_progress(idx):
    with open(PROGRESS_FILE, "w") as f:
        f.write(str(idx))

def clean_html(html):
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL)
    html = re.sub(r'<[^>]+>', ' ', html)
    html = re.sub(r'&amp;', '&', html)
    html = re.sub(r'&nbsp;', ' ', html)
    html = re.sub(r'&#\d+;', '', html)
    html = re.sub(r'\s+', ' ', html)
    return html

def extract_name(text, university, role):
    """Extract a person's name from search result text."""
    
    # Clean up text
    text = text[:5000]
    
    # Pattern 1: "Dr. Firstname Lastname" near role keywords
    role_keywords = role.lower().replace('/', '').replace('-', ' ').split()[:3]
    
    patterns = [
        # Dr./Prof. prefix
        r'\b(Dr\.?\s+[A-Z][a-z]{1,15}(?:\s+[A-Z]\.?\s+)?[A-Z][a-zA-Z\'\-]{1,20})\b',
        r'\b(Prof(?:essor)?\.?\s+[A-Z][a-z]{1,15}\s+[A-Z][a-zA-Z\'\-]{1,20})\b',
        # Name followed by title
        r'\b([A-Z][a-z]{1,15}\s+(?:[A-Z]\.\s+)?[A-Z][a-zA-Z\'\-]{1,20}),?\s+(?:Ph\.?D|MD|EdD|JD)\b',
        r'\b([A-Z][a-z]{1,15}\s+[A-Z][a-zA-Z\'\-]{1,20})\s+(?:is|serves as|was appointed|named)\s+(?:the\s+)?(?:Vice|Senior|Associate|Assistant|Interim)?\s*(?:President|Provost|Director|Dean|Librarian|Chancellor)',
        # "appointed X as Director"
        r'appointed\s+([A-Z][a-z]{1,15}\s+[A-Z][a-zA-Z\'\-]{1,20})\s+as',
        # "X, Director of..."  
        r'\b([A-Z][a-z]{1,15}\s+[A-Z][a-zA-Z\'\-]{1,20}),\s+(?:Vice|Senior|Associate|Assistant|Interim|Executive)?\s*(?:Vice\s+)?(?:President|Provost|Director|Dean|Librarian|Chancellor)',
    ]
    
    SKIP_WORDS = {
        'University', 'College', 'Institute', 'School', 'Department', 'Office',
        'Center', 'Research', 'Library', 'Academic', 'United', 'States', 'New',
        'North', 'South', 'East', 'West', 'National', 'American', 'January',
        'February', 'March', 'April', 'June', 'July', 'August', 'September',
        'October', 'November', 'December', 'Monday', 'Tuesday', 'Wednesday',
        'Thursday', 'Friday', 'Saturday', 'Sunday', 'Read', 'More', 'Skip',
        'View', 'About', 'Contact', 'Home', 'News', 'Events', 'Faculty',
        'Student', 'Graduate', 'Undergraduate', 'Annual', 'Report', 'Press'
    }
    
    for pat in patterns:
        matches = re.finditer(pat, text)
        for m in matches:
            name = m.group(1).strip()
            # Remove leading Dr./Prof.
            name_clean = re.sub(r'^(Dr\.?|Prof(?:essor)?\.?)\s+', '', name).strip()
            parts = name_clean.split()
            if len(parts) < 2 or len(parts) > 4:
                continue
            if any(p in SKIP_WORDS for p in parts):
                continue
            if any(p[0].islower() for p in parts if len(p) > 1):
                continue
            # Check name is near university name
            uni_words = university.replace('University', '').replace('College', '').strip().split()[:2]
            uni_nearby = any(w in text[max(0, text.find(name)-200):text.find(name)+200] 
                           for w in uni_words if len(w) > 3)
            if uni_nearby or len(patterns) > 3:  # be lenient with later patterns
                return name_clean
    return None

def search_ddg(query):
    """Search DuckDuckGo HTML version."""
    try:
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query, "b": "", "kl": "us-en"}
        resp = requests.post(url, data=data, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            return clean_html(resp.text)
    except Exception as e:
        pass
    return ""

def find_name(university, role):
    role_query = ROLE_SEARCH.get(role, role.split('/')[0].strip())
    
    # Primary search
    query1 = f'"{university}" {role_query} name'
    text1 = search_ddg(query1)
    if text1:
        name = extract_name(text1, university, role)
        if name:
            return name
    
    time.sleep(random.uniform(1, 2))
    
    # Fallback search  
    query2 = f'{university} {role_query}'
    text2 = search_ddg(query2)
    if text2:
        return extract_name(text2, university, role)
    
    return None

def main():
    print(f"\n{'='*55}")
    print("University Lead Name Finder v2")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*55)

    print(f"\nLoading {INPUT_FILE}...")
    df = pd.read_excel(INPUT_FILE)
    print(f"Loaded {len(df)} rows")

    if os.path.exists(OUTPUT_FILE):
        df_out = pd.read_excel(OUTPUT_FILE)
        print(f"Resuming from {OUTPUT_FILE}")
    else:
        df_out = df.copy()

    start_idx = get_saved_progress()
    
    # Only process rows with * as name
    needs_name = [i for i in df_out.index if str(df_out.at[i, 'Lead Name']).strip() in ('*', '', 'nan', 'Not found') and i >= start_idx]
    
    print(f"Rows needing names: {len(needs_name)}")
    est_mins = len(needs_name) * 5 // 60
    print(f"Estimated time at ~5s/row: ~{est_mins} minutes ({est_mins//60}h {est_mins%60}m)\n")

    found = 0
    processed = 0

    for idx in needs_name:
        row = df_out.iloc[idx]
        uni = str(row['University Name'])
        role = str(row['Lead Role'])

        print(f"[{idx}] {uni[:45]:<45} {role[:30]:<30}", end=" → ", flush=True)

        name = find_name(uni, role)

        if name:
            df_out.at[idx, 'Lead Name'] = name
            found += 1
            print(f"✅ {name}")
        else:
            print("❌")

        processed += 1

        if processed % 10 == 0:
            df_out.to_excel(OUTPUT_FILE, index=False)
            save_progress(idx)
            pct = 100 * found // processed
            print(f"\n  💾 Saved — {found}/{processed} found ({pct}%)\n")

        time.sleep(random.uniform(2, 5))

    df_out.to_excel(OUTPUT_FILE, index=False)
    save_progress(len(df_out))
    print(f"\n{'='*55}")
    print(f"DONE! {found}/{processed} names found ({100*found//max(processed,1)}%)")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
