import pandas as pd
import time
import random
from ddgs import DDGS

INPUT_FILE = "India_Master_WITH_EMAILS.xlsx"
OUTPUT_FILE = "Top_300_India_Named.xlsx"

def extract_name_from_search(university, role):
    with DDGS() as ddgs:
        try:
            query = f"{university} {role} name profile"
            results = list(ddgs.text(query, max_results=1))
            
            if results:
                title = results[0]['title']
                
                # Extract the potential name
                if "-" in title:
                    name = title.split("-")[0].strip()
                elif "|" in title:
                    name = title.split("|")[0].strip()
                else:
                    name = " ".join(title.split()[:3]).strip()
                
                # THE SMART FILTER: Block junk words, but don't force "Dr."
                bad_words = ["event", "nashville", "asian", "university", "college", "welcome", "home", "about", "contact", "syllabus", "admission", "department", "library", "past", "news", "academics", "fee", "login", "admin"]
                
                # Check 1: Does it contain garbage words?
                if any(b in name.lower() for b in bad_words):
                    return "University Official"
                    
                # Check 2: Is it just one word? (Real names usually have a first and last)
                if len(name.split()) < 2 or len(name.split()) > 6:
                    return "University Official"
                    
                # If it passes the checks, it's a real name!
                return name
                        
        except Exception as e:
            pass
            
    return "University Official"

def main():
    print("Loading Master Data...")
    df = pd.read_excel(INPUT_FILE).head(300)
    
    print(f"Starting SMART name extraction for {len(df)} leads...\n")
    
    for index, row in df.iterrows():
        uni = row['University Name']
        role = row['Lead Role']
        
        print(f"[{index + 1}/{len(df)}] Searching for {role} at {uni}...")
        
        if row['Lead Name'] == "University Official" or row['Lead Name'] == "*" or pd.isna(row['Lead Name']):
            found_name = extract_name_from_search(uni, role)
            df.at[index, 'Lead Name'] = found_name
            print(f"   > Result: {found_name}")
            
            time.sleep(random.uniform(4, 6))
        else:
            print(f"   > Already has name: {row['Lead Name']}")

        if (index + 1) % 10 == 0:
            df.to_excel(OUTPUT_FILE, index=False)
            
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nSUCCESS! Premium list saved as {OUTPUT_FILE}")

if __name__ == "__main__":
    main()