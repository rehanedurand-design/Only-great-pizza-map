import { useEffect, useState, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";

// Pages
import MapView from "@/pages/MapView";
import Explore from "@/pages/Explore";
import Favorites from "@/pages/Favorites";
import PizzaLists from "@/pages/PizzaLists";
import PizzeriaDetail from "@/pages/PizzeriaDetail";
import Auth from "@/pages/Auth";
import Navigation from "@/components/Navigation";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Auth Context
export const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setUser(response.data);
        } catch (error) {
          console.error("Auth init error:", error);
          localStorage.removeItem("token");
          setToken(null);
        }
      }
      setLoading(false);
    };
    initAuth();
  }, [token]);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { access_token, user: userData } = response.data;
    localStorage.setItem("token", access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (email, password, name) => {
    const response = await axios.post(`${API}/auth/register`, { email, password, name });
    const { access_token, user: userData } = response.data;
    localStorage.setItem("token", access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  const updateUserFavorites = (favorites) => {
    setUser(prev => prev ? { ...prev, favorites } : null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      loading, 
      login, 
      register, 
      logout,
      updateUserFavorites,
      isAuthenticated: !!user 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route wrapper
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="animate-spin-slow">
          <span className="text-4xl">🍕</span>
        </div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  
  return children;
};

function AppContent() {
  const { loading } = useAuth();
  const [dataSeeded, setDataSeeded] = useState(false);

  useEffect(() => {
    const seedData = async () => {
      try {
        await axios.post(`${API}/seed`);
        setDataSeeded(true);
      } catch (error) {
        console.log("Seed info:", error.response?.data?.message || "Data may already exist");
        setDataSeeded(true);
      }
    };
    seedData();
  }, []);

  if (loading || !dataSeeded) {
    return (
      <div className="min-h-screen bg-cream flex flex-col items-center justify-center gap-4">
        <div className="animate-spin-slow">
          <span className="text-6xl">🍕</span>
        </div>
        <p className="font-hand text-xl text-ink/60">Loading the best pizzas in Paris...</p>
      </div>
    );
  }

  return (
    <div className="app-container bg-cream">
      <Routes>
        <Route path="/" element={<MapView />} />
        <Route path="/explore" element={<Explore />} />
        <Route path="/pizzeria/:id" element={<PizzeriaDetail />} />
        <Route path="/auth" element={<Auth />} />
        <Route 
          path="/favorites" 
          element={
            <ProtectedRoute>
              <Favorites />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/lists" 
          element={
            <ProtectedRoute>
              <PizzaLists />
            </ProtectedRoute>
          } 
        />
      </Routes>
      <Navigation />
      <Toaster position="top-center" richColors />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
