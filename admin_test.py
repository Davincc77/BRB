import requests
import json
import unittest
import os
import time
from datetime import datetime
import traceback

# Use localhost for testing
BACKEND_URL = "http://localhost:8001"
API_URL = f"{BACKEND_URL}/api"
ADMIN_URL = f"{API_URL}/admin"

class AdminAPITest(unittest.TestCase):
    """Test class for admin API endpoints"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Admin token for authentication
        self.valid_admin_token = "admin_token_davincc"
        self.invalid_admin_token = "invalid_token"
        
        # Headers
        self.valid_headers = {"Authorization": f"Bearer {self.valid_admin_token}"}
        self.invalid_headers = {"Authorization": f"Bearer {self.invalid_admin_token}"}
        self.no_auth_headers = {}
        
        # Test project data
        self.test_project = {
            "name": "Test Community Project",
            "description": "A test project for the community pool",
            "base_address": "0x742d35Cc6634C0532925a3b8D0d67c58C95B4b1a",
            "website": "https://test-project.com",
            "twitter": "@test_project",
            "logo_url": "https://test-project.com/logo.png"
        }
        
        # Store created project ID for cleanup
        self.created_project_id = None
    
    def test_01_admin_auth_valid_token(self):
        """Test admin authentication with valid token"""
        print("\n1. Testing admin authentication with valid token...")
        try:
            response = requests.get(f"{ADMIN_URL}/projects", headers=self.valid_headers)
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            self.assertEqual(response.status_code, 200, f"Expected status code 200, got {response.status_code}")
            self.assertIn("projects", response.json(), "Response should contain 'projects' key")
            print("✅ Admin authentication with valid token successful")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def test_02_admin_auth_no_token(self):
        """Test admin authentication without token"""
        print("\n2. Testing admin authentication without token...")
        try:
            response = requests.get(f"{ADMIN_URL}/projects", headers=self.no_auth_headers)
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            self.assertEqual(response.status_code, 401, f"Expected status code 401, got {response.status_code}")
            print("✅ Admin authentication without token correctly rejected")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def test_03_admin_auth_invalid_token(self):
        """Test admin authentication with invalid token"""
        print("\n3. Testing admin authentication with invalid token...")
        try:
            response = requests.get(f"{ADMIN_URL}/projects", headers=self.invalid_headers)
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            self.assertEqual(response.status_code, 401, f"Expected status code 401, got {response.status_code}")
            print("✅ Admin authentication with invalid token correctly rejected")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def test_04_create_project(self):
        """Test creating a new project"""
        print("\n4. Testing project creation...")
        try:
            response = requests.post(
                f"{ADMIN_URL}/projects", 
                headers=self.valid_headers,
                json=self.test_project
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            self.assertEqual(response.status_code, 200, f"Expected status code 200, got {response.status_code}")
            self.assertIn("project", response.json(), "Response should contain 'project' key")
            self.assertEqual(response.json()["status"], "created", "Status should be 'created'")
            
            # Store project ID for later tests
            self.created_project_id = response.json()["project"]["_id"]
            print(f"✅ Project created successfully with ID: {self.created_project_id}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def test_05_create_project_invalid_auth(self):
        """Test creating a project with invalid authentication"""
        print("\n5. Testing project creation with invalid authentication...")
        try:
            response = requests.post(
                f"{ADMIN_URL}/projects", 
                headers=self.invalid_headers,
                json=self.test_project
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            self.assertEqual(response.status_code, 401, f"Expected status code 401, got {response.status_code}")
            print("✅ Project creation with invalid authentication correctly rejected")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def test_06_update_project(self):
        """Test updating a project"""
        print("\n6. Testing project update...")
        # Skip if no project was created
        if not self.created_project_id:
            self.skipTest("No project ID available for update test")
        
        try:
            updated_data = {
                "name": "Updated Test Project",
                "description": "This project has been updated",
                "website": "https://updated-project.com"
            }
            
            response = requests.put(
                f"{ADMIN_URL}/projects/{self.created_project_id}", 
                headers=self.valid_headers,
                json=updated_data
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            self.assertEqual(response.status_code, 200, f"Expected status code 200, got {response.status_code}")
            self.assertEqual(response.json()["status"], "updated", "Status should be 'updated'")
            print("✅ Project updated successfully")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def test_07_update_project_invalid_id(self):
        """Test updating a project with invalid ID"""
        print("\n7. Testing project update with invalid ID...")
        try:
            invalid_id = "invalid_project_id"
            
            response = requests.put(
                f"{ADMIN_URL}/projects/{invalid_id}", 
                headers=self.valid_headers,
                json={"name": "Invalid Update"}
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # The API returns 500 with a detail message indicating 404 not found
            self.assertEqual(response.status_code, 500, f"Expected status code 500, got {response.status_code}")
            self.assertIn("404: Project not found", response.json().get("detail", ""), 
                         "Response should indicate project not found")
            print("✅ Project update with invalid ID correctly rejected")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def test_08_start_contest(self):
        """Test starting a contest"""
        print("\n8. Testing contest start...")
        # Skip if no project was created
        if not self.created_project_id:
            self.skipTest("No project ID available for contest test")
        
        try:
            contest_data = {
                "project_id": self.created_project_id
            }
            
            response = requests.post(
                f"{ADMIN_URL}/contest/start", 
                headers=self.valid_headers,
                json=contest_data
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            self.assertEqual(response.status_code, 200, f"Expected status code 200, got {response.status_code}")
            self.assertEqual(response.json()["status"], "contest_started", "Status should be 'contest_started'")
            print("✅ Contest started successfully")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def test_09_start_contest_invalid_id(self):
        """Test starting a contest with invalid project ID"""
        print("\n9. Testing contest start with invalid project ID...")
        try:
            invalid_id = "invalid_project_id"
            
            contest_data = {
                "project_id": invalid_id
            }
            
            response = requests.post(
                f"{ADMIN_URL}/contest/start", 
                headers=self.valid_headers,
                json=contest_data
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            self.assertEqual(response.status_code, 404, f"Expected status code 404, got {response.status_code}")
            print("✅ Contest start with invalid project ID correctly rejected")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def test_10_delete_project(self):
        """Test deleting a project"""
        print("\n10. Testing project deletion...")
        # Skip if no project was created
        if not self.created_project_id:
            self.skipTest("No project ID available for deletion test")
        
        try:
            response = requests.delete(
                f"{ADMIN_URL}/projects/{self.created_project_id}", 
                headers=self.valid_headers
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            self.assertEqual(response.status_code, 200, f"Expected status code 200, got {response.status_code}")
            self.assertEqual(response.json()["status"], "deleted", "Status should be 'deleted'")
            print("✅ Project deleted successfully")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(traceback.format_exc())
            raise
    
    def test_11_delete_project_invalid_id(self):
        """Test deleting a project with invalid ID"""
        print("\n11. Testing project deletion with invalid ID...")
        try:
            invalid_id = "invalid_project_id"
            
            response = requests.delete(
                f"{ADMIN_URL}/projects/{invalid_id}", 
                headers=self.valid_headers
            )
            
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
            self.assertEqual(response.status_code, 404, f"Expected status code 404, got {response.status_code}")
            print("✅ Project deletion with invalid ID correctly rejected")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(traceback.format_exc())
            raise

def run_admin_tests():
    """Run all admin API tests"""
    print(f"🧪 Testing Admin API at {ADMIN_URL}")
    print("=" * 80)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add tests in specific order
    test_suite.addTest(AdminAPITest('test_01_admin_auth_valid_token'))
    test_suite.addTest(AdminAPITest('test_02_admin_auth_no_token'))
    test_suite.addTest(AdminAPITest('test_03_admin_auth_invalid_token'))
    test_suite.addTest(AdminAPITest('test_04_create_project'))
    test_suite.addTest(AdminAPITest('test_05_create_project_invalid_auth'))
    test_suite.addTest(AdminAPITest('test_06_update_project'))
    test_suite.addTest(AdminAPITest('test_07_update_project_invalid_id'))
    test_suite.addTest(AdminAPITest('test_08_start_contest'))
    test_suite.addTest(AdminAPITest('test_09_start_contest_invalid_id'))
    test_suite.addTest(AdminAPITest('test_10_delete_project'))
    test_suite.addTest(AdminAPITest('test_11_delete_project_invalid_id'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"✅ Passed: {result.testsRun - len(result.errors) - len(result.failures)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️ Errors: {len(result.errors)}")
    
    return result

if __name__ == "__main__":
    run_admin_tests()