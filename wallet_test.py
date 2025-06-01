import requests
import unittest
import json
import os

# Backend URL from frontend .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1]
            break
    else:
        BACKEND_URL = "https://2da4bb13-3091-4413-9807-6a6cfcfa1853.preview.emergentagent.com"

API_URL = f"{BACKEND_URL}/api"

class BurnReliefBotWalletTests(unittest.TestCase):
    """Test suite for Burn Relief Bot Wallet functionality"""

    def setUp(self):
        """Setup for each test"""
        self.admin_token = "admin_token_davincc"
        self.test_token = "0x5C6374a2ac4EBC38DeA0Fc1F8716e5Ea1AdD94dd"  # AERO token
        self.test_amount = "1000"
        
    def test_01_wallet_status_endpoint(self):
        """Test wallet status endpoint"""
        print("\n1. Testing /api/wallet/status endpoint")
        response = requests.get(f"{API_URL}/wallet/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify wallet status data structure
        self.assertIn("connected", data)
        self.assertIn("wallet_address", data)
        self.assertIn("network", data)
        self.assertIn("rpc_url", data)
        
        # Verify wallet is not connected since private key is not set
        self.assertFalse(data["connected"])
        self.assertIsNone(data["wallet_address"])
        self.assertEqual(data["network"], "Base Mainnet")
        
        print(f"✅ Wallet status endpoint verified - Wallet is not connected as expected")
        print(f"Wallet status: {json.dumps(data, indent=2)}")
        
    def test_02_admin_redistribution_endpoint(self):
        """Test admin redistribution endpoint with admin token"""
        print("\n2. Testing /api/execute-redistribution endpoint")
        
        # Prepare redistribution data
        redistribution_data = {
            "amount": self.test_amount,
            "token_address": self.test_token,
            "is_burnable": True
        }
        
        # Set admin token in headers
        headers = {
            "Authorization": f"Bearer {self.admin_token}"
        }
        
        # Make request
        response = requests.post(
            f"{API_URL}/execute-redistribution", 
            json=redistribution_data,
            headers=headers
        )
        
        # Verify response
        self.assertEqual(response.status_code, 500)  # Should fail with 500 since wallet is not connected
        data = response.json()
        
        # Verify error message
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "Wallet not connected")
        
        print(f"✅ Admin redistribution endpoint properly handles wallet not connected error")
        print(f"Error response: {json.dumps(data, indent=2)}")
        
    def test_03_wallet_setup_verification(self):
        """Test wallet setup verification"""
        print("\n3. Testing wallet initialization and error handling")
        
        # We can't directly test the wallet initialization since it happens at server startup
        # But we can verify the wallet status endpoint shows the wallet is not connected
        response = requests.get(f"{API_URL}/wallet/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify wallet is not connected
        self.assertFalse(data["connected"])
        
        # Try to execute a redistribution to verify error handling
        redistribution_data = {
            "amount": self.test_amount,
            "token_address": self.test_token,
            "is_burnable": True
        }
        
        headers = {
            "Authorization": f"Bearer {self.admin_token}"
        }
        
        response = requests.post(
            f"{API_URL}/execute-redistribution", 
            json=redistribution_data,
            headers=headers
        )
        
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data["detail"], "Wallet not connected")
        
        print(f"✅ Wallet initialization properly handles missing private key")
        print(f"✅ Error handling works correctly when private key is missing")

def run_wallet_tests():
    """Run all wallet tests"""
    print(f"🧪 Testing Burn Relief Bot Wallet Functionality at {API_URL}")
    print("=" * 80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(BurnReliefBotWalletTests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"✅ Passed: {result.testsRun - len(result.errors) - len(result.failures)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️ Errors: {len(result.errors)}")
    
    return result

if __name__ == "__main__":
    run_wallet_tests()