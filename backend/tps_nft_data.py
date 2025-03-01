import csv
import json
import os
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '../../../backend/.env.local')
load_dotenv(env_path)



# Solana JSON-RPC Public Endpoint
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

# HelloMoon API for NFT Trading Volume
HELLOMOON_API_URL = "https://rest-api.hellomoon.io/v0/nft/stats/solana"
API_KEY = "ebe4fff1-3d80-4013-b2ae-d8c209ea1701" 

# Headers for HelloMoon API
HELLOMOON_HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Function to get TPS (Transactions Per Second)
def get_tps():
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getRecentPerformanceSamples",
        "params": [100]  # Changed to get 100 samples
    }
    response = requests.post(SOLANA_RPC_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        if "result" in data and len(data["result"]) > 0:
            # Create lists to store data
            tps_values = []
            timestamps = []
            blockchain = []
            
            # Process each sample
            for sample in data["result"]:
                tps = sample["numTransactions"] / sample["samplePeriodSecs"]
                timestamp = datetime.now(timezone.utc) - timedelta(seconds=sample.get("samplePeriodSecs", 0))
                
                tps_values.append(round(tps, 2))
                timestamps.append(timestamp)
                blockchain.append('solana')
            
            # Create DataFrame
            df = pd.DataFrame({
                'blockchain': blockchain,
                'tps': tps_values,
                'timestamp': timestamps
            })
            
            # Sort by timestamp
            df = df.sort_values('timestamp', ascending=False)
            df= df.head(1)
            df = df.to_json()
            
            return df
    
    # Return empty DataFrame with correct columns if there's an error
    return pd.DataFrame(columns=['blockchain', 'tps', 'timestamp'])

# Function to get failed transactions dynamically
def get_failed_transactions():
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": ["Vote111111111111111111111111111111111111111"]  # Fetch latest transactions from a validator
    }
    
    response = requests.post(SOLANA_RPC_URL, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if "result" in data and len(data["result"]) > 0:
            latest_signature = data["result"][0]["signature"]

            status_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignatureStatuses",
                "params": [[latest_signature]]
            }
            status_response = requests.post(SOLANA_RPC_URL, json=status_payload)
            if status_response.status_code == 200:
                status_data = status_response.json()
                if "result" in status_data and "value" in status_data["result"]:
                    failed_count = sum(1 for tx in status_data["result"]["value"] if tx and not tx["confirmations"])
                    return failed_count
    return 0

# Function to get NFT Trading Volume using HelloMoon API
def get_nft_trading_volume():
    response = requests.get(HELLOMOON_API_URL, headers=HELLOMOON_HEADERS)

    if response.status_code == 200:
        data = response.json()
        if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
            nft_data = data["data"][0]  # Extract first entry
            if "volume24h" in nft_data:
                return round(nft_data["volume24h"], 2)  # Get 24-hour NFT trading volume
    return None

# Function to fetch and store data in CSV
def fetch_and_store_data():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tps = get_tps()
    failed_tx = get_failed_transactions()
    nft_trading_volume = get_nft_trading_volume()

    print(f"📊 Timestamp: {timestamp}")
    print(f"🔹 TPS: {tps}")
    print(f"🔻 Failed Transactions: {failed_tx}")
    print(f"🖼 NFT Trading Volume (SOL): {nft_trading_volume}")

    # Save to CSV
    filename = "solana_congestion_data.csv"
    file_exists = False
    try:
        with open(filename, "r"):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "TPS", "Failed Transactions", "NFT Trading Volume (SOL)"])
        writer.writerow([timestamp, tps, failed_tx, nft_trading_volume])

    print(f"✅ Data stored in {filename}")


def get_latest_failed_transactions():
    url = "https://rest-api.hellomoon.io/v0"
    
    current_time = datetime.now(timezone.utc)
    thirty_seconds_ago = current_time - timedelta(seconds=30)
    
    from_time = thirty_seconds_ago.isoformat()
    to_time = current_time.isoformat()
    
    # Fixed headers - using the correct key=value format
    headers = {
        "Accept": "application/json",
        "Authorization": f"key={API_KEY}"  # Changed to key=value format
    }
    
    params = {
        "start_time": from_time,
        "end_time": to_time,
        "status": "failed"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print('Response fetched at the moment ', response)
        if response.status_code == 200:
            data = response.json()
            return len(data.get('data', []))
        else:
            print(f"Error: API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching failed transactions: {str(e)}")
        return None


# Run script every 30 seconds (or adjust as needed)
if __name__ == "__main__":
    # get_df = analyze_transaction_fees()
    # print(get_df)

    tps_df  =  get_tps()
    tps_df['blockchain'] = 'solana'
    tps_df.to_csv('tps_df.csv')