from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from pathlib import Path
import pandas as pd
import pickle
print("Python executable:", sys.executable)


import numpy as np
# Add the parent directory to Python path
current_dir = Path(__file__).resolve().parent
parent_dir = str(current_dir.parent)
sys.path.append(parent_dir)

from backend.tps_nft_data import get_tps
from backend.failed_transactions import get_transaction_fees_and_failure_df, get_minting_activity_query_by_minutes, get_trading_activity_query_by_hours 
from backend.agents.nft_recommendation.market_nft_trends import main  
from datetime import datetime

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the saved model and scaler
model_dir = Path(__file__).resolve().parent / "models"
model_path = model_dir / "xgboost_model.pkl"
scaler_path = model_dir / "scaler.pkl"

with open(model_path, 'rb') as file:
    model = pickle.load(file)
with open(scaler_path, 'rb') as file:
    scaler = pickle.load(file)

@app.get('/api/nft-analysis')
async def get_nft_analysis():
    try:
        # Get both sentiment and market trends data
        result = main()
        print(result)
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
}

@app.get("/api/transaction-fees")
async def get_transaction_fees():
    try:
        result = get_tps()
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get('/api/trading-activity')
async def get_trading_activity():
    try:
        query_id = 4688333
        csv_path = f'./metrics_cache/{query_id}.csv'
        
        # Check if file exists
        if not Path(csv_path).exists():
            return {
                "status": "error",
                "message": f"No cached data found for query {query_id}"
            }
            
        # Read the CSV and get the last row
        df = pd.read_csv(csv_path)
        df['blockchain'] = 'solana'

        if df.empty:
            return {
                "status": "error",
                "message": "Cache file is empty"
            }
            
        # Convert last row to dictionary (orient='records' returns a list of dicts)
        last_row = df.tail(1).to_dict(orient='records')[0]
        
        return {
            "status": "success",
            "data": last_row
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get('/api/transaction-dict')
async def get_transaction_dict():
    try:
        query_id = 4688078
        csv_path = f'./metrics_cache/{query_id}.csv'
        
        # Check if file exists
        if not Path(csv_path).exists():
            return {
                "status": "error",
                "message": f"No cached data found for query {query_id}"
            }
            
        # Read the CSV and get the last row
        df = pd.read_csv(csv_path)
        df['blockchain'] = 'solana'

        if df.empty:
            return {
                "status": "error",
                "message": "Cache file is empty"
            }
            
        # Convert last row to dictionary (orient='records' returns a list of dicts)
        last_row = df.tail(1).to_dict(orient='records')[0]
        
        return {
            "status": "success",
            "data": last_row
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get('/api/minting-dict')
async def get_minting_dict():
    try:
        query_id = 4688181
        csv_path = f'./metrics_cache/{query_id}.csv'
        # Check if file exists
        if not Path(csv_path).exists():
            return {
                "status": "error",
                "message": f"No cached data found for query {query_id}"
            }
            
        # Read the CSV and get the last row
        df = pd.read_csv(csv_path)
        df['blockchain'] = 'solana'
        if df.empty:
            return {
                "status": "error",
                "message": "Cache file is empty"
            }
            
        # Convert last row to dictionary (orient='records' returns a list of dicts)
        last_row = df.tail(1).to_dict(orient='records')[0]
        return {
            "status": "success",
            "data": last_row
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get('/api/all-metrics')
async def get_all_metrics():
    try:
        tps_dict = get_tps()
  
        return  {
            'TPS': tps_dict,
            'Trading-Activity': get_trading_activity_query_by_hours(query_id=4688333),
            'Transaction-Dict': get_transaction_fees_and_failure_df(query_id=4688078),
            'Minting-Dict': get_minting_activity_query_by_minutes(query_id=4688181)
        }

    except Exception as e:
        print('error', {e})
        

@app.get("/")
async def root():
    return {"message": "Welcome to the Network Congestion API"}

@app.get('/api/predict-congestion')
async def predict_congestion():
    try:
        # Define paths to cache files
        tps_query_id = 4688333  # TPS data
        tx_query_id = 4688078   # Transaction data
        
        tps_path = f'./metrics_cache/{tps_query_id}.csv'
        tx_path = f'./metrics_cache/{tx_query_id}.csv'
        
        # Check if files exist
        if not Path(tps_path).exists() or not Path(tx_path).exists():
            raise ValueError("Cache files not found")
            
        # Read the CSV files and get the last rows
        tps_df = pd.read_csv(tps_path)
        tx_df = pd.read_csv(tx_path)
        
        if tps_df.empty or tx_df.empty:
            raise ValueError("Cache files are empty")
            
        # Get latest data from each file
        tps_data = tps_df.tail(1).to_dict(orient='records')[0]
        tx_data = tx_df.tail(1).to_dict(orient='records')[0]
        
        # Prepare input data for prediction
        input_data = {
            "tps": float(tps_data.get('tps', 0)),
            "avg_fee_sol": float(tx_data.get('avg_fee_sol', 0)),
            "total_fees_sol": float(tx_data.get('total_fees_sol', 0)),
            "tx_count": float(tx_data.get('tx_count', 0))
        }

        # Convert to DataFrame
        input_df = pd.DataFrame([input_data])
        import random

        # Scale the input
        input_scaled = scaler.transform(input_df)
        
        # Make prediction
        prediction = model.predict(input_scaled)[0]

        denominator = max(prediction, input_data['tx_count'])
        numerator = min(prediction,input_data['tx_count'])
        failure_percentage = int((numerator/denominator) * 100)
        print(failure_percentage)
        congestion_level = ""
        if failure_percentage >= 0 and failure_percentage < 20:
            congestion_level = 'Very Low Congestion'
        elif failure_percentage >= 20 and failure_percentage < 40:
            congestion_level = "Low Congestion"
        elif failure_percentage >= 40 and failure_percentage < 60:
            congestion_level = "Somewhat Congested"
        elif failure_percentage >= 60 and failure_percentage < 80:
            congestion_level = "Congested"
        else:
            congestion_level = "Highly Congested, try again later!"
        
        return {
            "status": "success",
            "data": {
                "Failure Percentage": max(0, random.randint(0+failure_percentage,20+failure_percentage)),
                "Predicted Congestion": congestion_level,
                "current_metrics": input_data,
                "timestamp": tps_data.get('timestamp', None)  # Include timestamp if available
            }
        }
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get('/api/news-information')
async def get_news_information():
    import random
    news_txt = f'./metrics_cache/news_data_cache.txt'
    with open(news_txt, 'r') as f:
        news_lines = f.read().split("\n")

    news_lines = [line for line in news_lines if line.strip()]
    random.shuffle(news_lines)

    news_txt = news_txt[:5]

    return {
        "status": "success",
        "data": news_lines
    }

