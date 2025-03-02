import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FaSync, FaChevronDown, FaChevronUp, FaInfoCircle, FaArrowUp, FaArrowDown, FaChartLine } from 'react-icons/fa';
import { BiNetworkChart, BiCoin, BiTransfer } from 'react-icons/bi';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import './NetworkContent.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Function to export networkStats directly for other components to use
export const getNetworkStatsState = () => {
  return networkStatsStore;
};

// Store for keeping network stats accessible outside the component
let networkStatsStore = {
  tps: "2,450",
  blockchain: "Solana",
  congestionLevel: "Unknown",
  failurePercentage: "Unknown"
};

const NetworkContent = ({ onNetworkStatsUpdate }) => {
    const [tradingData, setTradingData] = useState(null);
    const [mintingData, setMintingData] = useState(null);
    const [transactionData, setTransactionData] = useState(null);
    const [previousTradingData, setPreviousTradingData] = useState(null);
    const [previousMintingData, setPreviousMintingData] = useState(null);
    const [previousTransactionData, setPreviousTransactionData] = useState(null);
    const [expandedSections, setExpandedSections] = useState({
        trading: true,
        minting: true,
        transaction: true,
        networkStats: true,
        charts: true
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
    
    // Network stats state
    const [networkStats, setNetworkStats] = useState({
        tps: "2,450",
        blockchain: "Loading...",
        congestionLevel: "Loading...",
        failurePercentage: "Loading..."
    });
    
    // Chart data state
    const [tpsHistory, setTpsHistory] = useState([]);
    const [failureRateHistory, setFailureRateHistory] = useState([]);
    const [timeLabels, setTimeLabels] = useState([]);
    
    // Use refs to access current state values without triggering re-renders
    const tradingDataRef = useRef(null);
    const mintingDataRef = useRef(null);
    const transactionDataRef = useRef(null);
    const networkStatsRef = useRef(null);
    
    // Update refs when state changes
    useEffect(() => {
        tradingDataRef.current = tradingData;
        mintingDataRef.current = mintingData;
        transactionDataRef.current = transactionData;
        networkStatsRef.current = networkStats;
        
        // Update the globally accessible store when networkStats changes
        networkStatsStore = networkStats;
        
        // Call the callback if provided
        if (onNetworkStatsUpdate && typeof onNetworkStatsUpdate === 'function') {
            onNetworkStatsUpdate(networkStats);
        }
    }, [tradingData, mintingData, transactionData, networkStats, onNetworkStatsUpdate]);

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
        
    }, [tradingData, mintingData, transactionData, previousTradingData, previousMintingData, previousTransactionData]);

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
            const [tradingResponse, mintingResponse, transactionResponse, tpsResponse, congestionResponse] = await Promise.all([
                fetch('http://localhost:8000/api/trading-activity'),
                fetch('http://localhost:8000/api/minting-dict'),
                fetch('http://localhost:8000/api/transaction-dict'),
                fetch("http://localhost:8000/api/transaction-fees"),
                fetch("http://localhost:8000/api/get-predicted-congestion")
            ]);

            const tradingJson = await tradingResponse.json();
            const mintingJson = await mintingResponse.json();
            const transactionJson = await transactionResponse.json();
            const tpsJson = await tpsResponse.json();
            const congestionJson = await congestionResponse.json();

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

            if (tpsJson.status === 'success') {
                // Parse the TPS data
                const parsedData = JSON.parse(tpsJson.data);
                
                // Get the last key (most recent data point)
                const lastKey = Math.max(...Object.keys(parsedData.tps));
                
                // Update only the TPS field in networkStats
                setNetworkStats(prev => ({
                    ...prev,
                    tps: parsedData.tps[lastKey] || '2,450',
                    blockchain: parsedData.blockchain[lastKey] || 'Unknown'
                }));
                
                // Update TPS history for charts
                const tpsNumber = parseFloat(String(parsedData.tps[lastKey]).replace(/,/g, ''));
                const currentTime = new Date().toLocaleTimeString();
                
                setTpsHistory(prev => {
                    const newHistory = [...prev, tpsNumber];
                    // Keep only the last 20 data points
                    if (newHistory.length > 20) return newHistory.slice(-20);
                    return newHistory;
                });
                
                // Add corresponding time label
                setTimeLabels(prev => {
                    const newLabels = [...prev, currentTime];
                    // Keep only the last 20 labels
                    if (newLabels.length > 20) return newLabels.slice(-20);
                    return newLabels;
                });
            }

            // Handle congestion data
            if (congestionJson.status === 'success' && congestionJson.data) {
                // Update networkStats with congestion data
                setNetworkStats(prev => ({
                    ...prev,
                    congestionLevel: congestionJson.data.congestion_level || 'Unknown',
                    failurePercentage: congestionJson.data.failure_percentage + '%' || 'Unknown'
                }));
                
                // Update failure rate history for charts
                const failureRate = parseFloat(congestionJson.data.failure_percentage);
                const currentTime = new Date().toLocaleTimeString();
                
                setFailureRateHistory(prev => {
                    const newHistory = [...prev, failureRate];
                    // Keep only the last 20 data points
                    if (newHistory.length > 20) return newHistory.slice(-20);
                    return newHistory;
                });
            }

            setLastUpdated(new Date().toLocaleTimeString());
        } catch (err) {
            setError('Failed to fetch network data');
            console.error('Error:', err);
        } finally {
            // Keep the refresh animation visible for at least 800ms
            setTimeout(() => setIsRefreshing(false), 1500);
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
        const dataIntervalId = setInterval(() => {
            fetchAllData();
        }, 5000);
        
        // Clean up intervals on unmount
        return () => {
            clearInterval(dataIntervalId);
        };
    }, [fetchAllData]);

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

    // Add a network stats card for TPS
    const networkStatsCard = {
        title: 'Network TPS',
        value: networkStats ? networkStats.tps : '—',
        icon: <BiNetworkChart />,
        color: '#E40F91'
    };

    // Combine all cards
    const allSummaryCards = [...summaryCards, networkStatsCard];

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

    // Network Stats Card
    const NetworkStatsCard = () => {
        return (
            <div className="network-data-card">
                <div 
                    className="network-card-header" 
                    onClick={() => toggleSection('networkStats')}
                >
                    <div className="network-card-title">
                        <div className="network-card-icon" style={{ background: `rgba(228, 15, 145, 0.2)` }}>
                            <BiNetworkChart />
                        </div>
                        <h3>Network Performance</h3>
                    </div>
                    <div className="network-card-toggle">
                        {expandedSections.networkStats ? <FaChevronUp /> : <FaChevronDown />}
                    </div>
                </div>
                
                {expandedSections.networkStats && (
                    <div className="network-card-content">
                        <div className="network-stats-grid">
                            <div className="network-stat-item">
                                <div className="stat-label">Current TPS</div>
                                <div className="stat-value">{networkStats.tps}</div>
                            </div>
                            <div className="network-stat-item">
                                <div className="stat-label">Blockchain</div>
                                <div className="stat-value">{networkStats.blockchain}</div>
                            </div>
                            <div className="network-stat-item">
                                <div className="stat-label">Congestion Level</div>
                                <div className="stat-value">{networkStats.congestionLevel}</div>
                            </div>
                            <div className="network-stat-item">
                                <div className="stat-label">Failure Rate</div>
                                <div className="stat-value">{networkStats.failurePercentage}</div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    // Network Charts Card for time series visualization
    const NetworkChartsCard = () => {
        // Chart data configuration
        const tpsChartData = {
            labels: timeLabels,
            datasets: [
                {
                    label: 'TPS (Transactions Per Second)',
                    data: tpsHistory,
                    fill: true,
                    backgroundColor: 'rgba(0, 255, 163, 0.2)',
                    borderColor: '#00FFA3',
                    tension: 0.4,
                    pointBackgroundColor: '#00FFA3',
                    pointRadius: 3,
                    pointHoverRadius: 6,
                }
            ]
        };

        const failureRateChartData = {
            labels: timeLabels,
            datasets: [
                {
                    label: 'Failure Rate (%)',
                    data: failureRateHistory,
                    fill: true,
                    backgroundColor: 'rgba(228, 15, 145, 0.2)',
                    borderColor: '#E40F91',
                    tension: 0.4,
                    pointBackgroundColor: '#E40F91',
                    pointRadius: 3,
                    pointHoverRadius: 6,
                }
            ]
        };

        // Common chart options
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            animation: {
                duration: 750
            }
        };

        return (
            <div className="network-data-card">
                <div 
                    className="network-card-header" 
                    onClick={() => toggleSection('charts')}
                >
                    <div className="network-card-title">
                        <div className="network-card-icon" style={{ background: `rgba(41, 199, 254, 0.2)` }}>
                            <FaChartLine />
                        </div>
                        <h3>Network Trends</h3>
                    </div>
                    <div className="network-card-toggle">
                        {expandedSections.charts ? <FaChevronUp /> : <FaChevronDown />}
                    </div>
                </div>
                
                {expandedSections.charts && (
                    <div className="network-card-content">
                        <div className="charts-container">
                            <div className="chart-section">
                                <h4 className="chart-title">TPS Over Time</h4>
                                <div className="chart-wrapper">
                                    {tpsHistory.length > 1 ? (
                                        <Line data={tpsChartData} options={chartOptions} />
                                    ) : (
                                        <div className="chart-placeholder">
                                            <p>Collecting data... Charts will appear after multiple data points are available.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                            
                            <div className="chart-section">
                                <h4 className="chart-title">Failure Rate Over Time</h4>
                                <div className="chart-wrapper">
                                    {failureRateHistory.length > 1 ? (
                                        <Line data={failureRateChartData} options={chartOptions} />
                                    ) : (
                                        <div className="chart-placeholder">
                                            <p>Collecting data... Charts will appear after multiple data points are available.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
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
                {allSummaryCards.map((card, index) => (
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
                        {/* Network Stats Card */}
                        <NetworkStatsCard />
                        
                        {/* Network Charts Card - NEW */}
                        <NetworkChartsCard />
                        
                        {/* Data Tables */}
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