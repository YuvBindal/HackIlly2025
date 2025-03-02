import json
import statistics
import time
from datetime import datetime

import requests


def get_solana_rpc_response(method, params=None):
    """Make a request to Solana RPC endpoint"""
    # You can choose mainnet-beta, testnet, or devnet
    url = "https://api.mainnet-beta.solana.com"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method
    }
    
    if params is not None:
        payload["params"] = params
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

def get_current_slot():
    """Get the current slot (latest block) on Solana"""
    response = get_solana_rpc_response("getSlot")
    if "result" in response:
        return response["result"]
    else:
        print(f"Error getting current slot: {response.get('error')}")
        return None

def get_block_time(slot):
    """Get the timestamp for a specific block/slot"""
    response = get_solana_rpc_response("getBlockTime", [slot])
    if "result" in response:
        return response["result"]
    else:
        # Some blocks might not have timestamps available
        return None

def calculate_block_production_time():
    """Calculate average block production time in the last minute"""
    # Get current slot
    current_slot = get_current_slot()
    if current_slot is None:
        return

    print(f"Current slot: {current_slot}")

    # Assuming ~400ms per block, we need ~150 blocks for 1 minute
    # Adding some buffer to ensure we cover at least a minute
    blocks_to_check = 200

    # Collect block times
    block_times = []

    # Start from current slot and work backwards
    slot = current_slot

    print("Collecting block times...")

    while len(block_times) < blocks_to_check:  # Removed timeout
        time_val = get_block_time(slot)
        if time_val is not None:
            block_times.append({"slot": slot, "time": time_val})
            print(f"Slot {slot}: {datetime.fromtimestamp(time_val).strftime('%H:%M:%S.%f')}")
        slot -= 1
        if slot <= 0:
            break

    # Sort by slot (ascending)
    block_times.sort(key=lambda x: x["slot"])

    print(f"Collected timestamps for {len(block_times)} blocks")

    # Calculate time differences between blocks
    time_diffs = []
    slot_diffs = []

    for i in range(1, len(block_times)):
        current = block_times[i]
        previous = block_times[i-1]

        time_diff = current["time"] - previous["time"]
        slot_diff = current["slot"] - previous["slot"]

        # Only consider reasonable time differences
        if 0 < time_diff < 10:  # reasonable range in seconds
            time_diffs.append(time_diff)
            slot_diffs.append(slot_diff)

    # Calculate statistics
    if len(time_diffs) > 0:
        # Calculate average time per block
        total_time = sum(time_diffs)
        total_slots = sum(slot_diffs)
        avg_time_per_block = total_time / total_slots

        # Other statistics
        raw_avg = statistics.mean(time_diffs)
        try:
            median_time = statistics.median(time_diffs)
        except:
            median_time = "N/A"
        try:
            min_time = min(time_diffs)
        except:
            min_time = "N/A"
        try:
            max_time = max(time_diffs)
        except:
            max_time = "N/A"

        # Convert to milliseconds for easier reading but don't round
        avg_ms = avg_time_per_block * 1000
        raw_avg_ms = raw_avg * 1000
        median_ms = median_time * 1000 if median_time != "N/A" else "N/A"
        min_ms = min_time * 1000 if min_time != "N/A" else "N/A"
        max_ms = max_time * 1000 if max_time != "N/A" else "N/A"

        print(f"\nAnalyzed {len(time_diffs)} block pairs:")
        print(f"Average time per block: {avg_ms} ms")  # Removed formatting to show full precision
        print(f"Raw average between consecutive blocks: {raw_avg_ms} ms")
        print(f"Median time between blocks: {median_ms if median_ms == 'N/A' else f'{median_ms} ms'}")
        print(f"Minimum time between blocks: {min_ms if min_ms == 'N/A' else f'{min_ms} ms'}")
        print(f"Maximum time between blocks: {max_ms if max_ms == 'N/A' else f'{max_ms} ms'}")

        # Calculate blocks per second (for reference)
        blocks_per_second = 1 / avg_time_per_block
        print(f"Estimated blocks per second: {blocks_per_second}")  # Full precision

        # Calculate time window covered by our sample
        first_time = datetime.fromtimestamp(block_times[0]["time"])
        last_time = datetime.fromtimestamp(block_times[-1]["time"])
        time_diff_seconds = (last_time - first_time).total_seconds()
        print(f"Time window analyzed: {time_diff_seconds} seconds")  # Full precision
        print(f"Total slots covered: {block_times[-1]['slot'] - block_times[0]['slot'] + 1}")
    else:
        print("Not enough data to calculate statistics.")

if __name__ == "__main__":
    calculate_block_production_time()