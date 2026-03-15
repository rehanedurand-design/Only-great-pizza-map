import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { 
  Plus, 
  Trash2, 
  Edit2, 
  Save, 
  X, 
  ChevronLeft,
  MapPin,
  Search
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Checkbox } from "@/components/ui/checkbox";

const emptyPizzeria = {
  name: "",
  address: "",
  neighborhood: "",
  latitude: 48.8566,
  longitude: 2.3522,
  google_rating: 4.8,
  review_count: 200,
  pizza_style: "neapolitan",
  description: "",
  signature_pizza_name: "",
  signature_pizza_description: "",
  signature_pizza_price: 14,
  photo_main: "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=1200",
  photo_interior: "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1200",
  photo_chef: "https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=1200",
  badges: [],
  sourdough: false,
  long_fermentation: true,
  gluten_free: false,
  italian_owners: true,
  italian_pizzaiolo: true,
  good_wine: false,
  famous_tiramisu: false,
  recommended_by: []
};

const Admin = () => {
  const navigate = useNavigate();
  const [pizzerias, setPizzerias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState(emptyPizzeria);
  const [saving, setSaving] = useState(false);
  const [badgeInput, setBadgeInput] = useState("");

  useEffect(() => {
    fetchPizzerias();
  }, []);

  const fetchPizzerias = async () => {
    try {
      const response = await axios.get(`${API}/pizzerias?include_wait_time=false`);
      setPizzerias(response.data);
    } catch (error) {
      toast.error("Failed to load pizzerias");
    } finally {
      setLoading(false);
    }
  };

  const filteredPizzerias = pizzerias.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.neighborhood.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.address) {
      toast.error("Name and address are required");
      return;
    }

    setSaving(true);
    try {
      if (editingId) {
        await axios.put(`${API}/pizzerias/${editingId}`, formData);
        toast.success("Pizzeria updated!");
      } else {
        await axios.post(`${API}/pizzerias`, formData);
        toast.success("Pizzeria added!");
      }
      setShowForm(false);
      setEditingId(null);
      setFormData(emptyPizzeria);
      fetchPizzerias();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save pizzeria");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (pizzeria) => {
    setFormData({
      name: pizzeria.name,
      address: pizzeria.address,
      neighborhood: pizzeria.neighborhood,
      latitude: pizzeria.latitude,
      longitude: pizzeria.longitude,
      google_rating: pizzeria.google_rating,
      review_count: pizzeria.review_count,
      pizza_style: pizzeria.pizza_style,
      description: pizzeria.description,
      signature_pizza_name: pizzeria.signature_pizzas?.[0]?.name || "",
      signature_pizza_description: pizzeria.signature_pizzas?.[0]?.description || "",
      signature_pizza_price: pizzeria.signature_pizzas?.[0]?.price || 14,
      photo_main: pizzeria.photos?.main || emptyPizzeria.photo_main,
      photo_interior: pizzeria.photos?.interior || emptyPizzeria.photo_interior,
      photo_chef: pizzeria.photos?.chef || emptyPizzeria.photo_chef,
      badges: pizzeria.badges || [],
      sourdough: pizzeria.filters?.sourdough || false,
      long_fermentation: pizzeria.filters?.long_fermentation || false,
      gluten_free: pizzeria.filters?.gluten_free || false,
      italian_owners: pizzeria.filters?.italian_owners || false,
      italian_pizzaiolo: pizzeria.filters?.italian_pizzaiolo || false,
      good_wine: pizzeria.filters?.good_wine || false,
      famous_tiramisu: pizzeria.filters?.famous_tiramisu || false,
      recommended_by: pizzeria.recommended_by || []
    });
    setEditingId(pizzeria.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/pizzerias/${id}`);
      toast.success("Pizzeria deleted");
      fetchPizzerias();
    } catch (error) {
      toast.error("Failed to delete pizzeria");
    }
  };

  const addBadge = () => {
    if (badgeInput.trim() && !formData.badges.includes(badgeInput.trim())) {
      setFormData({ ...formData, badges: [...formData.badges, badgeInput.trim()] });
      setBadgeInput("");
    }
  };

  const removeBadge = (badge) => {
    setFormData({ ...formData, badges: formData.badges.filter(b => b !== badge) });
  };

  return (
    <div className="min-h-screen bg-cream pb-8" data-testid="admin-page">
      {/* Header */}
      <header className="bg-white border-b border-stone/20 sticky top-0 z-50 px-4 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/")}
            className="w-10 h-10 bg-cream flex items-center justify-center"
          >
            <ChevronLeft size={24} className="text-ink" />
          </button>
          <div className="flex-1">
            <h1 className="font-heading text-2xl font-bold text-ink uppercase tracking-tight">
              Admin Panel
            </h1>
            <p className="text-sm text-stone">{pizzerias.length} pizzerias</p>
          </div>
          <Button
            onClick={() => {
              setFormData(emptyPizzeria);
              setEditingId(null);
              setShowForm(true);
            }}
            className="bg-brick hover:bg-brick-hover text-white"
            data-testid="add-pizzeria-btn"
          >
            <Plus size={18} className="mr-2" />
            Add Pizzeria
          </Button>
        </div>

        {/* Search */}
        <div className="relative mt-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-stone" size={20} />
          <Input
            type="text"
            placeholder="Search pizzerias..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-cream border-stone/30"
          />
        </div>
      </header>

      {/* Pizzeria List */}
      <div className="px-4 py-6">
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : filteredPizzerias.length > 0 ? (
          <div className="space-y-3">
            {filteredPizzerias.map((pizzeria) => (
              <div
                key={pizzeria.id}
                className="bg-white border border-stone/20 p-4 flex items-center gap-4"
              >
                <img
                  src={pizzeria.photos?.main}
                  alt={pizzeria.name}
                  className="w-16 h-16 object-cover"
                />
                <div className="flex-1 min-w-0">
                  <h3 className="font-heading text-lg uppercase tracking-wide text-ink truncate">
                    {pizzeria.name}
                  </h3>
                  <p className="text-sm text-stone flex items-center gap-1">
                    <MapPin size={12} />
                    {pizzeria.neighborhood}
                  </p>
                  <span className={`text-xs px-2 py-0.5 ${
                    pizzeria.pizza_style === "neapolitan" 
                      ? "bg-brick/10 text-brick" 
                      : "bg-gold/20 text-terracotta"
                  }`}>
                    {pizzeria.pizza_style}
                  </span>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(pizzeria)}
                  >
                    <Edit2 size={16} />
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="outline" size="sm" className="text-brick border-brick/30">
                        <Trash2 size={16} />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete Pizzeria</AlertDialogTitle>
                        <AlertDialogDescription>
                          Are you sure you want to delete "{pizzeria.name}"?
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => handleDelete(pizzeria.id)}
                          className="bg-brick hover:bg-brick-hover"
                        >
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-stone">No pizzerias found</div>
        )}
      </div>

      {/* Add/Edit Form Dialog */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading uppercase">
              {editingId ? "Edit Pizzeria" : "Add Pizzeria"}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Name *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label>Neighborhood</Label>
                <Input
                  value={formData.neighborhood}
                  onChange={(e) => setFormData({ ...formData, neighborhood: e.target.value })}
                />
              </div>
            </div>

            <div>
              <Label>Address *</Label>
              <Input
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Latitude</Label>
                <Input
                  type="number"
                  step="0.0001"
                  value={formData.latitude}
                  onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                />
              </div>
              <div>
                <Label>Longitude</Label>
                <Input
                  type="number"
                  step="0.0001"
                  value={formData.longitude}
                  onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Pizza Style</Label>
                <Select
                  value={formData.pizza_style}
                  onValueChange={(v) => setFormData({ ...formData, pizza_style: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="neapolitan">Neapolitan</SelectItem>
                    <SelectItem value="roman">Roman</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Google Rating</Label>
                <Input
                  type="number"
                  step="0.1"
                  min="1"
                  max="5"
                  value={formData.google_rating}
                  onChange={(e) => setFormData({ ...formData, google_rating: parseFloat(e.target.value) })}
                />
              </div>
              <div>
                <Label>Review Count</Label>
                <Input
                  type="number"
                  value={formData.review_count}
                  onChange={(e) => setFormData({ ...formData, review_count: parseInt(e.target.value) })}
                />
              </div>
            </div>

            <div>
              <Label>Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </div>

            {/* Signature Pizza */}
            <div className="border-t pt-4">
              <h4 className="font-heading uppercase text-sm mb-3">Signature Pizza</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Name</Label>
                  <Input
                    value={formData.signature_pizza_name}
                    onChange={(e) => setFormData({ ...formData, signature_pizza_name: e.target.value })}
                  />
                </div>
                <div className="col-span-2">
                  <Label>Description</Label>
                  <Input
                    value={formData.signature_pizza_description}
                    onChange={(e) => setFormData({ ...formData, signature_pizza_description: e.target.value })}
                  />
                </div>
              </div>
            </div>

            {/* Badges */}
            <div className="border-t pt-4">
              <h4 className="font-heading uppercase text-sm mb-3">Badges</h4>
              <div className="flex gap-2 mb-2">
                <Input
                  value={badgeInput}
                  onChange={(e) => setBadgeInput(e.target.value)}
                  placeholder="Add badge"
                  onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), addBadge())}
                />
                <Button type="button" variant="outline" onClick={addBadge}>Add</Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {formData.badges.map((badge, i) => (
                  <span key={i} className="px-2 py-1 bg-cream text-ink text-sm flex items-center gap-1">
                    {badge}
                    <button type="button" onClick={() => removeBadge(badge)}>
                      <X size={14} />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Filters */}
            <div className="border-t pt-4">
              <h4 className="font-heading uppercase text-sm mb-3">Characteristics</h4>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { key: "sourdough", label: "Sourdough" },
                  { key: "long_fermentation", label: "Long Fermentation" },
                  { key: "gluten_free", label: "Gluten Free" },
                  { key: "italian_owners", label: "Italian Owners" },
                  { key: "italian_pizzaiolo", label: "Italian Pizzaiolo" },
                  { key: "good_wine", label: "Good Wine" },
                  { key: "famous_tiramisu", label: "Famous Tiramisu" }
                ].map(({ key, label }) => (
                  <div key={key} className="flex items-center gap-2">
                    <Checkbox
                      id={key}
                      checked={formData[key]}
                      onCheckedChange={(checked) => setFormData({ ...formData, [key]: checked })}
                    />
                    <Label htmlFor={key} className="text-sm">{label}</Label>
                  </div>
                ))}
              </div>
            </div>

            {/* Submit */}
            <div className="flex gap-3 pt-4 border-t">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving} className="bg-brick hover:bg-brick-hover text-white">
                <Save size={16} className="mr-2" />
                {saving ? "Saving..." : editingId ? "Update" : "Create"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Admin;
