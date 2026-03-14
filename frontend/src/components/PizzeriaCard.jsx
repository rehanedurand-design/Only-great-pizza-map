import { useNavigate } from "react-router-dom";
import { Star, MapPin, Heart, Clock, Users } from "lucide-react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";

const WaitTimeBadge = ({ waitTime }) => {
  if (!waitTime || !waitTime.is_open) {
    return (
      <div className="flex items-center gap-1 text-xs px-2 py-1 bg-stone/10 text-stone font-heading uppercase tracking-wider">
        <Clock size={12} />
        <span>Closed</span>
      </div>
    );
  }

  const { current_wait, crowd_level } = waitTime;
  
  const colors = {
    low: "bg-olive/10 text-olive",
    moderate: "bg-gold/20 text-terracotta",
    busy: "bg-brick/10 text-brick",
    very_busy: "bg-brick/20 text-brick"
  };

  const labels = {
    low: "No wait",
    moderate: `~${current_wait} min`,
    busy: `~${current_wait} min`,
    very_busy: `~${current_wait}+ min`
  };

  return (
    <div className={`flex items-center gap-1 text-xs px-2 py-1 font-heading uppercase tracking-wider ${colors[crowd_level]}`}>
      <Users size={12} />
      <span>{labels[crowd_level]}</span>
    </div>
  );
};

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
      {/* Image with grayscale hover effect */}
      <div className="relative aspect-[4/3] overflow-hidden">
        <img 
          src={pizzeria.photos?.main} 
          alt={pizzeria.name}
          className="w-full h-full object-cover card-image-grayscale group-hover:scale-105 transition-all duration-500"
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
          className="absolute top-3 right-3 w-10 h-10 bg-white/95 flex items-center justify-center transition-all hover:bg-brick hover:text-white"
          data-testid={`favorite-btn-${pizzeria.id}`}
        >
          <Heart 
            size={18} 
            className={isFavorite ? "fill-brick text-brick group-hover:fill-white group-hover:text-white" : "text-ink/60"}
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
        <h3 className="font-heading text-lg uppercase tracking-wide text-ink mb-1 group-hover:text-brick transition-colors">
          {pizzeria.name}
        </h3>
        
        <div className="flex items-center gap-2 text-sm text-stone mb-3">
          <MapPin size={14} />
          <span>{pizzeria.neighborhood}</span>
          {pizzeria.distance && (
            <>
              <span>·</span>
              <span className="text-olive font-medium">{pizzeria.distance} km</span>
            </>
          )}
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Star size={16} className="fill-gold text-gold" />
            <span className="font-bold text-ink">{pizzeria.google_rating}</span>
            <span className="text-stone text-sm">({pizzeria.review_count})</span>
          </div>
          <WaitTimeBadge waitTime={pizzeria.wait_time} />
        </div>

        {/* Mini Badges */}
        <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-stone/10">
          {pizzeria.badges?.slice(0, 2).map((badge, index) => (
            <span 
              key={index}
              className="text-xs px-2 py-1 bg-cream text-ink/70 font-heading uppercase tracking-wider"
            >
              {badge}
            </span>
          ))}
          {pizzeria.badges?.length > 2 && (
            <span className="text-xs px-2 py-1 bg-cream text-ink/70 font-heading uppercase tracking-wider">
              +{pizzeria.badges.length - 2}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default PizzeriaCard;
