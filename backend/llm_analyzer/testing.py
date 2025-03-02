#!/usr/bin/env python3
"""
Testing script for the line-by-line analysis flow of the SolanaSecurityAnalyzer.
This script demonstrates how to use the analyzer to perform a line-by-line security analysis
of a Solana repository.
"""

import os
import sys
import time
import json
from pprint import pprint

# Add the parent directory to the path so we can import the modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import the analyzer modules
from llm_analyzer.security_analyzer import SolanaSecurityAnalyzer
from github_fetcher.github_fetcher import GitHubFetcher

def print_section(title):
    """Print a section header to make the output more readable."""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80)

def print_step(step_number, description):
    """Print a step header to make the output more readable."""
    print(f"\n--- STEP {step_number}: {description} ---")

def analyze_repository_line_by_line(repo_url, llm_provider="openai", model_name="gpt-4o-mini-2024-07-18"):
    """
    Analyze a Solana repository for security vulnerabilities using line-by-line analysis.
    
    Args:
        repo_url (str): URL of the GitHub repository to analyze
        llm_provider (str): The LLM provider to use (e.g., "openai")
        model_name (str): The name of the model to use
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    print_section("INITIALIZING")
    print(f"Repository URL: {repo_url}")
    print(f"LLM Provider: {llm_provider}")
    print(f"Model Name: {model_name}")
    
    start_time = time.time()
    
    # Step 1: Initialize the analyzer
    print_step(1, "Initializing the SolanaSecurityAnalyzer")
    analyzer = SolanaSecurityAnalyzer(llm_provider=llm_provider, model_name=model_name)
    print(f"Analyzer initialized with {llm_provider} provider and {model_name} model")
    
    # Step 2: Initialize the GitHub fetcher
    print_step(2, "Initializing the GitHubFetcher")
    github_fetcher = analyzer.github_fetcher
    print(f"GitHub fetcher initialized")
    
    # Step 3: Get repository structure
    print_step(3, "Fetching repository structure")
    print(f"Getting file structure for {repo_url}...")
    repo_structure = github_fetcher.get_file_structure_for_llm(repo_url)
    print(f"Repository structure fetched with {len(repo_structure['files'])} files")
    
    # Print some sample files to give an idea of the repository structure
    print("\nSample files from the repository:")
    for file in repo_structure['files'][:5]:  # Show first 5 files
        print(f"- {file['path']}")
    
    if len(repo_structure['files']) > 5:
        print(f"... and {len(repo_structure['files']) - 5} more files")
    
    # Step 4: Prepare the prompt for file selection
    print_step(4, "Preparing prompt for file selection")
    file_selection_prompt = f"""
You are a security expert specializing in Solana blockchain programs. Your task is to select the single most important file for security analysis.

Repository URL: {repo_url}

Examine the repository structure below and identify which file is most likely to contain Solana program code (typically Rust files, especially those in 'programs' directories, or files like Anchor.toml).

Repository Structure:
{json.dumps(repo_structure['structure'], indent=2)[:3000]}  # Truncated to avoid token limits

Based on the structure, select the SINGLE most important file that is most likely to contain security vulnerabilities or malicious behavior in Solana program code.

IMPORTANT: Format your response exactly as shown below. Do NOT use backticks, asterisks, or any other markdown formatting in the file path:

Selected file: file_path
Reason: brief explanation of why you selected this file

