#!/usr/bin/env python3
import os
import sys
import json
import time
from pprint import pprint
import re

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from github_fetcher.github_fetcher import GitHubFetcher
from llm_analyzer.security_analyzer import SolanaSecurityAnalyzer

# Test repository URL
# TEST_REPO_URL = "https://github.com/solana-developers/CRUD-dApp"
TEST_REPO_URL = "https://github.com/metaDAOproject/solana-timelock/tree/1a6d1e2dff20fbd46fb1209709c9a496d92f927d"


def test_openai_api():
    """Test if the OpenAI API is working with a simple prompt."""
    print("\n=== Testing OpenAI API Connection ===")
    
    try:
        # Initialize the analyzer with OpenAI using GPT-4o-mini
        analyzer = SolanaSecurityAnalyzer(llm_provider="openai", model_name="gpt-4o-mini-2024-07-18")
        
        # Simple test prompt
        test_prompt = "Hello, please respond with 'OpenAI API is working correctly' if you can read this message."
        
        print(f"Sending test prompt to OpenAI API (model: gpt-4o-mini-2024-07-18)...")
        start_time = time.time()
        
        # Call the API
        response = analyzer._call_llm_api(test_prompt, max_tokens=50)
        
        # Print the response and time taken
        print(f"Response received in {time.time() - start_time:.2f} seconds:")
        print(f"Response: {response}")
        
        # Check if the response contains the expected text
        if "working" in response.lower() and "openai" in response.lower():
            print("✅ OpenAI API test PASSED")
        else:
            print("❌ OpenAI API test FAILED: Unexpected response")
            
    except Exception as e:
        print(f"❌ OpenAI API test FAILED: {str(e)}")

def test_file_selection():
    """Test the file selection functionality using LLM."""
    print("\n=== Testing File Selection with LLM ===")
    
    try:
        # Initialize the analyzer with OpenAI using GPT-4o-mini
        analyzer = SolanaSecurityAnalyzer(llm_provider="openai", model_name="gpt-4o-mini-2024-07-18")
        
        print(f"Analyzing repository: {TEST_REPO_URL}")
        
        # Get repository structure using the hybrid approach
        print("Fetching repository structure...")
        github_fetcher = GitHubFetcher()
        repo_data = github_fetcher.get_files_for_llm_analysis(TEST_REPO_URL)

        # pprint(repo_data)

        # return
        
        # Prepare the prompt for file selection
        print("Preparing file selection prompt...")
        file_selection_prompt = analyzer._prepare_file_selection_prompt(TEST_REPO_URL, repo_data, approach="hybrid")
        
        # Call the LLM API to select files
        print("Asking LLM to select files for analysis...")
        start_time = time.time()
        file_selection_response = analyzer._call_llm_api(file_selection_prompt)

        print(file_selection_response)
        return
        
        # Parse the file selection response
        selected_files = analyzer._parse_file_selection_response(file_selection_response, repo_data)
        
        # Print the results
        print(f"\nFile selection completed in {time.time() - start_time:.2f} seconds")
        print(f"Selected {len(selected_files)} files for analysis:")
        for i, file_path in enumerate(selected_files, 1):
            print(f"{i}. {file_path}")
        
        # Verify if files exist in the repository
        print("\nVerifying selected files...")
        for file_path in selected_files:
            try:
                content = github_fetcher.read_file(TEST_REPO_URL, file_path)
                print(f"✅ File exists: {file_path} ({len(content)} bytes)")
            except Exception as e:
                print(f"❌ File does not exist: {file_path} - Error: {str(e)}")
        
        return selected_files
        
    except Exception as e:
        print(f"❌ File selection test FAILED: {str(e)}")
        return []

