import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import PizzeriaCard from "@/components/PizzeriaCard";
import FilterBar from "@/components/FilterBar";
import { Sparkles, Search, ChevronLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";

const Explore = () => {
  const navigate = useNavigate();
  const [pizzerias, setPizzerias] = useState([]);
  const [filteredPizzerias, setFilteredPizzerias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    fetchPizzerias();
  }, [filters]);

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

  const fetchPizzerias = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value);
        }
      });
      
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
      <header className="bg-white border-b border-stone/10 sticky top-0 z-50">
        <div className="px-4 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="font-serif text-2xl font-bold text-ink">Explore</h1>
              <p className="text-sm text-stone">Discover the best pizza in Paris</p>
            </div>
            <button
              onClick={handleSurpriseMe}
              className="flex items-center gap-2 bg-tomato text-white px-4 py-2 rounded-full font-semibold text-sm hover:bg-tomato-hover transition-colors"
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
              className="pl-10 bg-paper border-stone/20 focus:border-tomato"
              data-testid="explore-search-input"
            />
          </div>
        </div>
      </header>

      {/* Filters */}
      <FilterBar filters={filters} onFilterChange={setFilters} />

      {/* Results count */}
      <div className="px-4 py-3 flex items-center justify-between">
        <p className="text-sm text-stone">
          <span className="font-semibold text-ink">{filteredPizzerias.length}</span> pizzerias found
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
        <section className="mt-12 px-4">
          <h2 className="font-serif text-xl font-bold text-ink mb-4">
            Editor's Picks
          </h2>
          <div className="bg-paper rounded-2xl p-6">
            <p className="font-hand text-lg text-terracotta mb-3 -rotate-1">
              "The pizza scene in Paris has never been better"
            </p>
            <p className="text-ink/80 leading-relaxed">
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
