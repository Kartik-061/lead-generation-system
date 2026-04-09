import pandas as pd
from duckduckgo_search import DDGS
import time
import random

# CONFIGURATION
INPUT_FILE = "University Leads final done.xlsx"
OUTPUT_FILE = "leads_with_names_final.xlsx"

def get_name_from_ddg(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return "*"
            
            # Look at the first 3 snippets for a name
            for r in results:
                snippet = r['body']
                # Logic: Names in directories often appear before "is the Director" or after "Contact"
                # This is a basic capture; AI-based is better but this is the free way
                words = snippet.split()
                if len(words) > 2:
                    return " ".join(words[:2]) # Returns first two words as a guess
            return "*"
    except Exception as e:
        print(f"Error searching: {e}")
        return "*"

def main():
    df = pd.read_excel(INPUT_FILE)
    
    # We only want to search rows where Lead Name is still '*'
    to_process = df[df['Lead Name'] == '*']
    print(f"Total rows to find: {len(to_process)}")

    count = 0
    for index, row in to_process.iterrows():
        university = row['University Name']
        role = row['Lead Role']
        
        query = f"{university} {role} official directory"
        print(f"Searching: {query}")
        
        found_name = get_name_from_ddg(query)
        df.at[index, 'Lead Name'] = found_name
        
        count += 1
        # Save every 20 rows so you don't lose progress
        if count % 20 == 0:
            df.to_excel(OUTPUT_FILE, index=False)
            print("--- Progress Saved ---")
        
        # Short random delay to stay safe
        time.sleep(random.uniform(2, 4))

    df.to_excel(OUTPUT_FILE, index=False)
    print("Done! Check leads_with_names_final.xlsx")

if __name__ == "__main__":
    main()