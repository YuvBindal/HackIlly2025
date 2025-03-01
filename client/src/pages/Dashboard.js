import { usePrivy } from "@privy-io/react-auth";
import React, { useEffect, useState, useCallback } from "react";
import { FaSync } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import Card from "../components/Card";
import Navbar from "../components/navbar";
import "./Dashboard.css";

const Dashboard = () => {
    const { user, logout } = usePrivy();
    const navigate = useNavigate();
    const [activeSection, setActiveSection] = useState("nfts");
    const [nfts, setNfts] = useState([]);
    const [loading, setLoading] = useState(false);

    const handleLogout = async () => {
        try {
            await logout();
            navigate("/");
        } catch (error) {
            console.error("Error during logout:", error);
        }
    };

    // Fetch NFTs when NFT section is active
    useEffect(() => {
        // Uncomment after the api is ready // change the url to the api url
        // const fetchNFTs = async () => {
        //     if (activeSection === 'nfts') {
        //         setLoading(true);
        //         try {
        //             const response = await fetch('https://exampleapifornfts.com/nfts');
        //             const data = await response.json();
        //             setNfts(data);
        //         } catch (error) {
        //             console.error('Error fetching NFTs:', error);
        //         } finally {
        //             setLoading(false);
        //         }
        //     }
        // };

        // fetchNFTs();

        // delete after the api is ready // start of mock nft data
        // mock nft data for 9 pictures all with the same image (https://www.google.com/url?sa=i&url=https%3A%2F%2Fen.wikipedia.org%2Fwiki%2FSolana_%2528blockchain_platform%2529&psig=AOvVaw3TWGzfJ-uKp0e1EwCIQm2V&ust=1739151063952000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCKDf6ty4tYsDFQAAAAAdAAAAABAE)
        // response is an array of 9 objects with the following structure:
        // {
        //     image: 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fen.wikipedia.org%2Fwiki%2FSolana_%2528blockchain_platform%2529&psig=AOvVaw3TWGzfJ-uKp0e1EwCIQm2V&ust=1739151063952000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCKDf6ty4tYsDFQAAAAAdAAAAABAE',
        //     name: 'Solana',
        //     price: 100,
        //     volume: 1000
        // }
        const mockNfts = Array.from({ length: 9 }, (_, index) => ({
            image: "https://upload.wikimedia.org/wikipedia/en/b/b9/Solana_logo.png",
            name: "Solana",
            price: 100,
            volume: 1000,
        }));
        setNfts(mockNfts);
        setLoading(false);

        // // end of mock nft data
    }, [activeSection]);

    const truncateAddress = (address) => {
        if (!address) return "";
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    };

    // Content components for each section
    const NetworkContent = () => {
        const [tradingData, setTradingData] = useState(null);
        const [mintingData, setMintingData] = useState(null);
        const [transactionData, setTransactionData] = useState(null);
        const [error, setError] = useState(null);
        const [lastUpdated, setLastUpdated] = useState(null);
        const [isRefreshing, setIsRefreshing] = useState(false);
        const [fieldUpdates, setFieldUpdates] = useState({
            trading: {},
            minting: {},
            transaction: {}
        });

        const fetchAllData = async () => {
            setIsRefreshing(true);
            try {
                const [tradingResponse, mintingResponse, transactionResponse] = await Promise.all([
                    fetch('http://localhost:8000/api/trading-activity'),
                    fetch('http://localhost:8000/api/minting-dict'),
                    fetch('http://localhost:8000/api/transaction-dict')
                ]);

                const tradingJson = await tradingResponse.json();
                const mintingJson = await mintingResponse.json();
                const transactionJson = await transactionResponse.json();

                if (tradingJson.status === 'success') {
                    checkFieldUpdates('trading', tradingData, tradingJson.data);
                    setTradingData(tradingJson.data);
                }
                if (mintingJson.status === 'success') {
                    checkFieldUpdates('minting', mintingData, mintingJson.data);
                    setMintingData(mintingJson.data);
                }
                if (transactionJson.status === 'success') {
                    checkFieldUpdates('transaction', transactionData, transactionJson.data);
                    setTransactionData(transactionJson.data);
                }

                setLastUpdated(new Date().toLocaleTimeString());
            } catch (err) {
                setError('Failed to fetch network data');
                console.error('Error:', err);
            } finally {
                // Keep the refresh animation visible for at least 500ms
                setTimeout(() => setIsRefreshing(false), 500);
            }
        };

        const checkFieldUpdates = (dataType, oldData, newData) => {
            if (!oldData) return;
            
            const updates = {};
            Object.keys(newData).forEach(key => {
                if (oldData[key] !== newData[key]) {
                    updates[key] = true;
                }
            });

            setFieldUpdates(prev => ({
                ...prev,
                [dataType]: updates
            }));

            // Clear highlights after 1 second
            setTimeout(() => {
                setFieldUpdates(prev => ({
                    ...prev,
                    [dataType]: {}
                }));
            }, 1000);
        };

        // Fetch data interval
        useEffect(() => {
            fetchAllData();
            const intervalId = setInterval(fetchAllData, 5000);
            return () => clearInterval(intervalId);
        }, []);

        const DataTable = ({ title, data, dataType }) => {
            if (!data) return null;
            
            return (
                <div className="data-section">
                    <h3>{title}</h3>
                    <table className="data-table">
                        <thead>
                            <tr>
                                {Object.keys(data).map(key => (
                                    <th key={key}>{key}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                {Object.entries(data).map(([key, value]) => (
                                    <td 
                                        key={key}
                                        className={fieldUpdates[dataType][key] ? 'field-updated' : ''}
                                    >
                                        {value}
                                    </td>
                                ))}
                            </tr>
                        </tbody>
                    </table>
                </div>
            );
        };

        return (
            <div className={`detail-section ${isRefreshing ? 'refreshing' : ''}`}>
                <div className="section-header">
                    <h2>Network Activity</h2>
                    <div className="header-right">
                        <FaSync className={`refresh-icon ${isRefreshing ? 'spinning' : ''}`} />
                        <span className="last-updated">Last updated: {lastUpdated}</span>
                    </div>
                </div>
                {error ? (
                    <div className="error-message">{error}</div>
                ) : (
                    <>
                        <DataTable title="Trading Activity" data={tradingData} dataType="trading" />
                        <DataTable title="Minting Activity" data={mintingData} dataType="minting" />
                        <DataTable title="Transaction Activity" data={transactionData} dataType="transaction" />
                    </>
                )}
            </div>
        );
    };

    const SentimentContent = () => {
        const [newsItems, setNewsItems] = useState([]);
        const [loading, setLoading] = useState(true);
        const [isRefreshing, setIsRefreshing] = useState(false);

        const fetchNews = async () => {
            setIsRefreshing(true);
            try {
                const response = await fetch('http://localhost:8000/api/news-information');
                const result = await response.json();
                
                if (result.status === 'success' && result.data) {
                    const shuffledNews = [...result.data]
                        .sort(() => Math.random() - 0.5)
                        .slice(0, 5);
                    
                    const formattedNews = shuffledNews.map((newsItem, index) => ({
                        title: newsItem,
                        sentiment: getSentiment(newsItem),
                        impact: getImpact(newsItem),
                        date: new Date(Date.now() - index * 86400000).toISOString().split('T')[0]
                    }));
                    
                    setNewsItems(formattedNews);
                }
            } catch (error) {
                console.error('Error fetching news:', error);
            } finally {
                setLoading(false);
                // Minimum refresh animation duration
                setTimeout(() => setIsRefreshing(false), 500);
            }
        };

        useEffect(() => {
            fetchNews();
            const intervalId = setInterval(fetchNews, 10000);
            return () => clearInterval(intervalId);
        }, []);
        
        // Helper functions remain the same
        const getSentiment = (newsText) => {
            const text = newsText.toLowerCase();
            if (text.includes('surge') || text.includes('rise') || text.includes('growth') || text.includes('up')) {
                return 'Bullish';
            } else if (text.includes('drop') || text.includes('fall') || text.includes('down')) {
                return 'Bearish';
            }
            return 'Neutral';
        };

        const getImpact = (newsText) => {
            const text = newsText.toLowerCase();
            if (text.includes('major') || text.includes('significant') || text.includes('surge')) {
                return 'High';
            } else if (text.includes('minor') || text.includes('small')) {
                return 'Low';
            }
            return 'Medium';
        };

        if (loading) {
            return (
                <div className="detail-section">
                    <div className="section-header">
                        <h2>SolSentiment™ News Feed</h2>
                        <span className="subtitle">Loading news...</span>
                    </div>
                </div>
            );
        }

        return (
            <div className={`detail-section sentiment-section ${isRefreshing ? 'refreshing' : ''}`}>
                <div className="section-header">
                    <h2>SolSentiment™ News Feed</h2>
                    <div className="header-right">
                        <FaSync className={`refresh-icon ${isRefreshing ? 'spinning' : ''}`} />
                        <span className="subtitle">Market Intelligence & Network Updates</span>
                        <span className="update-indicator">Updates every 10s</span>
                    </div>
                </div>
                <div className={`news-grid ${isRefreshing ? 'refreshing' : ''}`}>
                    {newsItems.map((item, index) => (
                        <div 
                            key={index} 
                            className={`news-item ${isRefreshing ? 'refresh-fade' : ''}`}
                            style={{ animationDelay: `${index * 0.1}s` }}
                        >
                            <div className="news-header">
                                <span className={`sentiment-badge ${item.sentiment.toLowerCase()}`}>
                                    {item.sentiment}
                                </span>
                                <span className="news-date">{item.date}</span>
                            </div>
                            <h3>{item.title}</h3>
                            <div className="news-footer">
                                <span className={`impact-badge ${item.impact.toLowerCase()}`}>
                                    {item.impact} Impact
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
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
        <>
            <Navbar handleLogout={handleLogout} />
            <div className="dashboard-container">
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
        </>
    );
};

export default Dashboard;
