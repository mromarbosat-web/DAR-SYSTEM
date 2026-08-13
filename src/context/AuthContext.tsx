import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

interface User {
  id: string;
  username: string;
  avatar: string;
}

interface Guild {
  id: string;
  name: string;
  icon: string;
  permissions: string;
}

interface AuthContextType {
  user: User | null;
  guilds: Guild[];
  loading: boolean;
  selectedGuildId: string | null;
  setSelectedGuildId: (id: string | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [guilds, setGuilds] = useState<Guild[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedGuildId, setSelectedGuildId] = useState<string | null>(localStorage.getItem("selectedGuildId"));

  useEffect(() => {
    const fetchMe = async () => {
      try {
        const res = await axios.get("/api/auth/me");
        setUser(res.data.user);
        setGuilds(res.data.guilds);
        if (res.data.guilds.length > 0 && !selectedGuildId) {
          setSelectedGuildId(res.data.guilds[0].id);
        }
      } catch (e) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    fetchMe();
  }, []);

  useEffect(() => {
    if (selectedGuildId) {
      localStorage.setItem("selectedGuildId", selectedGuildId);
    }
  }, [selectedGuildId]);

  const logout = async () => {
    await axios.post("/api/auth/logout");
    setUser(null);
    setGuilds([]);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ user, guilds, loading, selectedGuildId, setSelectedGuildId, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};
