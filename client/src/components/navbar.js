import { useState } from "react";
import logo from "../assets/Blogo.png";
import "./navbar.css";
import { useNavigate } from "react-router-dom";

const Navbar = ({ handleLogout }) => {
    const [menuOpen, setMenuOpen] = useState(false);
    const navigate = useNavigate();

    // Navigation handlers
    const goToDashboard = () => navigate("/dashboard");
    const goToScheduler = () => navigate("/scheduler");
    const goToSecureScan = () => navigate("/securescan");

    return (
        <nav className="navbar">
            <div className="navbar-container">
                {/* Left Section - Logo & Project Name (clickable to go to dashboard) */}
                <div className="navbar-left" onClick={goToDashboard} style={{ cursor: 'pointer' }}>
                    <img
                        src={logo}
                        alt="SolArc Logo"
                        className="navbar-logo"
                    />
                    <span className="navbar-title">Solarc</span>
                </div>

                {/* Middle Section - Navigation Links */}
                <div className="navbar-center">
                    <ul className="nav-links">
                        <li className="nav-item" onClick={goToDashboard}>Dashboard</li>
                        <li className="nav-item" onClick={goToScheduler}>Scheduler</li>
                        <li className="nav-item" onClick={goToSecureScan}>SolScan</li>
                    </ul>
                </div>

                {/* Right Section - Logout */}
                <div className="navbar-right">
                    <button className="logout-button" onClick={handleLogout}>Logout</button>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;