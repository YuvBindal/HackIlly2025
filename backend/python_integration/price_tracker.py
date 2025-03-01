from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

class PriceTracker:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('GRAPH_API_KEY')
        if not api_key:
            raise ValueError("GRAPH_API_KEY not found in environment variables")

        self.transport = AIOHTTPTransport(
            url=f'https://gateway.thegraph.com/api/{api_key}/subgraphs/id/HUZDsRpEVP2AvzDCyzDHtdc64dyDxx8FQjzsmqSg4H3B',
            headers={'Content-Type': 'application/json'}
        )
        self.client = Client(
            transport=self.transport,
            fetch_schema_from_transport=True
        )

    async def get_market_overview(self):
        """Get overview of market data including ETH price and factory stats"""
        query = gql("""
        {
            factories(first: 5) {
                id
                poolCount
                txCount
                totalVolumeUSD
            }
            bundles(first: 1) {
                id
                ethPriceUSD
            }
        }
        """)

        try:
            result = await self.client.execute_async(query)
            return result
        except Exception as e:
            print(f"Error fetching market overview: {e}")
            return None

    async def get_token_data(self, token_address):
        """Get detailed data for a specific token"""
        query = gql("""
        {
            tokens(
                first: 5,
                orderBy: totalValueLockedUSD,
                orderDirection: desc,
                subgraphError: deny
            ) {
                id
                symbol
                name
                decimals
                volume
                volumeUSD
                totalValueLockedUSD
                txCount
                poolCount
            }
        }
        """)
        
        try:
            result = await self.client.execute_async(query)
            return result
        except Exception as e:
            print(f"Error fetching token data: {e}")
            return None

    async def get_pool_data(self, first=5):
        """Get data for top pools"""
        query = gql("""
        {
            pools(
                first: 5,
                orderBy: totalValueLockedUSD,
                orderDirection: desc,
                subgraphError: deny
            ) {
                id
                token0 {
                    id
                    symbol
                    name
                }
                token1 {
                    id
                    symbol
                    name
                }
                feeTier
                liquidity
                sqrtPrice
                token0Price
                token1Price
                volumeUSD
                totalValueLockedUSD
            }
        }
        """)
        
        try:
            result = await self.client.execute_async(query)
            return result
        except Exception as e:
            print(f"Error fetching pool data: {e}")
            return None

    async def get_recent_eth_swaps(self, limit=50):
        """Get recent ETH swaps/transactions"""
        query = gql("""
        {
            swaps(
                first: 50,
                orderBy: timestamp,
                orderDirection: desc,
                where: {
                    token0: "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"  # WETH address
                }
                subgraphError: deny
            ) {
                timestamp
                amount0
                amount1
                amountUSD
                token0 {
                    symbol
                }
                token1 {
                    symbol
                }
                pool {
                    token0Price
                    token1Price
                }
            }
        }
        """)

        try:
            result = await self.client.execute_async(query)
            if result and 'swaps' in result:
                formatted_swaps = []
                for swap in result['swaps']:
                    formatted_swaps.append({
                        'timestamp': datetime.fromtimestamp(int(swap['timestamp'])),
                        'eth_amount': abs(float(swap['amount0'])),  # Convert to positive number
                        'usd_value': float(swap['amountUSD']),
                        'pair': f"{swap['token0']['symbol']}/{swap['token1']['symbol']}",
                        'price': float(swap['pool']['token1Price']) if float(swap['amount0']) > 0 else float(swap['pool']['token0Price'])
                    })
                return formatted_swaps
            return []
        except Exception as e:
            print(f"Error fetching ETH swaps: {e}")
            return []

async def main():
    tracker = PriceTracker()
    
    # Get market overview
    print("\nFetching market overview...")
    overview = await tracker.get_market_overview()
    if overview:
        print("\nMarket Overview:")
        if 'bundles' in overview and overview['bundles']:
            eth_price = float(overview['bundles'][0]['ethPriceUSD'])
            print(f"ETH Price: ${eth_price:,.2f}")
        
        if 'factories' in overview and overview['factories']:
            factory = overview['factories'][0]
            print(f"Total Pools: {factory['poolCount']}")
            print(f"Total Transactions: {factory['txCount']}")
            print(f"Total Volume: ${float(factory['totalVolumeUSD']):,.2f}")

    # Get top pools
    print("\nFetching top pools...")
    pools = await tracker.get_pool_data(5)
    if pools and 'pools' in pools:
        print("\nTop Pools:")
        for pool in pools['pools']:
            print(f"\nPool: {pool['token0']['symbol']}/{pool['token1']['symbol']}")
            print(f"TVL: ${float(pool['totalValueLockedUSD']):,.2f}")
            print(f"Volume: ${float(pool['volumeUSD']):,.2f}")

    # Get recent ETH transactions
    print("\nFetching recent ETH swaps...")
    swaps = await tracker.get_recent_eth_swaps()
    
    if swaps:
        print("\nRecent ETH Transactions:")
        print("Time (UTC) | ETH Amount | USD Value | Price | Trading Pair")
        print("-" * 80)
        for swap in swaps:
            print(f"{swap['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} | "
                  f"{swap['eth_amount']:.4f} ETH | "
                  f"${swap['usd_value']:,.2f} | "
                  f"${swap['price']:,.2f} | "
                  f"{swap['pair']}")
    else:
        print("No recent ETH swaps found")

if __name__ == "__main__":
    asyncio.run(main())