import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import axios from "axios";
import { API } from "@/App";
import MapPopup from "@/components/MapPopup";
import { Sparkles, Navigation, Filter } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import "leaflet/dist/leaflet.css";

// Fix Leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// Custom pizza markers
const createPizzaIcon = (style) => {
  const color = style === "neapolitan" ? "#E63946" : "#DDA15E";
  return L.divIcon({
    className: "pizza-marker-wrapper",
    html: `
      <div class="pizza-marker ${style}" style="
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: ${color};
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        font-size: 18px;
      ">
        🍕
      </div>
    `,
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40],
  });
};

// User location marker
const userLocationIcon = L.divIcon({
  className: "user-marker-wrapper",
  html: `<div class="user-marker"></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

// Map controller component
const MapController = ({ center, userLocation }) => {
  const map = useMap();
  
  useEffect(() => {
    if (center) {
      map.flyTo(center, 14, { duration: 1 });
    }
  }, [center, map]);

  return null;
};

const MapView = () => {
  const navigate = useNavigate();
  const [pizzerias, setPizzerias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userLocation, setUserLocation] = useState(null);
  const [mapCenter, setMapCenter] = useState([48.8566, 2.3522]); // Paris center
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({});
  const mapRef = useRef(null);

  useEffect(() => {
    fetchPizzerias();
    getUserLocation();
  }, [filters]);

  const fetchPizzerias = async () => {
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value);
        }
      });
      
      const response = await axios.get(`${API}/pizzerias?${params.toString()}`);
      setPizzerias(response.data);
    } catch (error) {
      console.error("Error fetching pizzerias:", error);
      toast.error("Failed to load pizzerias");
    } finally {
      setLoading(false);
    }
  };

  const getUserLocation = () => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation([latitude, longitude]);
        },
        (error) => {
          console.log("Geolocation error:", error);
          // Default to Paris center
          setUserLocation([48.8566, 2.3522]);
        }
      );
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

  const centerOnUser = () => {
    if (userLocation) {
      setMapCenter(userLocation);
    } else {
      toast.info("Getting your location...");
      getUserLocation();
    }
  };

  const quickFilters = [
    { key: "style", value: "neapolitan", label: "Neapolitan", color: "tomato" },
    { key: "style", value: "roman", label: "Roman", color: "terracotta" },
    { key: "gluten_free", value: true, label: "Gluten-Free", color: "olive" },
  ];

  const toggleFilter = (key, value) => {
    if (filters[key] === value) {
      const newFilters = { ...filters };
      delete newFilters[key];
      setFilters(newFilters);
    } else {
      setFilters({ ...filters, [key]: value });
    }
  };

  return (
    <div className="relative h-screen w-full" data-testid="map-view">
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-30 bg-gradient-to-b from-cream via-cream/90 to-transparent pt-4 pb-8 px-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="font-serif text-2xl md:text-3xl font-bold text-ink">
            Only Great Pizza
          </h1>
          <p className="font-hand text-lg text-terracotta -rotate-1">Paris Edition</p>
        </div>

        {/* Quick Filters */}
        <div className="flex items-center gap-2 mt-4 overflow-x-auto pb-1 scrollbar-hide">
          {quickFilters.map(({ key, value, label, color }) => (
            <button
              key={`${key}-${value}`}
              onClick={() => toggleFilter(key, value)}
              className={`filter-pill whitespace-nowrap ${
                filters[key] === value ? "active" : "inactive"
              }`}
              data-testid={`map-filter-${label.toLowerCase()}`}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      {/* Map */}
      <div className="map-container" style={{ height: "100vh" }}>
        {!loading && (
          <MapContainer
            center={mapCenter}
            zoom={13}
            className="h-full w-full"
            ref={mapRef}
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            <MapController center={mapCenter} userLocation={userLocation} />

            {/* User location marker */}
            {userLocation && (
              <Marker position={userLocation} icon={userLocationIcon}>
                <Popup>
                  <div className="text-center p-2">
                    <p className="font-semibold text-ink">You are here</p>
                  </div>
                </Popup>
              </Marker>
            )}

            {/* Pizzeria markers */}
            {pizzerias.map((pizzeria) => (
              <Marker
                key={pizzeria.id}
                position={[pizzeria.latitude, pizzeria.longitude]}
                icon={createPizzaIcon(pizzeria.pizza_style)}
                data-testid={`map-marker-${pizzeria.id}`}
              >
                <Popup>
                  <MapPopup pizzeria={pizzeria} />
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        )}
      </div>

      {/* Floating Action Buttons */}
      <div className="absolute bottom-24 right-4 flex flex-col gap-3 z-30">
        {/* Center on user */}
        <button
          onClick={centerOnUser}
          className="w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center text-ink hover:bg-paper transition-colors"
          data-testid="center-location-btn"
        >
          <Navigation size={20} />
        </button>

        {/* Surprise me button */}
        <button
          onClick={handleSurpriseMe}
          className="w-14 h-14 bg-tomato rounded-full shadow-lg flex items-center justify-center text-white hover:bg-tomato-hover transition-all hover:scale-110"
          data-testid="surprise-me-btn"
        >
          <Sparkles size={24} />
        </button>
      </div>

      {/* Pizza count badge */}
      <div className="absolute bottom-24 left-4 bg-white/90 backdrop-blur-sm px-4 py-2 rounded-full shadow-md z-30">
        <span className="font-semibold text-ink">{pizzerias.length}</span>
        <span className="text-stone ml-1">pizzerias</span>
      </div>

      {/* Loading overlay */}
      {loading && (
        <div className="absolute inset-0 bg-cream/80 flex items-center justify-center z-50">
          <div className="text-center">
            <div className="animate-spin-slow inline-block text-5xl mb-4">🍕</div>
            <p className="font-hand text-xl text-ink/60">Finding the best slices...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MapView;
