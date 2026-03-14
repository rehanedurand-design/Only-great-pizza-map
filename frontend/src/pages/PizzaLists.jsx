import { useState, useEffect } from "react";
import axios from "axios";
import { API, useAuth } from "@/App";
import PizzeriaCard from "@/components/PizzeriaCard";
import { List, Plus, Trash2, ChevronRight, LogIn, ChevronLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
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

const PizzaLists = () => {
  const navigate = useNavigate();
  const { token, isAuthenticated } = useAuth();
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedList, setSelectedList] = useState(null);
  const [listPizzerias, setListPizzerias] = useState([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newListData, setNewListData] = useState({ name: "", description: "" });
  const [creatingList, setCreatingList] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      fetchLists();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const fetchLists = async () => {
    try {
      const response = await axios.get(`${API}/lists`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLists(response.data);
    } catch (error) {
      console.error("Error fetching lists:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchListPizzerias = async (listId) => {
    try {
      const response = await axios.get(`${API}/lists/${listId}/pizzerias`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setListPizzerias(response.data);
    } catch (error) {
      console.error("Error fetching list pizzerias:", error);
    }
  };

  const handleCreateList = async () => {
    if (!newListData.name.trim()) {
      toast.error("Please enter a list name");
      return;
    }

    setCreatingList(true);
    try {
      const response = await axios.post(`${API}/lists`, newListData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLists([...lists, response.data]);
      setShowCreateDialog(false);
      setNewListData({ name: "", description: "" });
      toast.success("List created!");
    } catch (error) {
      toast.error("Failed to create list");
    } finally {
      setCreatingList(false);
    }
  };

  const handleDeleteList = async (listId) => {
    try {
      await axios.delete(`${API}/lists/${listId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLists(lists.filter(l => l.id !== listId));
      if (selectedList?.id === listId) {
        setSelectedList(null);
        setListPizzerias([]);
      }
      toast.success("List deleted");
    } catch (error) {
      toast.error("Failed to delete list");
    }
  };

  const handleSelectList = (list) => {
    setSelectedList(list);
    fetchListPizzerias(list.id);
  };

  const handleRemoveFromList = async (pizzeriaId) => {
    try {
      await axios.delete(`${API}/lists/${selectedList.id}/pizzerias/${pizzeriaId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setListPizzerias(listPizzerias.filter(p => p.id !== pizzeriaId));
      // Update the list count
      setLists(lists.map(l => 
        l.id === selectedList.id 
          ? { ...l, pizzeria_ids: l.pizzeria_ids.filter(id => id !== pizzeriaId) }
          : l
      ));
      toast.success("Removed from list");
    } catch (error) {
      toast.error("Failed to remove from list");
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-cream flex flex-col items-center justify-center px-6 pb-24" data-testid="lists-page">
        <List size={64} className="text-stone/30 mb-4" />
        <h1 className="font-serif text-2xl font-bold text-ink mb-2">Pizza Lists</h1>
        <p className="text-stone text-center mb-6">
          Sign in to create custom lists and organize your favorite pizzerias.
        </p>
        <Button
          onClick={() => navigate("/auth")}
          className="bg-tomato hover:bg-tomato-hover text-white"
          data-testid="lists-login-btn"
        >
          <LogIn size={18} className="mr-2" />
          Sign In
        </Button>
      </div>
    );
  }

  // Show list detail view
  if (selectedList) {
    return (
      <div className="min-h-screen bg-cream pb-24" data-testid="list-detail-page">
        {/* Header */}
        <header className="bg-white border-b border-stone/10 sticky top-0 z-50 px-4 py-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setSelectedList(null);
                setListPizzerias([]);
              }}
              className="w-10 h-10 bg-paper rounded-full flex items-center justify-center"
              data-testid="back-to-lists-btn"
            >
              <ChevronLeft size={24} className="text-ink" />
            </button>
            <div className="flex-1">
              <h1 className="font-serif text-xl font-bold text-ink">{selectedList.name}</h1>
              <p className="text-sm text-stone">{listPizzerias.length} pizzerias</p>
            </div>
          </div>
          {selectedList.description && (
            <p className="text-sm text-stone mt-2">{selectedList.description}</p>
          )}
        </header>

        {/* Pizzerias */}
        <div className="px-4 py-6">
          {listPizzerias.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {listPizzerias.map((pizzeria) => (
                <div key={pizzeria.id} className="relative">
                  <PizzeriaCard pizzeria={pizzeria} />
                  <button
                    onClick={() => handleRemoveFromList(pizzeria.id)}
                    className="absolute top-3 right-14 w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-md hover:bg-red-50"
                    data-testid={`remove-from-list-${pizzeria.id}`}
                  >
                    <Trash2 size={18} className="text-tomato" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <List size={64} className="mx-auto text-stone/30 mb-4" />
              <h2 className="font-serif text-xl text-ink mb-2">Empty list</h2>
              <p className="text-stone mb-6">
                Start adding pizzerias to this list!
              </p>
              <Button
                onClick={() => navigate("/explore")}
                className="bg-tomato hover:bg-tomato-hover text-white"
              >
                Explore Pizzerias
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream pb-24" data-testid="lists-page">
      {/* Header */}
      <header className="bg-white border-b border-stone/10 sticky top-0 z-50 px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-serif text-2xl font-bold text-ink">Your Lists</h1>
            <p className="text-sm text-stone">{lists.length} list{lists.length !== 1 ? "s" : ""}</p>
          </div>
          
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button
                className="bg-tomato hover:bg-tomato-hover text-white"
                data-testid="create-list-btn"
              >
                <Plus size={18} className="mr-2" />
                New List
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="font-serif">Create New List</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <label className="text-sm font-medium text-ink">List Name</label>
                  <Input
                    placeholder="e.g., Date Night Spots"
                    value={newListData.name}
                    onChange={(e) => setNewListData({ ...newListData, name: e.target.value })}
                    className="mt-1"
                    data-testid="new-list-name-input"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-ink">Description (optional)</label>
                  <Textarea
                    placeholder="What's this list about?"
                    value={newListData.description}
                    onChange={(e) => setNewListData({ ...newListData, description: e.target.value })}
                    className="mt-1"
                    data-testid="new-list-description-input"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setShowCreateDialog(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateList}
                  disabled={creatingList}
                  className="bg-tomato hover:bg-tomato-hover text-white"
                  data-testid="confirm-create-list-btn"
                >
                  {creatingList ? "Creating..." : "Create List"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      {/* Content */}
      <div className="px-4 py-6">
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl p-4 animate-pulse">
                <div className="h-5 bg-stone/20 rounded w-1/2 mb-2" />
                <div className="h-4 bg-stone/20 rounded w-1/4" />
              </div>
            ))}
          </div>
        ) : lists.length > 0 ? (
          <div className="space-y-4">
            {lists.map((list) => (
              <div
                key={list.id}
                className="bg-white rounded-xl shadow-sm border border-stone/10 overflow-hidden"
              >
                <button
                  onClick={() => handleSelectList(list)}
                  className="w-full p-4 flex items-center justify-between text-left hover:bg-paper/50 transition-colors"
                  data-testid={`list-item-${list.id}`}
                >
                  <div>
                    <h3 className="font-serif font-semibold text-ink">{list.name}</h3>
                    {list.description && (
                      <p className="text-sm text-stone mt-1 line-clamp-1">{list.description}</p>
                    )}
                    <p className="text-sm text-stone mt-1">
                      {list.pizzeria_ids?.length || 0} pizzeria{(list.pizzeria_ids?.length || 0) !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <ChevronRight size={20} className="text-stone" />
                </button>
                
                <div className="border-t border-stone/10 px-4 py-2 flex justify-end">
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <button
                        className="text-sm text-tomato hover:text-tomato-hover flex items-center gap-1"
                        data-testid={`delete-list-${list.id}`}
                      >
                        <Trash2 size={14} />
                        Delete
                      </button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete List</AlertDialogTitle>
                        <AlertDialogDescription>
                          Are you sure you want to delete "{list.name}"? This action cannot be undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => handleDeleteList(list.id)}
                          className="bg-tomato hover:bg-tomato-hover"
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
          <div className="text-center py-16">
            <List size={64} className="mx-auto text-stone/30 mb-4" />
            <h2 className="font-serif text-xl text-ink mb-2">No lists yet</h2>
            <p className="text-stone mb-6">
              Create your first list to organize your favorite pizzerias!
            </p>
            <Button
              onClick={() => setShowCreateDialog(true)}
              className="bg-tomato hover:bg-tomato-hover text-white"
            >
              <Plus size={18} className="mr-2" />
              Create Your First List
            </Button>
          </div>
        )}
      </div>

      {/* Tips */}
      {lists.length > 0 && (
        <div className="px-4 mt-8">
          <div className="bg-paper rounded-2xl p-5">
            <p className="font-hand text-lg text-terracotta -rotate-1 mb-2">Pro Tip!</p>
            <p className="text-sm text-ink/80">
              Create lists for different occasions - "Best for Groups", "Quick Lunch Spots", 
              or "Special Date Nights". Then add pizzerias from any pizzeria page!
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PizzaLists;
