from github import Github
from urllib.parse import urlparse
from typing import Dict, List, Optional, Union, Any, Set, Tuple
import os
import json
import time
from datetime import datetime, timedelta
import pytz
from tzlocal import get_localzone
from dotenv import load_dotenv
import re
import pprint

# Create a pretty printer with custom settings
pp = pprint.PrettyPrinter(indent=2, width=100, compact=False)

# Solana-specific file patterns - improved to better detect Solana code
SOLANA_FILE_PATTERNS = {
    'program': [
        r'\.rs$',                          # Rust files (Solana programs)
        r'Cargo\.toml$',                   # Rust project configuration
        r'Anchor\.toml$',                  # Anchor framework configuration
        r'Xargo\.toml$',                   # Xargo configuration for Solana
        r'/programs/.+/src/.+\.rs$',       # Rust files in program directories
    ],
    'client': [
        r'\.ts$',                          # TypeScript files
        r'\.js$',                          # JavaScript files
        r'package\.json$',                 # Node.js project configuration
        r'tsconfig\.json$',                # TypeScript configuration
    ],
    'config': [
        r'\.env$',                         # Environment variables
        r'solana-config\.yml$',            # Solana configuration
        r'\.solana.*\.json$',              # Solana configuration files
        r'anchor/Anchor\.toml$',           # Anchor configuration
    ],
    'test': [
        r'test.*\.rs$',                    # Rust test files
        r'test.*\.ts$',                    # TypeScript test files
        r'test.*\.js$',                    # JavaScript test files
        r'tests/.+\.ts$',                  # TypeScript tests in tests directory
        r'tests/.+\.js$',                  # JavaScript tests in tests directory
        r'tests/.+\.rs$',                  # Rust tests in tests directory
    ]
}

# Files that might contain sensitive information
SENSITIVE_FILE_PATTERNS = [
    r'\.env$',
    r'.*key.*\.json$',
    r'.*wallet.*\.json$',
    r'.*secret.*',
    r'.*password.*',
]

# Files to ignore in analysis (common non-code files)
IGNORE_FILE_PATTERNS = [
    r'\.git/',
    r'\.github/',
    r'node_modules/',
    r'target/',
    r'dist/',
    r'build/',
    r'\.jpg$',
    r'\.png$',
    r'\.svg$',
    r'\.ico$',
    r'\.pdf$',
    r'\.DS_Store$',
    r'LICENSE$',
    r'\.gitignore$',
]

