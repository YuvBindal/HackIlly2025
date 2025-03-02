import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Keypair, 
  Connection, 
  LAMPORTS_PER_SOL, 
  PublicKey, 
  Transaction,
  SystemProgram
} from '@solana/web3.js';
import bs58 from 'bs58';
import './Scheduler.css';
import { Buffer } from 'buffer';
window.Buffer = Buffer;


function EnhancedSolanaWallet() {
  const [wallet, setWallet] = useState(null);
  const [balance, setBalance] = useState(null);
  const [network, setNetwork] = useState('devnet');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [showPrivateKey, setShowPrivateKey] = useState(false);
  const [isBalanceRefreshing, setIsBalanceRefreshing] = useState(false);
  const balanceInterval = useRef(null);
  
  // Send transaction state
  const [recipientAddress, setRecipientAddress] = useState('');
  const [sendAmount, setSendAmount] = useState('');
  const [isValidAddress, setIsValidAddress] = useState(false);

  // Network stats state
  const [networkStats, setNetworkStats] = useState({
    tps: '0',
    congestionLevel: 'Unknown',
    failurePercentage: '0%',
    blockchain: 'Solana',
    lastUpdated: new Date().toLocaleTimeString()
  });
  const [isRefreshingStats, setIsRefreshingStats] = useState(false);
  const [tpsHistory, setTpsHistory] = useState([]);
  const [failureRateHistory, setFailureRateHistory] = useState([]);
  const [timeLabels, setTimeLabels] = useState([]);
  
  // Scheduled transactions state
  const [scheduledTransactions, setScheduledTransactions] = useState([]);
  const [scheduledRecipient, setScheduledRecipient] = useState('');
  const [scheduledAmount, setScheduledAmount] = useState('');
  const [maxFailureRate, setMaxFailureRate] = useState(5); // Default max failure rate (5%)
  const [isValidScheduledAddress, setIsValidScheduledAddress] = useState(false);
  const scheduledTxChecker = useRef(null);
  
  // Multiple RPC endpoints for fallback
  const networks = {
    mainnet: [
      'https://api.mainnet-beta.solana.com',
      'https://solana-mainnet.g.alchemy.com/v2/demo'
    ],
    devnet: [
      'https://api.devnet.solana.com',
      'https://api.testnet.solana.com'
    ],
    testnet: [
      'https://api.testnet.solana.com',
      'https://api.devnet.solana.com'
    ],
  };

  // Fetch network congestion data
  const fetchNetworkStats = useCallback(async () => {
    if (isRefreshingStats) return; // Prevent concurrent fetches
    
    setIsRefreshingStats(true);
    
    try {
      const [tpsResponse, congestionResponse] = await Promise.all([
        fetch("http://localhost:8000/api/transaction-fees"),
        fetch("http://localhost:8000/api/get-predicted-congestion")
      ]);

      const tpsJson = await tpsResponse.json();
      const congestionJson = await congestionResponse.json();

      // Handle TPS data
      if (tpsJson.status === 'success' && tpsJson.data) {
        // Parse the TPS data
        const parsedData = typeof tpsJson.data === 'string' 
          ? JSON.parse(tpsJson.data) 
          : tpsJson.data;
        
        // Get the last key (most recent data point)
        const lastKey = Math.max(...Object.keys(parsedData.tps || {}));
        
        // Update TPS in networkStats
        setNetworkStats(prev => ({
          ...prev,
          tps: parsedData.tps?.[lastKey] || '0',
          blockchain: parsedData.blockchain?.[lastKey] || 'Solana',
          lastUpdated: new Date().toLocaleTimeString()
        }));
        
        // Update TPS history for potential charts
        if (parsedData.tps && lastKey) {
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
      }

      // Handle congestion data
      if (congestionJson.status === 'success' && congestionJson.data) {
        // Update networkStats with congestion data
        setNetworkStats(prev => ({
          ...prev,
          congestionLevel: congestionJson.data.congestion_level || 'Unknown',
          failurePercentage: congestionJson.data.failure_percentage + '%' || '0%',
          lastUpdated: new Date().toLocaleTimeString()
        }));
        
        // Update failure rate history for potential charts
        const failureRate = parseFloat(congestionJson.data.failure_percentage || 0);
        
        setFailureRateHistory(prev => {
          const newHistory = [...prev, failureRate];
          // Keep only the last 20 data points
          if (newHistory.length > 20) return newHistory.slice(-20);
          return newHistory;
        });
        
        // After updating the network stats, check if any scheduled transactions
        // can now be processed
        checkScheduledTransactions();
      }
    } catch (error) {
      console.error('Error fetching network stats:', error);
      
      // Fallback to estimating stats using RPC if API fails
      try {
        if (wallet) {
          const connection = new Connection(networks[network][0]);
          
          // Get performance samples to estimate TPS
          const performanceSamples = await connection.getRecentPerformanceSamples(10);
          
          // Calculate average TPS from recent samples
          let totalTPS = 0;
          let validSamples = 0;
          
          for (const sample of performanceSamples) {
            if (sample.numTransactions && sample.samplePeriodSecs) {
              totalTPS += sample.numTransactions / sample.samplePeriodSecs;
              validSamples++;
            }
          }
          
          const averageTPS = validSamples > 0 ? Math.floor(totalTPS / validSamples) : 0;
          
          // Simple congestion estimation
          const startTime = performance.now();
          await connection.getRecentBlockhash();
          const endTime = performance.now();
          const responseTime = endTime - startTime;
          
          // Simplified congestion estimation
          let congestionLevel = 'Low';
          if (responseTime > 500 || averageTPS > 1500) {
            congestionLevel = 'High';
          } else if (responseTime > 200 || averageTPS > 1000) {
            congestionLevel = 'Medium';
          }
          
          // Simplified failure percentage estimation
          let failurePercentage = '< 1%';
          if (congestionLevel === 'High') {
            failurePercentage = '10-20%';
          } else if (congestionLevel === 'Medium') {
            failurePercentage = '2-5%';
          }
          
          setNetworkStats(prev => ({
            ...prev,
            tps: averageTPS.toLocaleString(),
            congestionLevel,
            failurePercentage,
            lastUpdated: new Date().toLocaleTimeString()
          }));
          
          // Check scheduled transactions with the updated stats
          checkScheduledTransactions();
        }
      } catch (fallbackError) {
        console.error('Fallback estimation also failed:', fallbackError);
      }
    } finally {
      // Keep the refreshing indicator visible for a moment for UX
      setTimeout(() => setIsRefreshingStats(false), 10000);
    }
  }, [isRefreshingStats, network, wallet]);

  // Check if any scheduled transactions are ready to process
  const checkScheduledTransactions = async () => {
    if (!wallet || scheduledTransactions.length === 0) return;
    
    // Get current failure rate from network stats
    const currentFailureRate = parseFloat(networkStats.failurePercentage.replace('%', ''));
    if (isNaN(currentFailureRate)) return;
    
    // Find transactions that can be processed
    const readyTransactions = scheduledTransactions.filter(tx => 
      tx.status === 'Waiting' && currentFailureRate <= tx.maxFailureRate
    );
    
    if (readyTransactions.length > 0) {
      console.log(`Processing ${readyTransactions.length} scheduled transactions`);
      
      // Process each ready transaction
      for (const tx of readyTransactions) {
        // Update status to processing
        setScheduledTransactions(prev => 
          prev.map(item => 
            item.id === tx.id ? { ...item, status: 'Processing' } : item
          )
        );
        
        // Process the transaction
        try {
          const signature = await processScheduledTransaction(tx);
          
          // Update status to sent
          setScheduledTransactions(prev => 
            prev.map(item => 
              item.id === tx.id ? { 
                ...item, 
                status: 'Sent', 
                sentAt: new Date().toLocaleString(),
                signature: signature
              } : item
            )
          );
        } catch (error) {
          console.error('Error processing scheduled transaction:', error);
          
          // Update status to failed
          setScheduledTransactions(prev => 
            prev.map(item => 
              item.id === tx.id ? { ...item, status: 'Failed', error: error.message } : item
            )
          );
        }
      }
      
      // Refresh balance after processing transactions
      setTimeout(() => {
        checkBalance();
      }, 2000);
    }
  };

  // Process a single scheduled transaction
  const processScheduledTransaction = async (tx) => {
    const connection = new Connection(networks[network][0]);
    const recipientPubkey = new PublicKey(tx.recipientAddress);
    
    // Create a transfer instruction
    const transaction = new Transaction().add(
      SystemProgram.transfer({
        fromPubkey: wallet.publicKey,
        toPubkey: recipientPubkey,
        lamports: tx.amount * LAMPORTS_PER_SOL
      })
    );
    
    // Get recent blockhash
    const { blockhash } = await connection.getRecentBlockhash();
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = wallet.publicKey;
    
    // Sign transaction
    transaction.sign(wallet.keyPair);
    
    // Send transaction
    const signature = await connection.sendRawTransaction(transaction.serialize());
    
    // Confirm transaction
    await connection.confirmTransaction(signature);
    
    // Add to our transactions list
    const newTx = {
      signature: signature,
      timestamp: new Date().toLocaleString(),
      status: 'Success',
      amount: -tx.amount * LAMPORTS_PER_SOL,
      type: 'Send (Scheduled)'
    };
    
    setTransactions([newTx, ...transactions]);
    
    return signature;
  };

  // Schedule a transaction
  const scheduleTransaction = () => {
    if (!wallet || !isValidScheduledAddress || !scheduledAmount || parseFloat(scheduledAmount) <= 0) {
      setErrorMessage('Please enter a valid recipient address and amount');
      return;
    }
    
    if (parseFloat(scheduledAmount) > balance) {
      setErrorMessage('Insufficient balance');
      return;
    }
    
    const newScheduledTx = {
      id: Date.now(), // Simple unique ID
      recipientAddress: scheduledRecipient,
      amount: parseFloat(scheduledAmount),
      maxFailureRate: maxFailureRate,
      status: 'Waiting',
      createdAt: new Date().toLocaleString(),
    };
    
    setScheduledTransactions([...scheduledTransactions, newScheduledTx]);
    
    // Reset form
    setScheduledRecipient('');
    setScheduledAmount('');
    
    // Check immediately if the transaction can be processed
    checkScheduledTransactions();
  };

  // Cancel a scheduled transaction
  const cancelScheduledTransaction = (txId) => {
    setScheduledTransactions(prev => prev.filter(tx => tx.id !== txId));
  };

  // Set up automatic balance refresh when wallet changes
  useEffect(() => {
    if (wallet) {
      checkBalance();
      
      // Set up interval to refresh balance every 15 seconds
      balanceInterval.current = setInterval(() => {
        checkBalance(true);
      }, 15000);
      
      // Fetch recent transactions
      fetchTransactions();
      
      // Fetch network stats initially
      fetchNetworkStats();
    }
    
    return () => {
      if (balanceInterval.current) {
        clearInterval(balanceInterval.current);
      }
    };
  }, [wallet, network, fetchNetworkStats]);
  
  // Set up network stats refresh interval
  useEffect(() => {
    if (wallet) {
      // Set up interval to refresh network stats every 30 seconds
      const statsInterval = setInterval(() => {
        fetchNetworkStats();
      }, 30000);
      
      return () => {
        clearInterval(statsInterval);
      };
    }
  }, [wallet, fetchNetworkStats]);

  // Add card glow effect
  useEffect(() => {
    const cards = document.querySelectorAll('.solana-card');
    
    const handleMouseMove = (e, card) => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      
      card.style.setProperty('--mouse-x', `${x}%`);
      card.style.setProperty('--mouse-y', `${y}%`);
    };
    
    cards.forEach(card => {
      card.addEventListener('mousemove', (e) => handleMouseMove(e, card));
    });
    
    return () => {
      cards.forEach(card => {
        card.removeEventListener('mousemove', (e) => handleMouseMove(e, card));
      });
    };
  }, [wallet]);
  
  // Validate recipient address
  useEffect(() => {
    try {
      if (recipientAddress) {
        new PublicKey(recipientAddress);
        setIsValidAddress(true);
      } else {
        setIsValidAddress(false);
      }
    } catch (error) {
      setIsValidAddress(false);
    }
  }, [recipientAddress]);
  
  // Validate scheduled recipient address
  useEffect(() => {
    try {
      if (scheduledRecipient) {
        new PublicKey(scheduledRecipient);
        setIsValidScheduledAddress(true);
      } else {
        setIsValidScheduledAddress(false);
      }
    } catch (error) {
      setIsValidScheduledAddress(false);
    }
  }, [scheduledRecipient]);
  
  const generateWallet = () => {
    const newWallet = Keypair.generate();
    const privateKey = bs58.encode(newWallet.secretKey);
    
    setWallet({
      publicKey: newWallet.publicKey,
      publicKeyString: newWallet.publicKey.toString(),
      privateKey: privateKey,
      keyPair: newWallet,
    });
    
    setBalance(null);
    setErrorMessage('');
    setTransactions([]);
    setShowPrivateKey(false);
  };
  
  const importWallet = (event) => {
    try {
      const privateKeyInput = event.target.value;
      if (!privateKeyInput) return;
      
      const secretKey = bs58.decode(privateKeyInput);
      const importedKeypair = Keypair.fromSecretKey(secretKey);
      
      setWallet({
        publicKey: importedKeypair.publicKey,
        publicKeyString: importedKeypair.publicKey.toString(),
        privateKey: privateKeyInput,
        keyPair: importedKeypair,
      });
      
      setBalance(null);
      setErrorMessage('');
      setTransactions([]);
    } catch (error) {
      console.error('Error importing wallet:', error);
      setErrorMessage('Invalid private key format');
    }
  };
  
  const checkBalance = async (isAutoRefresh = false) => {
    if (!wallet) return;
    
    if (isAutoRefresh) {
      setIsBalanceRefreshing(true);
    } else {
      setIsLoading(true);
    }
    
    setErrorMessage('');
    
    try {
      // Use primary endpoint
      const connection = new Connection(networks[network][0]);
      const balanceInLamports = await connection.getBalance(wallet.publicKey);
      setBalance(balanceInLamports / LAMPORTS_PER_SOL);
    } catch (error) {
      console.error('Error checking balance:', error);
      
      // Try fallback endpoint
      try {
        const fallbackConnection = new Connection(networks[network][1]);
        const balanceInLamports = await fallbackConnection.getBalance(wallet.publicKey);
        setBalance(balanceInLamports / LAMPORTS_PER_SOL);
      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError);
        if (!isAutoRefresh) {
          setErrorMessage('Failed to fetch balance. Network error.');
        }
      }
    } finally {
      setIsLoading(false);
      setIsBalanceRefreshing(false);
    }
  };
  
  const fetchTransactions = async () => {
    if (!wallet) return;
    
    try {
      const connection = new Connection(networks[network][0]);
      const signatures = await connection.getSignaturesForAddress(wallet.publicKey, { limit: 10 });
      
      const txDetails = await Promise.all(
        signatures.map(async (sig) => {
          try {
            const tx = await connection.getTransaction(sig.signature, {
              maxSupportedTransactionVersion: 0
            });
            
            // Find our account index in the accounts array
            const accountIndex = tx?.transaction?.message?.accountKeys.findIndex(
              pubkey => pubkey.equals(wallet.publicKey)
            );
            
            // Initialize type as unknown
            let type = 'Unknown';
            let amount = 0;
            
            if (accountIndex !== undefined && accountIndex >= 0) {
              // Check if our balance increased or decreased
              const preBalance = tx?.meta?.preBalances[accountIndex] || 0;
              const postBalance = tx?.meta?.postBalances[accountIndex] || 0;
              amount = postBalance - preBalance;
              
              // Determine transaction type
              if (tx?.meta?.logMessages?.some(msg => msg.includes('request_airdrop'))) {
                type = 'Airdrop';
              } else if (amount > 0) {
                type = 'Receive';
              } else if (amount < 0) {
                type = 'Send';
              }
            }
            
            return {
              signature: sig.signature,
              timestamp: new Date(sig.blockTime * 1000).toLocaleString(),
              status: sig.err ? 'Failed' : 'Success',
              amount: amount,
              type: type
            };
          } catch (e) {
            console.error('Error fetching transaction details:', e);
            return {
              signature: sig.signature,
              timestamp: new Date(sig.blockTime * 1000).toLocaleString(),
              status: 'Unknown',
              amount: 0,
              type: 'Unknown'
            };
          }
        })
      );
      
      setTransactions(txDetails);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };
  
  const sendTransaction = async () => {
    if (!wallet || !isValidAddress || !sendAmount || parseFloat(sendAmount) <= 0) {
      setErrorMessage('Please enter a valid recipient address and amount');
      return;
    }
    
    if (parseFloat(sendAmount) > balance) {
      setErrorMessage('Insufficient balance');
      return;
    }
    
    setIsLoading(true);
    setErrorMessage('');
    
    try {
      const connection = new Connection(networks[network][0]);
      const recipientPubkey = new PublicKey(recipientAddress);
      
      // Create a simple transfer instruction
      const transaction = new Transaction().add(
        SystemProgram.transfer({
          fromPubkey: wallet.publicKey,
          toPubkey: recipientPubkey,
          lamports: parseFloat(sendAmount) * LAMPORTS_PER_SOL
        })
      );
      
      // Get recent blockhash
      const { blockhash } = await connection.getRecentBlockhash();
      transaction.recentBlockhash = blockhash;
      transaction.feePayer = wallet.publicKey;
      
      // Sign transaction
      transaction.sign(wallet.keyPair);
      
      // Send transaction
      const signature = await connection.sendRawTransaction(transaction.serialize());
      
      // Confirm transaction
      await connection.confirmTransaction(signature);
      
      // Add to our transactions list
      const newTx = {
        signature: signature,
        timestamp: new Date().toLocaleString(),
        status: 'Success',
        amount: -parseFloat(sendAmount) * LAMPORTS_PER_SOL,
        type: 'Send'
      };
      
      setTransactions([newTx, ...transactions]);
      
      // Reset form
      setSendAmount('');
      
      // Update balance
      setTimeout(() => {
        checkBalance();
      }, 2000);
      
    } catch (error) {
      console.error('Error sending transaction:', error);
      setErrorMessage(`Transaction failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  
  
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        alert('Copied to clipboard!');
      })
      .catch(err => {
        console.error('Failed to copy: ', err);
      });
  };
  
  const toggleShowPrivateKey = () => {
    setShowPrivateKey(!showPrivateKey);
  };
  
  const formatBalance = (bal) => {
    if (bal === null) return '0.00';
    return bal.toLocaleString(undefined, { minimumFractionDigits: 6, maximumFractionDigits: 6 });
  };
  
  const truncateAddress = (address, start = 6, end = 6) => {
    if (!address) return '';
    if (address.length <= start + end) return address;
    return `${address.slice(0, start)}...${address.slice(-end)}`;
  };
  
  return (
    <div className="solana-wallet-container">
      {/* Animated background blobs */}
      <div 
        className="blob-oval blob-oval-horizontal glow" 
        style={{
          background: 'linear-gradient(135deg, rgba(0, 255, 163, 0.4) 0%, rgba(3, 225, 255, 0.3) 100%)',
          top: '10%',
          left: '-10%',
          animation: 'float-slow 20s ease-in-out infinite'
        }}
      />
      
      <div 
        className="blob-oval blob-oval-vertical" 
        style={{
          background: 'linear-gradient(135deg, rgba(0, 255, 163, 0.2) 0%, rgba(3, 225, 255, 0.15) 100%)',
          bottom: '15%',
          right: '-8%',
          animation: 'float-medium 18s ease-in-out infinite'
        }}
      />
      
      <div 
        className="blob-pill" 
        style={{
          background: 'linear-gradient(135deg, rgba(3, 225, 255, 0.25) 0%, rgba(0, 255, 163, 0.2) 100%)',
          top: '30%',
          right: '10%',
          animation: 'float-fast 15s ease-in-out infinite'
        }}
      />
      
      <div 
        className="blob-ring" 
        style={{
          borderColor: 'rgba(0, 255, 163, 0.3)',
          bottom: '10%',
          left: '15%',
          animation: 'rotate-slow 30s linear infinite'
        }}
      />
      
      <div 
        className="blob-small-circle" 
        style={{
          background: 'rgba(0, 255, 163, 0.8)',
          top: '25%',
          left: '20%',
          animation: 'pulse 10s ease-in-out infinite'
        }}
      />
      
      <div 
        className="blob-small-circle" 
        style={{
          background: 'rgba(3, 225, 255, 0.8)',
          top: '60%',
          right: '25%',
          animation: 'pulse 8s ease-in-out infinite'
        }}
      />

      {/* Original wallet cards */}
      <div className="solana-card wallet-card">
        <div className="card-glow"></div>
        <div className="solana-card-content">
          <div className="card-header">
            <div className="icon-container">
              <i className="card-icon">💰</i>
            </div>
            <h3 className="card-title">Solana Wallet</h3>
          </div>
          
          <div className="network-selector">
            <label>Network:</label>
            <select 
              value={network} 
              onChange={(e) => setNetwork(e.target.value)}
              className="network-select"
            >
              <option value="devnet">Devnet</option>
              <option value="testnet">Testnet</option>
              <option value="mainnet">Mainnet</option>
            </select>
          </div>
          
          <div className="wallet-actions">
            <button 
              onClick={generateWallet} 
              disabled={isLoading}
              className="action-button generate-button"
            >
              Generate New Wallet
            </button>
            
            <div className="import-section">
              <input 
                type="password" 
                placeholder="Import wallet (enter private key)" 
                onChange={importWallet}
                disabled={isLoading}
                className="private-key-input"
              />
            </div>
          </div>
        </div>
      </div>
      
      {wallet && (
        <>
          {/* Add a floating blob near wallet details */}
          <div 
            className="blob-small-circle" 
            style={{
              background: 'rgba(0, 255, 163, 0.6)',
              top: '32%',
              left: '30%',
              width: '8px',
              height: '8px',
              animation: 'pulse 6s ease-in-out infinite'
            }}
          />

        <div 
            className="blob-small-circle" 
            style={{
              background: 'rgba(0, 255, 163, 0.6)',
              top: '32%',
              left: '30%',
              width: '8px',
              height: '8px',
              animation: 'pulse 6s ease-in-out infinite'
            }}
          />
          
          <div className="cards-row"
          
          style={{
            display: 'flex',
            gap: '30px',
            flexDirection: 'row',
            width: '100%'
          }}>
            <div className="solana-card wallet-details-card" style={{ flex: 1 }}>
              <div className="card-glow"></div>
              <div className="solana-card-content">
                <div className="card-header">
                  <div className="icon-container">
                    <i className="card-icon">🔑</i>
                  </div>
                  <h3 className="card-title">Wallet Details</h3>
                </div>
                
                <div className="key-display">
                  <div className="key-item">
                    <div className="key-label">Public Key:</div>
                    <div className="key-value">
                      <div className="key-text">{wallet.publicKeyString}</div>
                      <button 
                        className="copy-button"
                        onClick={() => copyToClipboard(wallet.publicKeyString)}
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                  
                  <div className="key-item">
                    <div className="key-label">Private Key:</div>
                    <div className="key-value">
                      <div className="key-text private-key-text">
                        {showPrivateKey 
                          ? wallet.privateKey 
                          : `${truncateAddress(wallet.privateKey, 5, 5)}`
                        }
                      </div>
                      <button 
                        className="copy-button"
                        onClick={() => copyToClipboard(wallet.privateKey)}
                      >
                        Copy
                      </button>
                      <button 
                        className="toggle-button"
                        onClick={toggleShowPrivateKey}
                      >
                        {showPrivateKey ? 'Hide' : 'Show'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
  
            <div className="solana-card balance-card" style={{ flex: 1 }}>
              <div className="card-glow"></div>
              <div className="solana-card-content">
                <div className="card-header">
                  <div className="icon-container">
                    <i className="card-icon">💎</i>
                  </div>
                  <h3 className="card-title">Balance</h3>
                  <button 
                    onClick={() => checkBalance()} 
                    disabled={isLoading}
                    className="refresh-button"
                  >
                    🔄
                  </button>
                </div>
                
                <div className="balance-display">
                  {isBalanceRefreshing && (
                    <div className="refresh-indicator">Refreshing...</div>
                  )}
                  
                  <div className="balance-amount">
                    <span className="balance-value">{formatBalance(balance)}</span>
                    <span className="balance-currency">SOL</span>
                  </div>
                  
                  <div className="balance-usd">
                    {balance !== null && (
                      <span>≈ ${(balance * 20).toFixed(2)} USD</span>
                    )}
                  </div>
                </div>
                
                <div className="balance-info">
                  <div className="info-item">
                    <span className="info-label">Network</span>
                    <span className="info-value">{network.charAt(0).toUpperCase() + network.slice(1)}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Last Updated</span>
                    <span className="info-value">{new Date().toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Add a blob between the cards */}
          <div 
            className="blob-pill" 
            style={{
              background: 'linear-gradient(135deg, rgba(3, 225, 255, 0.15) 0%, rgba(0, 255, 163, 0.1) 100%)',
              top: '45%',
              left: '45%',
              width: '60px',
              height: '20px',
              transform: 'rotate(45deg)',
              animation: 'float-fast 12s ease-in-out infinite'
            }}
          />
          
          {/* Network Stats Card */}
          <div className="solana-card network-stats-card">
            <div className="card-glow"></div>
            <div className="solana-card-content">
              <div className="card-header">
                <div className="icon-container">
                  <i className="card-icon">📊</i>
                </div>
                <h3 className="card-title">Network Status</h3>
                <button 
                  onClick={fetchNetworkStats} 
                  disabled={isRefreshingStats}
                  className="refresh-button"
                >
                  🔄
                </button>
              </div>
              
              <div className="network-stats-container">
                {isRefreshingStats && (
                  <div className="refresh-indicator">Refreshing...</div>
                )}
                
                <div className="stats-grid">
                  <div className="stat-item">
                    <div className="stat-label">Transactions Per Second</div>
                    <div className="stat-value">{networkStats.tps}</div>
                  </div>
                  
                  <div className="stat-item">
                    <div className="stat-label">Congestion Level</div>
                    <div className={`stat-value congestion-${networkStats.congestionLevel.toLowerCase()}`}>
                      {networkStats.congestionLevel}
                    </div>
                  </div>
                  
                  <div className="stat-item">
                    <div className="stat-label">Est. Failure Rate</div>
                    <div className="stat-value">{networkStats.failurePercentage}</div>
                  </div>
                  
                  <div className="stat-item">
                    <div className="stat-label">Blockchain</div>
                    <div className="stat-value">{networkStats.blockchain}</div>
                  </div>
                </div>
                
                <div className="stats-info">
                  <div className="info-note">
                    <i className="info-icon">ℹ️</i> 
                    Last updated: {networkStats.lastUpdated}
                  </div>
                  <div className="info-note">
                    <i className="info-icon">⚠️</i> 
                    Higher congestion may result in slower transactions or higher fees
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Add a glowing ring near send/receive area */}
          <div 
            className="blob-ring" 
            style={{
              borderColor: 'rgba(3, 225, 255, 0.2)',
              width: '100px',
              height: '100px',
              top: '65%',
              right: '12%',
              animation: 'rotate-slow 25s linear infinite reverse'
            }}
          />

          {/* Send Transaction Card */}
          <div className="solana-card send-card">
            <div className="card-glow"></div>
            <div className="solana-card-content">
              <div className="card-header">
                <div className="icon-container">
                  <i className="card-icon">📤</i>
                </div>
                <h3 className="card-title">Send SOL</h3>
              </div>
              
              <div className="send-container">
                <div className="form-group">
                  <label htmlFor="recipient">Recipient Address</label>
                  <input
                    id="recipient"
                    type="text"
                    value={recipientAddress}
                    onChange={(e) => setRecipientAddress(e.target.value)}
                    placeholder="Enter Solana address"
                    className={`form-input ${!isValidAddress && recipientAddress ? 'input-error' : ''}`}
                  />
                  {!isValidAddress && recipientAddress && (
                    <div className="input-error-message">Invalid Solana address</div>
                  )}
                </div>
                
                <div className="form-group">
                  <label htmlFor="amount">Amount (SOL)</label>
                  <div className="amount-input-group">
                    <input
                      id="amount"
                      type="number"
                      value={sendAmount}
                      onChange={(e) => setSendAmount(e.target.value)}
                      placeholder="0.00"
                      className="form-input"
                      min="0"
                      step="0.000001"
                    />
                    <span className="max-amount">
                      <button
                        className="max-button"
                        onClick={() => setSendAmount(balance ? balance.toString() : '0')}
                      >
                        MAX
                      </button>
                    </span>
                  </div>
                  <div className="balance-hint">
                    Available: {formatBalance(balance)} SOL
                  </div>
                </div>
                
                <button
                  onClick={sendTransaction}
                  disabled={!isValidAddress || !sendAmount || parseFloat(sendAmount) <= 0 || parseFloat(sendAmount) > balance || isLoading}
                  className="action-button send-button"
                >
                  Send Transaction
                </button>
              </div>
            </div>
          </div>
          
          {/* Add animated blob near schedule area */}
          <div 
            className="blob-oval blob-oval-horizontal" 
            style={{
              background: 'linear-gradient(135deg, rgba(0, 255, 163, 0.1) 0%, rgba(3, 225, 255, 0.08) 100%)',
              width: '200px',
              height: '100px',
              bottom: '15%',
              left: '25%',
              zIndex: '-1',
              animation: 'float-medium 25s ease-in-out infinite'
            }}
          />
          
          {/* Schedule Transaction Card */}
          <div className="solana-card schedule-card">
            <div className="card-glow"></div>
            <div className="solana-card-content">
              <div className="card-header">
                <div className="icon-container">
                  <i className="card-icon">⏱️</i>
                </div>
                <h3 className="card-title">Schedule Transaction</h3>
              </div>
              
              <div className="schedule-container">
                <div className="form-group">
                  <label htmlFor="scheduled-recipient">Recipient Address</label>
                  <input
                    id="scheduled-recipient"
                    type="text"
                    value={scheduledRecipient}
                    onChange={(e) => setScheduledRecipient(e.target.value)}
                    placeholder="Enter Solana address"
                    className={`form-input ${!isValidScheduledAddress && scheduledRecipient ? 'input-error' : ''}`}
                  />
                  {!isValidScheduledAddress && scheduledRecipient && (
                    <div className="input-error-message">Invalid Solana address</div>
                  )}
                </div>
                
                <div className="form-group">
                  <label htmlFor="scheduled-amount">Amount (SOL)</label>
                  <div className="amount-input-group">
                    <input
                      id="scheduled-amount"
                      type="number"
                      value={scheduledAmount}
                      onChange={(e) => setScheduledAmount(e.target.value)}
                      placeholder="0.00"
                      className="form-input"
                      min="0"
                      step="0.000001"
                    />
                    <span className="max-amount">
                      <button
                        className="max-button"
                        onClick={() => setScheduledAmount(balance ? balance.toString() : '0')}
                      >
                        MAX
                      </button>
                    </span>
                  </div>
                  <div className="balance-hint">
                    Available: {formatBalance(balance)} SOL
                  </div>
                </div>
                
                <div className="form-group">
                  <label htmlFor="max-failure-rate">Max Failure Rate (%)</label>
                  <div className="slider-container">
                    <input
                      id="max-failure-rate"
                      type="range"
                      min="0"
                      max="50"
                      step="0.5"
                      value={maxFailureRate}
                      onChange={(e) => setMaxFailureRate(parseFloat(e.target.value))}
                      className="failure-rate-slider"
                    />
                    <div className="slider-value">{maxFailureRate}%</div>
                  </div>
                  <div className="rate-hint">
                    Current network failure rate: {networkStats.failurePercentage}
                  </div>
                  <div className="rate-hint info">
                    <i className="info-icon">ℹ️</i> Transaction will execute when network failure rate drops below your set maximum
                  </div>
                </div>
                
                <button
                  onClick={scheduleTransaction}
                  disabled={!isValidScheduledAddress || !scheduledAmount || parseFloat(scheduledAmount) <= 0 || parseFloat(scheduledAmount) > balance || isLoading}
                  className="action-button schedule-button"
                >
                  Schedule Transaction
                </button>
              </div>
              
              {/* Scheduled Transactions List */}
              <div className="scheduled-transactions">
                <h4 className="section-subtitle">Scheduled Transactions</h4>
                
                {scheduledTransactions.length === 0 ? (
                  <div className="no-transactions">
                    No scheduled transactions
                  </div>
                ) : (
                  <div className="scheduled-items">
                    {scheduledTransactions.map((tx) => (
                      <div key={tx.id} className={`scheduled-item ${tx.status.toLowerCase()}`}>
                        <div className="scheduled-icon">
                          {tx.status === 'Waiting' ? '⏳' : 
                           tx.status === 'Processing' ? '⚙️' : 
                           tx.status === 'Sent' ? '✅' : '❌'}
                        </div>
                        <div className="scheduled-details">
                          <div className="scheduled-recipient">To: {truncateAddress(tx.recipientAddress)}</div>
                          <div className="scheduled-info">
                            <span className="scheduled-amount">{tx.amount.toFixed(6)} SOL</span>
                            <span className="scheduled-condition">Max Failure Rate: {tx.maxFailureRate}%</span>
                          </div>
                          <div className="scheduled-status">
                            <span className={`status-text ${tx.status.toLowerCase()}`}>{tx.status}</span>
                            <span className="scheduled-date">{tx.createdAt}</span>
                          </div>
                        </div>
                        {tx.status === 'Waiting' && (
                          <button 
                            className="cancel-button"
                            onClick={() => cancelScheduledTransaction(tx.id)}
                          >
                            Cancel
                          </button>
                        )}
                        {tx.status === 'Sent' && tx.signature && (
                          <a 
                            href={`https://explorer.solana.com/tx/${tx.signature}?cluster=${network}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="explorer-link small"
                          >
                            View
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Add some sparkle blobs near transactions */}
          <div 
            className="blob-small-circle" 
            style={{
              background: 'rgba(0, 255, 163, 0.7)',
              width: '6px',
              height: '6px',
              bottom: '5%',
              right: '10%',
              animation: 'pulse 4s ease-in-out infinite'
            }}
          />
          
          <div 
            className="blob-small-circle" 
            style={{
              background: 'rgba(3, 225, 255, 0.7)',
              width: '10px',
              height: '10px',
              bottom: '8%',
              right: '15%',
              animation: 'pulse 7s ease-in-out infinite'
            }}
          />
          
          <div className="solana-card transactions-card">
            <div className="card-glow"></div>
            <div className="solana-card-content">
              <div className="card-header">
                <div className="icon-container">
                  <i className="card-icon">📝</i>
                </div>
                <h3 className="card-title">Recent Transactions</h3>
                <button 
                  onClick={fetchTransactions} 
                  className="refresh-button"
                >
                  🔄
                </button>
              </div>
              
              <div className="transactions-list">
                {transactions.length === 0 ? (
                  <div className="no-transactions">
                    No transactions found for this wallet
                  </div>
                ) : (
                  <div className="transaction-items">
                    {transactions.map((tx, index) => (
                      <div key={index} className={`transaction-item ${tx.type.toLowerCase()}`}>
                        <div className="transaction-icon">
                          {tx.type === 'Receive' ? '↓' : 
                           tx.type === 'Send' ? '↑' : 
                           tx.type === 'Send (Scheduled)' ? '🕒' :
                           tx.type === 'Airdrop' ? '🪂' : '•'}
                        </div>
                        <div className="transaction-details">
                          <div className="transaction-type">{tx.type}</div>
                          <div className="transaction-date">{tx.timestamp}</div>
                        </div>
                        <div className="transaction-status">
                          <span className={`status-indicator ${tx.status.toLowerCase()}`}>
                            {tx.status}
                          </span>
                        </div>
                        <div className="transaction-amount">
                          {tx.amount !== 0 ? (
                          <span className={tx.type === 'Receive' || tx.type === 'Airdrop' ? 'positive-amount' : 'negative-amount'}>
                              {tx.type === 'Receive' || tx.type === 'Airdrop' ? '+' : '-'} 
                              {Math.abs(tx.amount / LAMPORTS_PER_SOL).toFixed(6)} SOL
                          </span>
                          ) : (
                          '0 SOL'
                          )}
                        </div>
                        <div className="transaction-signature">
                          <a 
                            href={`https://explorer.solana.com/tx/${tx.signature}?cluster=${network}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="explorer-link"
                          >
                            {truncateAddress(tx.signature, 4, 4)}
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
      
      {errorMessage && <div className="error-message">{errorMessage}</div>}
      {isLoading && <div className="loading-overlay">Processing...</div>}
    </div>
  );
}

export default EnhancedSolanaWallet;