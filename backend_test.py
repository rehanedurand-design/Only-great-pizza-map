import requests
import sys
import json
from datetime import datetime

class PizzaAPITester:
    def __init__(self, base_url="https://paris-pizza-guide.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.log_test(name, True)
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n=== HEALTH CHECK TESTS ===")
        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_seed_data(self):
        """Test data seeding"""
        print("\n=== DATA SEEDING TESTS ===")
        success, response = self.run_test("Seed Data", "POST", "seed", 200)
        if success:
            print(f"   Seeded pizzerias: {response.get('count', 'unknown')}")

    def test_pizzeria_endpoints(self):
        """Test pizzeria-related endpoints"""
        print("\n=== PIZZERIA TESTS ===")
        
        # Get all pizzerias
        success, pizzerias = self.run_test("Get All Pizzerias", "GET", "pizzerias", 200)
        if success and pizzerias:
            print(f"   Found {len(pizzerias)} pizzerias")
            
            # Test individual pizzeria
            first_pizzeria = pizzerias[0]
            pizzeria_id = first_pizzeria['id']
            self.run_test("Get Single Pizzeria", "GET", f"pizzerias/{pizzeria_id}", 200)
            
            # Test filters
            self.run_test("Filter by Neapolitan", "GET", "pizzerias?style=neapolitan", 200)
            self.run_test("Filter by Roman", "GET", "pizzerias?style=roman", 200)
            self.run_test("Filter by Gluten Free", "GET", "pizzerias?gluten_free=true", 200)
            
        # Test surprise me
        self.run_test("Surprise Me", "GET", "pizzerias/random/surprise", 200)
        
        # Test non-existent pizzeria
        self.run_test("Non-existent Pizzeria", "GET", "pizzerias/invalid-id", 404)

    def test_auth_flow(self):
        """Test authentication flow"""
        print("\n=== AUTHENTICATION TESTS ===")
        
        # Generate unique test user
        timestamp = datetime.now().strftime('%H%M%S')
        test_email = f"test_user_{timestamp}@example.com"
        test_password = "TestPass123!"
        test_name = f"Test User {timestamp}"

        # Test registration
        success, response = self.run_test(
            "User Registration", 
            "POST", 
            "auth/register", 
            200,
            data={
                "email": test_email,
                "password": test_password,
                "name": test_name
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Registered user: {test_email}")
            
            # Test get current user
            self.run_test("Get Current User", "GET", "auth/me", 200)
            
            # Test login with same credentials
            success, login_response = self.run_test(
                "User Login",
                "POST",
                "auth/login",
                200,
                data={
                    "email": test_email,
                    "password": test_password
                }
            )
            
            if success and 'access_token' in login_response:
                self.token = login_response['access_token']
                print(f"   Login successful")
        
        # Test invalid login
        self.run_test(
            "Invalid Login",
            "POST",
            "auth/login",
            401,
            data={
                "email": "invalid@example.com",
                "password": "wrongpassword"
            }
        )
        
        # Test duplicate registration
        self.run_test(
            "Duplicate Registration",
            "POST",
            "auth/register",
            400,
            data={
                "email": test_email,
                "password": test_password,
                "name": test_name
            }
        )

    def test_favorites_flow(self):
        """Test favorites functionality"""
        print("\n=== FAVORITES TESTS ===")
        
        if not self.token:
            print("❌ Skipping favorites tests - no auth token")
            return
            
        # Get pizzerias first
        success, pizzerias = self.run_test("Get Pizzerias for Favorites", "GET", "pizzerias", 200)
        if not success or not pizzerias:
            print("❌ Cannot test favorites - no pizzerias available")
            return
            
        pizzeria_id = pizzerias[0]['id']
        
        # Test add to favorites
        self.run_test("Add to Favorites", "POST", f"favorites/{pizzeria_id}", 200)
        
        # Test get favorites
        success, favorites = self.run_test("Get Favorites", "GET", "favorites", 200)
        if success:
            print(f"   User has {len(favorites)} favorites")
            
        # Test remove from favorites
        self.run_test("Remove from Favorites", "DELETE", f"favorites/{pizzeria_id}", 200)
        
        # Test favorites with invalid pizzeria
        self.run_test("Add Invalid Pizzeria to Favorites", "POST", "favorites/invalid-id", 404)

    def test_lists_flow(self):
        """Test pizza lists functionality"""
        print("\n=== PIZZA LISTS TESTS ===")
        
        if not self.token:
            print("❌ Skipping lists tests - no auth token")
            return
            
        # Create a list
        list_data = {
            "name": "Test List",
            "description": "A test list for API testing"
        }
        success, list_response = self.run_test("Create List", "POST", "lists", 200, data=list_data)
        
        if not success:
            print("❌ Cannot continue lists tests - list creation failed")
            return
            
        list_id = list_response['id']
        print(f"   Created list: {list_id}")
        
        # Get all lists
        success, lists = self.run_test("Get All Lists", "GET", "lists", 200)
        if success:
            print(f"   User has {len(lists)} lists")
            
        # Get specific list
        self.run_test("Get Specific List", "GET", f"lists/{list_id}", 200)
        
        # Get pizzerias for testing
        success, pizzerias = self.run_test("Get Pizzerias for Lists", "GET", "pizzerias", 200)
        if success and pizzerias:
            pizzeria_id = pizzerias[0]['id']
            
            # Add pizzeria to list
            self.run_test("Add Pizzeria to List", "POST", f"lists/{list_id}/pizzerias/{pizzeria_id}", 200)
            
            # Get list pizzerias
            success, list_pizzerias = self.run_test("Get List Pizzerias", "GET", f"lists/{list_id}/pizzerias", 200)
            if success:
                print(f"   List has {len(list_pizzerias)} pizzerias")
                
            # Remove pizzeria from list
            self.run_test("Remove Pizzeria from List", "DELETE", f"lists/{list_id}/pizzerias/{pizzeria_id}", 200)
            
        # Delete list
        self.run_test("Delete List", "DELETE", f"lists/{list_id}", 200)
        
        # Test invalid operations
        self.run_test("Get Non-existent List", "GET", "lists/invalid-id", 404)

    def test_unauthorized_access(self):
        """Test endpoints that require authentication without token"""
        print("\n=== UNAUTHORIZED ACCESS TESTS ===")
        
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        self.run_test("Unauthorized Get Me", "GET", "auth/me", 401)
        self.run_test("Unauthorized Get Favorites", "GET", "favorites", 401)
        self.run_test("Unauthorized Get Lists", "GET", "lists", 401)
        
        # Restore token
        self.token = original_token

    def run_all_tests(self):
        """Run all test suites"""
        print("🍕 Starting Pizza API Tests...")
        print(f"Testing API at: {self.base_url}")
        
        self.test_health_check()
        self.test_seed_data()
        self.test_pizzeria_endpoints()
        self.test_auth_flow()
        self.test_favorites_flow()
        self.test_lists_flow()
        self.test_unauthorized_access()
        
        # Print summary
        print(f"\n📊 TEST SUMMARY")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = PizzaAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())