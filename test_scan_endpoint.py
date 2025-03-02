#!/usr/bin/env python3
"""
Test script for the scan_code endpoint
"""

import requests
import json
import sys

def test_scan_code(github_url):
    """
    Test the scan_code endpoint with the given GitHub URL
    """
    url = "http://localhost:8000/api/scan"
    payload = {"githubUrl": github_url}
    headers = {"Content-Type": "application/json"}
    
    print(f"Testing scan_code endpoint with GitHub URL: {github_url}")
    print("This may take a minute or two as it performs a full security analysis...")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            
            # Print metadata if available
            metadata = data.get('metadata', {})
            if metadata:
                print("\nMetadata:")
                print(f"Repository URL: {metadata.get('repository_url')}")
                print(f"Analyzed File: {metadata.get('analyzed_file')}")
                print(f"Analysis Time: {metadata.get('analysis_time')} seconds")
                print(f"LLM API Calls: {metadata.get('llm_api_calls')}")
            
            # Print a sample of the raw code
            raw_code = data.get('RawCode', '')
            if raw_code:
                print("\nRaw Code (first 200 chars):")
                print(raw_code[:200] + "..." if len(raw_code) > 200 else raw_code)
            
            # Print the security issues
            lines = data.get('Lines', [])
            if lines:
                print("\nSecurity Issues:")
                for line in lines[:5]:  # Show first 5 issues
                    print(f"Line {line[0]}: {line[1]} - {line[2]}")
                
                if len(lines) > 5:
                    print(f"... and {len(lines) - 5} more issues")
            
            # Print a sample of the report
            report = data.get('Report', '')
            if report:
                print("\nReport (first 500 chars):")
                print(report[:500] + "..." if len(report) > 500 else report)
            
            # Save the full response to a file for detailed review
            with open('scan_results.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("\nFull results saved to scan_results.json")
            
        else:
            print(f"Error: {response.text}")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Use command line argument if provided, otherwise use a default GitHub URL
    github_url = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/metaDAOproject/solana-timelock/tree/1a6d1e2dff20fbd46fb1209709c9a496d92f927d"
    
    test_scan_code(github_url) 