class GitHubFetcher:
    def __init__(self, github_token: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize the GitHubFetcher with a GitHub token.
        
        Args:
            github_token (Optional[str]): GitHub API token. If None, will try to get from env vars
            cache_dir (Optional[str]): Directory to store cache files. If None, uses './github_cache'
        """
        self.github_token = github_token or self._load_token_from_env()
        self.github = Github(self.github_token)
        
        # Set up API call tracking
        self.api_call_count = 0
        
        # Set up caching
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'github_cache')
        self._setup_cache_dir()
        
        # Initialize repository structure cache
        self.repo_structures_cache_file = os.path.join(self.cache_dir, 'repo_structures_cache.json')
        self.repo_structures_cache = self._load_repo_structures_cache()
        
    def _load_token_from_env(self) -> str:
        """Load GitHub token from environment variables."""
        # Get the directory where this file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Get the parent (backend) directory
        parent_dir = os.path.dirname(current_dir)
        
        # Try to load from both .env and .env.local in the parent directory
        load_dotenv(os.path.join(parent_dir, '.env'))
        load_dotenv(os.path.join(parent_dir, '.env.local'))
        
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError(
                "GitHub token is required. Either:\n"
                "1. Pass it directly to GitHubFetcher(github_token='your-token')\n"
                "2. Set GITHUB_TOKEN in backend/.env or backend/.env.local file\n"
                "3. Set GITHUB_TOKEN as an environment variable\n"
                f"Looking for .env files in: {parent_dir}"
            )
        return token
    
    def _setup_cache_dir(self):
        """Create cache directory if it doesn't exist."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _load_repo_structures_cache(self) -> Dict:
        """Load the repository structures cache file."""
        if not os.path.exists(self.repo_structures_cache_file):
            return {}
            
        try:
            with open(self.repo_structures_cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Error loading repository structures cache: {str(e)}")
            return {}
    
    def _save_repo_structures_cache(self):
        """Save the repository structures cache to file."""
        try:
            with open(self.repo_structures_cache_file, 'w') as f:
                json.dump(self.repo_structures_cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Error saving repository structures cache: {str(e)}")
    
    def _track_api_call(self):
        """Track GitHub API call."""
        self.api_call_count += 1
        
    def _get_cache_path(self, key: str) -> str:
        """Get the path to a cache file for a given key."""
        # Create a safe filename from the key
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return os.path.join(self.cache_dir, f"{safe_key}_cache.json")
    
    def _get_from_cache(self, key: str, max_age_hours: int = 24) -> Optional[Any]:
        """
        Try to get data from cache.
        
        Args:
            key (str): Cache key
            max_age_hours (int): Maximum age of cache in hours
            
        Returns:
            Optional[Any]: Cached data or None if not found/expired
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                
            # Check if cache is expired
            timestamp = cache_data.get('timestamp')
            if not timestamp:
                return None
                
            cache_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - cache_time > timedelta(hours=max_age_hours):
                return None
                
            return cache_data.get('data')
        except Exception as e:
            print(f"Warning: Error reading cache: {str(e)}")
            return None
    
    def _save_to_cache(self, key: str, data: Any):
        """
        Save data to cache.
        
        Args:
            key (str): Cache key
            data (Any): Data to cache
        """
        cache_path = self._get_cache_path(key)
        
        try:
            cache_data = {
                'timestamp': datetime.now().timestamp(),
                'data': data
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Warning: Error writing to cache: {str(e)}")

    def parse_github_url(self, url: str) -> tuple[str, str]:
        """
        Parse a GitHub repository URL to extract owner and repository name.
        
        Args:
            url (str): GitHub repository URL
            
        Returns:
            tuple[str, str]: Repository owner and name
        """
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub repository URL")
            
        return path_parts[0], path_parts[1]

    def get_repository_structure(self, repo_url: str, path: str = "", recursive: bool = True, use_cache: bool = True) -> List[Dict]:
        """
        Get the flat structure of a repository at a specific path.
        
        Args:
            repo_url (str): GitHub repository URL
            path (str): Path within the repository to get contents for
            recursive (bool): Whether to recursively fetch directory contents
            use_cache (bool): Whether to use cached data if available
            
        Returns:
            List[Dict]: List of dictionaries containing file/directory information
        """
        # Try to get from cache first
        cache_key = f"structure_{repo_url}_{path}"
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        owner, repo_name = self.parse_github_url(repo_url)
        repo = self.github.get_repo(f"{owner}/{repo_name}")
        
        try:
            self._track_api_call()
            contents = repo.get_contents(path)
            structure = []
            
            if not isinstance(contents, list):
                contents = [contents]
                
            for item in contents:
                file_category = self._categorize_file(item.path) if item.type == "file" else None
                content_info = {
                    "name": item.name,
                    "path": item.path,
                    "type": "file" if item.type == "file" else "directory",
                    "size": item.size if item.type == "file" else None,
                    "file_category": file_category,
                    "is_sensitive": self._is_sensitive_file(item.path) if item.type == "file" else False,
                    "should_ignore": self._should_ignore_file(item.path)
                }
                
                # Debug output for program files
                if file_category == "program":
                    print(f"Debug: Found program file: {item.path}")
                
                # Skip ignored files/directories if they should be ignored
                if content_info["should_ignore"]:
                    continue
                    
                structure.append(content_info)
                
                # Recursively get contents if it's a directory
                if recursive and item.type == "directory" and not content_info["should_ignore"]:
                    try:
                        sub_contents = self.get_repository_structure(repo_url, item.path, recursive, use_cache)
                        structure.extend(sub_contents)
                    except Exception as e:
                        print(f"Warning: Could not fetch contents of directory {item.path}: {str(e)}")
            
            # Save to cache
            if use_cache:
                self._save_to_cache(cache_key, structure)
                
            return structure
            
        except Exception as e:
            raise Exception(f"Error fetching repository structure: {str(e)}")

    def get_complete_repository_structure(self, repo_url: str, use_cache: bool = True, max_age_hours: int = 24) -> Dict:
        """
        Get a complete hierarchical map of the repository structure.
        This method explicitly traverses each directory to ensure all contents are fetched.
        
        Args:
            repo_url (str): GitHub repository URL
            use_cache (bool): Whether to use cached data if available
            max_age_hours (int): Maximum age of cache in hours
            
        Returns:
            Dict: Nested dictionary representing the repository structure
        """
        # Try to get from cache first
        cache_key = f"complete_structure_{repo_url}"
        if use_cache and cache_key in self.repo_structures_cache:
            cache_entry = self.repo_structures_cache[cache_key]
            cache_time = datetime.fromtimestamp(cache_entry.get('timestamp', 0))
            
            # Check if cache is still valid
            if datetime.now() - cache_time <= timedelta(hours=max_age_hours):
                print(f"Using cached repository structure for {repo_url}")
                return cache_entry.get('data', {})
        
        owner, repo_name = self.parse_github_url(repo_url)
        repo = self.github.get_repo(f"{owner}/{repo_name}")
        
        def traverse_directory(path=""):
            result = {}
            try:
                self._track_api_call()
                contents = repo.get_contents(path)
                
                if not isinstance(contents, list):
                    contents = [contents]
                
                for item in contents:
                    # Skip ignored files/directories
                    if self._should_ignore_file(item.path):
                        continue
                        
                    if item.type == "file":
                        # Create a file entry with minimal metadata
                        result[item.name] = {
                            "path": item.path,
                            "type": "file",
                            "category": self._categorize_file(item.path),
                            "is_sensitive": self._is_sensitive_file(item.path)
                        }
                    else:  # directory
                        result[item.name] = traverse_directory(item.path)
            except Exception as e:
                print(f"Warning: Error traversing {path}: {str(e)}")
            
            return result
        
        structure = traverse_directory()
        
        # Save to cache
        if use_cache:
            self.repo_structures_cache[cache_key] = {
                'timestamp': datetime.now().timestamp(),
                'data': structure
            }
            self._save_repo_structures_cache()
            
        return structure

    def create_deep_map(self, repo_url: str, use_cache: bool = True) -> Dict:
        """
        Create a hierarchical map of the repository structure where directories are
        nested objects and files are represented by their paths.
        
        Args:
            repo_url (str): GitHub repository URL
            use_cache (bool): Whether to use cached data if available
            
        Returns:
            Dict: Nested dictionary representing the repository structure
        """
        # Try to get from cache first
        cache_key = f"deep_map_{repo_url}"
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        flat_structure = self.get_repository_structure(repo_url, use_cache=use_cache)
        deep_map = {}
        
        for item in flat_structure:
            # Skip ignored files
            if item.get("should_ignore", False):
                continue
                
            path_parts = item['path'].split('/')
            current_level = deep_map
            
            # For files, store the full path as the value
            if item['type'] == 'file':
                # Handle files in root directory
                if len(path_parts) == 1:
                    current_level[path_parts[0]] = {
                        "path": item['path'],
                        "category": item.get('file_category'),
                        "is_sensitive": item.get('is_sensitive', False)
                    }
                else:
                    # Navigate to the correct directory level
                    for part in path_parts[:-1]:
                        if part not in current_level:
                            current_level[part] = {}
                        current_level = current_level[part]
                    current_level[path_parts[-1]] = {
                        "path": item['path'],
                        "category": item.get('file_category'),
                        "is_sensitive": item.get('is_sensitive', False)
                    }
            else:  # For directories, create nested dictionaries
                for part in path_parts:
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]
        
        # Save to cache
        if use_cache:
            self._save_to_cache(cache_key, deep_map)
            
        return deep_map

    def read_file(self, repo_url: str, file_path: str, use_cache: bool = True) -> str:
        """
        Read the contents of a specific file from the repository.
        
        Args:
            repo_url (str): GitHub repository URL
            file_path (str): Path to the file within the repository
            use_cache (bool): Whether to use cached data if available
            
        Returns:
            str: Contents of the file
        """
        # Try to get from cache first
        cache_key = f"file_{repo_url}_{file_path}"
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        owner, repo_name = self.parse_github_url(repo_url)
        repo = self.github.get_repo(f"{owner}/{repo_name}")
        
        try:
            self._track_api_call()
            file_content = repo.get_contents(file_path)
            if isinstance(file_content, list):
                raise ValueError("Provided path is a directory, not a file")
                
            content = file_content.decoded_content.decode('utf-8')
            
            # Save to cache
            if use_cache:
                self._save_to_cache(cache_key, content)
                
            return content
            
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")

    def get_api_call_stats(self) -> Dict:
        """
        Get statistics about API calls made.
        
        Returns:
            Dict: API call statistics
        """
        return {
            "total_calls": self.api_call_count,
            "rate_limit": self._get_rate_limit_info()
        }
    
    def _get_rate_limit_info(self) -> Dict:
        """
        Get information about the current rate limit status.
        
        Returns:
            Dict: Rate limit information with reset times in local timezone
        """
        self._track_api_call()
        rate_limit = self.github.get_rate_limit()
        
        # Convert UTC times to local timezone
        local_tz = get_localzone()
        
        def format_reset_time(reset_time):
            # GitHub API returns time in UTC
            utc_time = reset_time.replace(tzinfo=pytz.UTC)
            # Convert to local time
            local_time = utc_time.astimezone(local_tz)
            return local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        return {
            "core": {
                "limit": rate_limit.core.limit,
                "remaining": rate_limit.core.remaining,
                "reset_time": format_reset_time(rate_limit.core.reset)
            },
            "search": {
                "limit": rate_limit.search.limit,
                "remaining": rate_limit.search.remaining,
                "reset_time": format_reset_time(rate_limit.search.reset)
            }
        }

    def clear_cache(self, clear_structures: bool = True, clear_files: bool = True):
        """
        Clear cached data.
        
        Args:
            clear_structures (bool): Whether to clear the repository structures cache
            clear_files (bool): Whether to clear individual file caches
        """
        if clear_structures:
            if os.path.exists(self.repo_structures_cache_file):
                os.remove(self.repo_structures_cache_file)
            self.repo_structures_cache = {}
            
        if clear_files:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('_cache.json') and filename != 'repo_structures_cache.json':
                    os.remove(os.path.join(self.cache_dir, filename))
    
    def _categorize_file(self, file_path: str) -> Optional[str]:
        """
        Categorize a file based on its path and extension.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            Optional[str]: Category of the file or None if not categorized
        """
        for category, patterns in SOLANA_FILE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, file_path, re.IGNORECASE):
                    # Debug output for program files
                    if category == "program":
                        print(f"Debug: Categorized {file_path} as program file (matched pattern: {pattern})")
                    return category
        return None
    
    def _is_sensitive_file(self, file_path: str) -> bool:
        """
        Check if a file might contain sensitive information.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            bool: True if the file might contain sensitive information
        """
        for pattern in SENSITIVE_FILE_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True
        return False
    
    def _should_ignore_file(self, file_path: str) -> bool:
        """
        Check if a file should be ignored in analysis.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            bool: True if the file should be ignored
        """
        for pattern in IGNORE_FILE_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True
        return False
    
    def get_solana_files(self, repo_url: str, use_cache: bool = True) -> Dict[str, List[Dict]]:
        """
        Get all Solana-related files from a repository, categorized by type.
        
        Args:
            repo_url (str): GitHub repository URL
            use_cache (bool): Whether to use cached data if available
            
        Returns:
            Dict[str, List[Dict]]: Dictionary of categorized Solana files
        """
        # Try to get from cache first
        cache_key = f"solana_files_{repo_url}"
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Initialize categories
        categorized_files = {
            'program': [],
            'client': [],
            'config': [],
            'test': [],
            'other': []
        }
        
        # Get the complete repository structure
        complete_structure = self.get_complete_repository_structure(repo_url, use_cache=use_cache)
        
        # Helper function to recursively extract files from the complete structure
        def extract_files(structure, path_prefix=""):
            for name, info in structure.items():
                if isinstance(info, dict) and "type" in info and info["type"] == "file":
                    # This is a file entry
                    file_info = {
                        "name": name,
                        "path": info["path"],
                        "type": "file",
                        "file_category": info.get("category"),
                        "is_sensitive": info.get("is_sensitive", False)
                    }
                    
                    # Add to appropriate category
                    category = info.get("category")
                    if category and category in categorized_files:
                        categorized_files[category].append(file_info)
                    else:
                        categorized_files['other'].append(file_info)
                elif isinstance(info, dict) and "type" not in info:
                    # This is a directory entry
                    extract_files(info, path_prefix + name + "/")
        
        # Extract files from the complete structure
        extract_files(complete_structure)
        
        # Debug output
        print(f"\nDebug: Found {len(categorized_files['program'])} program files")
        if categorized_files['program']:
            print("First few program files:")
            for file in categorized_files['program'][:5]:
                print(f"- {file['path']} (category: {file['file_category']})")
        
        # Save to cache
        if use_cache:
            self._save_to_cache(cache_key, categorized_files)
            
        return categorized_files
    
    def analyze_repository_structure(self, repo_url: str, use_cache: bool = True) -> Dict:
        """
        Analyze the repository structure to provide insights about the codebase.
        
        Args:
            repo_url (str): GitHub repository URL
            use_cache (bool): Whether to use cached data if available
            
        Returns:
            Dict: Analysis results
        """
        # Try to get from cache first
        cache_key = f"analysis_{repo_url}"
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Get categorized files
        categorized_files = self.get_solana_files(repo_url, use_cache=use_cache)
        
        # Debug output
        print("\nDebug: Categories in analyze_repository_structure:")
        for category, files in categorized_files.items():
            print(f"- {category}: {len(files)} files")
        
        # Analyze repository
        analysis = {
            'file_counts': {
                'program': len(categorized_files['program']),
                'client': len(categorized_files['client']),
                'config': len(categorized_files['config']),
                'test': len(categorized_files['test']),
                'other': len(categorized_files['other']),
                'total': sum(len(files) for files in categorized_files.values())
            },
            'sensitive_files': [
                item['path'] for category in categorized_files.values() 
                for item in category if item.get('is_sensitive', False)
            ],
            'program_files': [item['path'] for item in categorized_files['program']],
            'has_solana_program': len(categorized_files['program']) > 0,
            'has_tests': len(categorized_files['test']) > 0
        }
        
        # Save to cache
        if use_cache:
            self._save_to_cache(cache_key, analysis)
            
        return analysis
    
    def get_files_for_llm_analysis(self, repo_url: str, use_cache: bool = True) -> Dict[str, List[Dict]]:
        """
        Get a categorized list of files that are relevant for LLM analysis, with minimal metadata.
        This is optimized for passing to an LLM for file selection.
        
        Args:
            repo_url (str): GitHub repository URL
            use_cache (bool): Whether to use cached data if available
            
        Returns:
            Dict[str, List[Dict]]: Dictionary of categorized files with minimal metadata
        """
        # Get the categorized files
        categorized_files = self.get_solana_files(repo_url, use_cache=use_cache)
        
        # Create a simplified version with minimal metadata
        simplified_files = {}
        
        for category, files in categorized_files.items():
            simplified_files[category] = [
                {
                    "path": file['path'],
                    "category": file.get('file_category', category),
                    "is_sensitive": file.get('is_sensitive', False)
                }
                for file in files
            ]
        
        # Add summary information
        simplified_files['summary'] = {
            "total_files": sum(len(files) for files in categorized_files.values()),
            "program_files": len(categorized_files['program']),
            "client_files": len(categorized_files['client']),
            "config_files": len(categorized_files['config']),
            "test_files": len(categorized_files['test']),
            "other_files": len(categorized_files['other']),
            "has_solana_program": len(categorized_files['program']) > 0
        }
        
        return simplified_files
    
    def get_file_structure_for_llm(self, repo_url: str, use_cache: bool = True) -> Dict:
        """
        Get a simplified file structure for LLM analysis without pre-categorization.
        This approach provides just the file paths and structure, letting the LLM decide which files to analyze.
        
        Args:
            repo_url (str): GitHub repository URL
            use_cache (bool): Whether to use cached data if available
            
        Returns:
            Dict: Repository structure with file paths and minimal metadata
        """
        # Get the complete repository structure
        complete_structure = self.get_complete_repository_structure(repo_url, use_cache=use_cache)
        
        # Create a flattened list of all file paths for easier processing by the LLM
        all_files = []
        
        def extract_file_paths(structure, current_path=""):
            for name, info in structure.items():
                if isinstance(info, dict) and "type" in info and info["type"] == "file":
                    # This is a file entry
                    all_files.append({
                        "path": info["path"],
                        "is_sensitive": info.get("is_sensitive", False)
                    })
                elif isinstance(info, dict) and "type" not in info:
                    # This is a directory entry
                    extract_file_paths(info, current_path + "/" + name if current_path else name)
        
        extract_file_paths(complete_structure)
        
        # Return both the hierarchical structure and the flattened file list
        return {
            "structure": complete_structure,
            "files": all_files,
            "summary": {
                "total_files": len(all_files),
                "repository_url": repo_url
            }
        }

# Example usage:
if __name__ == "__main__":
    # Initialize the fetcher
    fetcher = GitHubFetcher()
    
    # Example repository URL
    # repo_url = "https://github.com/metasal1/helloworld"
    # repo_url = "https://github.com/dhilt/hello-world-js"
    repo_url = "https://github.com/solana-developers/CRUD-dApp"
    
    # Get repository structure
    try:
        print("\n" + "="*80)
        print("INITIALIZING GITHUB FETCHER")
        print("="*80)
        
        # Clear cache to test the updated patterns
        print("\nClearing cache to test updated patterns...")
        fetcher.clear_cache()
        
        print("\n" + "="*80)
        print("REPOSITORY STRUCTURE")
        print("="*80)
        
        # Get the complete repository structure
        print("\nFetching complete repository structure...")
        start_time = time.time()
        complete_structure = fetcher.get_complete_repository_structure(repo_url)
        end_time = time.time()
        
        # Print the structure in a pretty format
        print("\nRepository structure (complete map):")
        pp.pprint(complete_structure)
        
        print("\n" + "="*80)
        print("SOLANA FILES ANALYSIS")
        print("="*80)
        
        # Get Solana files
        print("\nFetching Solana files...")
        solana_files = fetcher.get_solana_files(repo_url)
        print("\nSolana program files:")
        for file in solana_files['program']:
            print(f"- {file['path']}")
        
        print("\n" + "="*80)
        print("REPOSITORY ANALYSIS")
        print("="*80)
        
        # Analyze repository
        print("\nAnalyzing repository...")
        analysis = fetcher.analyze_repository_structure(repo_url)
        print("\nRepository analysis:")
        pp.pprint(analysis)
        
        print("\n" + "="*80)
        print("LLM ANALYSIS FILES (HYBRID APPROACH)")
        print("="*80)
        
        # Get files for LLM analysis (hybrid approach)
        print("\nGetting files for LLM analysis (hybrid approach)...")
        llm_files = fetcher.get_files_for_llm_analysis(repo_url)
        print(f"\nFound {len(llm_files['program'])} program files")
        pp.pprint(llm_files['program'])
        
        # Print summary information
        print("\nSummary of files for LLM analysis (hybrid approach):")
        pp.pprint(llm_files['summary'])
        
        print("\n" + "="*80)
        print("LLM ANALYSIS FILES (STRUCTURE-ONLY APPROACH)")
        print("="*80)
        
        # Get file structure for LLM analysis (structure-only approach)
        print("\nGetting file structure for LLM analysis (structure-only approach)...")
        structure_only = fetcher.get_file_structure_for_llm(repo_url)
        
        # Print summary information
        print("\nSummary of file structure for LLM (structure-only approach):")
        pp.pprint(structure_only['summary'])
        print(f"\nTotal files: {len(structure_only['files'])}")
        
        print("\n" + "="*80)
        print("API STATISTICS")
        print("="*80)
        
        # Print API call statistics
        api_stats = fetcher.get_api_call_stats()
        print("\nAPI Call Statistics:")
        print(f"Total API calls made: {api_stats['total_calls']}")
        print(f"Core rate limit: {api_stats['rate_limit']['core']['remaining']}/{api_stats['rate_limit']['core']['limit']}")
        print(f"Core rate limit resets at: {api_stats['rate_limit']['core']['reset_time']}")
        print(f"Time taken: {end_time - start_time:.2f} seconds")
        
        print("\n" + "="*80)
            
    except Exception as e:
        print(f"Error: {str(e)}")
