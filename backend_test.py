
import requests
import sys
import json
from datetime import datetime

class CryptoBurnAgentTester:
    def __init__(self, base_url="https://1af30e40-7884-4105-ba09-e96103d2ddbc.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Constants for testing
        self.valid_base_token = "0x4200000000000000000000000000000000000006"  # Example token on Base
        self.drb_token = "0x3ec2156D4c0A9CBdAB4a016633b7BcF6a8d68Ea2"  # Blacklisted DRB token
        self.test_wallet = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Test wallet address
        
    def run_test(self, name, method, endpoint, expected_status=200, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            
            status_success = response.status_code == expected_status
            
            if status_success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Response: {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None
    
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "")
    
    def test_validate_valid_token(self):
        """Test token validation with a valid token"""
        data = {
            "token_address": self.valid_base_token,
            "chain": "base"
        }
        return self.run_test("Valid Token Validation", "POST", "validate-token", data=data)
    
    def test_validate_invalid_token_format(self):
        """Test token validation with invalid token format"""
        data = {
            "token_address": "invalid-address",
            "chain": "base"
        }
        return self.run_test("Invalid Token Format Validation", "POST", "validate-token", data=data)
    
    def test_validate_blacklisted_token(self):
        """Test token validation with a blacklisted token"""
        data = {
            "token_address": self.drb_token,
            "chain": "base"
        }
        success, response = self.run_test("Blacklisted Token Validation", "POST", "validate-token", data=data)
        
        if success and response:
            # For blacklisted tokens, we expect is_valid to be False
            if not response.get("is_valid", True):
                print("✅ Correctly identified as blacklisted token")
                return True, response
            else:
                print("❌ Failed - Blacklisted token was not rejected")
                return False, response
        
        return success, response
    
    def test_burn_transaction(self):
        """Test creating a burn transaction"""
        data = {
            "wallet_address": self.test_wallet,
            "token_address": self.valid_base_token,
            "amount": "1000",
            "chain": "base"
        }
        return self.run_test("Create Burn Transaction", "POST", "burn", data=data)
    
    def test_burn_blacklisted_token(self):
        """Test creating a burn transaction with blacklisted token"""
        data = {
            "wallet_address": self.test_wallet,
            "token_address": self.drb_token,
            "amount": "1000",
            "chain": "base"
        }
        # We expect this to fail with 400 status
        return self.run_test("Burn Blacklisted Token", "POST", "burn", expected_status=400, data=data)
    
    def test_get_transactions(self):
        """Test fetching transactions"""
        return self.run_test("Get Transactions", "GET", "transactions")
    
    def test_get_transactions_by_wallet(self):
        """Test fetching transactions for a specific wallet"""
        params = {"wallet_address": self.test_wallet}
        return self.run_test("Get Transactions By Wallet", "GET", "transactions", params=params)
    
    def test_burn_amount_calculation(self):
        """Test the 88/6/6 split calculation"""
        data = {
            "wallet_address": self.test_wallet,
            "token_address": self.valid_base_token,
            "amount": "1000",
            "chain": "base"
        }
        success, response = self.run_test("Burn Amount Calculation", "POST", "burn", data=data)
        
        if success and response:
            # Check if the amounts are calculated correctly
            burn_amount = float(response.get("burn_amount", 0))
            drb_amount = float(response.get("drb_swap_amount", 0))
            cbbtc_amount = float(response.get("cbbtc_swap_amount", 0))
            
            expected_burn = 1000 * 0.88
            expected_drb = 1000 * 0.06
            expected_cbbtc = 1000 * 0.06
            
            calculation_correct = (
                abs(burn_amount - expected_burn) < 0.01 and
                abs(drb_amount - expected_drb) < 0.01 and
                abs(cbbtc_amount - expected_cbbtc) < 0.01
            )
            
            if calculation_correct:
                print("✅ Burn calculation is correct (88/6/6 split)")
                return True, response
            else:
                print(f"❌ Burn calculation is incorrect:")
                print(f"  Expected: {expected_burn}/{expected_drb}/{expected_cbbtc}")
                print(f"  Got: {burn_amount}/{drb_amount}/{cbbtc_amount}")
                return False, response
        
        return success, response

def main():
    print("=" * 50)
    print("Crypto Burn Agent API Test Suite")
    print("=" * 50)
    
    tester = CryptoBurnAgentTester()
    
    # Run tests
    tester.test_root_endpoint()
    tester.test_validate_valid_token()
    tester.test_validate_invalid_token_format()
    tester.test_validate_blacklisted_token()
    tester.test_burn_transaction()
    tester.test_burn_blacklisted_token()
    tester.test_get_transactions()
    tester.test_get_transactions_by_wallet()
    tester.test_burn_amount_calculation()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
