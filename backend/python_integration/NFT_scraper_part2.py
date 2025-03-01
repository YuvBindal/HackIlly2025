from googlesearch import search
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
#general comment
class NFTTrendScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }

    def search_google(self, query: str, num_results: int = 5) -> List[str]:
        """Search Google for NFT trends"""
        try:
            print(f"Searching for: {query}")
            urls = list(search(query, num_results=num_results))
            return urls
        except Exception as e:
            print(f"Error searching Google: {e}")
            return []

    def get_content(self, url: str) -> str:
        """Get main content from URL if response is successful"""
        try:
            print(f"Fetching content from: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            
            # Only process successful responses (not 404 or 403)
            if response.status_code not in [404, 403]:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Get text content
                text = soup.get_text()
                
                # Clean up text: remove extra whitespace and empty lines
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text if text else None
            return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_trend_content(self) -> List[str]:
        """Get content from NFT trend searches"""
        queries = [
            "latest NFT trends 2024",
            "NFT market trends analysis",
            "popular NFT projects current",
            "NFT trading trends",
            "NFT technology developments"
        ]
        
        all_content = []
        
        for query in queries:
            # Get URLs from Google
            urls = self.search_google(query)
            
            # Get content from each URL
            for url in urls:
                content = self.get_content(url)
                if content:  # Only add non-None content
                    all_content.append({
                        'query': query,
                        'url': url,
                        'content': content[:1000]  # Limit content length for manageability
                    })
                    print(f"Found content from: {url}")
        
        return all_content

def main():
    scraper = NFTTrendScraper()
    contents = scraper.get_trend_content()
    
    print("\nCollected Content:")
    for i, item in enumerate(contents, 1):
        print(f"\n{i}. Query: {item['query']}")
        print(f"URL: {item['url']}")
        print(f"Preview: {item['content'][:200]}...")  # Show first 200 chars
    
    print(f"\nTotal successful content pieces collected: {len(contents)}")

if __name__ == "__main__":
    main()