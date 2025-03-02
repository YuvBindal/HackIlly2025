// App.js
import { PrivyProvider } from "@privy-io/react-auth";
import React from "react";
import { Route, BrowserRouter as Router, Routes, Outlet } from "react-router-dom";
import "./App.css";
import Dashboard from "./pages/Dashboard";
import Signup from "./pages/Signup";
import EnhancedSolanaWallet from "./pages/Scheduler";
import SecureScan from "./pages/SecureScan";
import Layout from "./components/Layout";

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
        <Routes>
          {/* Signup page without navbar */}
          <Route path="/" element={<Signup />} />
          
          {/* Routes with navbar */}
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/scheduler" element={<EnhancedSolanaWallet />} />
            <Route path="/securescan" element={<SecureScan />} />
            
          </Route>
        </Routes>
      </Router>
    </PrivyProvider>
  );
}

export default App;