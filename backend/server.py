from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'pizza-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

# Create the main app
app = FastAPI(title="Only Great Pizza Map Paris API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============ MODELS ============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    favorites: List[str] = []
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class PizzaListCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class PizzaListResponse(BaseModel):
    id: str
    name: str
    description: str
    pizzeria_ids: List[str]
    user_id: str
    created_at: str

class PizzeriaResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    address: str
    neighborhood: str
    latitude: float
    longitude: float
    google_rating: float
    review_count: int
    pizza_style: str  # neapolitan or roman
    description: str
    signature_pizzas: List[dict]
    photos: dict
    badges: List[str]
    filters: dict
    recommended_by: List[str]
    created_at: str

# ============ AUTH HELPERS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "favorites": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            favorites=[],
            created_at=user_doc["created_at"]
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            favorites=user.get("favorites", []),
            created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        favorites=current_user.get("favorites", []),
        created_at=current_user["created_at"]
    )

# ============ PIZZERIA ROUTES ============

@api_router.get("/pizzerias", response_model=List[PizzeriaResponse])
async def get_pizzerias(
    style: Optional[str] = None,
    sourdough: Optional[bool] = None,
    long_fermentation: Optional[bool] = None,
    gluten_free: Optional[bool] = None,
    italian_owners: Optional[bool] = None,
    italian_pizzaiolo: Optional[bool] = None,
    good_wine: Optional[bool] = None,
    famous_tiramisu: Optional[bool] = None
):
    query = {}
    if style:
        query["pizza_style"] = style
    if sourdough is not None:
        query["filters.sourdough"] = sourdough
    if long_fermentation is not None:
        query["filters.long_fermentation"] = long_fermentation
    if gluten_free is not None:
        query["filters.gluten_free"] = gluten_free
    if italian_owners is not None:
        query["filters.italian_owners"] = italian_owners
    if italian_pizzaiolo is not None:
        query["filters.italian_pizzaiolo"] = italian_pizzaiolo
    if good_wine is not None:
        query["filters.good_wine"] = good_wine
    if famous_tiramisu is not None:
        query["filters.famous_tiramisu"] = famous_tiramisu
    
    pizzerias = await db.pizzerias.find(query, {"_id": 0}).to_list(100)
    return pizzerias

@api_router.get("/pizzerias/{pizzeria_id}", response_model=PizzeriaResponse)
async def get_pizzeria(pizzeria_id: str):
    pizzeria = await db.pizzerias.find_one({"id": pizzeria_id}, {"_id": 0})
    if not pizzeria:
        raise HTTPException(status_code=404, detail="Pizzeria not found")
    return pizzeria

@api_router.get("/pizzerias/random/surprise")
async def surprise_me():
    pizzerias = await db.pizzerias.find({}, {"_id": 0}).to_list(100)
    if not pizzerias:
        raise HTTPException(status_code=404, detail="No pizzerias found")
    return random.choice(pizzerias)

# ============ FAVORITES ROUTES ============

@api_router.post("/favorites/{pizzeria_id}")
async def add_favorite(pizzeria_id: str, current_user: dict = Depends(get_current_user)):
    pizzeria = await db.pizzerias.find_one({"id": pizzeria_id})
    if not pizzeria:
        raise HTTPException(status_code=404, detail="Pizzeria not found")
    
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$addToSet": {"favorites": pizzeria_id}}
    )
    return {"message": "Added to favorites"}

@api_router.delete("/favorites/{pizzeria_id}")
async def remove_favorite(pizzeria_id: str, current_user: dict = Depends(get_current_user)):
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$pull": {"favorites": pizzeria_id}}
    )
    return {"message": "Removed from favorites"}

@api_router.get("/favorites", response_model=List[PizzeriaResponse])
async def get_favorites(current_user: dict = Depends(get_current_user)):
    favorite_ids = current_user.get("favorites", [])
    if not favorite_ids:
        return []
    pizzerias = await db.pizzerias.find({"id": {"$in": favorite_ids}}, {"_id": 0}).to_list(100)
    return pizzerias

# ============ PIZZA LISTS ROUTES ============