The file path should be exactly as it appears in the repository structure, with no additional formatting.
"""
    print("File selection prompt prepared")
    
    # Step 5: Call the LLM API to select the most important file
    print_step(5, "Calling LLM API to select the most important file")
    print(f"Sending request to {llm_provider} API ({model_name})...")
    file_selection_response = analyzer._call_llm_api(file_selection_prompt)
    print("\nLLM Response for file selection:")
    print(file_selection_response)
    
    # Step 6: Parse the file selection response
    print_step(6, "Parsing file selection response")
    # Extract the selected file path using regex
    import re
    selected_file_match = re.search(r'Selected file:?\s*([^\n]+)', file_selection_response)
    
    if selected_file_match:
        selected_file = selected_file_match.group(1).strip()
        print(f"Selected file: {selected_file}")
    else:
        # Fallback: try to find any file path in the response
        file_path_match = re.search(r'([a-zA-Z0-9_\-/.]+\.(rs|toml|json|js|ts|py))', file_selection_response)
        if file_path_match:
            selected_file = file_path_match.group(0)
            print(f"Selected file (fallback method): {selected_file}")
        else:
            # Last resort: use the first Rust file in the repository
            rust_files = [f['path'] for f in repo_structure['files'] if f['path'].endswith('.rs')]
            if rust_files:
                selected_file = rust_files[0]
                print(f"Selected file (last resort): {selected_file}")
            else:
                print("Error: Could not determine which file to analyze")
                return {"error": "Could not determine which file to analyze"}
    
    # Step 7: Fetch content of the selected file
    print_step(7, "Fetching content of the selected file")
    try:
        file_content = github_fetcher.read_file(repo_url, selected_file)
        print(f"Successfully fetched content for {selected_file} ({len(file_content)} characters)")
        
        # Print a preview of the file content
        content_preview = file_content[:500] + "..." if len(file_content) > 500 else file_content
        print(f"\nFile content preview:\n{content_preview}")
    except Exception as e:
        print(f"Error fetching content for {selected_file}: {str(e)}")
        return {"error": f"Error fetching file content: {str(e)}"}
    
    # Step 8: Prepare the prompt for line-by-line analysis
    print_step(8, "Preparing prompt for line-by-line analysis")
    
    # Limit to first 250 lines to avoid token limits
    file_lines = file_content.split('\n')
    lines_to_analyze = file_lines[:250]
    
    print(f"Analyzing first {len(lines_to_analyze)} lines of {len(file_lines)} total lines")
    
    # Create a numbered version of the code for the prompt
    numbered_code = ""
    for i, line in enumerate(lines_to_analyze, 1):
        numbered_code += f"{i}: {line}\n"
    
    # Escape any curly braces in the code to avoid f-string formatting issues
    numbered_code = numbered_code.replace("{", "{{").replace("}", "}}")
    
    line_analysis_prompt = f"""
You are a security expert specializing in Solana blockchain programs. Your task is to analyze the following Solana code for security vulnerabilities and malicious behavior, line by line.

Repository URL: {repo_url}
File: {selected_file}

Below is the code with line numbers. For each line that contains a security-relevant pattern (either good or bad), provide an assessment.

{numbered_code}

For each security-relevant line, provide:
1. The line number
2. Whether it's a "good" or "bad" practice
3. A brief explanation of why

Format your response as a JSON array of arrays, where each inner array contains:
[line_number, "good"/"bad", "explanation"]

For example:
[
  [12, "good", "Proper validation of account ownership"],
  [25, "bad", "Missing input validation, could lead to integer overflow"],
  [37, "good", "Correctly checks for signer authorization"]
]

After the line-by-line analysis, provide a summary of the overall security posture of the code.
Format your response as follows:

