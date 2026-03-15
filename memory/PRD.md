# Only Great Pizza Map Paris - PRD

## Original Problem Statement
Create a mobile and web application called "Only Great Pizza Map Paris" - a curated pizza guide focused on high-quality pizzerias in Paris. The app should feel like a mix between a map, a food guide, and a discovery tool, similar to European Coffee Trip.

## User Personas
1. **Tourists** - Visitors to Paris looking for authentic Italian pizza experiences
2. **Local Foodies** - Parisians who want to discover the best pizza spots in their city
3. **Casual Diners** - People looking for a quick, quality pizza meal nearby

## Design System (Updated March 14, 2026)
- **Typography**: Antonio (condensed, uppercase headings), DM Sans (body), Caveat (accents)
- **Colors**: Cream (#FDFBF7), Deep Brick (#9B2226), Olive (#606C38), Gold (#DDA15E), Ink (#1A1A1A)
- **Style**: Architectural, minimalist, sharp corners, elegant
- **Map Pins**: Custom illustrated pizza slice inside teardrop (brick=Neapolitan, gold=Roman)
- **Images**: Grayscale-to-color hover effect

## Tech Stack
- **Frontend**: React with Tailwind CSS, Leaflet/OpenStreetMap
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT-based
- **PWA**: Service Worker for offline support

## What's Been Implemented

### Backend (Complete)
- [x] User authentication (register, login, JWT tokens)
- [x] Pizzeria endpoints (list, detail, filter, random/surprise)
- [x] Favorites system (add, remove, list)
- [x] Pizza lists (CRUD, add/remove pizzerias)
- [x] **43 curated pizzerias** (31 Neapolitan, 12 Roman) with editorial descriptions
- [x] **Real-time wait time simulation** based on time of day & popularity
- [x] **User reviews system** (create, read, delete)
- [x] **GPS distance calculation** (Haversine formula)
- [x] **Sorting** by rating, distance, or wait time
- [x] **Idempotent POST /api/pizzerias** - prevents duplicate entries

### Frontend (Complete)
- [x] Interactive Map with OpenStreetMap + Leaflet
- [x] **Custom illustrated pizza pins** (minimalist, elegant SVG design)
- [x] Explore page with grid layout (43 pizzerias)
- [x] **Grayscale-to-color hover effect** on images
- [x] **Antonio condensed uppercase typography**
- [x] Filter system (style, dough, authenticity)
- [x] Search functionality
- [x] Sort by rating, distance, or wait time
- [x] "Use My Location" button for GPS-based sorting
- [x] Pizzeria detail page with photos gallery
- [x] Wait time display with crowd level and refresh button
- [x] User reviews section with star ratings
- [x] Auth pages (login/register)
- [x] Favorites page
- [x] Pizza Lists page
- [x] Navigation (Map, Explore, Favorites, Lists)
- [x] "Surprise me" feature
- [x] **PWA support** (manifest.json, service worker, offline page)
- [x] **Admin Panel** (/admin route) for CRUD operations

## Latest Updates (March 15, 2026)

### Admin Panel Testing Complete ✓
- All CRUD operations verified working (100% pass rate)
- Search by name and neighborhood working
- Add/Edit/Delete pizzeria forms functional
- Form validation, badges, and characteristics all working
- Testing agent added `/admin` route fix and test files

### Added 4 User-Requested Pizzerias:
1. **Ceprano** - 5 Rue Constant Berthaut, 75020 Paris (Jourdain) - 4.4★
2. **Brutti E Cattivi** - 6 Rue du Surmelin, 75020 Paris (Pelleport) - 4.7★
3. **Fratellino** - 11 Rue Saint-Lazare, 75009 Paris (Saint-Lazare) - 4.9★
4. **Libertino** (Big Mamma) - 44 Rue de Paradis, 75010 Paris (Gare du Nord) - 4.8★ (updated address)

### Fixed Data Duplication Issue:
- Made POST /api/pizzerias idempotent (checks for existing name before insert)
- Added pizzerias to seed data for persistence across restarts

## Data Notes
- Wait times are **SIMULATED** based on time of day and popularity
- Pizzeria data is **MOCK/CURATED** (not from Google Places API)

## Next Action Items
1. Complete Admin Panel testing
2. Add user profile page with account settings
3. Connect to real wait-time data source
4. Add photo upload capability for reviews
5. Consider premium partnerships for monetization
