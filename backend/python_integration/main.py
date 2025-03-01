from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from price_tracker import PriceTracker
import os
from dotenv import load_dotenv
from datetime import datetime

class SubgraphInteractor:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Get Graph URL from environment variable
        graph_url = os.getenv('GRAPH_URL', 'https://api.studio.thegraph.com/query/103469/sepolia/v0.0.4')

        # Set up transport with proper headers
        transport = RequestsHTTPTransport(
            url=graph_url,
            headers={
                'Content-Type': 'application/json',
            },
            verify=True,
            retries=3,
        )

        self.client = Client(
            transport=transport,
            fetch_schema_from_transport=True
        )

    def test_connection(self):
        """Test the connection to the subgraph"""
        try:
            # Simple query to test connection
            query = gql("""
            {
                _meta {
                    block {
                        number
                    }
                    deployment
                    hasIndexingErrors
                }
            }
            """)
            result = self.client.execute(query)
            print("Connection test result:", result)
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def fetch_smart_contracts(self):
        """Fetch smart contracts"""
        query = gql("""
        {
            smartContracts(first: 5, orderBy: timestamp, orderDirection: asc) {
                id
                address
                creator
                timestamp
                transactionHash
            }
        }
        """)

        try:
            result = self.client.execute(query)
            print("Raw response:", result)  # Debug print
            return result.get('smartContracts', [])
        except Exception as e:
            print(f"Error fetching smart contracts: {e}")
            return []

def main():
    try:
        interactor = SubgraphInteractor()

        # Test connection first
        print("\nTesting connection to subgraph...")
        if interactor.test_connection():
            print("Connection successful!")
        else:
            print("Failed to connect to subgraph")
            return

        print("\nFetching smart contracts...")
        contracts = interactor.fetch_smart_contracts()

        if contracts:
            for contract in contracts:
                print(f"ID: {contract['id']}")
                print(f"Address: {contract['address']}")
                print(f"Creator: {contract['creator']}")
                # Convert timestamp to readable format
                timestamp = int(contract['timestamp'])
                readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                print(f"Timestamp: {readable_time}")
                print("---")
        else:
            print("No contracts found")

        

    except Exception as e:
        print(f"Main error: {e}")

if __name__ == "__main__":
    main()