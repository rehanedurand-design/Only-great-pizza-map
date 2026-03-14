import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { API, useAuth } from "@/App";
import { 
  ChevronLeft, 
  Star, 
  MapPin, 
  Heart, 
  Share2, 
  ExternalLink,
  Clock,
  Wine,
  Award,
  ChefHat,
  Wheat,
  Leaf,
  Plus,
  Users,
  RefreshCw
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";

const badgeIcons = {
  "Best Margherita": Award,
  "Great Wine List": Wine,
  "Italian Owners": ChefHat,
  "Italian Pizzaiolo": ChefHat,
  "Sourdough Dough": Wheat,
  "Famous Tiramisu": Award,
  "Gluten-Free Option": Leaf,
  "Roman Style": Award,
  "Family Recipe": Heart,
  "Seasonal Menu": Leaf,
};

const WaitTimeCard = ({ waitTime, onRefresh, refreshing }) => {
  if (!waitTime) return null;

  const { is_open, current_wait, crowd_level, last_updated } = waitTime;

  if (!is_open) {
    return (
      <div className="bg-stone/10 rounded-xl p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock size={20} className="text-stone" />
            <span className="font-semibold text-stone">Currently Closed</span>
          </div>
        </div>
        <p className="text-sm text-stone mt-1">Opens at 11:00 AM</p>
      </div>
    );
  }

  const colors = {
    low: { bg: "bg-olive/10", text: "text-olive", label: "Not busy" },
    moderate: { bg: "bg-gold/20", text: "text-terracotta", label: "Moderately busy" },
    busy: { bg: "bg-tomato/10", text: "text-tomato", label: "Busy" },
    very_busy: { bg: "bg-tomato/20", text: "text-tomato", label: "Very busy" }
  };

  const style = colors[crowd_level] || colors.moderate;

  return (
    <div className={`${style.bg} rounded-xl p-4 mb-6`} data-testid="wait-time-card">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Users size={20} className={style.text} />
          <span className={`font-semibold ${style.text}`}>{style.label}</span>
        </div>
        <button 
          onClick={onRefresh}
          disabled={refreshing}
          className="p-2 hover:bg-white/50 rounded-full transition-colors"
          data-testid="refresh-wait-time-btn"
        >
          <RefreshCw size={16} className={`text-ink/60 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>
      
      <div className="flex items-baseline gap-1">
        <span className={`text-3xl font-bold ${style.text}`}>
          {current_wait === 0 ? "No" : `~${current_wait}`}
        </span>
        <span className={`text-lg ${style.text}`}>
          {current_wait === 0 ? "wait" : "min wait"}
        </span>
      </div>
      
      <p className="text-xs text-stone mt-2">
        Updated {new Date(last_updated).toLocaleTimeString()}
      </p>
    </div>
  );
};

const PizzeriaDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, token, isAuthenticated, updateUserFavorites } = useAuth();
  const [pizzeria, setPizzeria] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lists, setLists] = useState([]);
  const [showListDialog, setShowListDialog] = useState(false);
  const [refreshingWaitTime, setRefreshingWaitTime] = useState(false);

  const isFavorite = user?.favorites?.includes(id);

  useEffect(() => {
    fetchPizzeria();
    if (isAuthenticated) {
      fetchLists();
    }
  }, [id, isAuthenticated]);

  const fetchPizzeria = async () => {
    try {
      const response = await axios.get(`${API}/pizzerias/${id}`);
      setPizzeria(response.data);
    } catch (error) {
      console.error("Error fetching pizzeria:", error);
      toast.error("Failed to load pizzeria");
      navigate("/explore");
    } finally {
      setLoading(false);
    }
  };

  const refreshWaitTime = async () => {
    setRefreshingWaitTime(true);
    try {
      const response = await axios.get(`${API}/pizzerias/${id}/wait-time`);
      setPizzeria(prev => ({ ...prev, wait_time: response.data }));
    } catch (error) {
      toast.error("Failed to refresh wait time");
    } finally {
      setRefreshingWaitTime(false);
    }
  };

  const fetchLists = async () => {
    try {
      const response = await axios.get(`${API}/lists`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLists(response.data);
    } catch (error) {
      console.error("Error fetching lists:", error);
    }
  };

  const handleFavorite = async () => {
    if (!isAuthenticated) {
      toast.error("Please login to save favorites");
      navigate("/auth");
      return;
    }

    try {
      if (isFavorite) {
        await axios.delete(`${API}/favorites/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const newFavorites = user.favorites.filter(fid => fid !== id);
        updateUserFavorites(newFavorites);
        toast.success("Removed from favorites");
      } else {
        await axios.post(`${API}/favorites/${id}`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const newFavorites = [...(user.favorites || []), id];
        updateUserFavorites(newFavorites);
        toast.success("Added to favorites!");
      }
    } catch (error) {
      toast.error("Failed to update favorites");
    }
  };

  const handleAddToList = async (listId) => {
    try {
      await axios.post(`${API}/lists/${listId}/pizzerias/${id}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Added to list!");
      setShowListDialog(false);
    } catch (error) {
      toast.error("Failed to add to list");
    }
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: pizzeria.name,
        text: `Check out ${pizzeria.name} - amazing pizza in ${pizzeria.neighborhood}, Paris!`,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      toast.success("Link copied to clipboard!");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="animate-spin-slow">
          <span className="text-5xl">🍕</span>
        </div>
      </div>
    );
  }

  if (!pizzeria) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <p className="text-ink">Pizzeria not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream pb-8" data-testid="pizzeria-detail-page">
      {/* Header with back button */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-b from-black/50 to-transparent">
        <div className="flex items-center justify-between p-4">
          <button
            onClick={() => navigate(-1)}
            className="w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-md"
            data-testid="back-btn"
          >
            <ChevronLeft size={24} className="text-ink" />
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={handleShare}
              className="w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-md"
              data-testid="share-btn"
            >
              <Share2 size={20} className="text-ink" />
            </button>
            <button
              onClick={handleFavorite}
              className="w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-md"
              data-testid="detail-favorite-btn"
            >
              <Heart 
                size={20} 
                className={isFavorite ? "fill-tomato text-tomato" : "text-ink"} 
              />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Image */}
      <div className="relative h-72 md:h-96">
        <img
          src={pizzeria.photos?.main}
          alt={pizzeria.name}
          className="w-full h-full object-cover"
        />
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-6">
          <span className={`inline-block mb-2 ${
            pizzeria.pizza_style === "neapolitan" ? "badge-neapolitan" : "badge-roman"
          }`}>
            {pizzeria.pizza_style}
          </span>
          <h1 className="font-serif text-3xl md:text-4xl font-bold text-white">
            {pizzeria.name}
          </h1>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 -mt-4 relative z-10">
        {/* Wait Time Card */}
        <WaitTimeCard 
          waitTime={pizzeria.wait_time} 
          onRefresh={refreshWaitTime}
          refreshing={refreshingWaitTime}
        />

        {/* Quick Info Card */}
        <div className="bg-white rounded-2xl shadow-md p-5 mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-1">
              <Star size={20} className="fill-gold text-gold" />
              <span className="font-bold text-lg text-ink">{pizzeria.google_rating}</span>
            </div>
            <span className="text-stone">({pizzeria.review_count} reviews)</span>
          </div>

          <div className="flex items-start gap-2 text-ink mb-2">
            <MapPin size={18} className="text-tomato mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">{pizzeria.address}</p>
              <p className="text-sm text-stone">{pizzeria.neighborhood}</p>
            </div>
          </div>

          {/* Recommended By */}
          {pizzeria.recommended_by?.length > 0 && (
            <div className="flex items-center gap-2 mt-4 pt-4 border-t border-stone/10">
              <Award size={16} className="text-olive" />
              <span className="text-sm text-stone">Recommended by</span>
              <div className="flex flex-wrap gap-1">
                {pizzeria.recommended_by.map((source, i) => (
                  <span key={i} className="recommended-badge">
                    {source}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3 mb-6">
          <Button
            onClick={handleFavorite}
            variant={isFavorite ? "default" : "outline"}
            className={`flex-1 ${isFavorite ? "bg-tomato hover:bg-tomato-hover" : ""}`}
            data-testid="add-favorite-btn"
          >
            <Heart size={18} className={isFavorite ? "fill-white mr-2" : "mr-2"} />
            {isFavorite ? "Saved" : "Save"}
          </Button>
          
          <Dialog open={showListDialog} onOpenChange={setShowListDialog}>
            <DialogTrigger asChild>
              <Button 
                variant="outline" 
                className="flex-1"
                data-testid="add-to-list-btn"
                onClick={() => {
                  if (!isAuthenticated) {
                    toast.error("Please login to create lists");
                    navigate("/auth");
                  }
                }}
              >
                <Plus size={18} className="mr-2" />
                Add to List
              </Button>
            </DialogTrigger>
            {isAuthenticated && (
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="font-serif">Add to List</DialogTitle>
                </DialogHeader>
                <ScrollArea className="max-h-64">
                  {lists.length > 0 ? (
                    <div className="space-y-2">
                      {lists.map((list) => (
                        <button
                          key={list.id}
                          onClick={() => handleAddToList(list.id)}
                          className="w-full text-left p-3 rounded-lg hover:bg-paper transition-colors"
                          data-testid={`list-option-${list.id}`}
                        >
                          <p className="font-medium text-ink">{list.name}</p>
                          <p className="text-sm text-stone">{list.pizzeria_ids.length} pizzerias</p>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-stone mb-4">No lists yet</p>
                      <Button
                        onClick={() => {
                          setShowListDialog(false);
                          navigate("/lists");
                        }}
                        variant="outline"
                      >
                        Create a List
                      </Button>
                    </div>
                  )}
                </ScrollArea>
              </DialogContent>
            )}
          </Dialog>
        </div>

        {/* Photo Gallery */}
        <section className="mb-6">
          <h2 className="font-serif text-xl font-semibold text-ink mb-3">Photos</h2>
          <div className="photo-grid rounded-xl overflow-hidden">
            <div className="main-photo">
              <img 
                src={pizzeria.photos?.main} 
                alt="Main"
                className="w-full h-full object-cover"
              />
            </div>
            <div>
              <img 
                src={pizzeria.photos?.interior} 
                alt="Interior"
                className="w-full h-full object-cover"
              />
            </div>
            <div>
              <img 
                src={pizzeria.photos?.chef} 
                alt="Chef"
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </section>

        {/* Description */}
        <section className="mb-6">
          <h2 className="font-serif text-xl font-semibold text-ink mb-3">About</h2>
          <p className="text-ink/80 leading-relaxed">{pizzeria.description}</p>
        </section>

        {/* Badges */}
        <section className="mb-6">
          <h2 className="font-serif text-xl font-semibold text-ink mb-3">Features</h2>
          <div className="flex flex-wrap gap-2">
            {pizzeria.badges?.map((badge, index) => {
              const IconComponent = badgeIcons[badge] || Award;
              return (
                <div 
                  key={index}
                  className="flex items-center gap-2 px-3 py-2 bg-paper rounded-full"
                >
                  <IconComponent size={16} className="text-olive" />
                  <span className="text-sm font-medium text-ink">{badge}</span>
                </div>
              );
            })}
          </div>
        </section>

        {/* Signature Pizzas */}
        <section className="mb-6">
          <h2 className="font-serif text-xl font-semibold text-ink mb-3">Signature Pizzas</h2>
          <div className="space-y-3">
            {pizzeria.signature_pizzas?.map((pizza, index) => (
              <div 
                key={index}
                className="bg-white rounded-xl p-4 shadow-sm border border-stone/10"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-serif font-semibold text-ink">{pizza.name}</h3>
                    <p className="text-sm text-stone mt-1">{pizza.description}</p>
                  </div>
                  <span className="font-bold text-tomato">€{pizza.price}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Filters/Characteristics */}
        <section className="mb-6">
          <h2 className="font-serif text-xl font-semibold text-ink mb-3">Characteristics</h2>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(pizzeria.filters || {}).map(([key, value]) => {
              if (!value) return null;
              const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
              return (
                <div 
                  key={key}
                  className="flex items-center gap-2 p-3 bg-olive/10 rounded-lg"
                >
                  <div className="w-2 h-2 bg-olive rounded-full" />
                  <span className="text-sm text-ink">{label}</span>
                </div>
              );
            })}
          </div>
        </section>

        {/* Get Directions Button */}
        <a
          href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(pizzeria.address)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full py-4 bg-ink text-white text-center font-semibold rounded-full hover:bg-ink-light transition-colors"
          data-testid="directions-btn"
        >
          <span className="flex items-center justify-center gap-2">
            <MapPin size={18} />
            Get Directions
            <ExternalLink size={16} />
          </span>
        </a>
      </div>
    </div>
  );
};

export default PizzeriaDetail;
