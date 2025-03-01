from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import sys

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), './.env.local')
load_dotenv(env_path)


class SOLUSDTTracker:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('GRAPH_API_KEY')
        if not api_key:
            raise ValueError("GRAPH_API_KEY not found in environment variables")

        # Using Uniswap v3 subgraph for SOL/USDT pair
        self.transport = AIOHTTPTransport(
            url=f'https://gateway.thegraph.com/api/{api_key}/subgraphs/id/ELUcwgpm14LKPLrBRuVvPvNKHQ9HvwmtKgKSH6123cr7',
            headers={'Content-Type': 'application/json'}
        )
        self.client = Client(
            transport=self.transport,
            fetch_schema_from_transport=True
        )

    async def get_sol_usdt_swaps(self, limit=50):
        """Get recent SOL/USDT swap data and return as DataFrame"""
        query = gql("""
        {
            swaps(
                first: $limit,
                orderBy: timestamp,
                orderDirection: desc,
                where: {
                    token0: "So11111111111111111111111111111111111111112",  # SOL
                    token1: "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"   # USDT
                }
                subgraphError: deny
            ) {
                timestamp
                amount0
                amount1
                amountUSD
                pool {
                    token0Price
                    token1Price
                }
            }
        }
        """.replace("$limit", str(limit)))

        try:
            result = await self.client.execute_async(query)
            if result and 'swaps' in result:
                # Create list of dictionaries for DataFrame
                swaps_data = [{
                    'timestamp': datetime.fromtimestamp(int(swap['timestamp'])),
                    'sol_amount': abs(float(swap['amount0'])),
                    'usdt_amount': abs(float(swap['amount1'])),
                    'usd_value': float(swap['amountUSD']),
                    'price': float(swap['pool']['token1Price'])
                } for swap in result['swaps']]
                
                # Convert to DataFrame
                df = pd.DataFrame(swaps_data)
                # Set timestamp as index
                df.set_index('timestamp', inplace=True)
                return df
            return pd.DataFrame()  # Return empty DataFrame if no data
        except Exception as e:
            print(f"Error fetching SOL/USDT swaps: {e}")
            return pd.DataFrame()

async def main():
    tracker = SOLUSDTTracker()
    
    print("\nFetching recent SOL/USDT swaps...")
    df = await tracker.get_sol_usdt_swaps()
    
    if not df.empty:
        print("\nRecent SOL/USDT Transactions:")
        print(df)
        
        # Add some basic statistics
        print("\nSummary Statistics:")
        print(df.describe())
        
        # Calculate some additional metrics
        print("\nTrading Metrics:")
        print(f"Average Price: ${df['price'].mean():.2f}")
        print(f"Total SOL Volume: {df['sol_amount'].sum():.4f}")
        print(f"Total USDT Volume: ${df['usdt_amount'].sum():.2f}")
    else:
        print("No recent SOL/USDT swaps found")

if __name__ == "__main__":
    asyncio.run(main())
