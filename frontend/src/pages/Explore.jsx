import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import PizzeriaCard from "@/components/PizzeriaCard";
import FilterBar from "@/components/FilterBar";
import { Sparkles, Search, MapPin, Star, Clock, Navigation } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const Explore = () => {
  const navigate = useNavigate();
  const [pizzerias, setPizzerias] = useState([]);
  const [filteredPizzerias, setFilteredPizzerias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("rating");
  const [userLocation, setUserLocation] = useState(null);
  const [gettingLocation, setGettingLocation] = useState(false);

  useEffect(() => {
    fetchPizzerias();
  }, [filters, sortBy, userLocation]);

  useEffect(() => {
    // Client-side search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const filtered = pizzerias.filter(p => 
        p.name.toLowerCase().includes(query) ||
        p.neighborhood.toLowerCase().includes(query) ||
        p.description.toLowerCase().includes(query)
      );
      setFilteredPizzerias(filtered);
    } else {
      setFilteredPizzerias(pizzerias);
    }
  }, [searchQuery, pizzerias]);

  const getUserLocation = () => {
    if (!navigator.geolocation) {
      toast.error("Geolocation not supported");
      return;
    }
    
    setGettingLocation(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          lat: position.coords.latitude,
          lon: position.coords.longitude
        });
        setSortBy("distance");
        toast.success("Location found! Sorting by distance");
        setGettingLocation(false);
      },
      (error) => {
        toast.error("Could not get your location");
        setGettingLocation(false);
      }
    );
  };

  const fetchPizzerias = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value);
        }
      });
      
      if (sortBy) {
        params.append("sort_by", sortBy);
      }
      
      if (userLocation) {
        params.append("user_lat", userLocation.lat);
        params.append("user_lon", userLocation.lon);
      }
      
      const response = await axios.get(`${API}/pizzerias?${params.toString()}`);
      setPizzerias(response.data);
      setFilteredPizzerias(response.data);
    } catch (error) {
      console.error("Error fetching pizzerias:", error);
      toast.error("Failed to load pizzerias");
    } finally {
      setLoading(false);
    }
  };

  const handleSurpriseMe = async () => {
    try {
      const response = await axios.get(`${API}/pizzerias/random/surprise`);
      const randomPizzeria = response.data;
      toast.success(`Let's try ${randomPizzeria.name}!`, {
        description: randomPizzeria.neighborhood
      });
      navigate(`/pizzeria/${randomPizzeria.id}`);
    } catch (error) {
      toast.error("No pizzerias found!");
    }
  };

  return (
    <div className="min-h-screen bg-cream pb-24" data-testid="explore-page">
      {/* Header */}
      <header className="bg-white border-b border-stone/20 sticky top-0 z-50">
        <div className="px-4 py-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="font-heading text-3xl font-bold text-ink uppercase tracking-tight">Explore</h1>
              <p className="text-sm text-stone uppercase tracking-widest mt-1">Discover the best pizza in Paris</p>
            </div>
            <button
              onClick={handleSurpriseMe}
              className="flex items-center gap-2 bg-brick text-white px-5 py-2 font-heading uppercase tracking-wider text-sm hover:bg-brick-hover transition-colors"
              data-testid="explore-surprise-btn"
            >
              <Sparkles size={16} />
              Surprise me
            </button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-stone" size={20} />
            <Input
              type="text"
              placeholder="Search pizzerias, neighborhoods..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-cream border-stone/30 focus:border-brick rounded-none"
              data-testid="explore-search-input"
            />
          </div>

          {/* Sort and Location */}
          <div className="flex items-center gap-3 mt-4">
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-40 rounded-none border-stone/30" data-testid="sort-select">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="rating">
                  <span className="flex items-center gap-2">
                    <Star size={14} /> Rating
                  </span>
                </SelectItem>
                <SelectItem value="distance" disabled={!userLocation}>
                  <span className="flex items-center gap-2">
                    <MapPin size={14} /> Distance
                  </span>
                </SelectItem>
                <SelectItem value="wait_time">
                  <span className="flex items-center gap-2">
                    <Clock size={14} /> Wait Time
                  </span>
                </SelectItem>
              </SelectContent>
            </Select>

            <button
              onClick={getUserLocation}
              disabled={gettingLocation}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-heading uppercase tracking-wider transition-colors ${
                userLocation 
                  ? "bg-olive/10 text-olive border border-olive/30" 
                  : "bg-cream text-ink/70 border border-stone/30 hover:border-ink"
              }`}
              data-testid="get-location-btn"
            >
              <Navigation size={16} className={gettingLocation ? "animate-spin" : ""} />
              {userLocation ? "Location On" : "Use My Location"}
            </button>
          </div>
        </div>
      </header>

      {/* Filters */}
      <FilterBar filters={filters} onFilterChange={setFilters} />

      {/* Results count */}
      <div className="px-4 py-4 flex items-center justify-between border-b border-stone/10">
        <p className="text-sm text-stone uppercase tracking-widest">
          <span className="font-heading text-ink">{filteredPizzerias.length}</span> pizzerias found
        </p>
      </div>

      {/* Pizzeria Grid */}
      <div className="px-4">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="pizzeria-card animate-pulse">
                <div className="aspect-[4/3] bg-stone/20" />
                <div className="p-4 space-y-3">
                  <div className="h-5 bg-stone/20 rounded w-3/4" />
                  <div className="h-4 bg-stone/20 rounded w-1/2" />
                  <div className="h-4 bg-stone/20 rounded w-1/4" />
                </div>
              </div>
            ))}
          </div>
        ) : filteredPizzerias.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPizzerias.map((pizzeria) => (
              <PizzeriaCard key={pizzeria.id} pizzeria={pizzeria} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">🍕</div>
            <h3 className="font-serif text-xl text-ink mb-2">No pizzerias found</h3>
            <p className="text-stone mb-4">Try adjusting your filters</p>
            <button
              onClick={() => setFilters({})}
              className="text-tomato font-semibold hover:underline"
              data-testid="clear-filters-btn"
            >
              Clear all filters
            </button>
          </div>
        )}
      </div>

      {/* Featured Section */}
      {!loading && filteredPizzerias.length > 0 && (
        <section className="mt-16 px-4">
          <h2 className="font-heading text-2xl font-bold text-ink uppercase tracking-tight mb-4">
            Editor's Picks
          </h2>
          <div className="bg-paper border border-stone/20 p-6">
            <p className="font-accent text-xl text-terracotta -rotate-1 mb-3">
              "The pizza scene in Paris has never been better"
            </p>
            <p className="text-ink/80 leading-relaxed font-body">
              Our curated selection features only pizzerias with exceptional ratings, 
              authentic Italian techniques, and unforgettable flavors. Each spot has 
              been vetted by food critics and passionate locals alike.
            </p>
          </div>
        </section>
      )}
    </div>
  );
};

export default Explore;
