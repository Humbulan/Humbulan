#!/data/data/com.termux/files/usr/bin/python3
import os
import json
import time
import requests

API_KEY = "2457b00d9974a5d80341db7a431d9597"
CACHE_FILE = os.path.expanduser("~/imperial_network/cache/metal_cache.json")
CACHE_DURATION = 86400  # 24 hours

def get_metal_prices(base="USD", currencies="EUR,XAU,XAG"):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    
    if os.path.exists(CACHE_FILE):
        file_age = time.time() - os.path.getmtime(CACHE_FILE)
        if file_age < CACHE_DURATION:
            print("[CACHE HIT] Serving cached metal prices (API quota conserved).")
            with open(CACHE_FILE, "r") as f:
                return json.load(f)

    print("[CACHE MISS] Requesting fresh rates from MetalpriceAPI...")
    url = f"https://api.metalpriceapi.com/v1/latest?api_key={API_KEY}&base={base}&currencies={currencies}"
    
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if not data.get("success", True) and data.get("error", {}).get("statusCode") == 105:
            print("[API LIMIT] Monthly request allowance exceeded. Falling back to local cache.")
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r") as f:
                    return json.load(f)
            return {"error": "Quota exceeded and no cache available."}
            
        response.raise_for_status()
        
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
            
        return data
    except Exception as e:
        print(f"[ERROR] {e}")
        if os.path.exists(CACHE_FILE):
            print("[FALLBACK] Using stale cache due to connection failure.")
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        return None

if __name__ == "__main__":
    result = get_metal_prices()
    print(json.dumps(result, indent=2))
