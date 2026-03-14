# Only Great Pizza Map Paris - PRD

## Original Problem Statement
Create a mobile and web application called "Only Great Pizza Map Paris" - a curated pizza guide focused on high-quality pizzerias in Paris. The app should feel like a mix between a map, a food guide, and a discovery tool, similar to European Coffee Trip.

## User Personas
1. **Tourists** - Visitors to Paris looking for authentic Italian pizza experiences
2. **Local Foodies** - Parisians who want to discover the best pizza spots in their city
3. **Casual Diners** - People looking for a quick, quality pizza meal nearby

## Core Requirements (Static)
- Interactive map with custom pizza-shaped pins
- Curated pizzeria listings (rating 4.8+, 200+ reviews, artisanal pizza)
- Filters by pizza style (Neapolitan/Roman), dough type, authenticity
- Detailed pizzeria pages with photos, badges, signature pizzas
- User accounts with favorites and custom lists
- "Surprise me" random discovery feature
- Editorial recommendations from food guides
- Real-time wait time information

## Tech Stack
- **Frontend**: React with Tailwind CSS, Leaflet/OpenStreetMap
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT-based

## What's Been Implemented (March 14, 2026)

### Backend
- [x] User authentication (register, login, JWT tokens)
- [x] Pizzeria endpoints (list, detail, filter, random/surprise)
- [x] Favorites system (add, remove, list)
- [x] Pizza lists (CRUD, add/remove pizzerias)
- [x] **40 curated pizzerias** (28 Neapolitan, 12 Roman) with editorial descriptions
- [x] **Real-time wait time simulation** based on time of day & popularity

### Frontend
- [x] Map View with OpenStreetMap + Leaflet
- [x] Custom pizza markers (red=Neapolitan, yellow=Roman)
- [x] Explore page with grid layout (40 pizzerias)
- [x] Filter system (style, dough, authenticity)
- [x] Search functionality
- [x] Pizzeria detail page with photos gallery
- [x] **Wait time display** with crowd level and refresh button
- [x] Auth pages (login/register)
- [x] Favorites page
- [x] Pizza Lists page with create/delete
- [x] Navigation (Map, Explore, Favorites, Lists)
- [x] "Surprise me" feature
- [x] Mediterranean design theme

## Prioritized Backlog

### P0 - Critical (Shipped)
- [x] Core map functionality
- [x] 40 curated pizzerias with descriptions
- [x] Real-time wait times
- [x] User authentication
- [x] Favorites & Lists system

### P1 - Important (Next Phase)
- [ ] User profile page with settings
- [ ] Distance calculation from user location
- [ ] Push notifications for wait time drops
- [ ] User reviews and ratings

### P2 - Nice to Have
- [ ] Offline mode / PWA
- [ ] Admin panel for managing pizzerias
- [ ] Integration with real Google Places API
- [ ] Reservation system integration
- [ ] Social sharing features

## Next Action Items
1. Add user profile page
2. Implement GPS distance calculation
3. Connect to real wait-time data source (if available)
4. Add user review submission
5. Consider PWA for offline access
