import os
import sys
import json
from typing import Dict, List, Optional, Any, Tuple
import time
import dotenv

# Add the parent directory to the path so we can import the github_fetcher module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from github_fetcher.github_fetcher import GitHubFetcher

class SolanaSecurityAnalyzer:
    """
    A class that uses LLMs to analyze Solana code for security vulnerabilities and malicious behavior.
    Uses an agentic approach with multiple LLM calls.
    """
    
    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4", api_key: Optional[str] = None):
        """
        Initialize the SolanaSecurityAnalyzer.
        
        Args:
            llm_provider (str): The LLM provider to use (e.g., "openai", "anthropic")
            model_name (str): The name of the model to use
            api_key (Optional[str]): API key for the LLM provider. If None, will try to get from env vars
        """
        # Load environment variables from .env.local
        self._load_env_vars()
        
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.api_key = api_key or self._load_api_key()
        
        # Initialize the GitHub fetcher
        self.github_fetcher = GitHubFetcher()
        
        # Track analysis time and API calls
        self.analysis_time = 0
        self.llm_api_calls = 0
        
    def _load_env_vars(self):
        """Load environment variables from .env.local file."""
        # Try to load from .env.local in the backend directory
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(backend_dir, '.env.local')
        
        if os.path.exists(env_path):
            print(f"Loading environment variables from {env_path}")
            dotenv.load_dotenv(env_path)
        else:
            # Try to load from .env.local in the project root
            project_root = os.path.dirname(backend_dir)
            env_path = os.path.join(project_root, '.env.local')
            if os.path.exists(env_path):
                print(f"Loading environment variables from {env_path}")
                dotenv.load_dotenv(env_path)
            else:
                print("Warning: .env.local file not found. Using existing environment variables.")
        
    def _load_api_key(self) -> str:
        """Load API key from environment variables."""
        # For OpenAI, try to get the API key from environment variables
        if self.llm_provider.lower() == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                return api_key
        
        # For other providers, try the standard format
        env_var_name = f"{self.llm_provider.upper()}_API_KEY"
        api_key = os.getenv(env_var_name)
        
        if not api_key:
            raise ValueError(
                f"API key for {self.llm_provider} is required. Set {env_var_name} environment variable."
            )
        return api_key
    
    def _call_llm_api(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        Call the LLM API with the given prompt.
        
        Args:
            prompt (str): The prompt to send to the LLM
            max_tokens (int): Maximum number of tokens to generate
            
        Returns:
            str: The LLM's response
        """
        print(f"Calling {self.llm_provider} API with model {self.model_name}...")
        print(f"Prompt length: {len(prompt)} characters")
        
        # Increment API call counter
        self.llm_api_calls += 1
        
        # For OpenAI provider, call the actual API
        if self.llm_provider.lower() == "openai":
            try:
                import openai
                
                # Initialize the OpenAI client
                client = openai.OpenAI(api_key=self.api_key)
                
                # Call the OpenAI API
                print(f"Sending request to OpenAI API ({self.model_name})...")
                start_time = time.time()
                
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a security expert specializing in Solana blockchain programs."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.5,  # Lower temperature for more deterministic responses
                )
                
                # Extract the response text
                response_text = response.choices[0].message.content
                
                # Log the API call time
                print(f"OpenAI API call completed in {time.time() - start_time:.2f} seconds")
                
                return response_text
                
            except ImportError:
                raise ImportError("openai package not installed. Please install it with 'pip install openai'.")
                
            except Exception as e:
                raise Exception(f"Error calling OpenAI API: {str(e)}")
        
        # For other providers (not implemented yet)
        else:
            raise ValueError(f"{self.llm_provider} provider not implemented. Please use 'openai'.")
    
    def analyze_repository_hybrid(self, repo_url: str) -> Dict[str, Any]:
        """
        Analyze a Solana repository for security vulnerabilities and malicious behavior using the hybrid approach.
        Uses an agentic approach with multiple LLM calls.
        
        Args:
            repo_url (str): URL of the GitHub repository to analyze
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        start_time = time.time()
        
        # Step 1: Get categorized files using the hybrid approach
        print(f"Fetching repository structure for {repo_url}...")
        llm_files = self.github_fetcher.get_files_for_llm_analysis(repo_url)
        
        # Step 2: Prepare the prompt for file selection
        file_selection_prompt = self._prepare_file_selection_prompt(repo_url, llm_files, approach="hybrid")
        
        # Step 3: Call the LLM API to select files
        print("Asking LLM to select files for analysis...")
        file_selection_response = self._call_llm_api(file_selection_prompt)
        
        # Step 4: Parse the file selection response
        selected_files = self._parse_file_selection_response(file_selection_response, llm_files)
        
        # Step 5: Fetch content of selected files
        print(f"Fetching content of {len(selected_files)} selected files...")
        file_contents = self._fetch_file_contents(repo_url, selected_files)
        
        # Step 6: Prepare the prompt for security analysis
        security_analysis_prompt = self._prepare_security_analysis_prompt(repo_url, file_contents)
        
        # Step 7: Call the LLM API for security analysis
        print("Performing security analysis...")
        security_analysis_response = self._call_llm_api(security_analysis_prompt)
        
        # Step 8: Parse the security analysis response
        analysis_results = self._parse_security_analysis_response(security_analysis_response)
        
        # Add metadata to the results
        analysis_results["metadata"] = {
            "repository_url": repo_url,
            "analysis_approach": "hybrid",
            "llm_provider": self.llm_provider,
            "model_name": self.model_name,
            "analysis_time": time.time() - start_time,
            "llm_api_calls": self.llm_api_calls
        }
        
        self.analysis_time = time.time() - start_time
        return analysis_results
    
    def analyze_repository_structure_only(self, repo_url: str) -> Dict[str, Any]:
        """
        Analyze a Solana repository for security vulnerabilities and malicious behavior using the structure-only approach.
        Uses an agentic approach with multiple LLM calls.
        
        Args:
            repo_url (str): URL of the GitHub repository to analyze
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        start_time = time.time()
        
        # Step 1: Get the repository structure
        print(f"Fetching repository structure for {repo_url}...")
        repo_structure = self.github_fetcher.get_file_structure_for_llm(repo_url)
        
        # Step 2: Prepare the prompt for file selection
        file_selection_prompt = self._prepare_file_selection_prompt(repo_url, repo_structure, approach="structure_only")
        
        # Step 3: Call the LLM API to select files
        print("Asking LLM to select files for analysis...")
        file_selection_response = self._call_llm_api(file_selection_prompt)
        
        # Step 4: Parse the file selection response
        selected_files = self._parse_file_selection_response(file_selection_response, repo_structure)
        
        # Step 5: Fetch content of selected files
        print(f"Fetching content of {len(selected_files)} selected files...")
        file_contents = self._fetch_file_contents(repo_url, selected_files)
        
        # Step 6: Prepare the prompt for security analysis
        security_analysis_prompt = self._prepare_security_analysis_prompt(repo_url, file_contents)
        
        # Step 7: Call the LLM API for security analysis
        print("Performing security analysis...")
        security_analysis_response = self._call_llm_api(security_analysis_prompt)
        
        # Step 8: Parse the security analysis response
        analysis_results = self._parse_security_analysis_response(security_analysis_response)
        
        # Add metadata to the results
        analysis_results["metadata"] = {
            "repository_url": repo_url,
            "analysis_approach": "structure_only",
            "llm_provider": self.llm_provider,
            "model_name": self.model_name,
            "analysis_time": time.time() - start_time,
            "llm_api_calls": self.llm_api_calls
        }
        
        self.analysis_time = time.time() - start_time
        return analysis_results
    
    def _prepare_file_selection_prompt(self, repo_url: str, repo_data: Dict, approach: str) -> str:
        """
        Prepare a prompt for the LLM to select files for security analysis.
        
        Args:
            repo_url (str): URL of the GitHub repository
            repo_data (Dict): Repository data (either categorized files or structure)
            approach (str): The approach being used ("hybrid" or "structure_only")
            
        Returns:
            str: The prompt for the LLM
        """
        if approach == "hybrid":
            # For the hybrid approach, we provide pre-categorized files
            program_files = repo_data.get("program", [])
            client_files = repo_data.get("client", [])
            config_files = repo_data.get("config", [])
            summary = repo_data.get("summary", {})
            
            prompt = f"""
You are a security expert specializing in Solana blockchain programs. Your task is to select the most relevant files for security analysis.

Repository URL: {repo_url}

Repository Summary:
- Total Files: {summary.get('total_files', 0)}
- Program Files: {summary.get('program_files', 0)}
- Client Files: {summary.get('client_files', 0)}
- Config Files: {summary.get('config_files', 0)}
- Test Files: {summary.get('test_files', 0)}
- Other Files: {summary.get('other_files', 0)}

I'll provide you with lists of files categorized by type. Please select up to 3 files that are most likely to contain security vulnerabilities or malicious behavior.

Program Files:
"""
            
            # Add program files
            for file_info in program_files:
                file_path = file_info.get("path", "")
                prompt += f"- {file_path}\n"
            
            # Add config files if there are few program files
            if len(program_files) < 3 and config_files:
                prompt += "\nConfig Files:\n"
                for file_info in config_files:
                    file_path = file_info.get("path", "")
                    prompt += f"- {file_path}\n"
            
            # Add client files if there are very few program and config files
            if len(program_files) + len(config_files) < 3 and client_files:
                prompt += "\nClient Files:\n"
                for file_info in client_files[:10]:  # Limit to first 10 client files
                    file_path = file_info.get("path", "")
                    prompt += f"- {file_path}\n"
            
            prompt += """
Please rank the top 3 files in order of importance for security analysis. For each file, provide a brief explanation of why you selected it.

IMPORTANT: Format your response exactly as shown below. Do NOT use backticks, asterisks, or any other markdown formatting in the file paths:

1. file_path - reason for selection
2. file_path - reason for selection
3. file_path - reason for selection

The file paths should be exactly as they appear in the list above, with no additional formatting.
"""
            
        else:  # structure_only approach
            # For the structure-only approach, we provide the raw structure and let the LLM decide
            files = repo_data.get("files", [])
            structure = repo_data.get("structure", {})
            summary = repo_data.get("summary", {})
            
            prompt = f"""
You are a security expert specializing in Solana blockchain programs. Your task is to select the most relevant files for security analysis.

Repository URL: {repo_url}

Repository Summary:
- Total Files: {summary.get('total_files', 0)}

Examine the repository structure below and identify which files are likely to contain Solana program code (typically Rust files, especially those in 'programs' directories, or files like Anchor.toml).

Repository Structure:
{json.dumps(structure, indent=2)[:3000]}  # Truncated to avoid token limits

Based on the structure, select up to 3 files that are most likely to contain security vulnerabilities or malicious behavior in Solana program code.

Please rank the top 3 files in order of importance for security analysis. For each file, provide a brief explanation of why you selected it.

IMPORTANT: Format your response exactly as shown below. Do NOT use backticks, asterisks, or any other markdown formatting in the file paths:

1. file_path - reason for selection
2. file_path - reason for selection
3. file_path - reason for selection

The file paths should be exactly as they appear in the repository structure, with no additional formatting.
"""
        
        return prompt
    
    def _parse_file_selection_response(self, response: str, repo_data: Dict) -> List[str]:
        """
        Parse the LLM's file selection response to get the list of selected files.
        
        Args:
            response (str): The LLM's response
            repo_data (Dict): Repository data (for validation)
            
        Returns:
            List[str]: List of selected file paths
        """
        # This is a simplified parser. In a real implementation, we would use regex or more robust parsing.
        selected_files = []
        
        # Split the response into lines
        lines = response.strip().split('\n')
        
        # First, try to find numbered lines with file paths (1. file_path - reason)
        for line in lines:
            # Look for numbered lines (1. file_path - reason)
            if line.strip() and line[0].isdigit() and '. ' in line and ' - ' in line:
                # Extract the file path (everything between the number and the dash)
                parts = line.split(' - ', 1)
                if len(parts) > 0:
                    file_with_num = parts[0].strip()
                    # Remove the number and dot
                    file_path = file_with_num.split('. ', 1)[-1].strip()
                    
                    # Clean up the file path (remove backticks, brackets, etc.)
                    file_path = self._clean_file_path(file_path)
                    
                    # Validate that this looks like a file path (contains a dot or slash)
                    if ('.' in file_path or '/' in file_path) and file_path not in selected_files:
                        selected_files.append(file_path)
        
        # If no files were found using the numbered format, try to find file paths in the text
        if not selected_files:
            # Look for file paths in the text (simple heuristic)
            import re
            file_patterns = [
                r'`([^`]+\.(rs|toml|json|js|ts|py))`',  # Paths in backticks
                r'([a-zA-Z0-9_\-/.]+\.(rs|toml|json|js|ts|py))',  # Paths with extensions
                r'(anchor/[a-zA-Z0-9_\-/.]+)',  # Paths starting with anchor/
                r'(programs/[a-zA-Z0-9_\-/.]+)'  # Paths starting with programs/
            ]
            
            for pattern in file_patterns:
                matches = re.findall(pattern, response)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]  # Take the first group if there are multiple
                    
                    # Clean up the file path
                    file_path = self._clean_file_path(match)
                    
                    if file_path and file_path not in selected_files:
                        selected_files.append(file_path)
                
                if selected_files:
                    break
        
        # If we still don't have any files, use a fallback approach
        if not selected_files:
            # Use a generic fallback approach
            print("Warning: Could not parse file paths from LLM response.")
            
            # Try to extract some reasonable files from the repository data
            if "program" in repo_data:
                # This is the hybrid approach data
                program_files = repo_data.get("program", [])
                for file_info in program_files[:3]:  # Take up to 3 program files
                    file_path = file_info.get("path", "")
                    if file_path and file_path not in selected_files:
                        selected_files.append(file_path)
            elif "files" in repo_data:
                # This is the structure-only approach data
                files = repo_data.get("files", [])
                for file_path in files[:3]:  # Take up to 3 files
                    if file_path and (file_path.endswith('.rs') or file_path.endswith('.toml')) and file_path not in selected_files:
                        selected_files.append(file_path)
        
        # Limit to 3 files
        selected_files = selected_files[:3]
        
        print(f"Selected files for analysis: {selected_files}")
        return selected_files
    
    def _clean_file_path(self, file_path: str) -> str:
        """
        Clean up a file path by removing backticks, brackets, and other formatting.
        
        Args:
            file_path (str): The file path to clean
            
        Returns:
            str: The cleaned file path
        """
        # Remove backticks
        clean_path = file_path.replace('`', '')
        
        # Remove brackets
        clean_path = clean_path.replace('[', '').replace(']', '')
        
        # Remove asterisks (markdown formatting)
        clean_path = clean_path.replace('*', '')
        
        # Remove any text in parentheses at the end of the file path
        import re
        clean_path = re.sub(r'\s*\([^)]*\)\s*$', '', clean_path)
        
        # Remove any leading/trailing whitespace
        clean_path = clean_path.strip()
        
        return clean_path
    
    def _fetch_file_contents(self, repo_url: str, file_paths: List[str]) -> Dict[str, str]:
        """
        Fetch the content of the selected files.
        
        Args:
            repo_url (str): URL of the GitHub repository
            file_paths (List[str]): List of file paths to fetch
            
        Returns:
            Dict[str, str]: Dictionary mapping file paths to their content
        """
        file_contents = {}
        
        for file_path in file_paths:
            try:
                content = self.github_fetcher.read_file(repo_url, file_path)
                file_contents[file_path] = content
                print(f"Successfully fetched content for {file_path} ({len(content)} characters)")
            except Exception as e:
                print(f"Error fetching content for {file_path}: {str(e)}")
                file_contents[file_path] = f"Error: {str(e)}"
        
        return file_contents
    
    def _prepare_security_analysis_prompt(self, repo_url: str, file_contents: Dict[str, str]) -> str:
        """
        Prepare a prompt for the LLM to analyze the selected files for security vulnerabilities.
        
        Args:
            repo_url (str): URL of the GitHub repository
            file_contents (Dict[str, str]): Dictionary mapping file paths to their content
            
        Returns:
            str: The prompt for the LLM
        """
        prompt = f"""
You are a security expert specializing in Solana blockchain programs. Your task is to analyze the following files from a Solana repository for security vulnerabilities and malicious behavior.

Repository URL: {repo_url}

I'll provide you with the content of the selected files. For each file, analyze it for:

1. Security Vulnerabilities:
   - Unauthorized access vulnerabilities
   - Reentrancy vulnerabilities
   - Integer overflow/underflow
   - Improper validation
   - Insecure randomness

2. Malicious Behavior Patterns:
   - Backdoors
   - Rugpull mechanisms
   - Honeypot patterns
   - Fee manipulation
   - Ownership concentration

Provide a detailed analysis with specific line references and explanations of each issue found.
If no issues are found in a particular category, explicitly state that.

Also provide an overall risk score on a scale of 0-10, where:
- 0-2: Very Low Risk
- 3-4: Low Risk
- 5-6: Moderate Risk
- 7-8: High Risk
- 9-10: Critical Risk

Here are the files to analyze:
"""
        
        # Add content of each file to the prompt
        for file_path, content in file_contents.items():
            prompt += f"\n\n--- FILE: {file_path} ---\n{content}\n--- END FILE ---"
        
        return prompt
    
    def _parse_security_analysis_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM's security analysis response into a structured format.
        
        Args:
            response (str): The LLM's response
            
        Returns:
            Dict[str, Any]: Parsed analysis results
        """
        # Initialize the result structure
        security_vulnerabilities = {
            "unauthorized_access": [],
            "reentrancy": [],
            "integer_overflow": [],
            "improper_validation": [],
            "insecure_randomness": []
        }
        
        malicious_behavior = {
            "backdoors": [],
            "rugpull_mechanisms": [],
            "honeypot_patterns": [],
            "fee_manipulation": [],
            "ownership_concentration": []
        }
        
        # Extract overall risk score
        import re
        risk_score = 0
        risk_match = re.search(r'risk score:?\s*(\d+)[/\\]10', response, re.IGNORECASE)
        if not risk_match:
            risk_match = re.search(r'overall risk:?\s*(\d+)[/\\]10', response, re.IGNORECASE)
        if not risk_match:
            risk_match = re.search(r'risk:?\s*(\d+)[/\\]10', response, re.IGNORECASE)
        
        if risk_match:
            risk_score = int(risk_match.group(1))
        
        # Define patterns to match vulnerability and behavior sections
        section_patterns = {
            "unauthorized_access": [
                r'unauthorized access vulnerabilities?.*?(?=##|\n\n\w|$)',
                r'access control vulnerabilities?.*?(?=##|\n\n\w|$)'
            ],
            "reentrancy": [
                r'reentrancy vulnerabilities?.*?(?=##|\n\n\w|$)'
            ],
            "integer_overflow": [
                r'integer overflow/underflow.*?(?=##|\n\n\w|$)',
                r'arithmetic vulnerabilities?.*?(?=##|\n\n\w|$)'
            ],
            "improper_validation": [
                r'improper validation.*?(?=##|\n\n\w|$)',
                r'input validation.*?(?=##|\n\n\w|$)'
            ],
            "insecure_randomness": [
                r'insecure randomness.*?(?=##|\n\n\w|$)',
                r'random number.*?(?=##|\n\n\w|$)'
            ],
            "backdoors": [
                r'backdoors?.*?(?=##|\n\n\w|$)'
            ],
            "rugpull_mechanisms": [
                r'rugpull mechanisms?.*?(?=##|\n\n\w|$)',
                r'rug pull.*?(?=##|\n\n\w|$)'
            ],
            "honeypot_patterns": [
                r'honeypot patterns?.*?(?=##|\n\n\w|$)'
            ],
            "fee_manipulation": [
                r'fee manipulation.*?(?=##|\n\n\w|$)'
            ],
            "ownership_concentration": [
                r'ownership concentration.*?(?=##|\n\n\w|$)',
                r'centralized control.*?(?=##|\n\n\w|$)'
            ]
        }
        
        # Extract findings for each category
        for category, patterns in section_patterns.items():
            for pattern in patterns:
                matches = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if matches:
                    section_text = matches.group(0)
                    
                    # Skip if "No X detected" or "No X found" or "No X vulnerabilities"
                    if re.search(r'no .*(detected|found|vulnerabilities|issues)', section_text, re.IGNORECASE):
                        continue
                    
                    # Extract individual findings
                    findings = self._extract_findings(section_text)
                    
                    # Determine which dictionary to update
                    if category in ["unauthorized_access", "reentrancy", "integer_overflow", "improper_validation", "insecure_randomness"]:
                        security_vulnerabilities[category].extend(findings)
                    else:
                        malicious_behavior[category].extend(findings)
        
        return {
            "security_vulnerabilities": security_vulnerabilities,
            "malicious_behavior": malicious_behavior,
            "overall_risk_score": risk_score,
            "summary": self._extract_summary(response),
            "raw_llm_response": response
        }
    
    def _extract_findings(self, section_text: str) -> List[Dict[str, str]]:
        """
        Extract individual findings from a section of the LLM response.
        
        Args:
            section_text (str): Text of a section from the LLM response
            
        Returns:
            List[Dict[str, str]]: List of findings with details
        """
        findings = []
        
        # Look for bullet points or numbered items
        import re
        
        # Pattern to match file and line information
        file_line_pattern = r'(?:found in|file:?)\s+([a-zA-Z0-9_\-/.]+)(?:,?\s+lines?:?\s+(\d+(?:-\d+)?))?\b'
        
        # Split by bullet points or numbered items
        items = re.split(r'\n\s*[-*]\s+|\n\s*\d+\.\s+', section_text)
        
        for item in items:
            if not item.strip():
                continue
                
            finding = {
                "description": item.strip(),
                "severity": "unknown",
                "file": "unknown",
                "lines": "unknown"
            }
            
            # Extract severity
            severity_match = re.search(r'severity:?\s*(critical|high|medium|low|info)', item, re.IGNORECASE)
            if severity_match:
                finding["severity"] = severity_match.group(1).lower()
            elif "critical" in item.lower():
                finding["severity"] = "critical"
            elif "high" in item.lower():
                finding["severity"] = "high"
            elif "medium" in item.lower() or "moderate" in item.lower():
                finding["severity"] = "medium"
            elif "low" in item.lower():
                finding["severity"] = "low"
            
            # Extract file and line information
            file_line_match = re.search(file_line_pattern, item, re.IGNORECASE)
            if file_line_match:
                finding["file"] = file_line_match.group(1)
                if file_line_match.group(2):
                    finding["lines"] = file_line_match.group(2)
            
            findings.append(finding)
        
        # If no items were found but there's content, add the whole section as one finding
        if not findings and section_text.strip():
            finding = {
                "description": section_text.strip(),
                "severity": "unknown",
                "file": "unknown",
                "lines": "unknown"
            }
            
            # Extract severity, file, and line information from the whole section
            severity_match = re.search(r'severity:?\s*(critical|high|medium|low|info)', section_text, re.IGNORECASE)
            if severity_match:
                finding["severity"] = severity_match.group(1).lower()
            
            file_line_match = re.search(file_line_pattern, section_text, re.IGNORECASE)
            if file_line_match:
                finding["file"] = file_line_match.group(1)
                if file_line_match.group(2):
                    finding["lines"] = file_line_match.group(2)
            
            findings.append(finding)
        
        return findings
    
    def _extract_summary(self, response: str) -> str:
        """
        Extract a summary from the LLM response.
        
        Args:
            response (str): The LLM's response
            
        Returns:
            str: Summary of the analysis
        """
        # Look for a summary section
        import re
        summary_match = re.search(r'summary:?\s*(.*?)(?=##|\n\n\w|$)', response, re.IGNORECASE | re.DOTALL)
        
        if summary_match:
            return summary_match.group(1).strip()
        
        # If no summary section, look for recommendations
        recommendations_match = re.search(r'recommendations:?\s*(.*?)(?=##|\n\n\w|$)', response, re.IGNORECASE | re.DOTALL)
        
        if recommendations_match:
            return "Recommendations: " + recommendations_match.group(1).strip()
        
        # If no summary or recommendations, return a generic summary
        return "Analysis completed. See detailed findings for more information."
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the analysis.
        
        Returns:
            Dict[str, Any]: Analysis statistics
        """
        return {
            "analysis_time": self.analysis_time,
            "llm_api_calls": self.llm_api_calls,
            "github_api_stats": self.github_fetcher.get_api_call_stats()
        }


# Example usage
if __name__ == "__main__":
    # Initialize the analyzer
    analyzer = SolanaSecurityAnalyzer(llm_provider="openai", model_name="gpt-4")
    
    # Example repository URL
    repo_url = "https://github.com/solana-developers/CRUD-dApp"
    
    # Analyze the repository using both approaches
    print("\n=== HYBRID APPROACH ===")
    hybrid_results = analyzer.analyze_repository_hybrid(repo_url)
    print(f"Analysis completed in {analyzer.analysis_time:.2f} seconds")
    print(f"Overall risk score: {hybrid_results['overall_risk_score']}/10")
    
    print("\n=== STRUCTURE-ONLY APPROACH ===")
    structure_results = analyzer.analyze_repository_structure_only(repo_url)
    print(f"Analysis completed in {analyzer.analysis_time:.2f} seconds")
    print(f"Overall risk score: {structure_results['overall_risk_score']}/10")
    
    # Compare the results
    print("\n=== COMPARISON ===")
    print(f"Hybrid approach found {sum(len(vulns) for vulns in hybrid_results['security_vulnerabilities'].values())} security vulnerabilities")
    print(f"Structure-only approach found {sum(len(vulns) for vulns in structure_results['security_vulnerabilities'].values())} security vulnerabilities")
    
    print(f"Hybrid approach found {sum(len(behaviors) for behaviors in hybrid_results['malicious_behavior'].values())} malicious behaviors")
    print(f"Structure-only approach found {sum(len(behaviors) for behaviors in structure_results['malicious_behavior'].values())} malicious behaviors") 