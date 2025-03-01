import { PrivyProvider } from "@privy-io/react-auth";
import React from "react";
import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import "./App.css";
import Dashboard from "./pages/Dashboard";
import Signup from "./pages/Signup";

function App() {
    return (
        <PrivyProvider
            appId="cm6o3jyqn0169wfqaz2gnityb"
            config={{
                loginMethods: ["email", "wallet", "google"],
                appearance: {
                    theme: "light",
                    accentColor: "#676FFF",
                },
            }}
        >
            <Router>
                <div className="app">
                    <Routes>
                        <Route path="/" element={<Signup />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                    </Routes>
                </div>
            </Router>
        </PrivyProvider>
    );
}

export default App;
