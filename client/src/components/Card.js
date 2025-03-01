import React, { useState, useEffect, useRef } from 'react';
import { FaChartLine, FaImages, FaNetworkWired, FaPalette } from 'react-icons/fa';
import './Cards.css'; // Linking CSS

const Card = ({ type, isActive, onClick }) => {
    const [networkStats, setNetworkStats] = useState({
        tps: "2,450",
        blockchain: "Loading...",
        congestionLevel: "Loading...",
        failurePercentage: "Loading..."
    });
    const cardRef = useRef(null);
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
    const [isHovered, setIsHovered] = useState(false);

    // 3D tilt effect
    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!cardRef.current || !isHovered) return;
            
            const rect = cardRef.current.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;
            
            cardRef.current.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
            
            setMousePosition({ x, y });
        };

        const resetTransform = () => {
            if (cardRef.current) {
                cardRef.current.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
            }
        };

        if (isHovered) {
            window.addEventListener('mousemove', handleMouseMove);
        } else {
            resetTransform();
        }

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
        };
    }, [isHovered]);

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
            stat: "24h Volume: 2.98B",
            gradient: "linear-gradient(135deg, #00FFA3 0%, #00B8D9 100%)",
            hoverGradient: "linear-gradient(135deg, #00FFA3 0%, #00B8D9 70%, #0077FF 100%)"
        },
        network: {
            icon: <FaNetworkWired className="card-icon" />,
            title: "Network Status",
            content: (
                <>
                    <div className="stat-item">
                        <span className="stat-label">Current TPS:</span>
                        <span className="stat-value">{networkStats.tps}</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">Congestion:</span>
                        <span className="stat-value">{networkStats.congestionLevel}</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">Failure Rate:</span>
                        <span className="stat-value">{networkStats.failurePercentage}</span>
                    </div>
                </>
            ),
            stat: `Chain: ${networkStats.blockchain}`,
            gradient: "linear-gradient(135deg, #9945FF 0%, #14F195 100%)",
            hoverGradient: "linear-gradient(135deg, #9945FF 0%, #14F195 70%, #00FFA3 100%)"
        },
        sentiment: {
            icon: <FaPalette className="card-icon" />,
            title: "Market Sentiment",
            content: "Track Market Trends",
            stat: "Keep Up with the Latest Solana News!",
            gradient: "linear-gradient(135deg, #E40F91 0%, #9945FF 100%)",
            hoverGradient: "linear-gradient(135deg, #E40F91 0%, #9945FF 70%, #14F195 100%)"
        },
        ai: {
            icon: <FaChartLine className="card-icon" />,
            title: "AI Insights",
            content: "Market Direction: Bullish",
            stat: "Confidence: 85%",
            gradient: "linear-gradient(135deg, #29C7FE 0%, #9945FF 100%)",
            hoverGradient: "linear-gradient(135deg, #29C7FE 0%, #9945FF 70%, #E40F91 100%)"
        }
    };

    const config = cardConfig[type];

    return (
        <div className="card-container">
            <div 
                ref={cardRef}
                className={`solana-card ${type} ${isActive ? 'active' : ''}`} 
                onClick={onClick}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                style={{
                    transition: isHovered ? 'transform 0.1s ease-out' : 'transform 0.5s ease-out',
                    "--card-gradient": config.gradient,
                    "--card-hover-gradient": config.hoverGradient
                }}
            >
                {/* Animated glow background */}
                <div className="card-glow"></div>
                
                {/* Card content */}
                <div className="solana-card-content">
                    <div className="card-header">
                        <div className="icon-container">
                            {config.icon}
                        </div>
                        <h3 className="card-title">{config.title}</h3>
                    </div>
                    
                    <div className="network-stats">
                        {config.content}
                    </div>
                    
                    <div className="card-footer">
                        <div className="card-stat">{config.stat}</div>
                        {isActive && <div className="active-indicator"></div>}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Card;