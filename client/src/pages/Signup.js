import { usePrivy } from '@privy-io/react-auth';
import React, { useEffect, useState, useRef } from 'react';
import { FaEnvelope, FaWallet, FaPlay, FaChartLine, FaRocket, FaShieldAlt } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import './Signup.css';
import logo from '../assets/logo.png';

const Signup = () => {
    const { login, logout, authenticated, user } = usePrivy();
    const navigate = useNavigate();
    const videoRef = useRef(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [sparkles, setSparkles] = useState([]);
    const containerRef = useRef(null);
    
    // Redirect to dashboard if authenticated
    useEffect(() => {
        if (authenticated) {
            navigate('/dashboard');
        }
    }, [authenticated, navigate]);

    // Create sparkle animation
    useEffect(() => {
        if (!containerRef.current) return;
        
        // Create initial sparkles
        const initialSparkles = [];
        for (let i = 0; i < 30; i++) {
            initialSparkles.push({
                id: i,
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 4}s`,
                size: `${Math.random() * 3 + 1}px`,
                opacity: Math.random() * 0.7 + 0.3
            });
        }
        setSparkles(initialSparkles);
    }, []);

    // Handle scroll-based parallax effect
    useEffect(() => {
        const handleScroll = () => {
            const scrollY = window.scrollY;
            // Apply parallax effect to elements with .parallax-layer class
            document.querySelectorAll('.parallax-layer').forEach(el => {
                const speed = el.classList.contains('parallax-deep') ? 0.1 :
                            el.classList.contains('parallax-medium') ? 0.05 : 0.02;
                el.style.transform = `translateY(${scrollY * speed}px)`;
            });
        };

        window.addEventListener('scroll', handleScroll);
        
        return () => {
            window.removeEventListener('scroll', handleScroll);
        };
    }, []);

    const toggleVideo = () => {
        if (videoRef.current) {
            if (isPlaying) {
                videoRef.current.pause();
            } else {
                videoRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    // If not authenticated, show landing page with login
    if (!authenticated) {
        return (
            <div className="signup-container" ref={containerRef}>
                {/* Enhanced Animated Background */}
                <div className="animated-background">
                    {/* Original circular blobs */}
                    <div className="blob blob-1"></div>
                    <div className="blob blob-2"></div>
                    <div className="blob blob-3"></div>
                    <div className="blob blob-4"></div>
                    
                    {/* New oval shapes */}
                    <div className="blob-oval blob-oval-horizontal" 
                         style={{ 
                             background: 'var(--neon-cyan)',
                             top: '15%', 
                             left: '5%',
                             animation: 'float-slow 20s ease-in-out infinite'
                         }}>
                    </div>
                    
                    <div className="blob-oval blob-oval-vertical" 
                         style={{ 
                             background: 'var(--electric-purple)',
                             bottom: '10%', 
                             right: '8%',
                             animation: 'float-medium 18s ease-in-out infinite'
                         }}>
                    </div>

                    
                    
                    {/* Pill shape */}
                    <div className="blob-oval blob-pill" 
                         style={{ 
                             background: 'var(--bright-magenta)',
                             top: '70%', 
                             left: '15%',
                             animation: 'float-fast 15s ease-in-out infinite'
                         }}>
                    </div>

                    
                    
                    {/* Small glowing circle */}
                    <div className="blob-small-circle glow" 
                         style={{ 
                             background: 'var(--neon-cyan)',
                             top: '35%', 
                             left: '60%',
                             animation: 'pulse 8s ease-in-out infinite'
                         }}>
                    </div>
                    
                    {/* Ring shape */}
                    <div className="blob-ring" 
                         style={{ 
                             borderColor: 'var(--neon-cyan)',
                             top: '20%', 
                             right: '20%',
                             animation: 'rotate-slow 30s linear infinite'
                         }}>
                    </div>
                    
                    {/* Another small accent circle like in your 2nd screenshot */}
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
                
                {/* Sparkles */}
                {sparkles.map(sparkle => (
                    <div 
                        key={sparkle.id} 
                        className="sparkle" 
                        style={{
                            left: sparkle.left,
                            top: sparkle.top,
                            animationDelay: sparkle.animationDelay,
                            width: sparkle.size,
                            height: sparkle.size,
                            opacity: sparkle.opacity
                        }}
                    />
                ))}
                
                {/* Floating 3D Elements */}
                <div className="floating-element" style={{ width: '80px', height: '80px', top: '20%', left: '10%' }}></div>
                <div className="floating-element" style={{ width: '50px', height: '50px', top: '60%', right: '15%', animationDelay: '2s' }}></div>
                <div className="floating-element" style={{ width: '30px', height: '30px', bottom: '20%', left: '20%', animationDelay: '4s' }}></div>
                
                {/* Header */}
                {/* <header className="header">
                    <img src={logo} alt="HiveSolana Logo" className="logo" />
                    <div className="nav-links">
                        <a href="#features">Features</a>
                        <a href="#demo">Demo</a>
                        <a href="#about">About</a>
                    </div>
                </header> */}
                
                {/* Hero Section */}
                <section className="hero-section parallax-layer parallax-shallow">
                    <div className="hero-content">
                        <h1 className="hero-title">Optimize Your Solana Experience</h1>
                        <p className="hero-subtitle">
                            HiveSolana predicts network congestion, automates transactions, and detects security vulnerabilities to help you navigate the Solana blockchain with confidence.
                        </p>
                        <div className="hero-buttons">
                            <button className="hero-button primary-button">Learn More</button>
                            <button className="hero-button secondary-button">View Docs</button>
                        </div>
                    </div>
                </section>
                
                {/* Auth Section */}
                <section className="auth-section">
                    <div className="welcome-header">
                        <h1>Welcome to HiveSolana</h1>
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
                </section>
                
                {/* Features Section */}
                <section id="features" className="features-section parallax-layer parallax-medium">
                    <h2 className="section-title">Powerful Features</h2>
                    <div className="features-grid">
                        <div className="feature-card">
                            <FaChartLine className="feature-icon" />
                            <h3 className="feature-title">Network Congestion Prediction</h3>
                            <p className="feature-description">
                                Real-time AI-powered analytics that predict Solana network congestion to help you time your transactions perfectly.
                            </p>
                        </div>
                        <div className="feature-card">
                            <FaRocket className="feature-icon" />
                            <h3 className="feature-title">Transaction Scheduler</h3>
                            <p className="feature-description">
                                Schedule transactions to execute automatically during low-congestion periods for optimal fees and success rates.
                            </p>
                        </div>
                        <div className="feature-card">
                            <FaShieldAlt className="feature-icon" />
                            <h3 className="feature-title">Smart Contract Security</h3>
                            <p className="feature-description">
                                Scan smart contracts for vulnerabilities before interacting with them to protect your assets.
                            </p>
                        </div>
                    </div>
                </section>
                
                {/* Demo Section */}
                <section id="demo" className="demo-section parallax-layer parallax-deep">
                    <h2 className="section-title">See HiveSolana in Action</h2>
                    <div className="demo-card">
                        <div className="video-container">
                            <video ref={videoRef} className="demo-video" poster="../assets/video-thumbnail.jpg">
                                <source src="../assets/demo.mp4" type="video/mp4" />
                                Your browser does not support the video tag.
                            </video>
                            <button 
                                className="play-button"
                                onClick={toggleVideo}
                            >
                                <FaPlay />
                            </button>
                        </div>
                        <div className="demo-content">
                            <h3 className="demo-title">Navigate Solana with Confidence</h3>
                            <p className="demo-description">
                                Watch how HiveSolana helps you avoid network congestion, optimize transaction fees, and interact securely with smart contracts on the Solana blockchain.
                            </p>
                            <button className="demo-button">Get Started Now</button>
                        </div>
                    </div>
                </section>
                
                {/* Footer */}
                <footer className="footer">
                    <div className="footer-content">
                        <div>
                            <img src={logo} alt="HiveSolana Logo" className="footer-logo" />
                            <p>Making Solana accessible and efficient for everyone.</p>
                        </div>
                        <div className="footer-links">
                            <div className="footer-column">
                                <h4>Product</h4>
                                <a href="#features">Features</a>
                                <a href="#demo">Demo</a>
                                <a href="#pricing">Pricing</a>
                            </div>
                            <div className="footer-column">
                                <h4>Resources</h4>
                                <a href="#docs">Documentation</a>
                                <a href="#blog">Blog</a>
                                <a href="#help">Help Center</a>
                            </div>
                            <div className="footer-column">
                                <h4>Company</h4>
                                <a href="#about">About</a>
                                <a href="#careers">Careers</a>
                                <a href="#contact">Contact</a>
                            </div>
                        </div>
                    </div>
                    <div className="footer-bottom">
                        <p>© 2025 HiveSolana. All rights reserved.</p>
                    </div>
                </footer>
            </div>
        );
    }

    // The rest of the component won't render as we're redirecting
    return null;
};

export default Signup;