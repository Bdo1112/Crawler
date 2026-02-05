import requests
import json
import os

def scrape_website(target_url, output_filename="result.json"):
    # 1. Define your self-hosted API endpoint
    api_url = "http://localhost:3002/v2/scrape"
    
    # 2. Construct the payload
    # We include 'timeout' based on your previous success with heavy sites
    payload = {
        "url": target_url,
        "formats": ["markdown", "html", "links"], # Add 'screenshot' if needed
        "timeout": 60000,  # 60 seconds (Good for heavy sites like nate.com)
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(f"🔥 Sending crawler to: {target_url} ...")
        
        # 3. Make the POST request
        response = requests.post(api_url, json=payload, headers=headers)
        
        # 4. Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Check if the API reported success internally
            if data.get("success"):
                # 5. Save the result to a JSON file
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Success! Data saved to '{output_filename}'")
                return True
            else:
                print(f"❌ API Error: {data.get('error')}")
                return False
                
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Script Error: {str(e)}")
        return False

# --- Usage Example ---
if __name__ == "__main__":
    # Change this URL to whatever you want to scrape
    my_url = "https://www.dogdrip.net/" 
    
    scrape_website(my_url, "dogdrip_scrape.json")