def test_file_selection_hybrid():
    """Test the file selection functionality using LLM with the hybrid approach."""
    print("\n=== Testing File Selection with LLM (Hybrid Approach) ===")
    
    try:
        # Initialize the analyzer with OpenAI using GPT-4o-mini
        analyzer = SolanaSecurityAnalyzer(llm_provider="openai", model_name="gpt-4o-mini-2024-07-18")
        
        print(f"Analyzing repository: {TEST_REPO_URL}")
        
        # Get repository structure using the hybrid approach
        print("Fetching repository structure using hybrid approach...")
        github_fetcher = GitHubFetcher()
        repo_data = github_fetcher.get_files_for_llm_analysis(TEST_REPO_URL)

        # pprint(repo_data)
        # return
    
        # Prepare the prompt for file selection
        print("Preparing file selection prompt...")
        file_selection_prompt = analyzer._prepare_file_selection_prompt(TEST_REPO_URL, repo_data, approach="hybrid")
        
        # Call the LLM API to select files
        print("Asking LLM to select files for analysis...")
        start_time = time.time()
        file_selection_response = analyzer._call_llm_api(file_selection_prompt)
        
        print("\nLLM Response (Hybrid Approach):")
        print(file_selection_response)
        
        # Parse the file selection response
        selected_files = analyzer._parse_file_selection_response(file_selection_response, repo_data)
        
        # Print the results
        print(f"\nFile selection completed in {time.time() - start_time:.2f} seconds")
        print(f"Selected {len(selected_files)} unique files for analysis (Hybrid Approach):")
        for i, file_path in enumerate(selected_files, 1):
            print(f"{i}. {file_path}")
        
        # Verify if files exist in the repository
        print("\nVerifying selected files...")
        for file_path in selected_files:
            try:
                content = github_fetcher.read_file(TEST_REPO_URL, file_path)
                print(f"✅ File exists: {file_path} ({len(content)} bytes)")
            except Exception as e:
                print(f"❌ File does not exist: {file_path} - Error: {str(e)}")
        
        return selected_files
        
    except Exception as e:
        print(f"❌ File selection test (Hybrid) FAILED: {str(e)}")
        return []

def test_file_selection_structure():
    """Test the file selection functionality using LLM with the structure-only approach."""
    print("\n=== Testing File Selection with LLM (Structure-Only Approach) ===")
    
    try:
        # Initialize the analyzer with OpenAI using GPT-4o-mini
        analyzer = SolanaSecurityAnalyzer(llm_provider="openai", model_name="gpt-4o-mini-2024-07-18")
        
        print(f"Analyzing repository: {TEST_REPO_URL}")
        
        # Get repository structure using the structure-only approach
        print("Fetching repository structure using structure-only approach...")
        github_fetcher = GitHubFetcher()
        repo_data = github_fetcher.get_file_structure_for_llm(TEST_REPO_URL)
        
        # Prepare the prompt for file selection
        print("Preparing file selection prompt...")
        file_selection_prompt = analyzer._prepare_file_selection_prompt(TEST_REPO_URL, repo_data, approach="structure_only")
        
        # Call the LLM API to select files
        print("Asking LLM to select files for analysis...")
        start_time = time.time()
        file_selection_response = analyzer._call_llm_api(file_selection_prompt)
        
        print("\nLLM Response (Structure-Only Approach):")
        print(file_selection_response)
        
        # Parse the file selection response
        selected_files = analyzer._parse_file_selection_response(file_selection_response, repo_data)
        
        # Print the results
        print(f"\nFile selection completed in {time.time() - start_time:.2f} seconds")
        print(f"Selected {len(selected_files)} unique files for analysis (Structure-Only Approach):")
        for i, file_path in enumerate(selected_files, 1):
            print(f"{i}. {file_path}")
        
        # Verify if files exist in the repository
        print("\nVerifying selected files...")
        for file_path in selected_files:
            try:
                content = github_fetcher.read_file(TEST_REPO_URL, file_path)
                print(f"✅ File exists: {file_path} ({len(content)} bytes)")
            except Exception as e:
                print(f"❌ File does not exist: {file_path} - Error: {str(e)}")
        
        return selected_files
        
    except Exception as e:
        print(f"❌ File selection test (Structure-Only) FAILED: {str(e)}")
        return []

