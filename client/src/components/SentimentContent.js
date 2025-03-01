import React, { useState, useEffect } from 'react';
import { FaSync } from 'react-icons/fa';
import './SentimentContent.css';

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
    
    // Helper functions
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
            <div className="sentiment-container">
                <div className="animated-background">
                    <div className="blob blob-1"></div>
                    <div className="blob blob-2"></div>
                    <div className="blob blob-3"></div>
                    <div className="blob blob-4"></div>
                </div>
                <div className="detail-section">
                    <div className="section-header">
                        <h2>SolSentiment™ News Feed</h2>
                        <span className="subtitle">Loading news...</span>
                    </div>
                    <div className="loading-indicator glow"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="sentiment-container">
            {/* Animated Background */}
            <div className="animated-background">
                <div className="blob blob-1"></div>
                <div className="blob blob-2"></div>
                <div className="blob blob-3"></div>
                <div className="blob blob-4"></div>
                <div className="blob-oval blob-oval-horizontal" style={{left: '10%', top: '30%', background: '#00FFA3', animation: 'float-slow 15s infinite'}}></div>
                <div className="blob-oval blob-oval-vertical" style={{right: '15%', top: '50%', background: '#9945FF', animation: 'float-medium 18s infinite'}}></div>
                <div className="blob-pill" style={{left: '40%', bottom: '10%', background: '#E40F91', animation: 'float-fast 12s infinite'}}></div>
            </div>
            
            {/* Content Section */}
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
        </div>
    );
};

export default SentimentContent;