from github import Github
from urllib.parse import urlparse
from typing import Dict, List, Optional, Union, Any
import os
import json
import time
from datetime import datetime, timedelta
import pytz
from tzlocal import get_localzone
from dotenv import load_dotenv

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
                content_info = {
                    "name": item.name,
                    "path": item.path,
                    "type": "file" if item.type == "file" else "directory",
                    "size": item.size if item.type == "file" else None
                }
                structure.append(content_info)
                
                # Recursively get contents if it's a directory
                if recursive and item.type == "directory":
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
                    if item.type == "file":
                        result[item.name] = item.path
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
            path_parts = item['path'].split('/')
            current_level = deep_map
            
            # For files, store the full path as the value
            if item['type'] == 'file':
                # Handle files in root directory
                if len(path_parts) == 1:
                    current_level[path_parts[0]] = item['path']
                else:
                    # Navigate to the correct directory level
                    for part in path_parts[:-1]:
                        if part not in current_level:
                            current_level[part] = {}
                        current_level = current_level[part]
                    current_level[path_parts[-1]] = item['path']
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

# Example usage:
if __name__ == "__main__":
    # Initialize the fetcher
    fetcher = GitHubFetcher()
    
    # Example repository URL
    # repo_url = "https://github.com/metasal1/helloworld"
    repo_url = "https://github.com/dhilt/hello-world-js"
    
    # Get repository structure
    try:
        # Get the complete repository structure
        print("\nFetching complete repository structure...")
        start_time = time.time()
        complete_structure = fetcher.get_complete_repository_structure(repo_url)
        end_time = time.time()
        
        # Print the structure in a pretty JSON format
        import json
        print("\nRepository structure (complete map):")
        print(json.dumps(complete_structure, indent=2))
        
        # Print API call statistics
        api_stats = fetcher.get_api_call_stats()
        print("\nAPI Call Statistics:")
        print(f"Total API calls made: {api_stats['total_calls']}")
        print(f"Core rate limit: {api_stats['rate_limit']['core']['remaining']}/{api_stats['rate_limit']['core']['limit']}")
        print(f"Core rate limit resets at: {api_stats['rate_limit']['core']['reset_time']}")
        print(f"Time taken: {end_time - start_time:.2f} seconds")
        
        # Run a second time to demonstrate caching
        print("\nFetching again (should use cache)...")
        start_time = time.time()
        complete_structure = fetcher.get_complete_repository_structure(repo_url)
        end_time = time.time()
        print(f"Time taken (cached): {end_time - start_time:.2f} seconds")
        
        # Print updated API call statistics
        api_stats = fetcher.get_api_call_stats()
        print(f"Total API calls made: {api_stats['total_calls']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
