import React, { useState, useEffect } from 'react';
import { FaChartLine, FaImages, FaNetworkWired, FaPalette } from 'react-icons/fa';
import './Cards.css'; // Linking CSS

const Card = ({ type, isActive, onClick }) => {
    const [networkStats, setNetworkStats] = useState({
        tps: "2,450",
        blockchain: "Loading...",
        congestionLevel: "Loading...",
        failurePercentage: "Loading..."
    });

    useEffect(() => {
        const fetchNetworkStats = async () => {
            if (type === 'network') {
                try {
                    // Fetch both endpoints in parallel
                    const [transactionResponse, congestionResponse] = await Promise.all([
                        fetch('http://localhost:8000/api/transaction-fees'),
                        fetch('http://localhost:8000/api/predict-congestion')
                    ]);

                    const transactionData = await transactionResponse.json();
                    const congestionData = await congestionResponse.json();

                    if (transactionData.status === 'success' && transactionData.data) {
                        const parsedData = JSON.parse(transactionData.data);
                        const lastKey = Math.max(...Object.keys(parsedData.tps));
                        
                        setNetworkStats(prev => ({
                            ...prev,
                            tps: parsedData.tps[lastKey] || '2,450',
                            blockchain: parsedData.blockchain[lastKey] || 'Unknown'
                        }));
                    }

                    if (congestionData.status === 'success' && congestionData.data) {
                        console.log('Congestion Data:', congestionData.data); // For debugging
                        
                        setNetworkStats(prev => ({
                            ...prev,
                            congestionLevel: String(congestionData.data['Predicted Congestion']),
                            failurePercentage: String(congestionData.data['Failure Percentage']).slice(0, 5) + '%'
                        }));
                    }
                } catch (err) {
                    console.error('Failed to fetch network stats:', err);
                    setNetworkStats({
                        tps: "Error loading TPS",
                        blockchain: "Error loading chain",
                        congestionLevel: "Error loading",
                        failurePercentage: "Error loading"
                    });
                }
            }
        };

        fetchNetworkStats();
        const intervalId = type === 'network' ? 
            setInterval(fetchNetworkStats, 30000) : null;

        return () => {
            if (intervalId) clearInterval(intervalId);
        };
    }, [type]);

    const cardConfig = {
        nfts: {
            icon: <FaImages className="card-icon" />,
            title: "Recommended NFTs",
            content: "Discover Top Picks",
            stat: "24h Volume: 2.98B"
        },
        network: {
            icon: <FaNetworkWired className="card-icon" />,
            title: "Network Status",
            content: (
                <>
                    <div>Current TPS: {networkStats.tps}</div>
                    <div>Congestion: {networkStats.congestionLevel}</div>
                    <div>Failure Rate: {networkStats.failurePercentage}</div>
                </>
            ),
            stat: `Chain: ${networkStats.blockchain}`
        },
        sentiment: {
            icon: <FaPalette className="card-icon" />,
            title: "Market Sentiment",
            stat: "Keep Up with the Latest Solana News!"
        },
        ai: {
            icon: <FaChartLine className="card-icon" />,
            title: "AI Insights",
            content: "Market Direction: Bullish",
            stat: "Confidence: 85%"
        }
    };

    const config = cardConfig[type];

    return (
        <div className="card-container">
            <div className={`card ${type}`} onClick={onClick}>
                <div className="card-content">
                    {config.icon}
                    <h3>{config.title}</h3>
                    <div className="network-stats">{config.content}</div>
                    <div className="card-stat">{config.stat}</div>
                </div>
            </div>
        </div>
    );
};

export default Card;
