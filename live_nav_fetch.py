import os
import requests
import pandas as pd

def fetch_scheme_nav(scheme_code):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    print(f"[FETCHING] Scheme Code {scheme_code} from {url}...")
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                # Extract meta and data
                meta = data.get("meta", {})
                nav_list = data["data"]
                
                # Convert to DataFrame
                df = pd.DataFrame(nav_list)
                
                # Ensure columns are ordered correctly: date, nav
                df = df[["date", "nav"]]
                
                # Clean up/check types
                df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
                
                # Save to data/raw/
                output_filename = f"live_nav_{scheme_code}.csv"
                output_path = os.path.join("data", "raw", output_filename)
                
                df.to_csv(output_path, index=False)
                
                print(f"[SUCCESS] Saved {len(df)} NAV records for '{meta.get('scheme_name', f'Scheme {scheme_code}')}' to {output_path}")
                return True
            else:
                print(f"[ERROR] No data found in response for scheme {scheme_code}")
                return False
        else:
            print(f"[ERROR] API returned status code {response.status_code} for scheme {scheme_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to fetch scheme {scheme_code}: {e}")
        return False

def main():
    # Schemes list:
    # 1. HDFC Top 100 / SBI Small Cap specified by user (125497)
    # 2. SBI Bluechip (119551)
    # 3. ICICI Bluechip (120503)
    # 4. Nippon Large Cap (118632)
    # 5. Axis Bluechip (119092)
    # 6. Kotak Bluechip (120841)
    schemes = [125497, 119551, 120503, 118632, 119092, 120841]
    
    os.makedirs(os.path.join("data", "raw"), exist_ok=True)
    
    print("=" * 80)
    print("STARTING LIVE MUTUAL FUND NAV FETCH")
    print("=" * 80)
    
    success_count = 0
    for code in schemes:
        if fetch_scheme_nav(code):
            success_count += 1
            
    print("=" * 80)
    print(f"FETCH COMPLETE: Successfully fetched {success_count}/{len(schemes)} schemes.")
    print("=" * 80)

if __name__ == "__main__":
    main()