```json
{{
  "lines": [
    [line_number, "good"/"bad", "explanation"],
    ...
  ],
  "summary": "Overall assessment of the code's security"
}}
```
"""
    print("Line-by-line analysis prompt prepared")
    
    # Step 9: Call the LLM API for line-by-line analysis
    print_step(9, "Calling LLM API for line-by-line analysis")
    print(f"Sending request to {llm_provider} API ({model_name})...")
    line_analysis_response = analyzer._call_llm_api(line_analysis_prompt)
    print("\nLLM Response for line-by-line analysis (preview):")
    response_preview = line_analysis_response[:500] + "..." if len(line_analysis_response) > 500 else line_analysis_response
    print(response_preview)
    
    # Step 10: Parse the line-by-line analysis response
    print_step(10, "Parsing line-by-line analysis response")
    
    # Extract the JSON part of the response
    json_match = re.search(r'```json\s*(.*?)\s*```', line_analysis_response, re.DOTALL)
    
    if json_match:
        json_str = json_match.group(1)
        try:
            analysis_results = json.loads(json_str)
            print("Successfully parsed JSON response")
        except json.JSONDecodeError:
            print("Error: Could not parse JSON response, trying fallback method")
            # Fallback: try to extract the lines and summary separately
            analysis_results = {"lines": [], "summary": ""}
            
            # Try to extract lines
            lines_match = re.search(r'"lines":\s*(\[\s*\[.*?\]\s*\])', line_analysis_response, re.DOTALL)
            if lines_match:
                try:
                    lines_str = lines_match.group(1)
                    analysis_results["lines"] = json.loads(lines_str)
                    print(f"Extracted {len(analysis_results['lines'])} lines using fallback method")
                except:
                    print("Error: Could not parse lines using fallback method")
            
            # Try to extract summary
            summary_match = re.search(r'"summary":\s*"(.*?)"', line_analysis_response, re.DOTALL)
            if summary_match:
                analysis_results["summary"] = summary_match.group(1)
                print("Extracted summary using fallback method")
    else:
        # If no JSON format is found, try to parse the response as best as possible
        print("Error: Could not find JSON in response, using best-effort parsing")
        
        # Initialize results
        analysis_results = {"lines": [], "summary": ""}
        
        # Look for line numbers followed by "good" or "bad"
        line_pattern = r'(\d+)[^\n]*?(good|bad)[^\n]*?:?\s*([^\n]+)'
        line_matches = re.findall(line_pattern, line_analysis_response, re.IGNORECASE)
        
        for match in line_matches:
            line_num = int(match[0])
            assessment = match[1].lower()
            explanation = match[2].strip()
            analysis_results["lines"].append([line_num, assessment, explanation])
        
        print(f"Extracted {len(analysis_results['lines'])} lines using regex pattern")
        
        # Try to extract a summary
        summary_match = re.search(r'summary:?\s*([^\n]+(?:\n[^\n]+)*)', line_analysis_response, re.IGNORECASE)
        if summary_match:
            analysis_results["summary"] = summary_match.group(1).strip()
            print("Extracted summary using regex pattern")
    
    # Add metadata to the results
    analysis_results["metadata"] = {
        "repository_url": repo_url,
        "analyzed_file": selected_file,
        "analysis_time": time.time() - start_time,
        "llm_provider": llm_provider,
        "model_name": model_name,
        "llm_api_calls": analyzer.llm_api_calls
    }
    
    # Step 11: Print the results
    print_step(11, "Printing analysis results")
    
    print(f"\nAnalyzed file: {selected_file}")
    print(f"Analysis time: {analysis_results['metadata']['analysis_time']:.2f} seconds")
    print(f"LLM API calls: {analysis_results['metadata']['llm_api_calls']}")
    
    print("\nLine-by-line analysis:")
    for line_info in analysis_results.get("lines", []):
        if len(line_info) >= 3:
            line_num, assessment, reasoning = line_info
            print(f"Line {line_num}: [{assessment.upper()}] - {reasoning}")
    
    print("\nSummary:")
    print(analysis_results.get("summary", "No summary available"))
    
    return analysis_results

if __name__ == "__main__":
    print_section("SOLANA SECURITY ANALYZER - LINE-BY-LINE ANALYSIS TEST")
    
    # Repository URL to analyze
    repo_url = "https://github.com/metaDAOproject/solana-timelock/tree/1a6d1e2dff20fbd46fb1209709c9a496d92f927d"
    
    # Use the model specified in the .env.local file
    # For this test, we'll use "gpt-4o-mini" as requested
    model_name = "gpt-4o-mini"
    
    # Run the analysis
    results = analyze_repository_line_by_line(repo_url, llm_provider="openai", model_name=model_name)
    
    # Save the results to a file for reference
    output_file = "analysis_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print_section("ANALYSIS COMPLETE")
    print(f"Results saved to {output_file}") 