// components/Layout.jsx
import React from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { usePrivy } from "@privy-io/react-auth";
import Navbar from "./navbar";

const Layout = () => {
  const { logout } = usePrivy();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/");
    } catch (error) {
      console.error("Error during logout:", error);
    }
  };

  return (
    <>
      <Navbar handleLogout={handleLogout} />
      <main>
        <Outlet />
      </main>
    </>
  );
};

export default Layout;