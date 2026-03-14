import { useState, useEffect } from "react";
import axios from "axios";
import { API, useAuth } from "@/App";
import PizzeriaCard from "@/components/PizzeriaCard";
import { Heart, LogIn } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

const Favorites = () => {
  const navigate = useNavigate();
  const { token, isAuthenticated, user } = useAuth();
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated) {
      fetchFavorites();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated, user?.favorites]);

  const fetchFavorites = async () => {
    try {
      const response = await axios.get(`${API}/favorites`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFavorites(response.data);
    } catch (error) {
      console.error("Error fetching favorites:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-cream flex flex-col items-center justify-center px-6 pb-24" data-testid="favorites-page">
        <Heart size={64} className="text-stone/30 mb-4" />
        <h1 className="font-serif text-2xl font-bold text-ink mb-2">Your Favorites</h1>
        <p className="text-stone text-center mb-6">
          Sign in to save your favorite pizzerias and build your personal pizza map.
        </p>
        <Button
          onClick={() => navigate("/auth")}
          className="bg-tomato hover:bg-tomato-hover text-white"
          data-testid="favorites-login-btn"
        >
          <LogIn size={18} className="mr-2" />
          Sign In
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream pb-24" data-testid="favorites-page">
      {/* Header */}
      <header className="bg-white border-b border-stone/10 sticky top-0 z-50 px-4 py-4">
        <h1 className="font-serif text-2xl font-bold text-ink">Your Favorites</h1>
        <p className="text-sm text-stone">
          {favorites.length} saved pizzeria{favorites.length !== 1 ? "s" : ""}
        </p>
      </header>

      {/* Content */}
      <div className="px-4 py-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="pizzeria-card animate-pulse">
                <div className="aspect-[4/3] bg-stone/20" />
                <div className="p-4 space-y-3">
                  <div className="h-5 bg-stone/20 rounded w-3/4" />
                  <div className="h-4 bg-stone/20 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : favorites.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {favorites.map((pizzeria) => (
              <PizzeriaCard 
                key={pizzeria.id} 
                pizzeria={pizzeria}
                onFavoriteChange={fetchFavorites}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <Heart size={64} className="mx-auto text-stone/30 mb-4" />
            <h2 className="font-serif text-xl text-ink mb-2">No favorites yet</h2>
            <p className="text-stone mb-6">
              Start exploring and save pizzerias you love!
            </p>
            <Button
              onClick={() => navigate("/explore")}
              className="bg-tomato hover:bg-tomato-hover text-white"
              data-testid="explore-btn"
            >
              Explore Pizzerias
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Favorites;
