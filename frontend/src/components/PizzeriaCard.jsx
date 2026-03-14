import { useNavigate } from "react-router-dom";
import { Star, MapPin, Heart } from "lucide-react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";

const PizzeriaCard = ({ pizzeria, onFavoriteChange }) => {
  const navigate = useNavigate();
  const { user, token, isAuthenticated, updateUserFavorites } = useAuth();
  
  const isFavorite = user?.favorites?.includes(pizzeria.id);

  const handleFavoriteClick = async (e) => {
    e.stopPropagation();
    
    if (!isAuthenticated) {
      toast.error("Please login to save favorites");
      navigate("/auth");
      return;
    }

    try {
      if (isFavorite) {
        await axios.delete(`${API}/favorites/${pizzeria.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const newFavorites = user.favorites.filter(id => id !== pizzeria.id);
        updateUserFavorites(newFavorites);
        toast.success("Removed from favorites");
      } else {
        await axios.post(`${API}/favorites/${pizzeria.id}`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const newFavorites = [...(user.favorites || []), pizzeria.id];
        updateUserFavorites(newFavorites);
        toast.success("Added to favorites!");
      }
      if (onFavoriteChange) onFavoriteChange();
    } catch (error) {
      toast.error("Failed to update favorites");
    }
  };

  return (
    <div 
      className="pizzeria-card cursor-pointer group"
      onClick={() => navigate(`/pizzeria/${pizzeria.id}`)}
      data-testid={`pizzeria-card-${pizzeria.id}`}
    >
      {/* Image */}
      <div className="relative aspect-[4/3] overflow-hidden">
        <img 
          src={pizzeria.photos?.main} 
          alt={pizzeria.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
        
        {/* Style Badge */}
        <div className="absolute top-3 left-3">
          <span className={pizzeria.pizza_style === "neapolitan" ? "badge-neapolitan" : "badge-roman"}>
            {pizzeria.pizza_style}
          </span>
        </div>
        
        {/* Favorite Button */}
        <button
          onClick={handleFavoriteClick}
          className="absolute top-3 right-3 w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-md transition-all hover:scale-110"
          data-testid={`favorite-btn-${pizzeria.id}`}
        >
          <Heart 
            size={20} 
            className={isFavorite ? "fill-tomato text-tomato" : "text-ink/60"}
          />
        </button>

        {/* Recommended Badge */}
        {pizzeria.recommended_by?.length > 0 && (
          <div className="absolute bottom-3 left-3 recommended-badge">
            <Star size={12} className="fill-olive text-olive" />
            <span>Recommended</span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-serif text-lg font-semibold text-ink mb-1 group-hover:text-tomato transition-colors">
          {pizzeria.name}
        </h3>
        
        <div className="flex items-center gap-2 text-sm text-stone mb-2">
          <MapPin size={14} />
          <span>{pizzeria.neighborhood}</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Star size={16} className="fill-gold text-gold" />
            <span className="font-bold text-ink">{pizzeria.google_rating}</span>
            <span className="text-stone text-sm">({pizzeria.review_count})</span>
          </div>
        </div>

        {/* Mini Badges */}
        <div className="flex flex-wrap gap-1 mt-3">
          {pizzeria.badges?.slice(0, 2).map((badge, index) => (
            <span 
              key={index}
              className="text-xs px-2 py-1 bg-paper text-ink/70 rounded-full"
            >
              {badge}
            </span>
          ))}
          {pizzeria.badges?.length > 2 && (
            <span className="text-xs px-2 py-1 bg-paper text-ink/70 rounded-full">
              +{pizzeria.badges.length - 2}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default PizzeriaCard;
