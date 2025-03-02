#!/usr/bin/env python3
"""
Test script for the validate_program_id endpoint
"""

import requests
import json
import sys

def test_validate_program_id(program_id):
    """
    Test the validate_program_id endpoint with the given program ID
    """
    url = "http://localhost:8000/api/validate-program"
    payload = {"programId": program_id}
    headers = {"Content-Type": "application/json"}
    
    print(f"Testing validate_program_id endpoint with program ID: {program_id}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Validated: {data.get('validated')}")
            
            repo_structure = data.get('RepoStructure', '')
            if repo_structure:
                print("\nRepository Structure (first 500 chars):")
                print(repo_structure[:500] + "..." if len(repo_structure) > 500 else repo_structure)
            else:
                print("\nNo repository structure returned")
        else:
            print(f"Error: {response.text}")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Use command line argument if provided, otherwise use a default program ID
    program_id = sys.argv[1] if len(sys.argv) > 1 else "tiME1hz9F5C5ZecbvE5z6Msjy8PKfTqo1UuRYXfndKF"
    
    test_validate_program_id(program_id) 