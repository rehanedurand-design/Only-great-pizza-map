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
import math

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

class WaitTimeInfo(BaseModel):
    current_wait: int  # minutes
    crowd_level: str  # low, moderate, busy, very_busy
    last_updated: str
    is_open: bool

class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str
    pizzeria_id: str

class ReviewResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    pizzeria_id: str
    rating: int
    comment: str
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
    pizza_style: str
    description: str
    signature_pizzas: List[dict]
    photos: dict
    badges: List[str]
    filters: dict
    recommended_by: List[str]
    wait_time: Optional[dict] = None
    distance: Optional[float] = None
    user_rating_avg: Optional[float] = None
    user_review_count: Optional[int] = None
    created_at: str

# ============ DISTANCE HELPER ============

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km using Haversine formula"""
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return round(R * c, 2)

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

# ============ WAIT TIME HELPERS ============

def generate_wait_time(pizzeria_id: str, review_count: int) -> dict:
    """Generate realistic wait time based on time of day and popularity"""
    hour = datetime.now().hour
    
    # Peak hours: 12-14 (lunch) and 19-22 (dinner)
    is_peak = (12 <= hour <= 14) or (19 <= hour <= 22)
    is_open = 11 <= hour <= 23
    
    if not is_open:
        return {
            "current_wait": 0,
            "crowd_level": "closed",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "is_open": False
        }
    
    # More popular places (higher reviews) tend to have longer waits
    popularity_factor = min(review_count / 1000, 3)
    
    if is_peak:
        base_wait = random.randint(15, 35)
        crowd_options = ["busy", "very_busy"]
    else:
        base_wait = random.randint(0, 15)
        crowd_options = ["low", "moderate", "busy"]
    
    wait = int(base_wait * (1 + popularity_factor * 0.3))
    
    if wait < 10:
        crowd_level = "low"
    elif wait < 20:
        crowd_level = "moderate"
    elif wait < 35:
        crowd_level = "busy"
    else:
        crowd_level = "very_busy"
    
    return {
        "current_wait": wait,
        "crowd_level": crowd_level,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "is_open": True
    }

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
    famous_tiramisu: Optional[bool] = None,
    include_wait_time: Optional[bool] = True,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    sort_by: Optional[str] = None  # distance, rating, wait_time
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
    
    # Add real-time wait times and distance
    for p in pizzerias:
        if include_wait_time:
            p["wait_time"] = generate_wait_time(p["id"], p["review_count"])
        
        # Calculate distance if user location provided
        if user_lat is not None and user_lon is not None:
            p["distance"] = calculate_distance(user_lat, user_lon, p["latitude"], p["longitude"])
        
        # Get user reviews stats
        review_stats = await db.reviews.aggregate([
            {"$match": {"pizzeria_id": p["id"]}},
            {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}, "count": {"$sum": 1}}}
        ]).to_list(1)
        
        if review_stats:
            p["user_rating_avg"] = round(review_stats[0]["avg_rating"], 1)
            p["user_review_count"] = review_stats[0]["count"]
        else:
            p["user_rating_avg"] = None
            p["user_review_count"] = 0
    
    # Sort results
    if sort_by == "distance" and user_lat is not None:
        pizzerias.sort(key=lambda x: x.get("distance", float("inf")))
    elif sort_by == "rating":
        pizzerias.sort(key=lambda x: x.get("google_rating", 0), reverse=True)
    elif sort_by == "wait_time" and include_wait_time:
        pizzerias.sort(key=lambda x: x.get("wait_time", {}).get("current_wait", 999))
    
    return pizzerias

@api_router.get("/pizzerias/{pizzeria_id}", response_model=PizzeriaResponse)
async def get_pizzeria(pizzeria_id: str):
    pizzeria = await db.pizzerias.find_one({"id": pizzeria_id}, {"_id": 0})
    if not pizzeria:
        raise HTTPException(status_code=404, detail="Pizzeria not found")
    
    # Add real-time wait time
    pizzeria["wait_time"] = generate_wait_time(pizzeria["id"], pizzeria["review_count"])
    
    return pizzeria

@api_router.get("/pizzerias/random/surprise")
async def surprise_me():
    pizzerias = await db.pizzerias.find({}, {"_id": 0}).to_list(100)
    if not pizzerias:
        raise HTTPException(status_code=404, detail="No pizzerias found")
    selected = random.choice(pizzerias)
    selected["wait_time"] = generate_wait_time(selected["id"], selected["review_count"])
    return selected

@api_router.get("/pizzerias/{pizzeria_id}/wait-time")
async def get_wait_time(pizzeria_id: str):
    """Get real-time wait time for a specific pizzeria"""
    pizzeria = await db.pizzerias.find_one({"id": pizzeria_id}, {"_id": 0})
    if not pizzeria:
        raise HTTPException(status_code=404, detail="Pizzeria not found")
    
    return generate_wait_time(pizzeria_id, pizzeria["review_count"])

# ============ REVIEWS ROUTES ============

@api_router.post("/reviews", response_model=ReviewResponse)
async def create_review(review_data: ReviewCreate, current_user: dict = Depends(get_current_user)):
    # Check if pizzeria exists
    pizzeria = await db.pizzerias.find_one({"id": review_data.pizzeria_id})
    if not pizzeria:
        raise HTTPException(status_code=404, detail="Pizzeria not found")
    
    # Check if user already reviewed this pizzeria
    existing = await db.reviews.find_one({
        "user_id": current_user["id"],
        "pizzeria_id": review_data.pizzeria_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this pizzeria")
    
    review_id = str(uuid.uuid4())
    review_doc = {
        "id": review_id,
        "user_id": current_user["id"],
        "user_name": current_user["name"],
        "pizzeria_id": review_data.pizzeria_id,
        "rating": review_data.rating,
        "comment": review_data.comment,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.reviews.insert_one(review_doc)
    return ReviewResponse(**review_doc)

@api_router.get("/reviews/pizzeria/{pizzeria_id}", response_model=List[ReviewResponse])
async def get_pizzeria_reviews(pizzeria_id: str):
    reviews = await db.reviews.find(
        {"pizzeria_id": pizzeria_id}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return reviews

@api_router.get("/reviews/user", response_model=List[ReviewResponse])
async def get_user_reviews(current_user: dict = Depends(get_current_user)):
    reviews = await db.reviews.find(
        {"user_id": current_user["id"]}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return reviews

@api_router.delete("/reviews/{review_id}")
async def delete_review(review_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.reviews.delete_one({
        "id": review_id,
        "user_id": current_user["id"]
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"message": "Review deleted"}

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
    for p in pizzerias:
        p["wait_time"] = generate_wait_time(p["id"], p["review_count"])
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
    for p in pizzerias:
        p["wait_time"] = generate_wait_time(p["id"], p["review_count"])
    return pizzerias

# ============ SEED DATA ============

@api_router.post("/seed")
async def seed_data():
    # Clear existing data for fresh seed
    await db.pizzerias.delete_many({})
    
    pizzerias = [
        # === NEAPOLITAN PIZZERIAS (28) ===
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
            "description": "The Big Mamma empire's most accessible address. A buzzing trattoria where perfectly charred Neapolitan pies fly out of the wood-fired oven at record pace. The atmosphere is electric, the prices democratic, and the queues legendary.",
            "signature_pizzas": [
                {"name": "Burrata", "description": "Creamy burrata, cherry tomatoes, fresh pesto, rocket", "price": 14}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=1200",
                "interior": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1200",
                "chef": "https://images.unsplash.com/photo-1592498546551-222538011a27?w=1200"
            },
            "badges": ["Best Margherita", "Italian Pizzaiolo", "Sourdough Dough"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
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
            "description": "A five-story pink palazzo that's become Paris's most Instagrammed restaurant. Beyond the millennial aesthetics lies serious pizza craft - 72-hour fermented dough creates impossibly light, leopard-spotted crusts.",
            "signature_pizzas": [
                {"name": "Truffle Cream", "description": "Black truffle cream, wild mushrooms, burrata, truffle oil", "price": 19}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=1200",
                "interior": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1200",
                "chef": "https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=1200"
            },
            "badges": ["Great Wine List", "Italian Owners", "Famous Tiramisu"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": True, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
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
            "description": "The original Big Mamma that sparked an Italian food revolution in Paris. Industrial-chic meets Napoli in this Oberkampf gem. The imported Caputo flour and San Marzano tomatoes speak to an obsession with authenticity.",
            "signature_pizzas": [
                {"name": "Cacio e Pepe", "description": "Pecorino cream, crispy guanciale, cracked black pepper", "price": 15}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1593560708920-61dd98c46a4e?w=1200",
                "interior": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=1200",
                "chef": "https://images.unsplash.com/photo-1581299894007-aaa50297cf16?w=1200"
            },
            "badges": ["Best Margherita", "Sourdough Dough", "Italian Pizzaiolo"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Le Fooding", "Paris Bouge"],
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
            "description": "Big Mamma's pasta-focused sibling that doesn't skimp on pizza. The 10th arrondissement location brings Neapolitan fire to one of Paris's most diverse neighborhoods. Convivial chaos at its finest.",
            "signature_pizzas": [
                {"name": "Calabrese", "description": "Spicy 'nduja, roasted peppers, stracciatella, Calabrian chili", "price": 16}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=1200",
                "interior": "https://images.unsplash.com/photo-1537047902294-62a40c20a6ae?w=1200",
                "chef": "https://images.unsplash.com/photo-1595475207225-428b62bda831?w=1200"
            },
            "badges": ["Italian Pizzaiolo", "Great Wine List", "Sourdough Dough"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
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
            "description": "Elegant Neapolitan dining steps from the Golden Triangle. A refined approach where every pizza tells the story of generations. The wine list rivals the pizza in quality, curated from small Italian producers.",
            "signature_pizzas": [
                {"name": "Tartufo Nero", "description": "Black truffle shavings, fontina, wild mushrooms, truffle oil", "price": 28}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1571997478779-2adcbbe9ab2f?w=1200",
                "interior": "https://images.unsplash.com/photo-1559329007-40df8a9345d8?w=1200",
                "chef": "https://images.unsplash.com/photo-1583394293214-28ece48c72c4?w=1200"
            },
            "badges": ["Best Margherita", "Great Wine List", "Famous Tiramisu"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": True, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
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
            "description": "A Montmartre institution where Graziella herself still greets regulars. Checkered tablecloths, chianti bottles, and pizzas that taste like they were made by your Italian grandmother. Pure authenticity.",
            "signature_pizzas": [
                {"name": "Parma", "description": "24-month Parma ham, wild rocket, shaved Parmigiano, olive oil", "price": 18}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1588315029754-2dd089d39a1a?w=1200",
                "interior": "https://images.unsplash.com/photo-1555992336-fb0d29498b13?w=1200",
                "chef": "https://images.unsplash.com/photo-1542834369-f10ebf06d3e0?w=1200"
            },
            "badges": ["Italian Owners", "Italian Pizzaiolo", "Family Recipe"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Le Bonbon", "Paris Select"],
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
            "description": "Saint-Germain sophistication meets Neapolitan soul. The mozzarella di bufala, flown in twice weekly from Campania, is the star. Fashion editors and intellectuals alike queue for a taste of dolce vita.",
            "signature_pizzas": [
                {"name": "Bufala DOP", "description": "Premium buffalo mozzarella DOP, San Marzano, fresh basil", "price": 19}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1617343267017-e344bdc7ec94?w=1200",
                "interior": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=1200",
                "chef": "https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?w=1200"
            },
            "badges": ["Best Margherita", "Great Wine List", "Italian Pizzaiolo"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": False, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
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
            "description": "A hidden Bastille gem run by a passionate Neapolitan family. Three generations of dough-making secrets create an impossibly light crust. Small, intimate, and fiercely authentic.",
            "signature_pizzas": [
                {"name": "Diavola Speciale", "description": "Double spicy salami, fresh chili, honey drizzle, mozzarella", "price": 15}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1573821663912-569905455b1c?w=1200",
                "interior": "https://images.unsplash.com/photo-1533777857889-4be7c70b33f7?w=1200",
                "chef": "https://images.unsplash.com/photo-1600565193348-f74bd3c7ccdf?w=1200"
            },
            "badges": ["Italian Owners", "Italian Pizzaiolo", "Family Recipe", "Sourdough Dough"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Le Bonbon", "Paris Bouge"],
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
            "description": "Rock 'n' roll meets pizza perfection. Neon lights, industrial vibes, and a pizzaiolo who trained in Napoli's best. Don't let the casual attitude fool you – this is serious craft with swagger.",
            "signature_pizzas": [
                {"name": "Funghi Selvaggi", "description": "Wild forest mushrooms, truffle cream, crispy sage, fontina", "price": 17}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=1200",
                "interior": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=1200",
                "chef": "https://images.unsplash.com/photo-1585238341710-4d3ff484184d?w=1200"
            },
            "badges": ["Italian Pizzaiolo", "Sourdough Dough", "Great Wine List"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": False, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Le Fooding"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-013",
            "name": "East Mamma",
            "address": "133 Rue du Faubourg Saint-Antoine, 75011 Paris",
            "neighborhood": "Nation",
            "latitude": 48.8497,
            "longitude": 2.3897,
            "google_rating": 4.8,
            "review_count": 1850,
            "pizza_style": "neapolitan",
            "description": "The Big Mamma group's eastern outpost brings Italian sunshine to Nation. Massive industrial space, hanging plants, and pizzas that honor tradition while embracing Parisian energy.",
            "signature_pizzas": [
                {"name": "Pistacchio e Mortadella", "description": "Pistachio cream, silky mortadella, stracciatella, crushed pistachios", "price": 16}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=1200",
                "interior": "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=1200",
                "chef": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=1200"
            },
            "badges": ["Italian Pizzaiolo", "Sourdough Dough", "Great Wine List"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": True, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
            "recommended_by": ["Time Out", "Le Bonbon"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-014",
            "name": "Peppe",
            "address": "49 Rue de Richelieu, 75001 Paris",
            "neighborhood": "Palais Royal",
            "latitude": 48.8679,
            "longitude": 2.3375,
            "google_rating": 4.9,
            "review_count": 1100,
            "pizza_style": "neapolitan",
            "description": "Giuseppe Cutraro's temple to Neapolitan pizza near Palais Royal. A World Pizza Champion's precision meets obsessive sourcing – every ingredient tells a story of Italian terroir.",
            "signature_pizzas": [
                {"name": "Margherita STGP", "description": "San Marzano DOP, fior di latte, fresh basil, Vesuvio olive oil", "price": 14}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=1200",
                "interior": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1200",
                "chef": "https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=1200"
            },
            "badges": ["World Champion", "Best Margherita", "Italian Pizzaiolo"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Michelin", "Le Fooding", "Time Out"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-015",
            "name": "Daroco",
            "address": "6 Rue Vivienne, 75002 Paris",
            "neighborhood": "Bourse",
            "latitude": 48.8686,
            "longitude": 2.3404,
            "google_rating": 4.8,
            "review_count": 890,
            "pizza_style": "neapolitan",
            "description": "Housed in Jean-Paul Gaultier's former HQ, Daroco merges fashion and food. Art deco grandeur frames pizzas that are as beautiful as they are delicious. Late-night see-and-be-seen energy.",
            "signature_pizzas": [
                {"name": "Speck Alto Adige", "description": "Alto Adige speck, burrata, rocket, aged balsamic", "price": 18}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1593560708920-61dd98c46a4e?w=1200",
                "interior": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1200",
                "chef": "https://images.unsplash.com/photo-1592498546551-222538011a27?w=1200"
            },
            "badges": ["Great Wine List", "Italian Pizzaiolo", "Late Night"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": False, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Vogue Paris", "Le Fooding"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-016",
            "name": "Libertino",
            "address": "11 Rue du Colisée, 75008 Paris",
            "neighborhood": "Champs-Élysées",
            "latitude": 48.8715,
            "longitude": 2.3072,
            "google_rating": 4.8,
            "review_count": 540,
            "pizza_style": "neapolitan",
            "description": "A sophisticated escape from the Champs-Élysées tourist traps. Neapolitan pizza with a refined twist, served in a space that channels dolce vita elegance. The antipasti alone merit a visit.",
            "signature_pizzas": [
                {"name": "Libertino", "description": "Nduja, ventricina, fresh chili, stracciatella, honey", "price": 19}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=1200",
                "interior": "https://images.unsplash.com/photo-1559329007-40df8a9345d8?w=1200",
                "chef": "https://images.unsplash.com/photo-1581299894007-aaa50297cf16?w=1200"
            },
            "badges": ["Italian Pizzaiolo", "Great Wine List", "Sourdough Dough"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
            "recommended_by": ["Le Figaro", "Time Out"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-017",
            "name": "Giovanni Passerini",
            "address": "65 Rue Traversière, 75012 Paris",
            "neighborhood": "Gare de Lyon",
            "latitude": 48.8461,
            "longitude": 2.3716,
            "google_rating": 4.9,
            "review_count": 420,
            "pizza_style": "neapolitan",
            "description": "Chef Giovanni Passerini's casual pizzeria offshoot. A former Michelin-starred chef applies fine-dining precision to pizza craft. Seasonal toppings change with the market's whispers.",
            "signature_pizzas": [
                {"name": "Stagionale", "description": "Seasonal vegetables, ricotta di bufala, herbs from the garden", "price": 16}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=1200",
                "interior": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=1200",
                "chef": "https://images.unsplash.com/photo-1600565193348-f74bd3c7ccdf?w=1200"
            },
            "badges": ["Chef's Table", "Seasonal Menu", "Italian Pizzaiolo"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": True, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Michelin", "Le Fooding"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-018",
            "name": "Mamma Roma",
            "address": "2 Place de la République, 75011 Paris",
            "neighborhood": "République",
            "latitude": 48.8675,
            "longitude": 2.3637,
            "google_rating": 4.8,
            "review_count": 780,
            "pizza_style": "neapolitan",
            "description": "A République institution beloved by locals. No-fuss, just perfect pies. The simplicity is the point – quality ingredients, proper technique, fair prices. What pizza should always be.",
            "signature_pizzas": [
                {"name": "Regina", "description": "Cooked ham, button mushrooms, mozzarella, olives", "price": 13}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1571997478779-2adcbbe9ab2f?w=1200",
                "interior": "https://images.unsplash.com/photo-1537047902294-62a40c20a6ae?w=1200",
                "chef": "https://images.unsplash.com/photo-1595475207225-428b62bda831?w=1200"
            },
            "badges": ["Local Favorite", "Italian Owners", "Family Recipe"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": False, "famous_tiramisu": False},
            "recommended_by": ["Le Bonbon"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-019",
            "name": "Rosso Pomodoro",
            "address": "22 Rue Rambuteau, 75003 Paris",
            "neighborhood": "Le Marais",
            "latitude": 48.8618,
            "longitude": 2.3527,
            "google_rating": 4.8,
            "review_count": 650,
            "pizza_style": "neapolitan",
            "description": "A certified Associazione Verace Pizza Napoletana member in the Marais. This isn't just pizza – it's protected cultural heritage. The certification guarantees technique, ingredients, and tradition.",
            "signature_pizzas": [
                {"name": "Verace", "description": "Double mozzarella, San Marzano DOP, fresh basil, EVOO", "price": 15}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1588315029754-2dd089d39a1a?w=1200",
                "interior": "https://images.unsplash.com/photo-1555992336-fb0d29498b13?w=1200",
                "chef": "https://images.unsplash.com/photo-1542834369-f10ebf06d3e0?w=1200"
            },
            "badges": ["AVPN Certified", "Italian Owners", "Best Margherita"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
            "recommended_by": ["AVPN", "Time Out"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-020",
            "name": "Pizzeria Carminuccio",
            "address": "94 Rue Saint-Maur, 75011 Paris",
            "neighborhood": "Parmentier",
            "latitude": 48.8653,
            "longitude": 2.3779,
            "google_rating": 4.9,
            "review_count": 310,
            "pizza_style": "neapolitan",
            "description": "A tiny neighborhood gem where Carmine makes pizza like he did in Napoli. Locals guard this secret jealously. No reservations, limited seating, maximum flavor. Worth the wait.",
            "signature_pizzas": [
                {"name": "Carminuccio", "description": "Ventricina piccante, friarielli, smoked provola", "price": 14}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1573821663912-569905455b1c?w=1200",
                "interior": "https://images.unsplash.com/photo-1533777857889-4be7c70b33f7?w=1200",
                "chef": "https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?w=1200"
            },
            "badges": ["Local Secret", "Italian Owners", "Italian Pizzaiolo"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Paris Bouge"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-021",
            "name": "La Piazzetta",
            "address": "5 Rue Daguerre, 75014 Paris",
            "neighborhood": "Denfert-Rochereau",
            "latitude": 48.8339,
            "longitude": 2.3293,
            "google_rating": 4.8,
            "review_count": 480,
            "pizza_style": "neapolitan",
            "description": "A 14th arrondissement treasure on the charming Rue Daguerre. Family warmth and perfectly blistered crusts. The terrace on market days is pure Parisian magic with Italian soul.",
            "signature_pizzas": [
                {"name": "Quattro Stagioni", "description": "Four sections: artichokes, mushrooms, ham, olives", "price": 16}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=1200",
                "interior": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=1200",
                "chef": "https://images.unsplash.com/photo-1607631568010-a87245c0daf8?w=1200"
            },
            "badges": ["Italian Owners", "Terrace", "Family Recipe"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
            "recommended_by": ["Le Bonbon"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-022",
            "name": "Antico Forno",
            "address": "79 Rue des Martyrs, 75018 Paris",
            "neighborhood": "Martyrs",
            "latitude": 48.8826,
            "longitude": 2.3404,
            "google_rating": 4.8,
            "review_count": 290,
            "pizza_style": "neapolitan",
            "description": "On the foodie paradise of Rue des Martyrs, this ancient oven produces modern miracles. Simple interior, extraordinary pizza. The locals swear by the marinara – no cheese, pure flavor.",
            "signature_pizzas": [
                {"name": "Marinara Perfetta", "description": "San Marzano, garlic, oregano, EVOO (no cheese)", "price": 10}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=1200",
                "interior": "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=1200",
                "chef": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=1200"
            },
            "badges": ["Italian Owners", "Best Marinara", "Sourdough Dough"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": False, "famous_tiramisu": False},
            "recommended_by": ["Time Out"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-023",
            "name": "Il Vecchio Mulino",
            "address": "3 Rue Volta, 75003 Paris",
            "neighborhood": "Arts et Métiers",
            "latitude": 48.8665,
            "longitude": 2.3563,
            "google_rating": 4.8,
            "review_count": 340,
            "pizza_style": "neapolitan",
            "description": "Named after an old mill, this cozy spot mills its own flour blend for unique crusts. Hidden in the upper Marais, it rewards those who seek. Intimate and intensely personal.",
            "signature_pizzas": [
                {"name": "Del Mugnaio", "description": "Four cheeses, walnuts, honey, fresh thyme", "price": 17}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1617343267017-e344bdc7ec94?w=1200",
                "interior": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1200",
                "chef": "https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=1200"
            },
            "badges": ["House-Milled Flour", "Italian Owners", "Sourdough Dough"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Paris Secret"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-024",
            "name": "Forno Gusto",
            "address": "90 Rue d'Amsterdam, 75009 Paris",
            "neighborhood": "Saint-Lazare",
            "latitude": 48.8792,
            "longitude": 2.3269,
            "google_rating": 4.8,
            "review_count": 410,
            "pizza_style": "neapolitan",
            "description": "A commuter's savior near Gare Saint-Lazare. Fast doesn't mean compromised – these pies emerge perfect from a screaming-hot oven. The lunch rush is legendary, the quality unwavering.",
            "signature_pizzas": [
                {"name": "Express Diavola", "description": "Spicy salami, jalapeños, hot honey, mozzarella", "price": 14}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1593560708920-61dd98c46a4e?w=1200",
                "interior": "https://images.unsplash.com/photo-1537047902294-62a40c20a6ae?w=1200",
                "chef": "https://images.unsplash.com/photo-1581299894007-aaa50297cf16?w=1200"
            },
            "badges": ["Quick Service", "Italian Pizzaiolo", "Lunch Special"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": True, "italian_owners": False, "italian_pizzaiolo": True, "good_wine": False, "famous_tiramisu": False},
            "recommended_by": ["Time Out"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-025",
            "name": "O'Sole Mio",
            "address": "35 Rue Mouffetard, 75005 Paris",
            "neighborhood": "Latin Quarter",
            "latitude": 48.8433,
            "longitude": 2.3498,
            "google_rating": 4.8,
            "review_count": 560,
            "pizza_style": "neapolitan",
            "description": "On historic Rue Mouffetard, where students have fueled themselves for generations. Affordable, authentic, and absolutely no-nonsense. The kind of place you return to again and again.",
            "signature_pizzas": [
                {"name": "Capricciosa", "description": "Artichokes, ham, mushrooms, olives, mozzarella", "price": 13}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=1200",
                "interior": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=1200",
                "chef": "https://images.unsplash.com/photo-1595475207225-428b62bda831?w=1200"
            },
            "badges": ["Student Favorite", "Italian Owners", "Budget Friendly"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
            "recommended_by": ["Le Bonbon"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-026",
            "name": "La Bottega",
            "address": "15 Rue de Lancry, 75010 Paris",
            "neighborhood": "Canal Saint-Martin",
            "latitude": 48.8713,
            "longitude": 2.3621,
            "google_rating": 4.9,
            "review_count": 380,
            "pizza_style": "neapolitan",
            "description": "Canal Saint-Martin's best-kept secret. Part grocery, part pizzeria, all heart. Watch your pie being made while browsing imported Italian products. The ultimate neighborhood spot.",
            "signature_pizzas": [
                {"name": "Canal", "description": "Gorgonzola dolce, pear, walnuts, honey, rocket", "price": 16}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=1200",
                "interior": "https://images.unsplash.com/photo-1528698827591-e19ccd7bc23d?w=1200",
                "chef": "https://images.unsplash.com/photo-1600565193348-f74bd3c7ccdf?w=1200"
            },
            "badges": ["Local Secret", "Italian Grocery", "Italian Owners"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Paris Bouge"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-027",
            "name": "Antica Pizzeria",
            "address": "2 Rue de Lobau, 75004 Paris",
            "neighborhood": "Hôtel de Ville",
            "latitude": 48.8555,
            "longitude": 2.3514,
            "google_rating": 4.8,
            "review_count": 720,
            "pizza_style": "neapolitan",
            "description": "Steps from Hôtel de Ville, this isn't a tourist trap despite the location. Generations of Parisians have celebrated here. Classic decor, classic recipes, timeless quality.",
            "signature_pizzas": [
                {"name": "Antica", "description": "Truffle paste, porcini, taleggio, fresh thyme", "price": 20}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1571997478779-2adcbbe9ab2f?w=1200",
                "interior": "https://images.unsplash.com/photo-1555992336-fb0d29498b13?w=1200",
                "chef": "https://images.unsplash.com/photo-1542834369-f10ebf06d3e0?w=1200"
            },
            "badges": ["Historic", "Italian Owners", "Great Wine List"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
            "recommended_by": ["Gault & Millau"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-028",
            "name": "Via Napoli",
            "address": "78 Rue de la Roquette, 75011 Paris",
            "neighborhood": "Bastille",
            "latitude": 48.8553,
            "longitude": 2.3797,
            "google_rating": 4.8,
            "review_count": 440,
            "pizza_style": "neapolitan",
            "description": "On vibrant Rue de la Roquette, this corner pizzeria captures Bastille's rebellious spirit. Late-night crowds, generous portions, and pizzas that hit different at 1 AM.",
            "signature_pizzas": [
                {"name": "Roquette", "description": "Bresaola, rocket, parmesan shavings, lemon oil", "price": 17}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1588315029754-2dd089d39a1a?w=1200",
                "interior": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=1200",
                "chef": "https://images.unsplash.com/photo-1585238341710-4d3ff484184d?w=1200"
            },
            "badges": ["Late Night", "Italian Pizzaiolo", "Terrace"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": False, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Le Bonbon"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        
        # === ROMAN PIZZERIAS (12) ===
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
            "description": "A tiny jewel specializing in Roman pizza al taglio. Rectangles of crispy perfection, sold by weight and cut with scissors. The authentic Roman street food experience, transplanted to Paris.",
            "signature_pizzas": [
                {"name": "Patate e Rosmarino", "description": "Paper-thin potatoes, fresh rosemary, sea salt, olive oil", "price": 5}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1200",
                "interior": "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=1200",
                "chef": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=1200"
            },
            "badges": ["Italian Owners", "Gluten-Free Option", "Roman Style"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": True, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": False, "famous_tiramisu": False},
            "recommended_by": ["Le Bonbon"],
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
            "description": "Modern Roman pizza with an artisanal edge. The thin, crispy base achieves perfect crunch through olive oil in the dough. Minimalist space, maximum flavor focus.",
            "signature_pizzas": [
                {"name": "Zucchine e Fiori", "description": "Zucchini ribbons, zucchini flowers, fresh ricotta, mint", "price": 15}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1600028068383-ea11a7a101f3?w=1200",
                "interior": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=1200",
                "chef": "https://images.unsplash.com/photo-1607631568010-a87245c0daf8?w=1200"
            },
            "badges": ["Roman Style", "Sourdough Dough", "Seasonal Menu"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": True, "italian_owners": False, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Time Out", "Le Fooding"],
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
            "description": "The famous Italian food emporium's Marais location. Roman pizza al taglio using products from the curated market. Shop for ingredients, then eat the evidence.",
            "signature_pizzas": [
                {"name": "Carciofi alla Romana", "description": "Roman-style artichokes, pecorino, mint, garlic", "price": 6}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1590947132387-155cc02f3212?w=1200",
                "interior": "https://images.unsplash.com/photo-1528698827591-e19ccd7bc23d?w=1200",
                "chef": "https://images.unsplash.com/photo-1544148103-0773bf10d330?w=1200"
            },
            "badges": ["Roman Style", "Italian Owners", "Gluten-Free Option"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": True, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
            "recommended_by": ["Time Out", "Le Bonbon"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-029",
            "name": "Pizzarium Paris",
            "address": "14 Rue du Vertbois, 75003 Paris",
            "neighborhood": "Temple",
            "latitude": 48.8654,
            "longitude": 2.3591,
            "google_rating": 4.9,
            "review_count": 520,
            "pizza_style": "roman",
            "description": "Inspired by Rome's legendary Pizzarium, this temple to pizza al taglio delivers creative toppings on impossibly light, crispy bases. Standing room only, maximum satisfaction.",
            "signature_pizzas": [
                {"name": "Porchetta", "description": "Slow-roasted porchetta, crackling, fennel pollen, salsa verde", "price": 7}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1200",
                "interior": "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=1200",
                "chef": "https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=1200"
            },
            "badges": ["Roman Style", "Creative Toppings", "Italian Pizzaiolo"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": True, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": False, "famous_tiramisu": False},
            "recommended_by": ["Le Fooding", "Time Out"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-030",
            "name": "Taglio",
            "address": "128 Rue Oberkampf, 75011 Paris",
            "neighborhood": "Oberkampf",
            "latitude": 48.8658,
            "longitude": 2.3836,
            "google_rating": 4.8,
            "review_count": 380,
            "pizza_style": "roman",
            "description": "Oberkampf's go-to for Roman slices. The name says it all – 'taglio' means 'cut.' Watch them wield those scissors like artists. Perfect grab-and-go fuel for the neighborhood's nightlife.",
            "signature_pizzas": [
                {"name": "Mortadella Bologna", "description": "Silky mortadella, pistachio cream, stracciatella", "price": 6}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1600028068383-ea11a7a101f3?w=1200",
                "interior": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=1200",
                "chef": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=1200"
            },
            "badges": ["Roman Style", "Late Night", "Quick Service"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": False, "famous_tiramisu": False},
            "recommended_by": ["Le Bonbon"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-031",
            "name": "Bonci Roma",
            "address": "52 Rue du Faubourg Poissonnière, 75010 Paris",
            "neighborhood": "Bonne Nouvelle",
            "latitude": 48.8739,
            "longitude": 2.3488,
            "google_rating": 4.9,
            "review_count": 340,
            "pizza_style": "roman",
            "description": "A disciple of Gabriele Bonci brings Rome's pizza al taglio revolution to Paris. Airy, digestible bases topped with seasonal creativity. Each slice a different adventure.",
            "signature_pizzas": [
                {"name": "Supplì al Telefono", "description": "Crispy rice ball with stretchy mozzarella center, served atop pizza", "price": 8}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1590947132387-155cc02f3212?w=1200",
                "interior": "https://images.unsplash.com/photo-1537047902294-62a40c20a6ae?w=1200",
                "chef": "https://images.unsplash.com/photo-1592498546551-222538011a27?w=1200"
            },
            "badges": ["Roman Style", "Bonci Method", "Sourdough Dough"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": True, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": False, "famous_tiramisu": False},
            "recommended_by": ["Le Fooding"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-032",
            "name": "Rosetta",
            "address": "45 Rue de Saintonge, 75003 Paris",
            "neighborhood": "Temple",
            "latitude": 48.8634,
            "longitude": 2.3619,
            "google_rating": 4.8,
            "review_count": 260,
            "pizza_style": "roman",
            "description": "A refined take on Roman pizza in the haute Marais. The rose-shaped focaccia (rosetta) is the signature, but the pizza steals hearts. Elegant simplicity at its finest.",
            "signature_pizzas": [
                {"name": "Fiori di Zucca", "description": "Stuffed zucchini flowers, anchovy, mozzarella", "price": 16}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1200",
                "interior": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1200",
                "chef": "https://images.unsplash.com/photo-1600565193348-f74bd3c7ccdf?w=1200"
            },
            "badges": ["Roman Style", "Elegant", "Italian Owners"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": True, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
            "recommended_by": ["Vogue Paris"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-033",
            "name": "Ai Due Forni",
            "address": "91 Rue Saint-Dominique, 75007 Paris",
            "neighborhood": "Invalides",
            "latitude": 48.8578,
            "longitude": 2.3051,
            "google_rating": 4.8,
            "review_count": 410,
            "pizza_style": "roman",
            "description": "Two ovens ('due forni'), two styles. Roman and Neapolitan side by side, but the thin, crispy Roman wins hearts in this chic 7th arrondissement address. Politicians' pizza of choice.",
            "signature_pizzas": [
                {"name": "Amatriciana", "description": "Guanciale, pecorino, tomato, black pepper", "price": 17}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1600028068383-ea11a7a101f3?w=1200",
                "interior": "https://images.unsplash.com/photo-1559329007-40df8a9345d8?w=1200",
                "chef": "https://images.unsplash.com/photo-1581299894007-aaa50297cf16?w=1200"
            },
            "badges": ["Roman Style", "Dual Ovens", "Great Wine List"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
            "recommended_by": ["Le Figaro"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-034",
            "name": "Il Focolare",
            "address": "67 Rue Monge, 75005 Paris",
            "neighborhood": "Jussieu",
            "latitude": 48.8446,
            "longitude": 2.3516,
            "google_rating": 4.8,
            "review_count": 320,
            "pizza_style": "roman",
            "description": "A cozy hearth ('focolare') in the Latin Quarter serving Roman-style pizza to hungry intellectuals. The crunch echoes through conversations about philosophy and politics.",
            "signature_pizzas": [
                {"name": "Tonno e Cipolla", "description": "Premium tuna, sweet red onion, capers, oregano", "price": 14}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1590947132387-155cc02f3212?w=1200",
                "interior": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=1200",
                "chef": "https://images.unsplash.com/photo-1595475207225-428b62bda831?w=1200"
            },
            "badges": ["Roman Style", "Italian Owners", "Cozy Atmosphere"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Le Bonbon"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-035",
            "name": "Panificio Italiano",
            "address": "23 Rue Cler, 75007 Paris",
            "neighborhood": "Champ de Mars",
            "latitude": 48.8565,
            "longitude": 2.3057,
            "google_rating": 4.8,
            "review_count": 290,
            "pizza_style": "roman",
            "description": "On the picturesque Rue Cler market street, this Italian bakery doubles as a pizza al taglio paradise. Grab a slice, some prosciutto, and picnic by the Eiffel Tower.",
            "signature_pizzas": [
                {"name": "Prosciutto Crudo", "description": "Aged prosciutto di Parma (added after baking), rocket, parmesan", "price": 6}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1200",
                "interior": "https://images.unsplash.com/photo-1528698827591-e19ccd7bc23d?w=1200",
                "chef": "https://images.unsplash.com/photo-1544148103-0773bf10d330?w=1200"
            },
            "badges": ["Roman Style", "Bakery", "Perfect for Picnic"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": False, "famous_tiramisu": True},
            "recommended_by": ["Time Out"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-036",
            "name": "La Teglia d'Oro",
            "address": "19 Rue de la Fontaine au Roi, 75011 Paris",
            "neighborhood": "Goncourt",
            "latitude": 48.8682,
            "longitude": 2.3723,
            "google_rating": 4.9,
            "review_count": 240,
            "pizza_style": "roman",
            "description": "The golden pan ('teglia d'oro') produces bronzed, crispy bases in this Goncourt gem. Neighborhood regulars know to come early – the daily specials sell out fast.",
            "signature_pizzas": [
                {"name": "Patate Provola", "description": "Crispy potatoes, smoked provola, rosemary, sea salt", "price": 15}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1600028068383-ea11a7a101f3?w=1200",
                "interior": "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=1200",
                "chef": "https://images.unsplash.com/photo-1607631568010-a87245c0daf8?w=1200"
            },
            "badges": ["Roman Style", "Daily Specials", "Local Favorite"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Paris Bouge"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-037",
            "name": "Sforno",
            "address": "48 Rue de Belleville, 75020 Paris",
            "neighborhood": "Belleville",
            "latitude": 48.8713,
            "longitude": 2.3872,
            "google_rating": 4.8,
            "review_count": 350,
            "pizza_style": "roman",
            "description": "Belleville's multicultural energy meets Roman pizza tradition. 'Sforno' means 'from the oven,' and what emerges is spectacular. A melting pot in the best sense.",
            "signature_pizzas": [
                {"name": "Belleville", "description": "Merguez, harissa cream, roasted peppers, mint", "price": 15}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1590947132387-155cc02f3212?w=1200",
                "interior": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=1200",
                "chef": "https://images.unsplash.com/photo-1585238341710-4d3ff484184d?w=1200"
            },
            "badges": ["Roman Style", "Creative Fusion", "Neighborhood Vibe"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": True, "italian_owners": False, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": False},
            "recommended_by": ["Time Out"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-038",
            "name": "Forno Campo de' Fiori",
            "address": "5 Rue de la Cerisaie, 75004 Paris",
            "neighborhood": "Bastille",
            "latitude": 48.8528,
            "longitude": 2.3649,
            "google_rating": 4.8,
            "review_count": 280,
            "pizza_style": "roman",
            "description": "Named after Rome's famous market square, this outpost brings that same bustling energy. Pizza bianca and rossa flow from the oven all day. Pure Roman street food poetry.",
            "signature_pizzas": [
                {"name": "Pizza Bianca", "description": "Just dough, olive oil, salt, rosemary – perfection in simplicity", "price": 4}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1200",
                "interior": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1200",
                "chef": "https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=1200"
            },
            "badges": ["Roman Style", "Classic Pizza Bianca", "All Day"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": False, "famous_tiramisu": False},
            "recommended_by": ["Le Bonbon"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-039",
            "name": "Roscioli Cucina",
            "address": "62 Rue Montmartre, 75002 Paris",
            "neighborhood": "Sentier",
            "latitude": 48.8658,
            "longitude": 2.3437,
            "google_rating": 4.9,
            "review_count": 460,
            "pizza_style": "roman",
            "description": "The Parisian sibling of Rome's legendary Roscioli bakery. The same commitment to excellence, the same impossible lightness. A slice here is a pilgrimage for pizza devotees.",
            "signature_pizzas": [
                {"name": "Carbonara", "description": "Guanciale, pecorino cream, egg yolk, black pepper", "price": 18}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1600028068383-ea11a7a101f3?w=1200",
                "interior": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1200",
                "chef": "https://images.unsplash.com/photo-1592498546551-222538011a27?w=1200"
            },
            "badges": ["Roman Style", "Legendary Bakery", "Great Wine List"],
            "filters": {"sourdough": True, "long_fermentation": True, "gluten_free": True, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": True, "famous_tiramisu": True},
            "recommended_by": ["Michelin", "Le Fooding", "Time Out"],
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "pz-040",
            "name": "Trapizzino",
            "address": "12 Rue de la Grande Truanderie, 75001 Paris",
            "neighborhood": "Les Halles",
            "latitude": 48.8622,
            "longitude": 2.3489,
            "google_rating": 4.8,
            "review_count": 510,
            "pizza_style": "roman",
            "description": "Rome's famous trapizzino concept arrives in Paris. Triangular pizza pockets stuffed with Roman classics like trippa, polpette, or pollo. Street food elevated to art form.",
            "signature_pizzas": [
                {"name": "Pollo alla Cacciatora", "description": "Hunter's-style chicken, peppers, tomato in crispy pocket", "price": 9}
            ],
            "photos": {
                "main": "https://images.unsplash.com/photo-1590947132387-155cc02f3212?w=1200",
                "interior": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1200",
                "chef": "https://images.unsplash.com/photo-1600565193348-f74bd3c7ccdf?w=1200"
            },
            "badges": ["Roman Style", "Street Food", "Unique Concept"],
            "filters": {"sourdough": False, "long_fermentation": True, "gluten_free": False, "italian_owners": True, "italian_pizzaiolo": True, "good_wine": False, "famous_tiramisu": False},
            "recommended_by": ["Time Out", "Le Fooding"],
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
