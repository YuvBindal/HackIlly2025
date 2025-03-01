import os
import pandas as pd
from datetime import datetime
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from backend.python_integration.eth_price_tracker import ETHUSDTTracker

import asyncio
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), './.env.local')
load_dotenv(env_path)

class MarketAnalyzer:
    def analyze_momentum(self, df):
        # Calculate key metrics
        volume_eth = df['ETH Amount'].sum()
        num_trades = len(df)
        price_volatility = df['Price'].std()
        time_range = (pd.to_datetime(df['Time (UTC)'].max()) -
                     pd.to_datetime(df['Time (UTC)'].min())).total_seconds() / 60

        # Calculate average trade size
        avg_trade_size = volume_eth / num_trades

        # Calculate trade frequency per minute
        trades_per_minute = num_trades / time_range

        return {
            'volume_eth': volume_eth,
            'num_trades': num_trades,
            'price_volatility': price_volatility,
            'avg_trade_size': avg_trade_size,
            'trades_per_minute': trades_per_minute
        }

def initialize_agent():
    """Initialize the market analysis agent."""
    llm = ChatOpenAI(model="gpt-4")

    market_analyzer = MarketAnalyzer()

    tools = [
        Tool(
            name="analyze_market_momentum",
            func=market_analyzer.analyze_momentum,
            description="Analyzes market momentum using trading data and returns metrics"
        )
    ]

    memory = MemorySaver()
    config = {"configurable": {"thread_id": "Market Analysis Agent"}}

    return create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        state_modifier=(
            "You are a market analysis agent specialized in evaluating cryptocurrency "
            "trading data. Your task is to analyze trading patterns and rate market "
            "momentum on a scale of 0-100, where 0 is extremely stable and 100 is "
            "highly volatile. Consider factors like trading volume, price volatility, "
            "trade frequency, and average trade size in your analysis.\n\n"
            "Always format your response as a JSON object with exactly this structure:\n"
            "{\n"
            '    "description_momentum": "Detailed analysis of market momentum including:\n'
            '        - Volume analysis\n'
            '        - Price volatility patterns\n'
            '        - Trading frequency observations\n'
            '        - Notable market behavior\n'
            '        - Supporting metrics and calculations",\n'
            '    "total_market_momentum": "0-100 numerical rating"\n'
            "}\n\n"
            "Example output:\n"
            "{\n"
            '    "description_momentum": "The market shows moderate volatility with increasing volume. '
            'Trading frequency has increased 25% in the last hour, with average trade size of 2.3 ETH. '
            'Price swings of ±2.5% observed in short intervals. Volume is up 15% compared to 24h average.",\n'
            '    "total_market_momentum": "65"\n'
            "}\n\n"
            "Ensure your response is always in this exact JSON format with these two fields."
        ),
    ), config

def process_trading_data(data_text):
    """Convert text data to DataFrame."""
    # Split the text into lines and parse
    lines = [line.strip() for line in data_text.split('\n') if '|' in line]

    # Parse header
    headers = [h.strip() for h in lines[0].split('|')]

    # Parse data rows
    data = []
    for line in lines[1:]:
        if line.startswith('-'): continue
        values = [v.strip() for v in line.split('|')]
        data.append(values)

    df = pd.DataFrame(data, columns=headers)

    # Clean up numeric columns
    df['ETH Amount'] = df['ETH Amount'].str.replace(' ETH', '').astype(float)
    df['USDT Amount'] = df['USDT Amount'].str.replace(' USDT', '').astype(float)
    df['Price'] = df['Price'].str.replace('$', '').astype(float)

    return df

async def main():
    agent_executor, config = initialize_agent()
    price_tracker = ETHUSDTTracker()

    # Get trading data as DataFrame
    df = await price_tracker.get_eth_usdt_swaps()
    print(df)
    # Convert DataFrame to a string representation
    trading_data_str = df.to_string()
    
    prompt = (
        f"Here is the recent ETH/USDT trading data:\n\n{trading_data_str}\n\n"
        "Please analyze this trading data and rate the market momentum on a "
        "scale of 0-100. Provide a detailed explanation of your rating based "
        "on the metrics provided."
    )

    for chunk in agent_executor.stream(
        {"messages": [HumanMessage(content=prompt)]},  # Remove df from input
        config
    ):
        if "agent" in chunk:
            print(chunk["agent"]["messages"][0].content)
        elif "tools" in chunk:
            print(chunk["tools"]["messages"][0].content)

if __name__ == "__main__":
    asyncio.run(main())