import { Star, MapPin } from "lucide-react";
import { useNavigate } from "react-router-dom";

const MapPopup = ({ pizzeria }) => {
  const navigate = useNavigate();

  return (
    <div 
      className="w-64 cursor-pointer"
      onClick={() => navigate(`/pizzeria/${pizzeria.id}`)}
      data-testid={`map-popup-${pizzeria.id}`}
    >
      {/* Image */}
      <div className="h-32 overflow-hidden rounded-t-lg">
        <img 
          src={pizzeria.photos?.main}
          alt={pizzeria.name}
          className="w-full h-full object-cover"
        />
      </div>

      {/* Content */}
      <div className="p-3 bg-white rounded-b-lg">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-serif font-semibold text-ink text-sm leading-tight">
            {pizzeria.name}
          </h3>
          <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full ${
            pizzeria.pizza_style === "neapolitan" 
              ? "bg-tomato/10 text-tomato" 
              : "bg-terracotta/10 text-terracotta"
          }`}>
            {pizzeria.pizza_style}
          </span>
        </div>

        <div className="flex items-center gap-1 text-xs text-stone mt-1">
          <MapPin size={12} />
          <span>{pizzeria.neighborhood}</span>
        </div>

        <div className="flex items-center gap-2 mt-2">
          <div className="flex items-center gap-1">
            <Star size={14} className="fill-gold text-gold" />
            <span className="font-bold text-ink text-sm">{pizzeria.google_rating}</span>
          </div>
          <span className="text-xs text-stone">({pizzeria.review_count} reviews)</span>
        </div>

        <button 
          className="w-full mt-3 py-2 bg-tomato text-white text-sm font-semibold rounded-full hover:bg-tomato-hover transition-colors"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/pizzeria/${pizzeria.id}`);
          }}
        >
          View Details
        </button>
      </div>
    </div>
  );
};

export default MapPopup;
