import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/App";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ChevronLeft, Eye, EyeOff } from "lucide-react";

const Auth = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, isAuthenticated } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    name: "",
  });

  // Redirect if already authenticated
  if (isAuthenticated) {
    const from = location.state?.from?.pathname || "/";
    navigate(from, { replace: true });
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
        toast.success("Welcome back!");
      } else {
        if (!formData.name.trim()) {
          toast.error("Please enter your name");
          setLoading(false);
          return;
        }
        await register(formData.email, formData.password, formData.name);
        toast.success("Account created successfully!");
      }
      
      const from = location.state?.from?.pathname || "/";
      navigate(from, { replace: true });
    } catch (error) {
      const message = error.response?.data?.detail || "Authentication failed";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream flex flex-col" data-testid="auth-page">
      {/* Header */}
      <header className="p-4">
        <button
          onClick={() => navigate("/")}
          className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-sm"
          data-testid="auth-back-btn"
        >
          <ChevronLeft size={24} className="text-ink" />
        </button>
      </header>

      {/* Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 pb-12">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">🍕</div>
          <h1 className="font-serif text-3xl font-bold text-ink">
            Only Great Pizza
          </h1>
          <p className="font-hand text-lg text-terracotta mt-1 -rotate-1">
            Paris Edition
          </p>
        </div>

        {/* Auth Card */}
        <div className="w-full max-w-sm bg-white rounded-2xl shadow-md p-6">
          <h2 className="font-serif text-xl font-semibold text-ink text-center mb-6">
            {isLogin ? "Welcome Back" : "Create Account"}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <Label htmlFor="name" className="text-ink">Name</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Your name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1"
                  data-testid="auth-name-input"
                />
              </div>
            )}

            <div>
              <Label htmlFor="email" className="text-ink">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                className="mt-1"
                data-testid="auth-email-input"
              />
            </div>

            <div>
              <Label htmlFor="password" className="text-ink">Password</Label>
              <div className="relative mt-1">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  minLength={6}
                  className="pr-10"
                  data-testid="auth-password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-stone"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-tomato hover:bg-tomato-hover text-white font-semibold py-3"
              data-testid="auth-submit-btn"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin">🍕</span>
                  {isLogin ? "Signing in..." : "Creating account..."}
                </span>
              ) : (
                isLogin ? "Sign In" : "Create Account"
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm text-stone hover:text-ink transition-colors"
              data-testid="auth-toggle-btn"
            >
              {isLogin ? (
                <>Don't have an account? <span className="text-tomato font-semibold">Sign up</span></>
              ) : (
                <>Already have an account? <span className="text-tomato font-semibold">Sign in</span></>
              )}
            </button>
          </div>
        </div>

        {/* Benefits */}
        <div className="mt-8 text-center">
          <p className="text-sm text-stone mb-3">Create an account to:</p>
          <div className="flex flex-wrap justify-center gap-4 text-sm">
            <span className="flex items-center gap-1 text-ink">
              <span className="text-tomato">♥</span> Save favorites
            </span>
            <span className="flex items-center gap-1 text-ink">
              <span className="text-olive">◉</span> Create lists
            </span>
            <span className="flex items-center gap-1 text-ink">
              <span className="text-terracotta">★</span> Personal map
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Auth;
