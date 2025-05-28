
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
        self.valid_eth_token = "0xdAC17F958D2ee523a2206206994597C13D831ec7"  # USDT on Ethereum
        self.valid_polygon_token = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC on Polygon
        self.valid_arbitrum_token = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"  # USDC on Arbitrum
        self.drb_token = "0x3ec2156D4c0A9CBdAB4a016633b7BcF6a8d68Ea2"  # Blacklisted DRB token
        self.test_wallet = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Test wallet address
        self.test_solana_wallet = "CtFtfe2pYRiJVAUrEZtdFKZVV2UFpdaWBU1Ve7aPC"  # Test Solana wallet
        
        # Expected chains
        self.expected_chains = ["base", "solana", "ethereum", "polygon", "arbitrum"]
        
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
    
    def test_get_chains(self):
        """Test fetching supported chains"""
        success, response = self.run_test("Get Supported Chains", "GET", "chains")
        
        if success and response:
            chains = response.get("chains", {})
            chain_keys = list(chains.keys())
            
            # Check if all expected chains are present
            all_chains_present = all(chain in chain_keys for chain in self.expected_chains)
            
            if all_chains_present:
                print(f"✅ All expected chains are supported: {', '.join(self.expected_chains)}")
                return True, response
            else:
                missing_chains = [chain for chain in self.expected_chains if chain not in chain_keys]
                print(f"❌ Missing chains: {', '.join(missing_chains)}")
                return False, response
        
        return success, response
    
    def test_get_config(self):
        """Test fetching app configuration"""
        success, response = self.run_test("Get App Configuration", "GET", "config")
        
        if success and response:
            # Check if config contains all required fields
            required_fields = ["burn_address", "drb_token_address", "cbbtc_token_address", 
                              "supported_chains", "burn_percentage", "drb_swap_percentage", 
                              "cbbtc_swap_percentage"]
            
            all_fields_present = all(field in response for field in required_fields)
            
            if all_fields_present:
                print("✅ Configuration contains all required fields")
                
                # Verify percentages add up to 100%
                total_percentage = (response.get("burn_percentage", 0) + 
                                   response.get("drb_swap_percentage", 0) + 
                                   response.get("cbbtc_swap_percentage", 0))
                
                if total_percentage == 100:
                    print("✅ Percentages add up to 100%")
                else:
                    print(f"❌ Percentages don't add up to 100%: {total_percentage}%")
                    return False, response
                
                return True, response
            else:
                missing_fields = [field for field in required_fields if field not in response]
                print(f"❌ Missing configuration fields: {', '.join(missing_fields)}")
                return False, response
        
        return success, response
    
    def test_get_burn_stats(self):
        """Test fetching community burn statistics"""
        success, response = self.run_test("Get Burn Stats", "GET", "stats")
        
        if success and response:
            # Check if stats contains all required fields
            required_fields = ["total_burns", "total_amount_burned", "total_users", 
                              "trending_tokens", "top_burners"]
            
            all_fields_present = all(field in response for field in required_fields)
            
            if all_fields_present:
                print("✅ Burn stats contain all required fields")
                return True, response
            else:
                missing_fields = [field for field in required_fields if field not in response]
                print(f"❌ Missing stats fields: {', '.join(missing_fields)}")
                return False, response
        
        return success, response
    
    def test_ethereum_token_validation(self):
        """Test token validation on Ethereum chain"""
        data = {
            "token_address": self.valid_eth_token,
            "chain": "ethereum"
        }
        return self.run_test("Ethereum Token Validation", "POST", "validate-token", data=data)
    
    def test_polygon_token_validation(self):
        """Test token validation on Polygon chain"""
        data = {
            "token_address": self.valid_polygon_token,
            "chain": "polygon"
        }
        return self.run_test("Polygon Token Validation", "POST", "validate-token", data=data)
    
    def test_arbitrum_token_validation(self):
        """Test token validation on Arbitrum chain"""
        data = {
            "token_address": self.valid_arbitrum_token,
            "chain": "arbitrum"
        }
        return self.run_test("Arbitrum Token Validation", "POST", "validate-token", data=data)
    
    def test_ethereum_burn_transaction(self):
        """Test creating a burn transaction on Ethereum"""
        data = {
            "wallet_address": self.test_wallet,
            "token_address": self.valid_eth_token,
            "amount": "1000",
            "chain": "ethereum"
        }
        return self.run_test("Create Ethereum Burn Transaction", "POST", "burn", data=data)
    
    def test_polygon_burn_transaction(self):
        """Test creating a burn transaction on Polygon"""
        data = {
            "wallet_address": self.test_wallet,
            "token_address": self.valid_polygon_token,
            "amount": "1000",
            "chain": "polygon"
        }
        return self.run_test("Create Polygon Burn Transaction", "POST", "burn", data=data)
    
    def test_arbitrum_burn_transaction(self):
        """Test creating a burn transaction on Arbitrum"""
        data = {
            "wallet_address": self.test_wallet,
            "token_address": self.valid_arbitrum_token,
            "amount": "1000",
            "chain": "arbitrum"
        }
        return self.run_test("Create Arbitrum Burn Transaction", "POST", "burn", data=data)

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