@api_router.post("/lists", response_model=PizzaListResponse)
async def create_list(list_data: PizzaListCreate, current_user: dict = Depends(get_current_user)):
    list_id = str(uuid.uuid4())
    list_doc = {
        "id": list_id,
        "name": list_data.name,
        "description": list_data.description or "",
        "pizzeria_ids": [],
        "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.pizza_lists.insert_one(list_doc)
    return PizzaListResponse(**list_doc)

@api_router.get("/lists", response_model=List[PizzaListResponse])
async def get_lists(current_user: dict = Depends(get_current_user)):
    lists = await db.pizza_lists.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
    return lists

@api_router.get("/lists/{list_id}", response_model=PizzaListResponse)
async def get_list(list_id: str, current_user: dict = Depends(get_current_user)):
    pizza_list = await db.pizza_lists.find_one(
        {"id": list_id, "user_id": current_user["id"]}, 
        {"_id": 0}
    )
    if not pizza_list:
        raise HTTPException(status_code=404, detail="List not found")
    return pizza_list

@api_router.post("/lists/{list_id}/pizzerias/{pizzeria_id}")
async def add_to_list(list_id: str, pizzeria_id: str, current_user: dict = Depends(get_current_user)):
    pizza_list = await db.pizza_lists.find_one({"id": list_id, "user_id": current_user["id"]})
    if not pizza_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    pizzeria = await db.pizzerias.find_one({"id": pizzeria_id})
    if not pizzeria:
        raise HTTPException(status_code=404, detail="Pizzeria not found")
    
    await db.pizza_lists.update_one(
        {"id": list_id},
        {"$addToSet": {"pizzeria_ids": pizzeria_id}}
    )
    return {"message": "Added to list"}

@api_router.delete("/lists/{list_id}/pizzerias/{pizzeria_id}")
async def remove_from_list(list_id: str, pizzeria_id: str, current_user: dict = Depends(get_current_user)):
    await db.pizza_lists.update_one(
        {"id": list_id, "user_id": current_user["id"]},
        {"$pull": {"pizzeria_ids": pizzeria_id}}
    )
    return {"message": "Removed from list"}

@api_router.delete("/lists/{list_id}")
async def delete_list(list_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.pizza_lists.delete_one({"id": list_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="List not found")
    return {"message": "List deleted"}

@api_router.get("/lists/{list_id}/pizzerias", response_model=List[PizzeriaResponse])
async def get_list_pizzerias(list_id: str, current_user: dict = Depends(get_current_user)):
    pizza_list = await db.pizza_lists.find_one({"id": list_id, "user_id": current_user["id"]}, {"_id": 0})
    if not pizza_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    pizzeria_ids = pizza_list.get("pizzeria_ids", [])
    if not pizzeria_ids:
        return []
    
    pizzerias = await db.pizzerias.find({"id": {"$in": pizzeria_ids}}, {"_id": 0}).to_list(100)
    return pizzerias

# ============ SEED DATA ============

@api_router.post("/seed")
async def seed_data():
    # Check if already seeded
    existing = await db.pizzerias.count_documents({})
    if existing > 0:
        return {"message": "Data already seeded", "count": existing}
    
    pizzerias = [
        {
            "id": "pz-001",
            "name": "Pizzeria Popolare",
            "address": "111 Rue Réaumur, 75002 Paris",
            "neighborhood": "Sentier",
            "latitude": 48.8676,
            "longitude": 2.3441,
            "google_rating": 4.8,
            "review_count": 3200,
            "pizza_style": "neapolitan",
            "description": "A buzzing trattoria by Big Mamma group serving authentic Neapolitan pizza with perfectly charred, airy crusts. The atmosphere is lively and energetic, with an open kitchen where you can watch pizzaiolos at work. Known for exceptional value and generous portions.",
            "signature_pizzas": [
                {"name": "Margherita", "description": "San Marzano tomatoes, fior di latte, fresh basil", "price": 8},
                {"name": "Burrata", "description": "Creamy burrata, cherry tomatoes, pesto", "price": 14},
                {"name": "Truffle", "description": "Truffle cream, mushrooms, mozzarella", "price": 16}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=800",
                "interior": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800",
                "chef": "https://images.unsplash.com/photo-1592498546551-222538011a27?w=800"
            },
            "badges": ["Best Margherita", "Italian Pizzaiolo", "Sourdough Dough"],
            "filters": {
                "sourdough": True,
                "long_fermentation": True,
                "gluten_free": False,
                "italian_owners": True,
                "italian_pizzaiolo": True,
                "good_wine": True,
                "famous_tiramisu": True
            },
            "recommended_by": ["Time Out", "Le Fooding"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-002",
            "name": "Pink Mamma",
            "address": "20bis Rue de Douai, 75009 Paris",
            "neighborhood": "Pigalle",
            "latitude": 48.8819,
            "longitude": 2.3328,
            "google_rating": 4.8,
            "review_count": 4500,
            "pizza_style": "neapolitan",
            "description": "A stunning five-story Italian palazzo with pink decor and Instagram-worthy interiors. The pizza features 72-hour fermented dough, resulting in an incredibly light and digestible crust. The rooftop terrace offers stunning views of Montmartre.",
            "signature_pizzas": [
                {"name": "Regina", "description": "Ham, mushrooms, mozzarella, olives", "price": 13},
                {"name": "Diavola", "description": "Spicy salami, tomato, mozzarella", "price": 12},
                {"name": "Quattro Formaggi", "description": "Four Italian cheeses blend", "price": 14}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800",
                "interior": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800",
                "chef": "https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=800"
            },
            "badges": ["Great Wine List", "Italian Owners", "Famous Tiramisu"],
            "filters": {
                "sourdough": True,
                "long_fermentation": True,
                "gluten_free": True,
                "italian_owners": True,
                "italian_pizzaiolo": True,
                "good_wine": True,
                "famous_tiramisu": True
            },
            "recommended_by": ["Le Bonbon", "Time Out"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-003",
            "name": "Ober Mamma",
            "address": "107 Boulevard Richard-Lenoir, 75011 Paris",
            "neighborhood": "Oberkampf",
            "latitude": 48.8633,
            "longitude": 2.3772,
            "google_rating": 4.9,
            "review_count": 2800,
            "pizza_style": "neapolitan",
            "description": "The original Big Mamma outpost that started the Italian revolution in Paris. Industrial-chic decor meets authentic Italian hospitality. Their pizzas are made with imported Italian flour and San Marzano tomatoes, baked in a traditional wood-fired oven.",
            "signature_pizzas": [
                {"name": "Margherita DOC", "description": "Buffalo mozzarella, basil, extra virgin olive oil", "price": 12},
                {"name": "Cacio e Pepe", "description": "Pecorino cream, black pepper, crispy guanciale", "price": 15},
                {"name": "Nduja", "description": "Spicy Calabrian nduja, stracciatella, honey", "price": 16}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1593560708920-61dd98c46a4e?w=800",
                "interior": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=800",
                "chef": "https://images.unsplash.com/photo-1581299894007-aaa50297cf16?w=800"
            },
            "badges": ["Best Margherita", "Sourdough Dough", "Italian Pizzaiolo"],
            "filters": {
                "sourdough": True,
                "long_fermentation": True,
                "gluten_free": False,
                "italian_owners": True,
                "italian_pizzaiolo": True,
                "good_wine": True,
                "famous_tiramisu": False
            },
            "recommended_by": ["Le Fooding", "Paris Bouge"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-004",
            "name": "Bijou",
            "address": "37 Rue du Faubourg Saint-Antoine, 75011 Paris",
            "neighborhood": "Bastille",
            "latitude": 48.8519,
            "longitude": 2.3719,
            "google_rating": 4.8,
            "review_count": 890,
            "pizza_style": "roman",
            "description": "A tiny gem specializing in Roman-style pizza al taglio. The rectangular pizzas are cut with scissors and sold by weight. Thin, crispy crust with a satisfying crunch. Perfect for a quick, authentic slice while exploring the Marais.",
            "signature_pizzas": [
                {"name": "Patate e Rosmarino", "description": "Thinly sliced potatoes, rosemary, olive oil", "price": 5},
                {"name": "Mortadella", "description": "Whipped ricotta, pistachio, mortadella", "price": 6},
                {"name": "Margherita Romana", "description": "Thin crispy base, tomato, mozzarella", "price": 4}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800",
                "interior": "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=800",
                "chef": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=800"
            },
            "badges": ["Italian Owners", "Gluten-Free Option", "Roman Style"],
            "filters": {
                "sourdough": False,
                "long_fermentation": True,
                "gluten_free": True,
                "italian_owners": True,
                "italian_pizzaiolo": True,
                "good_wine": False,
                "famous_tiramisu": False
            },
            "recommended_by": ["Le Bonbon"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-005",
            "name": "Mama Primi",
            "address": "71 Rue du Faubourg Saint-Denis, 75010 Paris",
            "neighborhood": "Strasbourg Saint-Denis",
            "latitude": 48.8716,
            "longitude": 2.3546,
            "google_rating": 4.8,
            "review_count": 1200,
            "pizza_style": "neapolitan",
            "description": "Another Big Mamma success story, Mama Primi brings the energy of Naples to the 10th arrondissement. The open kitchen lets you watch masters stretch dough, while the convivial atmosphere makes every meal feel like a celebration.",
            "signature_pizzas": [
                {"name": "Marinara", "description": "Tomato, garlic, oregano, olive oil (no cheese)", "price": 7},
                {"name": "Capricciosa", "description": "Artichokes, ham, mushrooms, olives", "price": 14},
                {"name": "Calabrese", "description": "Spicy sausage, peppers, onions", "price": 13}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=800",
                "interior": "https://images.unsplash.com/photo-1537047902294-62a40c20a6ae?w=800",
                "chef": "https://images.unsplash.com/photo-1595475207225-428b62bda831?w=800"
            },
            "badges": ["Italian Pizzaiolo", "Great Wine List", "Sourdough Dough"],
            "filters": {
                "sourdough": True,
                "long_fermentation": True,
                "gluten_free": False,
                "italian_owners": True,
                "italian_pizzaiolo": True,
                "good_wine": True,
                "famous_tiramisu": True
            },
            "recommended_by": ["Time Out", "Le Fooding"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-006",
            "name": "La Rotonda",
            "address": "14 Rue Jean Mermoz, 75008 Paris",
            "neighborhood": "Champs-Élysées",
            "latitude": 48.8688,
            "longitude": 2.3084,
            "google_rating": 4.9,
            "review_count": 650,
            "pizza_style": "neapolitan",
            "description": "An elegant pizzeria near the Champs-Élysées serving refined Neapolitan pizza. The dough is made with a secret family recipe and fermented for 48 hours. Sophisticated atmosphere with attentive service and an excellent Italian wine selection.",
            "signature_pizzas": [
                {"name": "Tartufo Nero", "description": "Black truffle, fontina, porcini", "price": 24},
                {"name": "Salsiccia", "description": "Italian sausage, friarielli, smoked provola", "price": 18},
                {"name": "Margherita Verace", "description": "Certified authentic Neapolitan margherita", "price": 14}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1571997478779-2adcbbe9ab2f?w=800",
                "interior": "https://images.unsplash.com/photo-1559329007-40df8a9345d8?w=800",
                "chef": "https://images.unsplash.com/photo-1583394293214-28ez9dacac?w=800"
            },
            "badges": ["Best Margherita", "Great Wine List", "Famous Tiramisu"],
            "filters": {
                "sourdough": True,
                "long_fermentation": True,
                "gluten_free": True,
                "italian_owners": True,
                "italian_pizzaiolo": True,
                "good_wine": True,
                "famous_tiramisu": True
            },
            "recommended_by": ["Le Fooding", "Gault & Millau"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-007",
            "name": "Da Graziella",
            "address": "83 Rue Lepic, 75018 Paris",
            "neighborhood": "Montmartre",
            "latitude": 48.8867,
            "longitude": 2.3359,
            "google_rating": 4.8,
            "review_count": 720,
            "pizza_style": "neapolitan",
            "description": "A charming family-run pizzeria in the heart of Montmartre. Graziella herself often greets guests while her husband works the oven. The cozy interior with checkered tablecloths transports you straight to Naples. Their secret is the passion.",
            "signature_pizzas": [
                {"name": "Parma", "description": "Prosciutto di Parma, arugula, parmesan shavings", "price": 16},
                {"name": "Frutti di Mare", "description": "Mixed seafood, garlic, white wine", "price": 18},
                {"name": "Napoli", "description": "Anchovies, capers, olives, oregano", "price": 13}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1588315029754-2dd089d39a1a?w=800",
                "interior": "https://images.unsplash.com/photo-1555992336-fb0d29498b13?w=800",
                "chef": "https://images.unsplash.com/photo-1542834369-f10ebf06d3e0?w=800"
            },
            "badges": ["Italian Owners", "Italian Pizzaiolo", "Family Recipe"],
            "filters": {
                "sourdough": False,
                "long_fermentation": True,
                "gluten_free": False,
                "italian_owners": True,
                "italian_pizzaiolo": True,
                "good_wine": True,
                "famous_tiramisu": False
            },
            "recommended_by": ["Le Bonbon", "Paris Select"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-008",
            "name": "Faggio",
            "address": "27 Rue de Charonne, 75011 Paris",
            "neighborhood": "Bastille",
            "latitude": 48.8536,
            "longitude": 2.3752,
            "google_rating": 4.9,
            "review_count": 480,
            "pizza_style": "roman",
            "description": "A modern take on Roman pizza with a focus on high-quality, seasonal ingredients. The thin, crispy base is achieved through a special technique using olive oil in the dough. Minimalist decor with an emphasis on the craft of pizza making.",
            "signature_pizzas": [
                {"name": "Zucchine e Fiori", "description": "Zucchini, zucchini flowers, ricotta", "price": 15},
                {"name": "Prosciutto Crudo", "description": "24-month aged prosciutto, burrata", "price": 17},
                {"name": "Pomodoro Fresco", "description": "Fresh tomatoes, basil, garlic", "price": 12}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1600028068383-ea11a7a101f3?w=800",
                "interior": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=800",
                "chef": "https://images.unsplash.com/photo-1607631568010-a87245c0daf8?w=800"
            },
            "badges": ["Roman Style", "Sourdough Dough", "Seasonal Menu"],
            "filters": {
                "sourdough": True,
                "long_fermentation": True,
                "gluten_free": True,
                "italian_owners": False,
                "italian_pizzaiolo": True,
                "good_wine": True,
                "famous_tiramisu": False
            },
            "recommended_by": ["Time Out", "Le Fooding"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-009",
            "name": "Pizza Chic",
            "address": "13 Rue de Mézières, 75006 Paris",
            "neighborhood": "Saint-Germain",
            "latitude": 48.8507,
            "longitude": 2.3309,
            "google_rating": 4.8,
            "review_count": 920,
            "pizza_style": "neapolitan",
            "description": "Upscale Neapolitan pizza in the heart of Saint-Germain. The elegant setting attracts a fashionable crowd, but the pizza remains authentic. Known for their exceptional mozzarella di bufala imported directly from Campania twice weekly.",
            "signature_pizzas": [
                {"name": "Bufala", "description": "Premium buffalo mozzarella, cherry tomatoes", "price": 18},
                {"name": "Porcini", "description": "Wild porcini mushrooms, truffle oil, taleggio", "price": 22},
                {"name": "Vegetariana", "description": "Grilled vegetables, goat cheese, herbs", "price": 16}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1617343267017-e344bdc7ec94?w=800",
                "interior": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=800",
                "chef": "https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?w=800"
            },
            "badges": ["Best Margherita", "Great Wine List", "Italian Pizzaiolo"],
            "filters": {
                "sourdough": True,
                "long_fermentation": True,
                "gluten_free": False,
                "italian_owners": False,
                "italian_pizzaiolo": True,
                "good_wine": True,
                "famous_tiramisu": True
            },
            "recommended_by": ["Gault & Millau", "Le Fooding"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-010",
            "name": "Il Brigante",
            "address": "46 Rue Saint-Sabin, 75011 Paris",
            "neighborhood": "Bastille",
            "latitude": 48.8576,
            "longitude": 2.3697,
            "google_rating": 4.9,
            "review_count": 380,
            "pizza_style": "neapolitan",
            "description": "A hidden gem run by a passionate Neapolitan family. The small space creates an intimate atmosphere where every guest feels like family. Their dough recipe has been passed down for three generations, resulting in an incomparably light crust.",
            "signature_pizzas": [
                {"name": "Diavola Speciale", "description": "Double spicy salami, chili oil, honey drizzle", "price": 15},
                {"name": "Bianca", "description": "No tomato, ricotta, mozzarella, black pepper", "price": 14},
                {"name": "Tonno", "description": "Tuna, red onion, capers, oregano", "price": 15}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1573821663912-569905455b1c?w=800",
                "interior": "https://images.unsplash.com/photo-1533777857889-4be7c70b33f7?w=800",
                "chef": "https://images.unsplash.com/photo-1600565193348-f74bd3c7ccdf?w=800"
            },
            "badges": ["Italian Owners", "Italian Pizzaiolo", "Family Recipe", "Sourdough Dough"],
            "filters": {
                "sourdough": True,
                "long_fermentation": True,
                "gluten_free": False,
                "italian_owners": True,
                "italian_pizzaiolo": True,
                "good_wine": True,
                "famous_tiramisu": False
            },
            "recommended_by": ["Le Bonbon", "Paris Bouge"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-011",
            "name": "Eataly Paris",
            "address": "37 Rue Sainte-Croix de la Bretonnerie, 75004 Paris",
            "neighborhood": "Le Marais",
            "latitude": 48.8578,
            "longitude": 2.3527,
            "google_rating": 4.8,
            "review_count": 2100,
            "pizza_style": "roman",
            "description": "The famous Italian food emporium's Paris location offers Roman-style pizza al taglio alongside their market. Perfect for foodies who want to explore Italian ingredients. The pizza counter uses only products from the store's curated selection.",
            "signature_pizzas": [
                {"name": "Fiori di Zucca", "description": "Squash blossoms, anchovies, mozzarella", "price": 6},
                {"name": "Carciofi", "description": "Roman artichokes, pecorino, mint", "price": 5},
                {"name": "Porchetta", "description": "Slow-roasted pork, rosemary, fennel", "price": 7}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1590947132387-155cc02f3212?w=800",
                "interior": "https://images.unsplash.com/photo-1528698827591-e19ccd7bc23d?w=800",
                "chef": "https://images.unsplash.com/photo-1544148103-0773bf10d330?w=800"
            },
            "badges": ["Roman Style", "Italian Owners", "Gluten-Free Option"],
            "filters": {
                "sourdough": False,
                "long_fermentation": True,
                "gluten_free": True,
                "italian_owners": True,
                "italian_pizzaiolo": True,
                "good_wine": True,
                "famous_tiramisu": True
            },
            "recommended_by": ["Time Out", "Le Bonbon"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-012",
            "name": "Napoli Gang",
            "address": "5 Rue du Faubourg Montmartre, 75009 Paris",
            "neighborhood": "Grands Boulevards",
            "latitude": 48.8721,
            "longitude": 2.3433,
            "google_rating": 4.8,
            "review_count": 560,
            "pizza_style": "neapolitan",
            "description": "A lively pizzeria with a rock 'n' roll attitude. The neon lights and industrial decor create an energetic atmosphere. Don't let the casual vibe fool you - their pizzaiolo trained in Naples and takes the craft seriously.",
            "signature_pizzas": [
                {"name": "Margherita Gang", "description": "Classic with extra basil and a touch of chili", "price": 11},
                {"name": "Funghi Porcini", "description": "Fresh porcini, truffle paste, parmesan", "price": 17},
                {"name": "Speck", "description": "Alto Adige speck, arugula, grana padano", "price": 15}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=800",
                "interior": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=800",
                "chef": "https://images.unsplash.com/photo-1585238341710-4d3ff484184d?w=800"
            },
            "badges": ["Italian Pizzaiolo", "Sourdough Dough", "Great Wine List"],
            "filters": {
                "sourdough": True,
                "long_fermentation": True,
                "gluten_free": False,
                "italian_owners": False,
                "italian_pizzaiolo": True,
                "good_wine": True,
                "famous_tiramisu": False
            },
            "recommended_by": ["Le Fooding"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.pizzerias.insert_many(pizzerias)
    return {"message": "Data seeded successfully", "count": len(pizzerias)}

# ============ HEALTH CHECK ============

@api_router.get("/")
async def root():
    return {"message": "Only Great Pizza Map Paris API", "version": "1.0.0"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
