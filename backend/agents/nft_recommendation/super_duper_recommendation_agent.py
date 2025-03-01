import os
from typing import List, Dict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool
import asyncio
import sys
# Import our existing agents
from visual_nft_scorer import VisualImpactAnalyzer
from price_predictor import initialize_agent as initialize_price_agent

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from backend.python_integration.eth_price_tracker import ETHUSDTTracker

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from backend.python_integration.NFT_scraper_part2 import NFTTrendScraper

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../../sepolia/.env.local')
load_dotenv(env_path)

class NFTRecommendationHandler:
    def __init__(self):
        load_dotenv()
        self.visual_analyzer = VisualImpactAnalyzer()
        self.trend_scraper = NFTTrendScraper()
        self.price_tracker = ETHUSDTTracker()
        
    async def gather_all_data(self, max_budget: str, nft_cids: List[str]) -> Dict:
        """Gather data from all agents"""
        
        # Get visual impact scores
        impact_scores = self.visual_analyzer.analyze_impact(nft_cids)
        print("Visual impact scores obtained:", impact_scores)

        # Get market trends
        market_trends = self.trend_scraper.get_trend_content()
        print("Market trends obtained")

        # Get price data
        price_agent, price_config = initialize_price_agent()
        price_data = await self.price_tracker.get_eth_usdt_swaps()
        print("Price data obtained")

        return {
            "max_budget": max_budget,
            "nft_cids": nft_cids,
            "impact_scores": impact_scores,
            "market_trends": market_trends,
            "price_data": price_data.to_dict() if not price_data.empty else {}
        }

class SuperDuperAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4")
        self.memory = MemorySaver()
        
    def initialize_agent(self):
        """Initialize the super agent"""
        config = {"configurable": {"thread_id": "Super NFT Recommendation Agent"}}

        return create_react_agent(
            self.llm,
            tools=[],  # No tools needed as we're just processing gathered data
            checkpointer=self.memory,
            state_modifier=(
                "You are a sophisticated NFT recommendation agent. Your task is to analyze multiple data points "
                "and provide purchase recommendations for NFTs. You will receive:\n"
                "1. User's maximum budget\n"
                "2. Visual impact scores for each NFT\n"
                "3. Current market trends\n"
                "4. ETH price data\n\n"
                "You must respond in the following JSON format ONLY:\n"
                "{\n"
                "  'Reasoning': 'Detailed explanation of your analysis and decision-making process',\n"
                "  'Recommendation': [score1, score2, ...]\n"
                "}\n\n"
                "Where:\n"
                "- 'Reasoning' is a string explaining your analysis of all factors\n"
                "- 'Recommendation' is a list of integers from 0-100 matching the order of input CIDs\n"
                "- 100 means highly recommended for purchase\n"
                "- 0 means not recommended\n\n"
                "Consider these factors in your scoring:\n"
                "- Visual appeal (from impact scores)\n"
                "- Market timing based on ETH price trends\n"
                "- Current NFT market trends\n"
                "- User's budget constraints\n\n"
                "Ensure your response is EXACTLY in the specified JSON format."
            ),
        ), config

    async def get_recommendations(self, data: Dict) -> List[Dict]:
        """Get recommendations based on all gathered data"""
        agent_executor, config = self.initialize_agent()
        
        prompt = (
            f"Please analyze the following data and provide NFT purchase recommendations:\n\n"
            f"User's Max Budget: {data['max_budget']}\n\n"
            f"NFT Visual Impact Scores: {data['impact_scores']}\n\n"
            f"Market Trends Summary: {data['market_trends'][:500]}...\n\n"
            f"Recent ETH Price Data: {data['price_data']}\n\n"
            f"Generate recommendation scores for these NFTs: {data['nft_cids']}"
        )

        recommendations = []
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=prompt)]},
            config
        ):
            if "agent" in chunk:
                recommendations.append(chunk["agent"]["messages"][0].content)

        return recommendations

async def main():
    # Example usage
    handler = NFTRecommendationHandler()
    super_agent = SuperDuperAgent()

    # Example data
    max_budget = "5 ETH"
    nft_cids = [
        "bafkreie44ehpnzcfupb46r5jsd5gs236oozpeidcp2qqou3hwxw7fj5pui",
        "bafkreihv4qmybxqeqv4lrzfyqxgjfyxjflz4znpkn5hhc6wjpgudzglv4a"
    ]

    # Gather all data
    data = await handler.gather_all_data(max_budget, nft_cids)
    
    # Get recommendations
    recommendations = await super_agent.get_recommendations(data)
    
    print("\nFinal Recommendations:")
    print(recommendations)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())