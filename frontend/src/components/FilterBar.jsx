import { useState } from "react";
import { X, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

const FilterBar = ({ filters, onFilterChange }) => {
  const [expanded, setExpanded] = useState(false);

  const filterGroups = [
    {
      label: "Pizza Style",
      filters: [
        { key: "style", value: "neapolitan", label: "Neapolitan" },
        { key: "style", value: "roman", label: "Roman" },
        { key: "featured_by_critics", value: true, label: "🏆 Critics' Pick" },
      ]
    },
    {
      label: "Dough",
      filters: [
        { key: "sourdough", value: true, label: "Sourdough" },
        { key: "long_fermentation", value: true, label: "Long Fermentation" },
        { key: "gluten_free", value: true, label: "Gluten-Free" },
      ]
    },
    {
      label: "Authenticity",
      filters: [
        { key: "italian_owners", value: true, label: "Italian Owners" },
        { key: "italian_pizzaiolo", value: true, label: "Italian Pizzaiolo" },
      ]
    },
    {
      label: "Extras",
      filters: [
        { key: "good_wine", value: true, label: "Good Wine" },
        { key: "famous_tiramisu", value: true, label: "Famous Tiramisu" },
      ]
    }
  ];

  const isFilterActive = (key, value) => {
    return filters[key] === value;
  };

  const toggleFilter = (key, value) => {
    if (isFilterActive(key, value)) {
      onFilterChange({ ...filters, [key]: undefined });
    } else {
      onFilterChange({ ...filters, [key]: value });
    }
  };

  const clearAllFilters = () => {
    onFilterChange({});
  };

  const activeFilterCount = Object.values(filters).filter(v => v !== undefined).length;

  return (
    <div className="bg-white border-b border-stone/10 sticky top-0 z-40" data-testid="filter-bar">
      {/* Main filter row */}
      <div className="px-4 py-3">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-hide">
          {/* Quick filters */}
          {filterGroups[0].filters.map(({ key, value, label }) => (
            <button
              key={`${key}-${value}`}
              onClick={() => toggleFilter(key, value)}
              className={`filter-pill whitespace-nowrap ${isFilterActive(key, value) ? "active" : "inactive"}`}
              data-testid={`filter-${label.toLowerCase()}`}
            >
              {label}
            </button>
          ))}
          
          {/* Expand button */}
          <button
            onClick={() => setExpanded(!expanded)}
            className="filter-pill inactive flex items-center gap-1 whitespace-nowrap"
            data-testid="filter-expand-btn"
          >
            More Filters
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            {activeFilterCount > 0 && (
              <span className="ml-1 w-5 h-5 bg-tomato text-white text-xs rounded-full flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </button>

          {/* Clear all */}
          {activeFilterCount > 0 && (
            <button
              onClick={clearAllFilters}
              className="filter-pill inactive flex items-center gap-1 text-tomato border-tomato/30 whitespace-nowrap"
              data-testid="filter-clear-btn"
            >
              <X size={14} />
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Expanded filters */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-stone/10 pt-3 animate-in">
          {filterGroups.slice(1).map((group) => (
            <div key={group.label} className="mb-4 last:mb-0">
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone mb-2">
                {group.label}
              </h4>
              <div className="flex flex-wrap gap-2">
                {group.filters.map(({ key, value, label }) => (
                  <button
                    key={`${key}-${value}`}
                    onClick={() => toggleFilter(key, value)}
                    className={`filter-pill ${isFilterActive(key, value) ? "active" : "inactive"}`}
                    data-testid={`filter-${label.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FilterBar;
