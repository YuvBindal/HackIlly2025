import os
import sys
from typing import List, Dict
import json
from datetime import datetime
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), './.env.local')
load_dotenv(env_path)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from backend.python_integration.NFT_scraper_part2 import NFTTrendScraper

class NFTMarketAnalyzer:
    def __init__(self):
        load_dotenv()

    def analyze_sentiment(self, market_signals: List[str]) -> Dict:
        """
        Analyzes NFT market signals and returns sentiment analysis

        Args:
            market_signals: List of strings containing market signals/news

        Returns:
            Dict containing market trends description and sentiment score
        """
        # Process market signals
        total_signals = len(market_signals)
        if total_signals == 0:
            return {
                "market_trends": "Insufficient market data",
                "nft_sentiment": 0
            }

        # This is a placeholder for more sophisticated analysis
        # In production, you might want to use NLP models or more complex analysis
        positive_signals = sum(1 for signal in market_signals
                             if any(word in signal.lower()
                                   for word in ['bull', 'rise', 'grow', 'surge', 'high', 'positive']))
        negative_signals = sum(1 for signal in market_signals
                             if any(word in signal.lower()
                                   for word in ['bear', 'fall', 'drop', 'crash', 'low', 'negative']))

        # Calculate sentiment score (-100 to 100)
        if total_signals > 0:
            sentiment_score = ((positive_signals - negative_signals) / total_signals) * 100
        else:
            sentiment_score = 0

        return {
            "market_trends": f"Analyzed {total_signals} market signals: {positive_signals} positive, {negative_signals} negative",
            "nft_sentiment": int(sentiment_score)
        }

def initialize_agent():
    """Initialize the NFT market trend analysis agent."""
    llm = ChatOpenAI(model="gpt-4")

    market_analyzer = NFTMarketAnalyzer()

    tools = [
        Tool(
            name="analyze_nft_market_sentiment",
            func=market_analyzer.analyze_sentiment,
            description="Analyzes NFT market signals and returns market trends and sentiment score"
        )
    ]

    memory = MemorySaver()
    config = {"configurable": {"thread_id": "NFT Market Trend Agent"}}

    return create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        state_modifier=(
            "You are an NFT market analysis agent specialized in evaluating market sentiment. "
            "Analyze market signals and provide a brief summary with a sentiment score.\n\n"
            "Always format your response as a JSON object with exactly this structure:\n"
            "{\n"
            '    "reasoning": "One concise paragraph summarizing current market conditions and key factors",\n'
            '    "sentiment_score": integer between -100 and 100\n'
            "}\n\n"
            "Example format:\n"
            "{\n"
            '    "reasoning": "NFT market showing strong momentum with increased trading volume and rising floor prices across major collections. Social sentiment is positive with growing interest in new launches.",\n'
            '    "sentiment_score": 75\n'
            "}\n\n"
            "Keep your reasoning brief and focused on key market indicators. The sentiment score should reflect the overall market direction where:\n"
            "-100 = Extremely Bearish\n"
            "  0  = Neutral\n"
            " 100 = Extremely Bullish\n\n"
            "Base your analysis only on the provided market signals."
        ),
    ), config

def analyze_nft_market():
    """
    Analyzes NFT market signals and returns both sentiment and market trends
    
    Returns:
        Dict containing market trends and sentiment analysis
    """
   
    # Get market signals from scraper
    scraper = NFTTrendScraper()
    market_signals = scraper.get_trend_content()
    agent_executor, config = initialize_agent()

    prompt = (
    f"Please analyze these NFT market signals:\n\n"
    f"{json.dumps(market_signals, indent=2)}\n\n"
    "Provide a detailed analysis of market trends and overall sentiment score."
    )
    for chunk in agent_executor.stream(
        {"messages": [HumanMessage(content=prompt)]},
        config
    ):
        if "agent" in chunk:
            return chunk["agent"]["messages"][0].content
        elif "tools" in chunk:
            return chunk["tools"]["messages"][0].content

        

def main():
    try:
        news_agent = NFTMarketAnalyzer()
        scraper = NFTTrendScraper()
        result = scraper.get_trend_content()
        
        # Process only the agent's response
        for chunk in result:
            if "agent" in chunk and "messages" in chunk["agent"]:
                return chunk["agent"]["messages"][0].content
            if "tool" in chunk and  "messages" in chunk['tool']:
                return chunk["tool"]["messages"][0].content

        # If no agent response found
        return {
            "reasoning": "No market data available",
            "sentiment_score": 0
        }
        
    except Exception as e:
        print(f"Error in main: {str(e)}")
        return {
            "reasoning": "Error analyzing market data",
            "sentiment_score": 0
        }
 
if __name__ == "__main__":
    print(main())