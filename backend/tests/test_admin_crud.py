"""
Backend API tests for Admin Panel CRUD operations
Tests: GET /api/pizzerias, POST /api/pizzerias (idempotent), PUT /api/pizzerias/{id}, DELETE /api/pizzerias/{id}
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://paris-pizzeria-map.preview.emergentagent.com')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestGetPizzerias:
    """Test GET /api/pizzerias endpoint"""
    
    def test_get_all_pizzerias(self, api_client):
        """Test fetching all pizzerias"""
        response = api_client.get(f"{BASE_URL}/api/pizzerias?include_wait_time=false")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 40  # Should have at least 40 pizzerias (43 seeded)
        print(f"Total pizzerias: {len(data)}")
        
    def test_pizzeria_has_required_fields(self, api_client):
        """Test that pizzerias have all required fields"""
        response = api_client.get(f"{BASE_URL}/api/pizzerias?include_wait_time=false")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        
        pizzeria = data[0]
        required_fields = ["id", "name", "address", "neighborhood", "latitude", "longitude", 
                          "google_rating", "review_count", "pizza_style", "description",
                          "signature_pizzas", "photos", "badges", "filters", "recommended_by"]
        
        for field in required_fields:
            assert field in pizzeria, f"Missing field: {field}"
            
    def test_filter_by_style_neapolitan(self, api_client):
        """Test filtering pizzerias by neapolitan style"""
        response = api_client.get(f"{BASE_URL}/api/pizzerias?style=neapolitan&include_wait_time=false")
        assert response.status_code == 200
        
        data = response.json()
        for pizzeria in data:
            assert pizzeria["pizza_style"] == "neapolitan"
        print(f"Neapolitan pizzerias: {len(data)}")
        
    def test_filter_by_style_roman(self, api_client):
        """Test filtering pizzerias by roman style"""
        response = api_client.get(f"{BASE_URL}/api/pizzerias?style=roman&include_wait_time=false")
        assert response.status_code == 200
        
        data = response.json()
        for pizzeria in data:
            assert pizzeria["pizza_style"] == "roman"
        print(f"Roman pizzerias: {len(data)}")


class TestCreatePizzeria:
    """Test POST /api/pizzerias endpoint (idempotent)"""
    
    def test_create_new_pizzeria(self, api_client):
        """Test creating a new pizzeria"""
        unique_name = f"TEST_Pizzeria_{uuid.uuid4().hex[:8]}"
        
        payload = {
            "name": unique_name,
            "address": "123 Test Street, 75001 Paris",
            "neighborhood": "Test District",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "google_rating": 4.5,
            "review_count": 100,
            "pizza_style": "neapolitan",
            "description": "A test pizzeria for automated testing",
            "signature_pizza_name": "Test Margherita",
            "signature_pizza_description": "Classic test pizza",
            "signature_pizza_price": 12,
            "badges": ["Test Badge"],
            "sourdough": True,
            "long_fermentation": True,
            "gluten_free": False,
            "italian_owners": True,
            "italian_pizzaiolo": True,
            "good_wine": False,
            "famous_tiramisu": False
        }
        
        response = api_client.post(f"{BASE_URL}/api/pizzerias", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == unique_name
        assert data["address"] == payload["address"]
        assert data["neighborhood"] == payload["neighborhood"]
        assert data["pizza_style"] == "neapolitan"
        assert "id" in data
        assert data["id"].startswith("pz-")
        
        # Verify data persisted - GET to confirm
        get_response = api_client.get(f"{BASE_URL}/api/pizzerias/{data['id']}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["name"] == unique_name
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/pizzerias/{data['id']}")
        print(f"Created and verified pizzeria: {unique_name}")
        
    def test_idempotent_create_updates_existing(self, api_client):
        """Test that POST with same name updates existing pizzeria (idempotent)"""
        unique_name = f"TEST_Idempotent_{uuid.uuid4().hex[:8]}"
        
        # First create
        payload1 = {
            "name": unique_name,
            "address": "Original Address",
            "neighborhood": "Original District",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "google_rating": 4.0,
            "review_count": 50,
            "pizza_style": "neapolitan",
            "description": "Original description",
            "signature_pizza_name": "Original Pizza",
            "signature_pizza_description": "Original",
            "signature_pizza_price": 10,
            "badges": [],
            "sourdough": False,
            "long_fermentation": True,
            "gluten_free": False,
            "italian_owners": False,
            "italian_pizzaiolo": False,
            "good_wine": False,
            "famous_tiramisu": False
        }
        
        response1 = api_client.post(f"{BASE_URL}/api/pizzerias", json=payload1)
        assert response1.status_code == 200
        original_id = response1.json()["id"]
        
        # Second create with same name but different data
        payload2 = {
            "name": unique_name,  # Same name
            "address": "Updated Address",  # Different address
            "neighborhood": "Updated District",
            "latitude": 48.8600,
            "longitude": 2.3600,
            "google_rating": 4.8,
            "review_count": 200,
            "pizza_style": "roman",  # Changed style
            "description": "Updated description",
            "signature_pizza_name": "Updated Pizza",
            "signature_pizza_description": "Updated",
            "signature_pizza_price": 15,
            "badges": ["Updated Badge"],
            "sourdough": True,
            "long_fermentation": True,
            "gluten_free": True,
            "italian_owners": True,
            "italian_pizzaiolo": True,
            "good_wine": True,
            "famous_tiramisu": True
        }
        
        response2 = api_client.post(f"{BASE_URL}/api/pizzerias", json=payload2)
        assert response2.status_code == 200
        
        data2 = response2.json()
        # Should have same ID (updated, not created new)
        assert data2["id"] == original_id
        # Should have updated values
        assert data2["address"] == "Updated Address"
        assert data2["pizza_style"] == "roman"
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/pizzerias/{original_id}")
        print(f"Verified idempotent behavior for: {unique_name}")
        
    def test_create_requires_name(self, api_client):
        """Test that name is required"""
        payload = {
            "address": "123 Test Street",
            "neighborhood": "Test",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "pizza_style": "neapolitan",
            "description": "Test",
            "signature_pizza_name": "Test",
            "signature_pizza_description": "Test",
            "signature_pizza_price": 10
        }
        
        response = api_client.post(f"{BASE_URL}/api/pizzerias", json=payload)
        assert response.status_code == 422  # Validation error
        
    def test_create_requires_address(self, api_client):
        """Test that address is required"""
        payload = {
            "name": f"TEST_NoAddress_{uuid.uuid4().hex[:8]}",
            "neighborhood": "Test",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "pizza_style": "neapolitan",
            "description": "Test",
            "signature_pizza_name": "Test",
            "signature_pizza_description": "Test",
            "signature_pizza_price": 10
        }
        
        response = api_client.post(f"{BASE_URL}/api/pizzerias", json=payload)
        assert response.status_code == 422  # Validation error


class TestUpdatePizzeria:
    """Test PUT /api/pizzerias/{id} endpoint"""
    
    def test_update_pizzeria(self, api_client):
        """Test updating an existing pizzeria"""
        # First create a pizzeria
        unique_name = f"TEST_Update_{uuid.uuid4().hex[:8]}"
        create_payload = {
            "name": unique_name,
            "address": "Original Address",
            "neighborhood": "Original",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "google_rating": 4.0,
            "review_count": 100,
            "pizza_style": "neapolitan",
            "description": "Original",
            "signature_pizza_name": "Original",
            "signature_pizza_description": "Original",
            "signature_pizza_price": 10,
            "badges": [],
            "sourdough": False,
            "long_fermentation": True,
            "gluten_free": False,
            "italian_owners": False,
            "italian_pizzaiolo": False,
            "good_wine": False,
            "famous_tiramisu": False
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/pizzerias", json=create_payload)
        assert create_response.status_code == 200
        pizzeria_id = create_response.json()["id"]
        
        # Update the pizzeria
        update_payload = {
            "name": f"{unique_name}_Updated",
            "address": "Updated Address",
            "neighborhood": "Updated District",
            "latitude": 48.8600,
            "longitude": 2.3600,
            "google_rating": 4.9,
            "review_count": 500,
            "pizza_style": "roman",
            "description": "Updated description",
            "signature_pizza_name": "Updated Pizza",
            "signature_pizza_description": "Updated",
            "signature_pizza_price": 18,
            "badges": ["Updated Badge"],
            "sourdough": True,
            "long_fermentation": True,
            "gluten_free": True,
            "italian_owners": True,
            "italian_pizzaiolo": True,
            "good_wine": True,
            "famous_tiramisu": True
        }
        
        update_response = api_client.put(f"{BASE_URL}/api/pizzerias/{pizzeria_id}", json=update_payload)
        assert update_response.status_code == 200
        
        updated_data = update_response.json()
        assert updated_data["name"] == f"{unique_name}_Updated"
        assert updated_data["address"] == "Updated Address"
        assert updated_data["pizza_style"] == "roman"
        
        # Verify persistence with GET
        get_response = api_client.get(f"{BASE_URL}/api/pizzerias/{pizzeria_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["name"] == f"{unique_name}_Updated"
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/pizzerias/{pizzeria_id}")
        print(f"Updated and verified pizzeria: {unique_name}")
        
    def test_update_nonexistent_pizzeria(self, api_client):
        """Test updating a non-existent pizzeria returns 404"""
        fake_id = "pz-nonexistent-12345"
        
        payload = {
            "name": "Test",
            "address": "Test Address",
            "neighborhood": "Test",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "google_rating": 4.0,
            "review_count": 100,
            "pizza_style": "neapolitan",
            "description": "Test",
            "signature_pizza_name": "Test",
            "signature_pizza_description": "Test",
            "signature_pizza_price": 10,
            "badges": [],
            "sourdough": False,
            "long_fermentation": True,
            "gluten_free": False,
            "italian_owners": False,
            "italian_pizzaiolo": False,
            "good_wine": False,
            "famous_tiramisu": False
        }
        
        response = api_client.put(f"{BASE_URL}/api/pizzerias/{fake_id}", json=payload)
        assert response.status_code == 404


class TestDeletePizzeria:
    """Test DELETE /api/pizzerias/{id} endpoint"""
    
    def test_delete_pizzeria(self, api_client):
        """Test deleting a pizzeria"""
        # First create a pizzeria
        unique_name = f"TEST_Delete_{uuid.uuid4().hex[:8]}"
        create_payload = {
            "name": unique_name,
            "address": "To Be Deleted",
            "neighborhood": "Test",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "google_rating": 4.0,
            "review_count": 100,
            "pizza_style": "neapolitan",
            "description": "Will be deleted",
            "signature_pizza_name": "Test",
            "signature_pizza_description": "Test",
            "signature_pizza_price": 10,
            "badges": [],
            "sourdough": False,
            "long_fermentation": True,
            "gluten_free": False,
            "italian_owners": False,
            "italian_pizzaiolo": False,
            "good_wine": False,
            "famous_tiramisu": False
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/pizzerias", json=create_payload)
        assert create_response.status_code == 200
        pizzeria_id = create_response.json()["id"]
        
        # Delete the pizzeria
        delete_response = api_client.delete(f"{BASE_URL}/api/pizzerias/{pizzeria_id}")
        assert delete_response.status_code == 200
        
        delete_data = delete_response.json()
        assert delete_data["message"] == "Pizzeria deleted"
        assert delete_data["id"] == pizzeria_id
        
        # Verify deletion with GET - should return 404
        get_response = api_client.get(f"{BASE_URL}/api/pizzerias/{pizzeria_id}")
        assert get_response.status_code == 404
        print(f"Deleted and verified removal: {unique_name}")
        
    def test_delete_nonexistent_pizzeria(self, api_client):
        """Test deleting a non-existent pizzeria returns 404"""
        fake_id = "pz-nonexistent-delete"
        
        response = api_client.delete(f"{BASE_URL}/api/pizzerias/{fake_id}")
        assert response.status_code == 404


class TestGetSinglePizzeria:
    """Test GET /api/pizzerias/{id} endpoint"""
    
    def test_get_single_pizzeria(self, api_client):
        """Test fetching a single pizzeria by ID"""
        # First get all pizzerias to get a valid ID
        list_response = api_client.get(f"{BASE_URL}/api/pizzerias?include_wait_time=false")
        assert list_response.status_code == 200
        pizzerias = list_response.json()
        assert len(pizzerias) > 0
        
        pizzeria_id = pizzerias[0]["id"]
        
        # Get single pizzeria
        response = api_client.get(f"{BASE_URL}/api/pizzerias/{pizzeria_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == pizzeria_id
        assert "name" in data
        assert "address" in data
        assert "wait_time" in data  # Single pizzeria includes wait time
        
    def test_get_nonexistent_pizzeria(self, api_client):
        """Test fetching a non-existent pizzeria returns 404"""
        fake_id = "pz-does-not-exist"
        
        response = api_client.get(f"{BASE_URL}/api/pizzerias/{fake_id}")
        assert response.status_code == 404


class TestCleanup:
    """Cleanup any remaining test data"""
    
    def test_cleanup_test_pizzerias(self, api_client):
        """Remove any TEST_ prefixed pizzerias"""
        response = api_client.get(f"{BASE_URL}/api/pizzerias?include_wait_time=false")
        assert response.status_code == 200
        
        pizzerias = response.json()
        test_pizzerias = [p for p in pizzerias if p["name"].startswith("TEST_")]
        
        for p in test_pizzerias:
            api_client.delete(f"{BASE_URL}/api/pizzerias/{p['id']}")
            print(f"Cleaned up: {p['name']}")
            
        print(f"Cleaned up {len(test_pizzerias)} test pizzerias")
