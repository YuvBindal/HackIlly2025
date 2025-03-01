import React, { useState, useEffect, useRef } from 'react';
import { Keypair, Connection, LAMPORTS_PER_SOL, PublicKey, clusterApiUrl } from '@solana/web3.js';
import bs58 from 'bs58';
import './Scheduler.css';

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
  
  // Multiple RPC endpoints for fallback
  const networks = {
    mainnet: [
      'https://api.mainnet-beta.solana.com',
      'https://solana-mainnet.g.alchemy.com/v2/demo'
    ],
    devnet: [
      'https://api.devnet.solana.com',
      'https://api.testnet.solana.com' // Using testnet as fallback for devnet
    ],
    testnet: [
      'https://api.testnet.solana.com',
      'https://api.devnet.solana.com' // Using devnet as fallback for testnet
    ],
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
    }
    
    return () => {
      if (balanceInterval.current) {
        clearInterval(balanceInterval.current);
      }
    };
  }, [wallet, network]);

  // Add this to your EnhancedSolanaWallet component
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
    }, [wallet]); // Re-run when wallet changes as new cards may be added
  
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
            
            return {
              signature: sig.signature,
              timestamp: new Date(sig.blockTime * 1000).toLocaleString(),
              status: sig.err ? 'Failed' : 'Success',
              amount: tx?.meta?.postBalances[0] - tx?.meta?.preBalances[0],
              type: tx?.meta?.postBalances[0] > tx?.meta?.preBalances[0] ? 'Receive' : 'Send'
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
          <div className="solana-card wallet-details-card">
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
          
          <div className="solana-card balance-card">
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
                          {tx.type === 'Receive' ? '↓' : tx.type === 'Send' ? '↑' : '•'}
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
                          {tx.amount !== 0 ? 
                            `${tx.type === 'Receive' ? '+' : '-'} ${Math.abs(tx.amount / LAMPORTS_PER_SOL).toFixed(6)} SOL` : 
                            '0 SOL'
                          }
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