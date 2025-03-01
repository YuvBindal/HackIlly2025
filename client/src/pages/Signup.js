import { usePrivy } from '@privy-io/react-auth';
import React, { useEffect, useState } from 'react';
import { FaEnvelope, FaWallet } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import './Signup.css';

const Signup = () => {
    const { login, logout, authenticated, user } = usePrivy();
    const navigate = useNavigate();
    const [notifications, setNotifications] = useState({
        nftAlerts: false,
        congestionWarnings: false,
        priceAlerts: false
    });

    // Redirect to dashboard if authenticated
    useEffect(() => {
        if (authenticated) {
            navigate('/dashboard');
        }
    }, [authenticated, navigate]);

    const handleNotificationChange = (type) => {
        setNotifications(prev => ({
            ...prev,
            [type]: !prev[type]
        }));
    };

    // Helper function to truncate wallet address
    const truncateAddress = (address) => {
        if (!address) return '';
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    };

    // If not authenticated, show login page
    if (!authenticated) {
        return (
            <div className="signup-container">
                <div className="auth-section">
                    <div className="welcome-header">
                        <h1>Welcome to SolanaHive</h1>
                        <h4>Connect your wallet or sign in with email to get started</h4>
                    </div>
                    <div className="auth-buttons">
                        <button 
                            className="auth-button wallet-button"
                            onClick={() => login({ loginMethod: 'wallet' })}
                        >
                            <FaWallet /> Connect Wallet
                        </button>
                        <button 
                            className="auth-button email-button"
                            onClick={() => login({ loginMethod: 'email' })}
                        >
                            <FaEnvelope /> Continue with Email
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // The rest of the component won't render as we're redirecting
    return null;
};

export default Signup;
