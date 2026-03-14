import { useLocation, useNavigate } from "react-router-dom";
import { Map, Compass, Heart, List } from "lucide-react";
import { useAuth } from "@/App";

const Navigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const navItems = [
    { path: "/", icon: Map, label: "Map" },
    { path: "/explore", icon: Compass, label: "Explore" },
    { path: "/favorites", icon: Heart, label: "Favorites" },
    { path: "/lists", icon: List, label: "Lists" },
  ];

  // Don't show nav on auth page
  if (location.pathname === "/auth") return null;

  // Hide on pizzeria detail page for cleaner view
  if (location.pathname.startsWith("/pizzeria/")) return null;

  return (
    <nav 
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-stone/20 z-50"
      data-testid="main-navigation"
    >
      <div className="flex items-center justify-around py-2 px-4 max-w-md mx-auto">
        {navItems.map(({ path, icon: Icon, label }) => {
          const isActive = location.pathname === path;
          const requiresAuth = path === "/favorites" || path === "/lists";
          
          return (
            <button
              key={path}
              onClick={() => {
                if (requiresAuth && !isAuthenticated) {
                  navigate("/auth");
                } else {
                  navigate(path);
                }
              }}
              className={`nav-link ${isActive ? "active" : ""}`}
              data-testid={`nav-${label.toLowerCase()}`}
            >
              <Icon 
                size={24} 
                strokeWidth={isActive ? 2.5 : 1.5}
                className={isActive ? "text-tomato" : "text-stone"}
              />
              <span className={`text-xs font-medium ${isActive ? "text-tomato" : "text-stone"}`}>
                {label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default Navigation;
