import os
import pandas as pd
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json

class SolanaDEXTracker:
    def __init__(self):
        self.jupiter_url = "https://stats.jup.ag/api"
        self.token_pair = "SOL-USDC"  # Default pair
        
    async def get_swap_data(self, time_range='24h'):
        """Fetch Solana DEX swap data from Jupiter."""
        try:
            async with aiohttp.ClientSession() as session:
                # Get swaps data
                url = f"{self.jupiter_url}/swaps"
                params = {
                    'timeRange': time_range,
                    'pair': self.token_pair
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Convert to DataFrame
                        swaps_df = pd.DataFrame(data['swaps'])
                        
                        # Process timestamps
                        swaps_df['timestamp'] = pd.to_datetime(swaps_df['timestamp'])
                        
                        # Calculate additional metrics
                        swaps_df['value_usd'] = swaps_df['inAmount'] * swaps_df['price']
                        swaps_df['price_impact'] = swaps_df['priceImpact'] * 100  # Convert to percentage
                        
                        # Calculate aggregated metrics
                        metrics = {
                            'total_volume_usd': swaps_df['value_usd'].sum(),
                            'avg_price': swaps_df['price'].mean(),
                            'num_swaps': len(swaps_df),
                            'avg_size_usd': swaps_df['value_usd'].mean(),
                            'avg_price_impact': swaps_df['price_impact'].mean(),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        result = {
                            'swaps': swaps_df.to_dict(orient='records'),
                            'metrics': metrics
                        }
                        
                        return result
                    else:
                        print(f"Error fetching swap data: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Error in get_swap_data: {str(e)}")
            return None

    async def get_liquidity_data(self):
        """Fetch liquidity pool data."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.jupiter_url}/liquidity"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Convert to DataFrame
                        pools_df = pd.DataFrame(data['pools'])
                        
                        # Calculate pool metrics
                        pools_df['tvl_usd'] = pools_df['tvl']
                        pools_df['volume_24h_usd'] = pools_df['volume24h']
                        
                        return pools_df.to_dict(orient='records')
                    else:
                        print(f"Error fetching liquidity data: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Error in get_liquidity_data: {str(e)}")
            return None

    async def get_market_summary(self):
        """Get comprehensive market summary."""
        swap_data = await self.get_swap_data()
        liquidity_data = await self.get_liquidity_data()
        
        if swap_data and liquidity_data:
            summary = {
                'swap_metrics': swap_data['metrics'],
                'liquidity_data': {
                    'total_tvl': sum(pool['tvl_usd'] for pool in liquidity_data),
                    'total_volume_24h': sum(pool['volume_24h_usd'] for pool in liquidity_data),
                    'num_pools': len(liquidity_data)
                },
                'timestamp': datetime.now().isoformat()
            }
            return summary
        return None

async def main():
    tracker = SolanaDEXTracker()
    
    # Fetch market data
    market_data = await tracker.get_market_summary()
    
    if market_data:
        # Save to cache file
        cache_dir = "./metrics_cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(cache_dir, f"solana_dex_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(cache_file, 'w') as f:
            json.dump(market_data, f, indent=2, default=str)
            
        print(f"Data saved to {cache_file}")
        return market_data
    else:
        print("Failed to fetch market data")
        return None

if __name__ == "__main__":
    asyncio.run(main())