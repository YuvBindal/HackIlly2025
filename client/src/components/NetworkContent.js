import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FaSync, FaChevronDown, FaChevronUp, FaInfoCircle, FaArrowUp, FaArrowDown } from 'react-icons/fa';
import { BiNetworkChart, BiCoin, BiTransfer } from 'react-icons/bi';
import './NetworkContent.css';

const NetworkContent = () => {
    const [tradingData, setTradingData] = useState(null);
    const [mintingData, setMintingData] = useState(null);
    const [transactionData, setTransactionData] = useState(null);
    const [previousTradingData, setPreviousTradingData] = useState(null);
    const [previousMintingData, setPreviousMintingData] = useState(null);
    const [previousTransactionData, setPreviousTransactionData] = useState(null);
    const [expandedSections, setExpandedSections] = useState({
        trading: true,
        minting: true,
        transaction: true
    });
    const [error, setError] = useState(null);
    const [lastUpdated, setLastUpdated] = useState(null);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [fieldUpdates, setFieldUpdates] = useState({
        trading: {},
        minting: {},
        transaction: {}
    });
    const [trendIndicators, setTrendIndicators] = useState({
        trading: {},
        minting: {},
        transaction: {}
    });
    
    // Use refs to access current state values without triggering re-renders
    const tradingDataRef = useRef(null);
    const mintingDataRef = useRef(null);
    const transactionDataRef = useRef(null);
    
    // Update refs when state changes
    useEffect(() => {
        tradingDataRef.current = tradingData;
        mintingDataRef.current = mintingData;
        transactionDataRef.current = transactionData;
    }, [tradingData, mintingData, transactionData]);

    // Calculate trends when data changes
    useEffect(() => {
        if (!tradingData || !mintingData || !transactionData) return;
        
        const calculateTrends = (dataType, data) => {
            const trends = {};
            
            // Compare with previous data to determine trend direction
            // This assumes you have previous data stored somewhere
            if (dataType === 'trading' && data.total_volume_usd !== undefined) {
                // Compare current total_volume_usd with previous value
                trends.total_volume_usd = data.total_volume_usd > previousTradingData?.total_volume_usd ? 'up' : 'down';
            } 
            else if (dataType === 'minting' && data.mint_count !== undefined) {
                // Compare current mint_count with previous value
                trends.mint_count = data.mint_count > previousMintingData?.mint_count ? 'up' : 'down';
            }
            else if (dataType === 'transaction' && data.tx_count !== undefined) {
                // Compare current tx_count with previous value
                trends.tx_count = data.tx_count > previousTransactionData?.tx_count ? 'up' : 'down';
            }
            
            return trends;
        };
        
        setTrendIndicators({
            trading: calculateTrends('trading', tradingData),
            minting: calculateTrends('minting', mintingData),
            transaction: calculateTrends('transaction', transactionData)
        });
        
        // Store current data as previous for next comparison
        setPreviousTradingData(tradingData);
        setPreviousMintingData(mintingData);
        setPreviousTransactionData(transactionData);
        
    }, [tradingData, mintingData, transactionData]);

    const toggleSection = (section) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    // Fixed fetchAllData function with NO dependencies on state that it modifies
    const fetchAllData = useCallback(async () => {
        if (isRefreshing) return; // Prevent concurrent fetches
        
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
                checkFieldUpdates('trading', tradingDataRef.current, tradingJson.data);
                setTradingData(tradingJson.data);
            }
            if (mintingJson.status === 'success') {
                checkFieldUpdates('minting', mintingDataRef.current, mintingJson.data);
                setMintingData(mintingJson.data);
            }
            if (transactionJson.status === 'success') {
                checkFieldUpdates('transaction', transactionDataRef.current, transactionJson.data);
                setTransactionData(transactionJson.data);
            }

            setLastUpdated(new Date().toLocaleTimeString());
        } catch (err) {
            setError('Failed to fetch network data');
            console.error('Error:', err);
        } finally {
            // Keep the refresh animation visible for at least 800ms
            setTimeout(() => setIsRefreshing(false), 800);
        }
    }, [isRefreshing]); // Only depends on isRefreshing state to prevent concurrent fetches

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

        // Clear highlights after 1.5 seconds
        setTimeout(() => {
            setFieldUpdates(prev => ({
                ...prev,
                [dataType]: {}
            }));
        }, 1500);
    };

    // Fetch data interval - now correctly set up to respect the 5 second interval
    useEffect(() => {
        // Initial fetch
        fetchAllData();
        
        // Set up interval for subsequent fetches
        const intervalId = setInterval(() => {
            fetchAllData();
        }, 5000);
        
        // Clean up interval on unmount
        return () => clearInterval(intervalId);
    }, []);

    // Get a summary metric
    const getSummaryMetric = (data, key = null) => {
        if (!data) return '—';
        
        // If a specific key is provided and exists in the data
        if (key && data[key] !== undefined) return data[key];
        
        // For specific data types, return the appropriate metric
        if (data.total_volume_usd !== undefined) return data.total_volume_usd;
        if (data.mint_count !== undefined) return data.mint_count;
        if (data.tx_count !== undefined) return data.tx_count;
        
        // Fallback if none of the expected fields are found
        return '—';
    };

    const handleManualRefresh = () => {
        fetchAllData();
    };

    const summaryCards = [
        {
            title: 'Trading Volume',
            value: tradingData ? getSummaryMetric(tradingData, 'Volume') : '—',
            icon: <BiNetworkChart />,
            color: '#00FFA3'
        },
        {
            title: 'Minting Rate',
            value: mintingData ? getSummaryMetric(mintingData, 'Rate') : '—',
            icon: <BiCoin />,
            color: '#29C7FE'
        },
        {
            title: 'Transaction Count',
            value: transactionData ? getSummaryMetric(transactionData, 'Count') : '—',
            icon: <BiTransfer />,
            color: '#9945FF'
        }
    ];

    const DataTable = ({ title, data, dataType, icon, color }) => {
        if (!data) return null;
        
        return (
            <div className="network-data-card">
                <div 
                    className="network-card-header" 
                    onClick={() => toggleSection(dataType)}
                >
                    <div className="network-card-title">
                        <div className="network-card-icon" style={{ background: `rgba(${color}, 0.2)` }}>
                            {icon}
                        </div>
                        <h3>{title}</h3>
                    </div>
                    <div className="network-card-toggle">
                        {expandedSections[dataType] ? <FaChevronUp /> : <FaChevronDown />}
                    </div>
                </div>
                
                {expandedSections[dataType] && (
                    <div className="network-card-content">
                        <div className="network-data-table-wrapper">
                            <table className="network-data-table">
                                <thead>
                                    <tr>
                                        {Object.keys(data).map(key => (
                                            <th key={key}>
                                                <div className="table-header-content">
                                                    <span>{key}</span>
                                                    <FaInfoCircle className="info-icon" title={`Information about ${key}`} />
                                                </div>
                                            </th>
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
                                                <div className="table-cell-content">
                                                    <span className="cell-value">{value}</span>
                                                    {trendIndicators[dataType][key] && (
                                                        <span className={`trend-indicator ${trendIndicators[dataType][key]}`}>
                                                            {trendIndicators[dataType][key] === 'up' ? 
                                                                <FaArrowUp className="trend-icon up" /> : 
                                                                <FaArrowDown className="trend-icon down" />
                                                            }
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                        ))}
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className={`network-content-wrapper ${isRefreshing ? 'refreshing' : ''}`}>
            <div className="section-header">
                <div className="section-title">
                    <h2>Network Activity</h2>
                    <p className="section-description">
                        Real-time data from the Solana blockchain showing current network performance metrics.
                    </p>
                </div>
                <div className="header-actions">
                    <button 
                        className="manual-refresh-button"
                        onClick={handleManualRefresh}
                        disabled={isRefreshing}
                    >
                        <FaSync className={isRefreshing ? 'spinning' : ''} />
                        <span>Refresh Data</span>
                    </button>
                    <div className="update-indicator">
                        <span className="update-pulse"></span>
                        <span className="last-updated">Last updated: {lastUpdated || '—'}</span>
                    </div>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="network-summary-cards">
                {summaryCards.map((card, index) => (
                    <div className="summary-card" key={index} style={{ '--card-accent': card.color }}>
                        <div className="summary-icon">{card.icon}</div>
                        <div className="summary-content">
                            <h4>{card.title}</h4>
                            <div className="summary-value">{card.value}</div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Main Content */}
            <div className="network-data-container">
                {error ? (
                    <div className="error-message">
                        <div className="error-icon">⚠️</div>
                        <div className="error-content">
                            <h4>Data Fetch Error</h4>
                            <p>{error}</p>
                            <button className="retry-button" onClick={handleManualRefresh}>
                                Try Again
                            </button>
                        </div>
                    </div>
                ) : !tradingData && !mintingData && !transactionData ? (
                    <div className="loading-state">
                        <div className="loading-spinner"></div>
                        <p>Loading network data...</p>
                    </div>
                ) : (
                    <>
                        <DataTable 
                            title="Trading Activity" 
                            data={tradingData} 
                            dataType="trading" 
                            icon={<BiNetworkChart />}
                            color="0, 255, 163"
                        />
                        <DataTable 
                            title="Minting Activity" 
                            data={mintingData} 
                            dataType="minting" 
                            icon={<BiCoin />}
                            color="41, 199, 254"
                        />
                        <DataTable 
                            title="Transaction Activity" 
                            data={transactionData} 
                            dataType="transaction" 
                            icon={<BiTransfer />}
                            color="153, 69, 255"
                        />
                    </>
                )}
            </div>

            {/* Live Update Indicator */}
            <div className="live-update-indicator">
                <div className={`pulse-dot ${isRefreshing ? 'active' : ''}`}></div>
                <span>Live Updates Active</span>
            </div>
        </div>
    );
};

export default NetworkContent;