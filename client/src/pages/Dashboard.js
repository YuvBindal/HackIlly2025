import { usePrivy } from "@privy-io/react-auth";
import React, { useEffect, useState, useCallback } from "react";
import { FaSync } from "react-icons/fa";
import Card from "../components/Card";
import "./Dashboard.css";
import NetworkContent from '../components/NetworkContent';
import SentimentContent from "../components/SentimentContent";

const Dashboard = () => {
    const { user } = usePrivy();
    const [activeSection, setActiveSection] = useState("nfts");
    const [nfts, setNfts] = useState([]);
    const [loading, setLoading] = useState(false);

    // Fetch NFTs when NFT section is active
    useEffect(() => {
        // Mock nft data
        const mockNfts = Array.from({ length: 9 }, (_, index) => ({
            image: "https://upload.wikimedia.org/wikipedia/en/b/b9/Solana_logo.png",
            name: "Solana",
            price: 100,
            volume: 1000,
        }));
        setNfts(mockNfts);
        setLoading(false);
    }, [activeSection]);

    const truncateAddress = (address) => {
        if (!address) return "";
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    };

    const NFTContent = () => {
        const [nfts, setNfts] = useState([]);
        const [loading, setLoading] = useState(false);
        const GATEWAY_URL = 'chocolate-hilarious-quokka-925.mypinata.cloud';
        const REFRESH_INTERVAL = 5000; // 5 seconds
        
        // All available CIDs
        const allNftCIDs = [
            'bafkreihcapi2wwosqeq57hotjiabnvcjsjpsucxpn2zgtuzu66matlcu2e',
            'bafkreibrjm5q7vfqsk2uns3sbojoxhqurjs2gkc2nccvzkw2ybhekythpi',
            'bafkreih2p2ubvzrxwfegarbysla2v5t2246ehcemlljz3qlpf2ba5gkwdq',
            'bafkreigdh4xhzl32srzbgwtat3zibkfc4yyuu2hfcnjqetscojjxarqwx4',
            'bafkreig24n7mqgk3xstzvzdkjiffvfk2w6ozawd22y57eqky6ah5bm5tcq',
            'bafkreih4opt5llx23mq52jlfj5itclxtzhpqus3defxgkbyw7dfe5f2v6m',
            'bafkreifviyj5dqtjekbzlmozktxgvpfflx3lytpuwutmcmwozezndcy5da',
            'bafkreiazx5oymsid7s75qfq5mff7jeailpl25347idqlmdlcfhilqhu2ni',
            'bafkreicszn6totdzz7q4lnljp3ekpxt34ikaufux7mat2x7vtfkd73wf6m'
        ];

        const getRandomCIDs = useCallback((count) => {
            const shuffled = [...allNftCIDs].sort(() => Math.random() - 0.5);
            return shuffled.slice(0, count);
        }, []);

        const refreshNFTs = useCallback(async () => {
            if (loading) return; // Prevent multiple simultaneous refreshes
            
            setLoading(true);
            try {
                const randomCIDs = getRandomCIDs(4);
                const nftList = randomCIDs.map(cid => ({
                    image: `https://${GATEWAY_URL}/ipfs/${cid}`
                }));
                setNfts(nftList);
            } catch (error) {
                console.error("Error refreshing NFTs:", error);
            } finally {
                setLoading(false);
            }
        }, [loading, getRandomCIDs, GATEWAY_URL]);

        useEffect(() => {
            // Initial load
            refreshNFTs();

            // Set up the interval
            const intervalId = setInterval(refreshNFTs, REFRESH_INTERVAL);

            // Cleanup function
            return () => clearInterval(intervalId);
        }, [refreshNFTs]); // Add refreshNFTs as a dependency

        return (
            <div className="detail-section">
                <div className="section-header">
                    <h2>Recommended NFTs</h2>
                    <button 
                        className="refresh-button" 
                        onClick={refreshNFTs}
                        disabled={loading}
                    >
                        <FaSync className={loading ? "spinning" : ""} />
                        <span>Refresh Recommendations</span>
                    </button>
                </div>
                {loading ? (
                    <div className="loading">Loading NFTs...</div>
                ) : (
                    <div className="nft-grid">
                        {nfts.map((nft, index) => (
                            <div key={index} className="nft-card">
                                <img 
                                    src={nft.image} 
                                    alt={`NFT ${index + 1}`}
                                    onError={(e) => {
                                        console.error(`Failed to load image: ${nft.image}`);
                                        e.target.onerror = null;
                                        e.target.src = 'https://via.placeholder.com/300?text=NFT+Image+Not+Found';
                                    }}
                                />
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    // Function to render active content
    const renderActiveContent = () => {
        switch (activeSection) {
            case "network":
                return <NetworkContent />;
            case "sentiment":
                return <SentimentContent />;
            case "nfts":
                return <NFTContent />;
            default:
                return <NetworkContent />;
        }
    };

    return (
        <div className="dashboard-container">
            {/* Animated Background */}
            <div className="animated-background">
                {/* Original circular blobs */}
                <div className="blob blob-1"></div>
                <div className="blob blob-2"></div>
                <div className="blob blob-3"></div>
                <div className="blob blob-4"></div>
                
                {/* New oval shapes - matching Solana site */}
                <div className="blob-oval blob-oval-horizontal" 
                    style={{ 
                        background: '#00FFA3',
                        top: '15%', 
                        left: '5%',
                        animation: 'float-slow 20s ease-in-out infinite'
                    }}>
                </div>
                
                <div className="blob-oval blob-oval-vertical" 
                    style={{ 
                        background: '#9945FF',
                        bottom: '10%', 
                        right: '8%',
                        animation: 'float-medium 18s ease-in-out infinite'
                    }}>
                </div>
                
                {/* Pill shape */}
                <div className="blob-oval blob-pill" 
                    style={{ 
                        background: '#E40F91',
                        top: '70%', 
                        left: '15%',
                        animation: 'float-fast 15s ease-in-out infinite'
                    }}>
                </div>
                
                {/* Small glowing circle */}
                <div className="blob-small-circle glow" 
                    style={{ 
                        background: '#00FFA3',
                        top: '35%', 
                        left: '60%',
                        animation: 'pulse 8s ease-in-out infinite'
                    }}>
                </div>
                
                {/* Ring shape */}
                <div className="blob-ring" 
                    style={{ 
                        borderColor: '#00FFA3',
                        top: '20%', 
                        right: '20%',
                        animation: 'rotate-slow 30s linear infinite'
                    }}>
                </div>
                
                {/* Small accent circle */}
                <div className="blob-small-circle" 
                    style={{ 
                        background: '#FFFFFF',
                        bottom: '40%', 
                        left: '48%',
                        width: '4px',
                        height: '4px',
                        filter: 'blur(2px)',
                        opacity: '0.7'
                    }}>
                </div>
            </div>
            <div className="main-content">
                <div className="cards-grid">
                    <Card
                        type="nfts"
                        isActive={activeSection === "nfts"}
                        onClick={() => setActiveSection("nfts")}
                    />
                    <Card
                        type="network"
                        isActive={activeSection === "network"}
                        onClick={() => setActiveSection("network")}
                    />
                    <Card
                        type="sentiment"
                        isActive={activeSection === "sentiment"}
                        onClick={() => setActiveSection("sentiment")}
                    />
                </div>

                <div className="dynamic-content">
                    {renderActiveContent()}
                </div>
            </div>
        </div>
    );
};

export default Dashboard;