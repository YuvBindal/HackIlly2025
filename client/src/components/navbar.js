import { useState } from "react";
import logo from "../assets/Blogo.png"; // Make sure you place your logo inside the assets folder
import "./navbar.css";


const Navbar = ({ handleLogout }) => {
    const [menuOpen, setMenuOpen] = useState(false);

    return (
        <nav className="navbar">
            <div className="navbar-container">
                {/* Left Section - Logo & Project Name */}
                <div className="navbar-left">
                    <img
                        src={logo}
                        alt="Sol Hive Logo"
                        className="navbar-logo"
                    />
                    <span className="navbar-title">Sol Hive</span>
                </div>

                {/* Right Section - Connect Wallet & Logout */}
                <div className="navbar-right">
                    <button className="connect-wallet">Connect Wallet</button>
                    <button className="logout-button" onClick={handleLogout}>Logout</button>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;