def test_github_fetcher_hybrid():
    """Test the GitHub fetcher hybrid approach."""
    print(f"\n=== Testing GitHub Fetcher (Hybrid Approach) ===")
    print(f"Repository: {TEST_REPO_URL}")
    
    # Initialize the GitHub fetcher
    github_fetcher = GitHubFetcher()
    
    # Test the hybrid approach (get_files_for_llm_analysis)
    start_time = time.time()
    hybrid_result = github_fetcher.get_files_for_llm_analysis(TEST_REPO_URL)
    hybrid_time = time.time() - start_time
    
    # Print summary of hybrid approach results
    summary = hybrid_result.get("summary", {})
    print(f"Hybrid Approach Summary:")
    print(f"- Total Files: {summary.get('total_files', 0)}")
    print(f"- Program Files: {summary.get('program_files', 0)}")
    print(f"- Client Files: {summary.get('client_files', 0)}")
    print(f"- Config Files: {summary.get('config_files', 0)}")
    print(f"- Test Files: {summary.get('test_files', 0)}")
    print(f"- Other Files: {summary.get('other_files', 0)}")
    print(f"- Time taken: {hybrid_time:.2f} seconds")
    
    # Print sample program files
    program_files = hybrid_result.get("program", [])
    print("\nSample Program Files:")
    for file_info in program_files[:5]:  # Show first 5 program files
        file_path = file_info.get("path", "")
        print(f"- {file_path}")
    
    # Test reading a file
    if program_files:
        sample_file = program_files[0].get("path", "")
        print(f"\n=== Testing File Reading for {sample_file} ===")
        try:
            content = github_fetcher.read_file(TEST_REPO_URL, sample_file)
            print(f"Successfully read file: {sample_file}")
            print(f"Content length: {len(content)} characters")
            print(f"First 200 characters:\n{content[:200]}...")
        except Exception as e:
            print(f"Error reading file {sample_file}: {str(e)}")
    
    # Print API call statistics
    print("\n=== GitHub API Call Statistics ===")
    api_stats = github_fetcher.get_api_call_stats()
    print(f"Total API calls: {api_stats.get('total_calls', 0)}")
    print(f"Cache hits: {api_stats.get('cache_hits', 0)}")
    print(f"Rate limit remaining: {api_stats.get('rate_limit_remaining', 'unknown')}")
    
    return hybrid_result

def test_github_fetcher_structure():
    """Test the GitHub fetcher structure-only approach."""
    print(f"\n=== Testing GitHub Fetcher (Structure-Only Approach) ===")
    print(f"Repository: {TEST_REPO_URL}")
    
    # Initialize the GitHub fetcher
    github_fetcher = GitHubFetcher()
    
    # Test the structure-only approach (get_file_structure_for_llm)
    start_time = time.time()
    structure_result = github_fetcher.get_file_structure_for_llm(TEST_REPO_URL)
    structure_time = time.time() - start_time
    
    # Print summary of structure-only approach results
    summary = structure_result.get("summary", {})
    print(f"Structure-Only Approach Summary:")
    print(f"- Total Files: {summary.get('total_files', 0)}")
    print(f"- Time taken: {structure_time:.2f} seconds")
    
    # Print sample files
    files = structure_result.get("files", [])
    print("\nSample Files:")
    for file_path in files[:5]:  # Show first 5 files
        print(f"- {file_path}")
    
    # Print the full repository structure
    print("\nFull Repository Structure:")
    structure = structure_result.get("structure", {})
    print(json.dumps(structure, indent=2)[:1000])  # Print first 1000 characters to avoid overwhelming output
    print("... (truncated)")
    
    # Print the number of directories and files in the structure
    def count_items(structure_dict):
        dirs = 0
        files = 0
        for key, value in structure_dict.items():
            if isinstance(value, dict):
                dirs += 1
                sub_dirs, sub_files = count_items(value)
                dirs += sub_dirs
                files += sub_files
            else:
                files += 1
        return dirs, files
    
    dirs, files = count_items(structure)
    print(f"\nStructure contains {dirs} directories and {files} files")
    
    # Print API call statistics
    print("\n=== GitHub API Call Statistics ===")
    api_stats = github_fetcher.get_api_call_stats()
    print(f"Total API calls: {api_stats.get('total_calls', 0)}")
    print(f"Cache hits: {api_stats.get('cache_hits', 0)}")
    print(f"Rate limit remaining: {api_stats.get('rate_limit_remaining', 'unknown')}")
    
    return structure_result

if __name__ == "__main__":
    # Test file selection with LLM (original)
    # test_file_selection()
    
    # Test file selection with LLM (hybrid approach)
    # test_file_selection_hybrid()
    
    # Test file selection with LLM (structure-only approach)
    # test_file_selection_structure()
    
    # Test the OpenAI API
    # test_openai_api()
    
    # Test the GitHub fetcher hybrid approach
    # test_github_fetcher_hybrid()
    
    # Test the GitHub fetcher structure-only approach
    # test_github_fetcher_structure() 

    pass