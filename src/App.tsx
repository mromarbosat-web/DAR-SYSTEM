import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import Home from "./pages/Home";
import Shortcuts from "./pages/Shortcuts";
import Protection from "./pages/Protection";
import Economy from "./pages/Economy";
import Logs from "./pages/Logs";
import Login from "./pages/Login";

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen bg-black text-right font-['Cairo']" dir="rtl">
      <Navbar />
      <Sidebar />
      <main className="pt-24 pb-12 px-4 md:px-8 md:mr-64 transition-all">
        <div className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/shortcuts" element={<Shortcuts />} />
            <Route path="/protection" element={<Protection />} />
            <Route path="/economy" element={<Economy />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
};

export default App;
