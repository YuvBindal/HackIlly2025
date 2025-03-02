import os
import pickle
import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print("Python executable:", sys.executable)

import json
import random

import numpy as np
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the parent directory to Python path
current_dir = Path(__file__).resolve().parent
parent_dir = str(current_dir.parent)
sys.path.append(parent_dir)

from datetime import datetime

from backend.agents.nft_recommendation.market_nft_trends import main
from backend.failed_transactions import (
    get_minting_activity_query_by_minutes,
    get_trading_activity_query_by_hours,
    get_transaction_fees_and_failure_df,
)
from backend.tps_nft_data import get_tps

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

@app.get('/api/get-predicted-congestion')
async def get_predicted_congestion():
    try:
        congestion_history_path = './metrics_cache/congestion_history.csv'
        
        # Check if file exists
        if not Path(congestion_history_path).exists():
            return {
                "status": "error",
                "message": "Congestion history file not found"
            }
            
        # Read the CSV and get the last row
        congestion_df = pd.read_csv(congestion_history_path)
        
        if congestion_df.empty:
            return {
                "status": "error",
                "message": "Congestion history file is empty"
            }
            
        # Get the last row as a dictionary
        last_row = congestion_df.tail(1).to_dict(orient='records')[0]

        #Call predict congestion to propogate calls
        await predict_congestion()
        
        return {
            'status': 'success',
            'data': last_row
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get('/api/predict-congestion')
async def predict_congestion():
    try:
        # Define paths to cache files
        tps_query_id = 4688333  # TPS data
        tx_query_id = 4688078   # Transaction data
        
        tps_path = f'./metrics_cache/{tps_query_id}.csv'
        tx_path = f'./metrics_cache/{tx_query_id}.csv'
        congestion_history_path = './metrics_cache/congestion_history.csv'
        
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
        
        # Add some randomness to the failure percentage for visual interest
        final_failure_percentage = max(0, random.randint(failure_percentage, 5+failure_percentage))
        
        congestion_level = ""
        if final_failure_percentage >= 0 and final_failure_percentage < 20:
            congestion_level = 'Very Low Congestion'
        elif final_failure_percentage >= 20 and final_failure_percentage < 40:
            congestion_level = "Low Congestion"
        elif final_failure_percentage >= 40 and final_failure_percentage < 60:
            congestion_level = "Somewhat Congested"
        elif final_failure_percentage >= 60 and final_failure_percentage < 80:
            congestion_level = "Congested"
        else:
            congestion_level = "Highly Congested, try again later!"
        
        # Get current timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save the congestion data to CSV
        congestion_data = {
            'timestamp': current_time,
            'failure_percentage': final_failure_percentage,
            'congestion_level': congestion_level,
            'tps': input_data['tps'],
            'tx_count': input_data['tx_count']
        }
        
        # Check if congestion history file exists
        if Path(congestion_history_path).exists():
            # Append to existing file
            congestion_df = pd.read_csv(congestion_history_path)
            congestion_df = pd.concat([congestion_df, pd.DataFrame([congestion_data])], ignore_index=True)
        else:
            # Create new file
            congestion_df = pd.DataFrame([congestion_data])
        
        # Save to CSV
        congestion_df.to_csv(congestion_history_path, index=False)
        
        return {
            "status": "success",
            "data": {
                "Failure Percentage": final_failure_percentage,
                "Predicted Congestion": congestion_level,
                "current_metrics": input_data,
                "timestamp": current_time
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





class ProgramIdRequest(BaseModel):
    programId: str

class ScanRequest(BaseModel):
    githubUrl: str

# Mock repository structures for different program IDs
MOCK_REPO_STRUCTURES = {
    "default": {
        "src": {
            "lib.rs": "Main library file",
            "utils": {
                "math.rs": "Math utility functions",
                "validation.rs": "Input validation functions"
            },
            "instructions": {
                "initialize.rs": "Program initialization logic",
                "process.rs": "Transaction processing logic"
            }
        },
        "tests": {
            "integration_tests.rs": "Integration tests",
            "unit_tests.rs": "Unit tests"
        },
        "Cargo.toml": "Rust package manifest"
    },
    "TokenProgram123": {
        "src": {
            "lib.rs": "Main token program entry point",
            "state.rs": "Program state definitions",
            "instructions": {
                "mint.rs": "Token minting logic",
                "transfer.rs": "Token transfer logic",
                "burn.rs": "Token burning logic"
            },
            "utils": {
                "validation.rs": "Token validation utilities",
                "math.rs": "Safe math operations"
            }
        },
        "tests": {
            "mint_tests.rs": "Mint functionality tests",
            "transfer_tests.rs": "Transfer functionality tests",
            "burn_tests.rs": "Burn functionality tests"
        },
        "Cargo.toml": "Rust package manifest",
        "Xargo.toml": "Solana program configuration"
    }
}

# Mock code for security scanning
MOCK_CODE = """// Token transfer function with potential vulnerabilities
pub fn process_transfer(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();

    // Get accounts
    let source_info = next_account_info(account_info_iter)?;
    let destination_info = next_account_info(account_info_iter)?;
    let authority_info = next_account_info(account_info_iter)?;

    // SECURITY ISSUE: No check if program_id owns the token accounts

    // Check if source account has enough tokens
    let mut source_data = source_info.try_borrow_mut_data()?;
    let mut source_account = TokenAccount::unpack(&source_data)?;

    if source_account.amount < amount {
        return Err(TokenError::InsufficientFunds.into());
    }

    // SECURITY ISSUE: Missing authority signature verification
    // if !authority_info.is_signer {
    //     return Err(ProgramError::MissingRequiredSignature);
    // }

    // SECURITY ISSUE: No check if the authority is actually authorized

    // Perform transfer
    source_account.amount = source_account.amount.checked_sub(amount)
        .ok_or(TokenError::Overflow)?;

    let mut destination_data = destination_info.try_borrow_mut_data()?;
    let mut destination_account = TokenAccount::unpack(&destination_data)?;

    // SECURITY ISSUE: Potential overflow not properly checked
    destination_account.amount += amount;

    // Repack accounts
    TokenAccount::pack(source_account, &mut source_data)?;
    TokenAccount::pack(destination_account, &mut destination_data)?;

    // Log the transfer
    msg!("Transfer {} tokens from {} to {}",
        amount,
        source_info.key,
        destination_info.key
    );

    Ok(())
}

// Secure implementation of token transfer
pub fn process_transfer_secure(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();

    // Get accounts
    let source_info = next_account_info(account_info_iter)?;
    let destination_info = next_account_info(account_info_iter)?;
    let authority_info = next_account_info(account_info_iter)?;

    // Verify program ownership
    if source_info.owner != program_id || destination_info.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }

    // Verify authority is a signer
    if !authority_info.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Check if source account has enough tokens
    let mut source_data = source_info.try_borrow_mut_data()?;
    let mut source_account = TokenAccount::unpack(&source_data)?;

    // Verify authority is allowed to transfer from source
    if !source_account.is_authority(authority_info.key) {
        return Err(TokenError::OwnerMismatch.into());
    }

    if source_account.amount < amount {
        return Err(TokenError::InsufficientFunds.into());
    }

    // Perform transfer with safe math
    source_account.amount = source_account.amount.checked_sub(amount)
        .ok_or(TokenError::Overflow)?;

    let mut destination_data = destination_info.try_borrow_mut_data()?;
    let mut destination_account = TokenAccount::unpack(&destination_data)?;

    destination_account.amount = destination_account.amount.checked_add(amount)
        .ok_or(TokenError::Overflow)?;

    // Repack accounts
    TokenAccount::pack(source_account, &mut source_data)?;
    TokenAccount::pack(destination_account, &mut destination_data)?;

    // Log the transfer
    msg!("Transfer {} tokens from {} to {}",
        amount,
        source_info.key,
        destination_info.key
    );

    Ok(())
}"""

# Mock security issues
MOCK_SECURITY_ISSUES = [
    (6, "Missing program ID ownership verification", "Bad"),
    (18, "Missing authority signature verification (commented out)", "Bad"),
    (21, "No verification if authority is authorized for this account", "Bad"),
    (29, "Potential integer overflow - using += without checked_add", "Bad"),
    (58, "Proper program ownership verification", "Good"),
    (63, "Correct authority signature verification", "Good"),
    (74, "Proper authority verification against source account", "Good"),
    (83, "Safe arithmetic with checked_sub", "Good"),
    (88, "Safe arithmetic with checked_add", "Good")
]

@app.post('/api/validate-program')
async def validate_program_id(request: ProgramIdRequest = Body(...)):
    import requests

    from backend.github_fetcher.github_fetcher import GitHubFetcher
    from backend.llm_analyzer.security_analyzer import SolanaSecurityAnalyzer
    
    program_id = request.programId
    
    try:
        # Step 1: Verify the program ID with osec.io
        verification_url = f"https://verify.osec.io/status/{program_id}"
        verification_response = requests.get(verification_url)
        
        if verification_response.status_code != 200:
            return {
                "status": "error",
                "validated": False,
                "RepoStructure": ""
            }
        
        verification_data = verification_response.json()
        is_verified = verification_data.get("is_verified", False)
        
        if not is_verified:
            return {
                "status": "error",
                "validated": False,
                "RepoStructure": ""
            }
        
        # Step 2: Get the repository URL from the verification response
        repo_url = verification_data.get("repo_url")
        if not repo_url:
            return {
                "status": "error",
                "validated": False,
                "message": "Repository URL not found in verification data",
                "RepoStructure": ""
            }
        
        # Step 3: Initialize the GitHub fetcher and get the repository structure
        github_fetcher = GitHubFetcher()
        repo_structure = github_fetcher.get_complete_repository_structure(repo_url)
        
        # Step 4: Generate descriptions for each file using LLM
        analyzer = SolanaSecurityAnalyzer(llm_provider="openai", model_name="gpt-4o-mini")
        enhanced_structure = await generate_file_descriptions(repo_structure, analyzer, repo_url)
        
        return {
            "status": "success",
            "validated": True,
            "RepoStructure": json.dumps(enhanced_structure, indent=2)
        }
        
    except Exception as e:
        print(f"Error validating program ID: {str(e)}")
        return {
            "status": "error",
            "validated": False,
            "message": str(e),
            "RepoStructure": ""
        }

async def generate_file_descriptions(repo_structure, analyzer, repo_url):
    """
    Generate brief descriptions for each file in the repository structure using LLM.
    
    Args:
        repo_structure (dict): The repository structure from GitHubFetcher
        analyzer (SolanaSecurityAnalyzer): The analyzer with LLM capabilities
        repo_url (str): The repository URL
        
    Returns:
        dict: Enhanced repository structure with descriptions
    """
    # Create a simplified version of the structure for the LLM prompt
    simplified_structure = json.dumps(repo_structure, indent=2)
    
    # Prepare the prompt for the LLM
    description_prompt = f"""
You are a Solana blockchain expert. I need brief descriptions for files in a Solana repository.

Repository URL: {repo_url}

Below is the repository structure:
{simplified_structure}

For each file in this structure, provide a brief (5-10 word) description of what the file likely contains or does based on its name and location.
Format your response as a JSON object with the same structure, but replace each file path with a brief description.

For example, if the input is:
{{
  "src": {{
    "lib.rs": {{
      "path": "src/lib.rs",
      "type": "file"
    }}
  }}
}}

Your response should be:
{{
  "src": {{
    "lib.rs": "Main program entry point and logic"
  }}
}}

Only include files, not metadata like "path" or "type". Keep the same nested structure.
"""
    
    # Call the LLM API
    llm_response = analyzer._call_llm_api(description_prompt)
    
    # Extract the JSON from the response
    import re
    json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
    
    if json_match:
        try:
            enhanced_structure = json.loads(json_match.group(1))
            return enhanced_structure
        except json.JSONDecodeError:
            pass
    
    # If we couldn't parse the JSON or no JSON was found, try to extract it without code blocks
    try:
        # Find the first { and the last }
        start_idx = llm_response.find('{')
        end_idx = llm_response.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = llm_response[start_idx:end_idx+1]
            enhanced_structure = json.loads(json_str)
            return enhanced_structure
    except (json.JSONDecodeError, ValueError):
        pass
    
    # If all else fails, create a simple description based on file extensions
    return create_fallback_descriptions(repo_structure)

def create_fallback_descriptions(repo_structure):
    """
    Create simple descriptions for files based on their extensions and names.
    This is a fallback method when LLM-based description generation fails.
    
    Args:
        repo_structure (dict): The repository structure from GitHubFetcher
        
    Returns:
        dict: Repository structure with basic descriptions
    """
    def process_structure(structure):
        result = {}
        for key, value in structure.items():
            if isinstance(value, dict):
                if "type" in value and value["type"] == "file":
                    # This is a file entry
                    result[key] = generate_basic_description(key)
                else:
                    # This is a directory or nested structure
                    result[key] = process_structure(value)
            else:
                # Unexpected format, just keep as is
                result[key] = value
        return result
    
    def generate_basic_description(filename):
        """Generate a basic description based on filename and extension"""
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        # Common Solana/Rust file descriptions
        if filename == "lib.rs":
            return "Main program entry point"
        elif filename == "Cargo.toml":
            return "Rust package configuration"
        elif filename == "Anchor.toml":
            return "Anchor framework configuration"
        elif filename == "Xargo.toml":
            return "Solana program configuration"
        elif filename == "package.json":
            return "JavaScript/TypeScript package configuration"
        elif filename == "tsconfig.json":
            return "TypeScript configuration"
        
        # Extension-based descriptions
        if ext == "rs":
            if "test" in filename:
                return "Rust test file"
            else:
                return "Rust source code"
        elif ext == "ts":
            if "test" in filename:
                return "TypeScript test file"
            else:
                return "TypeScript source code"
        elif ext == "js":
            if "test" in filename:
                return "JavaScript test file"
            else:
                return "JavaScript source code"
        elif ext == "json":
            return "JSON configuration file"
        elif ext == "md":
            return "Documentation file"
        elif ext == "gitignore":
            return "Git ignore rules"
        elif ext == "env":
            return "Environment variables"
        else:
            return f"{filename} file"
    
    return process_structure(repo_structure)

@app.post('/api/scan')
async def scan_code(request: ScanRequest = Body(...)):
    github_url = request.githubUrl

    # Mock successful scan response
    # In a real application, you would analyze the GitHub repository
    return {
        "status": "success",
        "RawCode": MOCK_CODE,
        "Lines": MOCK_SECURITY_ISSUES,
        "Report": f"""
# Security Scan Report for {github_url}

## Overview
The security scan identified several critical issues in the codebase that need attention.

## Vulnerability Summary
- **Missing Ownership Verification**: The code doesn't verify if the accounts are owned by the program.
- **Inadequate Authority Checks**: Authority signature verification is missing or commented out.
- **Unsafe Arithmetic**: Potential integer overflow vulnerabilities found.

## Recommendations
1. Always verify program ownership of accounts
2. Implement proper authority checks
3. Use checked arithmetic operations (checked_add, checked_sub)
4. Add proper error handling for all operations
5. Follow Solana security best practices for all privileged operations

## Secure Implementation
A secure implementation example is provided in the `process_transfer_secure` function.
"""
    }

