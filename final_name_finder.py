import pandas as pd
import time
import random
from duckduckgo_search import DDGS
from urllib.parse import urlparse

INPUT_FILE = "India_Universities_Master_1100.xlsx"
OUTPUT_FILE = "India_Master_WITH_EMAILS.xlsx"

def get_domain(univ_name):
    with DDGS() as ddgs:
        try:
            # Search for the official website
            query = f"{univ_name} official website"
            results = list(ddgs.text(query, max_results=1))
            if results:
                url = results[0]['href']
                domain = urlparse(url).netloc
                # Remove 'www.' if present
                return domain.replace("www.", "")
        except Exception as e:
            print(f"Search error for {univ_name}: {e}")
    return None

def main():
    df = pd.read_excel(INPUT_FILE)
    unique_unis = df['University Name'].unique()
    
    domain_map = {}
    print(f"Finding domains for {len(unique_unis)} universities...")

    for i, uni in enumerate(unique_unis):
        print(f"[{i+1}/{len(unique_unis)}] Fetching domain for: {uni}")
        domain = get_domain(uni)
        if domain:
            domain_map[uni] = domain
            print(f"   > Found: {domain}")
        else:
            print(f"   > Could not find domain.")
        
        # Respectful delay to prevent blocks
        time.sleep(random.uniform(2, 4))

        # Save progress every 10 universities
        if (i + 1) % 10 == 0:
            temp_df = df.copy()
            temp_df['Domain'] = temp_df['University Name'].map(domain_map)
            temp_df.to_excel(OUTPUT_FILE, index=False)

    # Final Email Construction
    print("\nConstructing final email addresses...")
    df['Domain'] = df['University Name'].map(domain_map)
    
    def build_email(row):
        if pd.isna(row['Domain']): return "manual.check@required.com"
        role = row['Lead Role']
        if "Research" in role: return f"dean.research@{row['Domain']}"
        if "Outreach" in role: return f"outreach@{row['Domain']}"
        if "Librarian" in role: return f"librarian@{row['Domain']}"
        return f"info@{row['Domain']}"

    df['Email'] = df.apply(build_email, axis=1)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"SUCCESS! File saved as {OUTPUT_FILE}")

if __name__ == "__main__":
    main()