import json
import os
import time
from datetime import datetime, timedelta
from functools import reduce

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

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

def analyze_transaction_fees(query_id):
    # Initialize Dune Analytics client
    api_key = '87fJDuUYzpeLYJ2XWKHzIYNKu1xNJyjS'
    dune = DuneAnalytics(api_key)

    try:
        # Get results
        results = dune.execute_query(query_id)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        print(df)
        
        # Basic fee analysis
        if not df.empty:
            file_path = f'./metrics_cache/{query_id}.csv'
            
            # Check if the file exists
            if os.path.exists(file_path):
                # Read existing data
                current_df = pd.read_csv(file_path)
                # Concatenate with new data
                combined_df = pd.concat([current_df, df])
                print(f"Appending to existing file: {file_path}")
            else:
                # If file doesn't exist, just use the new data
                combined_df = df
                # Ensure the directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                print(f"Creating new file: {file_path}")
            
            # Convert minute column to datetime if it exists and is not already datetime
            for col in combined_df.columns:
                if 'minute' in col.lower() or 'time' in col.lower() or 'date' in col.lower():
                    try:
                        if not pd.api.types.is_datetime64_any_dtype(combined_df[col]):
                            combined_df[col] = pd.to_datetime(combined_df[col])
                            print(f"Converted column '{col}' to datetime")
                    except Exception as e:
                        print(f"Could not convert column '{col}' to datetime: {str(e)}")
            
            # Sort by minute (ascending order - oldest first)
            try:
                if 'minute' in combined_df.columns:
                    combined_df = combined_df.sort_values(by='minute')
                    print("Data sorted by minute")
                # Sort by alternative time column if 'minute' not present
                else:
                    time_cols = [col for col in combined_df.columns if 'time' in col.lower() or 'date' in col.lower()]
                    if time_cols:
                        combined_df = combined_df.sort_values(by=time_cols[0])
                        print(f"Data sorted by {time_cols[0]}")
            except Exception as e:
                print(f"Error during sorting: {str(e)}")
            
            # Reset index after sorting
            combined_df = combined_df.reset_index(drop=True)
            print("Index reset after sorting")
            
            # Set blockchain column
            combined_df['blockchain'] = 'solana'
            
            # Save the combined dataframe
            combined_df.to_csv(file_path, index=False)
            print(f"\nResults saved to {file_path}")
        else:
            print("No data returned from query")
        
        df = df.to_json()
        return df

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

#Important
def get_transaction_fees_and_failure_df(query_id):
    transaction_fees_and_failure_df = analyze_transaction_fees(query_id)
    transaction_fees_and_failure_df['blockchain'] = 'solana'
    return transaction_fees_and_failure_df

def get_trading_activity_query_by_minutes(query_id):
    trading_activity_query_by_hours = '4688333'
    trading_actiivty_by_hours = analyze_transaction_fees(trading_activity_query_by_hours)
    trading_actiivty_by_hours['blockchain'] = 'solana'
    return trading_actiivty_by_hours
    

def get_minting_activity_query_by_minutes(query_id):
    minting_activity_query_by_minutes = "4688181"
    nft_minting_activity_by_hour = analyze_transaction_fees(minting_activity_query_by_minutes)
    nft_minting_activity_by_hour['blockchain'] = 'solana'
    return minting_activity_query_by_minutes

def merge_metrics_files(file_paths, output_path, merge_column='minute'):
    """
    Merge multiple metrics CSV files and handle duplicate indices.
    
    Args:
        file_paths (list): List of file paths to merge
        output_path (str): Path to save the merged file
        merge_column (str): Column to use for merging
    
    Returns:
        DataFrame: The merged DataFrame or None if error
    """
    try:
        dfs = []
        
        # Load each file
        for file_path in file_paths:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                
                # Convert time columns to datetime
                for col in df.columns:
                    if 'minute' in col.lower() or 'time' in col.lower() or 'date' in col.lower():
                        try:
                            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                                df[col] = pd.to_datetime(df[col])
                        except Exception as e:
                            print(f"Could not convert column '{col}' to datetime in {file_path}: {str(e)}")
                
                dfs.append(df)
                print(f"Loaded {file_path}, shape: {df.shape}")
            else:
                print(f"Warning: File not found: {file_path}")
        
        if not dfs:
            print("No valid files to merge")
            return None
        
        # Concatenate with ignore_index=True to avoid duplicate index issues
        merged_df = pd.concat(dfs, ignore_index=True)
        print(f"Initial merge complete, shape: {merged_df.shape}")
        
        # Drop duplicates if needed
        if merge_column in merged_df.columns:
            duplicates_count = merged_df.duplicated(subset=[merge_column]).sum()
            print(f"Found {duplicates_count} duplicate rows based on {merge_column}")
            if duplicates_count > 0:
                merged_df = merged_df.drop_duplicates(subset=[merge_column], keep='first')
                print(f"After dropping duplicates, shape: {merged_df.shape}")
        
        # Sort by time column
        if merge_column in merged_df.columns:
            merged_df = merged_df.sort_values(by=merge_column)
            print(f"Sorted by {merge_column}")
        
        # Reset index
        merged_df = merged_df.reset_index(drop=True)
        
        # Save merged result
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        merged_df.to_csv(output_path, index=False)
        print(f"Merged data saved to {output_path}")
        
        return merged_df
    
    except Exception as e:
        print(f"Error concatenating metrics: {str(e)}")
        return None

# # Execute the analysis
if __name__ == "__main__":
    load_dotenv()

    while True:
        print("Fetching Solana transaction fee and failure data...")
        transaction_fees_and_failure_df = analyze_transaction_fees(query_id=4688078)

        trading_activity_query_by_minutes = '4688333'
        print('Fetching Solana Trading Volume in minutes')
        trading_activity_by_minutes = analyze_transaction_fees(trading_activity_query_by_minutes)


        # print("Fetching NFT minting activity by hour")
        # minting_activity_query_by_minutes = "4688181"
        # nft_minting_activity_by_hour = analyze_transaction_fees(minting_activity_query_by_minutes)


        
        time.sleep(30)

