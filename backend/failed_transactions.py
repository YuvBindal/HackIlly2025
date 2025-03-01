import os
import time
from datetime import datetime, timedelta
from functools import reduce

import pandas as pd
import requests

#Using this to get -> Failed Transactions and Fees data on Solana

class DuneAnalytics:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.dune.com/api/v1"
        self.headers = {
            "x-dune-api-key": self.api_key
        }

    def execute_query(self, query_id):
        """Execute a query and return results"""
        # Execute query
        execute_endpoint = f"{self.base_url}/query/{query_id}/execute"
        execution = requests.post(execute_endpoint, headers=self.headers)
        
        if execution.status_code != 200:
            raise Exception(f"Query execution failed: {execution.text}")
            
        execution_id = execution.json()['execution_id']

        # Get results
        results_endpoint = f"{self.base_url}/execution/{execution_id}/results"
        
        while True:
            results = requests.get(results_endpoint, headers=self.headers)
            if results.status_code != 200:
                raise Exception(f"Failed to get results: {results.text}")
                
            state = results.json().get('state')
            if state == 'QUERY_STATE_COMPLETED':
                return results.json()['result']['rows']
            elif state in ['QUERY_STATE_FAILED', 'QUERY_STATE_CANCELLED']:
                raise Exception(f"Query failed or was cancelled: {state}")
                
            time.sleep(1)

def analyze_transaction_fees(query_id=4688078):
    # Initialize Dune Analytics client
    api_key = "fGgq2c7rz24Gev32VY3wdctdo1tQNIro"
    dune = DuneAnalytics(api_key)

    # Let's use a query that gets transaction fee data for the last hour
    # You'll need to create this query in Dune and get its ID
    # For now, I'll use a sample query ID (you'll need to replace this)
    # query_id = "4688078"  # This is a sample query ID

    try:
        # Get results
        results = dune.execute_query(query_id)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        print(df)
        # Basic fee analysis
        if not df.empty:            
            # Read existing data
            current_df = pd.read_csv(f'./metrics_cache/{query_id}.csv')
            current_df['blockchain'] = 'solana'
            # Concatenate and save the result to a new variable
            combined_df = pd.concat([current_df, df])
            combined_df['blockchain'] = 'solana'
            # Save the combined dataframe
            combined_df.to_csv(f'./metrics_cache/{query_id}.csv', index=False)
            print("\nResults saved to solana_transaction_fees.csv")
        else:
            print("No data returned from query")
        
        df = df.to_json()
        return df

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def get_transaction_fees_and_failure_df(query_id):
    transaction_fees_and_failure_df = analyze_transaction_fees(query_id)
    transaction_fees_and_failure_df['blockchain'] = 'solana'
    return transaction_fees_and_failure_df

def get_minting_activity_query_by_minutes(query_id):
    minting_activity_query_by_minutes = "4688181"
    nft_minting_activity_by_hour = analyze_transaction_fees(minting_activity_query_by_minutes)
    nft_minting_activity_by_hour['blockchain'] = 'solana'
    return minting_activity_query_by_minutes

def get_trading_activity_query_by_hours(query_id):
    trading_activity_query_by_hours = '4688333'
    trading_actiivty_by_hours = analyze_transaction_fees(trading_activity_query_by_hours)
    trading_actiivty_by_hours['blockchain'] = 'solana'
    return trading_actiivty_by_hours
    
# # Execute the analysis
if __name__ == "__main__":

    while True:

        print("Fetching Solana transaction fee and failure data...")
        transaction_fees_and_failure_df = analyze_transaction_fees()
    
        print("Fetching NFT minting activity by hour")
        minting_activity_query_by_minutes = "4688181"
        nft_minting_activity_by_hour = analyze_transaction_fees(minting_activity_query_by_minutes)

        trading_activity_query_by_hours = '4688333'
        print('Fetching NFT Trading Volume in hours')
        trading_actiivty_by_hours = analyze_transaction_fees(trading_activity_query_by_hours)
        
        time.sleep(30)

#     # # Create a list of dataframes, only including those that are actually dataframes
#     # dfs_to_combine = []
    
#     # if isinstance(get_tps_df, pd.DataFrame):
#     #     dfs_to_combine.append(get_tps_df.reset_index(drop=True))
    
#     # if isinstance(trading_actiivty_by_hours, pd.DataFrame):
#     #     dfs_to_combine.append(trading_actiivty_by_hours.reset_index(drop=True))
    
#     # if isinstance(minting_activity_query_by_minutes, pd.DataFrame):
#     #     dfs_to_combine.append(minting_activity_query_by_minutes.reset_index(drop=True))
    
#     # if isinstance(transaction_fees_and_failure_df, pd.DataFrame):
#     #     dfs_to_combine.append(transaction_fees_and_failure_df.reset_index(drop=True))
    
#     # # Only combine if we have dataframes to combine
#     # if dfs_to_combine:
#     #     df_combined = pd.concat(dfs_to_combine, axis=1)
#     #     # Move dropna to the combined DataFrame instead of the list
#     #     df_combined.dropna(inplace=True)
#     #     print(df_combined)
#     #     df_combined.to_csv('combined_df.csv')
#     # else:
#     #     print("No valid DataFrames to combine")

#     print(dfs_to_combine)


# Created/Modified files during execution:
# - solana_transaction_fees.csv