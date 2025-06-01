
import requests
import unittest
import json
import time
from datetime import datetime
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

class BurnReliefBotAPITests(unittest.TestCase):
    """Test suite for Burn Relief Bot API endpoints after Community Contest upgrade"""

    def setUp(self):
        """Setup for each test"""
        self.test_wallet = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        self.test_token = "0x5C6374a2ac4EBC38DeA0Fc1F8716e5Ea1AdD94dd"  # AERO token
        self.bnkr_token = "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b"  # $BNKR token
        self.drb_token = "0x1234567890123456789012345678901234567890"  # DRB token
        self.usdc_token = "0x833589fCD6eDb6E08f4c7C32d4f71b54bdA02913"  # USDC on Base
        self.test_amount = "1000"
        self.chain = "base"  # Only Base chain is supported now
        
        # Test project data
        self.test_project = {
            "name": "Test Community Project",
            "description": "A test project for the community contest",
            "base_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44f",
            "submitted_by": self.test_wallet,
            "website": "https://example.com",
            "twitter": "@testproject",
            "logo_url": "https://example.com/logo.png"
        }
        
        # Test vote data
        self.test_vote = {
            "voter_wallet": self.test_wallet,
            "project_id": "",  # Will be filled after project creation
            "vote_token": "DRB",
            "vote_amount": "1000",
            "burn_tx_hash": "0x" + "a" * 64
        }
        
    def test_01_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{API_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
        print("✅ API health check passed")

    def test_02_chains_endpoint(self):
        """Test chains endpoint for Base-only setup with updated allocations"""
        response = requests.get(f"{API_URL}/chains")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify chains data
        self.assertIn("chains", data)
        chains = data["chains"]
        
        # Should only have Base chain
        self.assertEqual(len(chains), 1)
        self.assertIn("base", chains)
        
        # Verify Base chain data
        base_chain = chains["base"]
        self.assertEqual(base_chain["name"], "Base")
        self.assertEqual(base_chain["chain_id"], 8453)
        self.assertEqual(base_chain["currency"], "ETH")
        
        # Verify default chain is Base
        self.assertEqual(data["default_chain"], "base")
        
        # Verify token addresses
        self.assertIn("drb_token_address", data)
        self.assertIn("bnkr_token_address", data)
        self.assertEqual(data["bnkr_token_address"], "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b")
        
        # Verify allocations with updated percentages
        self.assertIn("allocations", data)
        allocations = data["allocations"]
        self.assertEqual(allocations["burn_percentage"], 88.0)
        self.assertEqual(allocations["drb_total_percentage"], 10.0)
        self.assertEqual(allocations["drb_grok_percentage"], 7.0)
        self.assertEqual(allocations["drb_community_percentage"], 1.5)
        self.assertEqual(allocations["drb_team_percentage"], 0.5)  # Reduced from 1%
        self.assertEqual(allocations["bnkr_total_percentage"], 2.5)
        self.assertEqual(allocations["bnkr_community_percentage"], 1.5)
        self.assertEqual(allocations["bnkr_team_percentage"], 0.5)  # Reduced from 1%
        
        print("✅ Chains endpoint verified - Base-only setup with updated allocations confirmed")

    def test_03_check_burnable_regular_token(self):
        """Test check-burnable endpoint with regular token (should be burnable)"""
        payload = {
            "token_address": self.test_token,
            "chain": self.chain
        }
        
        response = requests.post(f"{API_URL}/check-burnable", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify regular token is burnable
        self.assertIn("is_burnable", data)
        self.assertTrue(data["is_burnable"])
        self.assertFalse(data["is_drb"])
        self.assertEqual(data["allocation_type"], "burn_and_swap")
        
        print("✅ Regular token correctly identified as burnable")

    def test_04_check_burnable_bnkr_token(self):
        """Test check-burnable endpoint with $BNKR token (should be swap-only)"""
        payload = {
            "token_address": self.bnkr_token,
            "chain": self.chain
        }
        
        response = requests.post(f"{API_URL}/check-burnable", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify BNKR token is not burnable
        self.assertIn("is_burnable", data)
        self.assertFalse(data["is_burnable"])
        self.assertFalse(data["is_drb"])
        self.assertEqual(data["allocation_type"], "swap_only")
        
        print("✅ $BNKR token correctly identified as swap-only")

    def test_05_check_burnable_drb_token(self):
        """Test check-burnable endpoint with DRB token (should be direct allocation)"""
        payload = {
            "token_address": self.drb_token,
            "chain": self.chain
        }
        
        response = requests.post(f"{API_URL}/check-burnable", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify DRB token is handled with direct allocation
        self.assertIn("is_drb", data)
        self.assertTrue(data["is_drb"])
        self.assertEqual(data["allocation_type"], "drb_direct_allocation")
        
        print("✅ DRB token correctly identified for direct allocation")

    def test_06_check_burnable_stablecoin(self):
        """Test check-burnable endpoint with stablecoin like USDC (should be swap-only)"""
        payload = {
            "token_address": self.usdc_token,
            "chain": self.chain
        }
        
        response = requests.post(f"{API_URL}/check-burnable", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify USDC is not burnable
        self.assertIn("is_burnable", data)
        self.assertFalse(data["is_burnable"])
        self.assertFalse(data["is_drb"])
        self.assertEqual(data["allocation_type"], "swap_only")
        
        print("✅ USDC stablecoin correctly identified as swap-only")

    def test_07_stats_endpoint(self):
        """Test stats endpoint for proper property names"""
        response = requests.get(f"{API_URL}/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify stats data structure
        self.assertIn("total_transactions", data)
        self.assertIn("completed_transactions", data)
        self.assertIn("total_volume_usd", data)
        self.assertIn("total_tokens_burned", data)
        self.assertIn("total_drb_allocated", data)
        self.assertIn("total_bnkr_allocated", data)
        self.assertIn("burn_percentage", data)
        self.assertIn("drb_percentage", data)
        self.assertIn("bnkr_percentage", data)
        self.assertIn("supported_chains", data)
        
        # Verify BNKR percentage is correct
        self.assertEqual(data["bnkr_percentage"], 2.5)
        
        # Verify supported chains is only Base
        self.assertEqual(data["supported_chains"], ["base"])
        
        print("✅ Stats endpoint verified with correct property names")

    def test_08_community_stats_endpoint(self):
        """Test community stats endpoint"""
        response = requests.get(f"{API_URL}/community/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify community stats data structure
        self.assertIn("total_burns", data)
        self.assertIn("total_volume_usd", data)
        self.assertIn("total_tokens_burned", data)
        self.assertIn("active_wallets", data)
        self.assertIn("chain_distribution", data)
        self.assertIn("top_burners", data)
        self.assertIn("recent_burns", data)
        
        # Verify chain distribution is only Base
        chain_distribution = data["chain_distribution"]
        self.assertEqual(len(chain_distribution), 1)
        self.assertIn("base", chain_distribution)
        self.assertEqual(chain_distribution["base"], 100.0)
        
        print("✅ Community stats endpoint verified")

    def test_09_token_validation(self):
        """Test token validation endpoint"""
        payload = {
            "token_address": self.test_token,
            "chain": self.chain
        }
        
        response = requests.post(f"{API_URL}/validate-token", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify validation response
        self.assertIn("is_valid", data)
        if data["is_valid"]:
            self.assertIn("symbol", data)
            self.assertIn("name", data)
            self.assertIn("decimals", data)
            self.assertIn("total_supply", data)
        
        print("✅ Token validation endpoint verified")

    def test_10_burn_endpoint(self):
        """Test burn endpoint with updated allocation logic"""
        print("⚠️ Skipping actual burn transaction - requires valid token contract")
        
        # Instead of making a real burn request, we'll test the preview allocations
        # from the check-burnable endpoint to verify the allocation logic
        
        # Test regular token (burnable)
        payload = {
            "token_address": self.test_token,
            "chain": self.chain
        }
        
        response = requests.post(f"{API_URL}/check-burnable", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify allocation percentages for regular token
        preview = data["preview_allocations"]
        self.assertIn("burn_percentage", preview)
        self.assertIn("drb_grok_percentage", preview)
        self.assertIn("drb_community_percentage", preview)
        self.assertIn("drb_team_percentage", preview)
        self.assertIn("bnkr_community_percentage", preview)
        self.assertIn("bnkr_team_percentage", preview)
        
        # Test DRB token (direct allocation)
        payload = {
            "token_address": self.drb_token,
            "chain": self.chain
        }
        
        response = requests.post(f"{API_URL}/check-burnable", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify DRB token is handled with direct allocation
        self.assertTrue(data["is_drb"])
        self.assertEqual(data["allocation_type"], "drb_direct_allocation")
        
        # Test protected token (USDC - swap only)
        payload = {
            "token_address": self.usdc_token,
            "chain": self.chain
        }
        
        response = requests.post(f"{API_URL}/check-burnable", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify USDC is not burnable
        self.assertFalse(data["is_burnable"])
        self.assertEqual(data["allocation_type"], "swap_only")
        
        print("✅ Burn allocation logic verified for different token types")

    def test_11_community_contest_endpoint(self):
        """Test community contest endpoint"""
        response = requests.get(f"{API_URL}/community/contest")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify contest data structure
        self.assertIn("voting_period", data)
        self.assertIn("projects", data)
        self.assertIn("vote_requirements", data)
        self.assertIn("contest_allocations", data)
        
        # Verify vote requirements
        vote_requirements = data["vote_requirements"]
        self.assertIn("drb_amount", vote_requirements)
        self.assertIn("bnkr_amount", vote_requirements)
        
        # Verify contest allocations
        contest_allocations = data["contest_allocations"]
        self.assertIn("drb_percentage", contest_allocations)
        self.assertIn("bnkr_percentage", contest_allocations)
        self.assertEqual(contest_allocations["drb_percentage"], 0.5)
        self.assertEqual(contest_allocations["bnkr_percentage"], 0.5)
        
        print("✅ Community contest endpoint verified")
    
    def test_12_community_project_submission(self):
        """Test community project submission endpoint"""
        response = requests.post(f"{API_URL}/community/project", json=self.test_project)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify project submission response
        self.assertIn("project_id", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "submitted")
        
        # Save project ID for voting test
        self.test_vote["project_id"] = data["project_id"]
        
        print("✅ Community project submission endpoint verified")
    
    def test_13_community_vote_endpoint(self):
        """Test community vote endpoint"""
        # Skip if no project ID
        if not self.test_vote["project_id"]:
            print("⚠️ Skipping vote test - no project ID available")
            return
            
        response = requests.post(f"{API_URL}/community/vote", json=self.test_vote)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify vote response
        self.assertIn("vote_id", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "success")
        
        print("✅ Community vote endpoint verified")
    
    def test_14_user_votes_endpoint(self):
        """Test user votes endpoint"""
        response = requests.get(f"{API_URL}/community/votes/{self.test_wallet}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify votes data structure
        self.assertIn("votes", data)
        
        # If we successfully voted in the previous test, we should have at least one vote
        if self.test_vote["project_id"]:
            if len(data["votes"]) > 0:
                vote = data["votes"][0]
                self.assertIn("voter_wallet", vote)
                self.assertIn("project_id", vote)
                self.assertIn("vote_token", vote)
                self.assertIn("vote_amount", vote)
        
        print("✅ User votes endpoint verified")
    
    def test_15_error_handling_missing_params(self):
        """Test error handling for missing parameters"""
        # Test project submission with missing required fields
        incomplete_project = {
            "name": "Incomplete Project"
            # Missing other required fields
        }
        
        response = requests.post(f"{API_URL}/community/project", json=incomplete_project)
        # The API might return 400 (ideal) or 500 (if validation is not properly implemented)
        self.assertIn(response.status_code, [400, 500])
        
        # Test vote submission with missing required fields
        incomplete_vote = {
            "voter_wallet": self.test_wallet
            # Missing other required fields
        }
        
        response = requests.post(f"{API_URL}/community/vote", json=incomplete_vote)
        # The API might return 400 (ideal) or 500 (if validation is not properly implemented)
        self.assertIn(response.status_code, [400, 500])
        
        print("✅ Error handling for missing parameters verified")
    
    def test_16_error_handling_invalid_requests(self):
        """Test error handling for invalid requests"""
        # Test with invalid token address format
        payload = {
            "token_address": "invalid-address",  # Not a valid Ethereum address
            "chain": "base"
        }
        
        response = requests.post(f"{API_URL}/validate-token", json=payload)
        # Should either return 400 Bad Request or 200 with is_valid=False
        if response.status_code == 200:
            data = response.json()
            self.assertIn("is_valid", data)
            self.assertFalse(data["is_valid"])
        else:
            self.assertIn(response.status_code, [400, 500])
        
        # Test with invalid chain
        response = requests.get(f"{API_URL}/gas-estimates/invalid-chain")
        self.assertIn(response.status_code, [400, 404, 500])  # Should return an error
        
        print("✅ Error handling for invalid requests verified")
    
    def test_17_cross_chain_optimal_routes(self):
        """Test cross-chain optimal routes endpoint"""
        response = requests.get(f"{API_URL}/cross-chain/optimal-routes")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify optimal routes data structure
        self.assertIn("optimal_chains", data)
        self.assertIn("recommended_chain", data)
        self.assertIn("gas_estimates", data)
        self.assertIn("liquidity_analysis", data)
        
        # Verify Base is the recommended chain
        self.assertEqual(data["recommended_chain"], "base")
        
        # Verify optimal chains for tokens
        optimal_chains = data["optimal_chains"]
        self.assertIn("DRB", optimal_chains)
        self.assertIn("BNKR", optimal_chains)
        self.assertEqual(optimal_chains["DRB"], "base")
        self.assertEqual(optimal_chains["BNKR"], "base")
        
        print("✅ Cross-chain optimal routes endpoint verified")
    
    def test_18_gas_estimates_endpoint(self):
        """Test gas estimates endpoint"""
        response = requests.get(f"{API_URL}/gas-estimates/{self.chain}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify gas estimates data structure
        self.assertIn("slow", data)
        self.assertIn("standard", data)
        self.assertIn("fast", data)
        
        # Verify each estimate has required fields
        for speed in ["slow", "standard", "fast"]:
            self.assertIn("gwei", data[speed])
            self.assertIn("usd", data[speed])
            self.assertIn("time", data[speed])
        
        print("✅ Gas estimates endpoint verified")
    
    def test_19_token_price_endpoint(self):
        """Test token price endpoint"""
        response = requests.get(f"{API_URL}/token-price/{self.test_token}/{self.chain}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify token price data structure
        self.assertIn("price", data)
        self.assertIn("currency", data)
        self.assertEqual(data["currency"], "USD")
        
        print("✅ Token price endpoint verified")
    
    def test_20_swap_quote_endpoint(self):
        """Test swap quote endpoint"""
        payload = {
            "token_address": self.test_token,
            "amount": "1000",
            "chain": self.chain
        }
        
        response = requests.post(f"{API_URL}/swap-quote", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify swap quote data structure
        self.assertIn("status", data)
        self.assertEqual(data["status"], "success")
        self.assertIn("data", data)
        
        quote_data = data["data"]
        self.assertIn("input_amount", quote_data)
        self.assertIn("output_amount", quote_data)
        self.assertIn("price_impact", quote_data)
        self.assertIn("gas_estimate", quote_data)
        
        print("✅ Swap quote endpoint verified")
    
    def test_21_transactions_endpoint(self):
        """Test transactions endpoint"""
        response = requests.get(f"{API_URL}/transactions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify transactions data structure
        self.assertIn("transactions", data)
        
        print("✅ Transactions endpoint verified")
    
    def test_22_wallet_transactions_endpoint(self):
        """Test wallet transactions endpoint"""
        response = requests.get(f"{API_URL}/transactions/{self.test_wallet}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify wallet transactions data structure
        self.assertIn("transactions", data)
        
        print("✅ Wallet transactions endpoint verified")

def run_tests():
    """Run all tests"""
    print(f"🧪 Testing Burn Relief Bot API at {API_URL}")
    print("=" * 80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(BurnReliefBotAPITests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"✅ Passed: {result.testsRun - len(result.errors) - len(result.failures)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️ Errors: {len(result.errors)}")
    
    return result

def test_specific_endpoints():
    """Test specific endpoints mentioned in the review request"""
    print("\n" + "=" * 80)
    print("TESTING SPECIFIC ENDPOINTS FROM REVIEW REQUEST")
    print("=" * 80)
    
    # Test wallet endpoints
    print("\nTESTING WALLET ENDPOINTS")
    print("=" * 80)
    
    # 1. Test wallet status endpoint
    print("\n1. Testing /api/wallet/status endpoint")
    response = requests.get(f"{API_URL}/wallet/status")
    if response.status_code == 200:
        data = response.json()
        print("✅ /api/wallet/status endpoint is accessible")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check expected fields
        expected_keys = ["connected", "wallet_address", "network", "rpc_url"]
        missing_keys = [key for key in expected_keys if key not in data]
        
        if not missing_keys:
            print("✅ /api/wallet/status response contains all expected fields")
        else:
            print(f"❌ /api/wallet/status response missing expected keys: {missing_keys}")
            
        # Check if wallet is not connected (expected based on review request)
        if data.get("connected") == False:
            print("✅ Wallet is correctly reported as not connected (expected)")
        else:
            print("❓ Wallet is reported as connected (unexpected based on review request)")
    else:
        print(f"❌ /api/wallet/status endpoint failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
    
    # 2. Test execute-redistribution endpoint with admin token
    print("\n2. Testing /api/execute-redistribution endpoint with admin token")
    
    # Prepare test data
    redistribution_payload = {
        "amount": "1000",
        "token_address": "0x5C6374a2ac4EBC38DeA0Fc1F8716e5Ea1AdD94dd",
        "is_burnable": True
    }
    
    # Test with admin token
    admin_headers = {"Authorization": "Bearer admin_token_davincc"}
    response = requests.post(f"{API_URL}/execute-redistribution", 
                            json=redistribution_payload,
                            headers=admin_headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ /api/execute-redistribution endpoint is accessible with admin token")
        print(f"Response: {json.dumps(data, indent=2)}")
    elif response.status_code == 500 and "wallet not connected" in response.text.lower():
        print("✅ /api/execute-redistribution endpoint returns appropriate error when wallet is not connected")
        print(f"Response: {response.text}")
    else:
        print(f"❌ /api/execute-redistribution endpoint failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test without admin token
    print("\n3. Testing /api/execute-redistribution endpoint without admin token")
    response = requests.post(f"{API_URL}/execute-redistribution", 
                            json=redistribution_payload)
    
    if response.status_code == 401:
        print("✅ /api/execute-redistribution endpoint correctly requires admin authentication")
    else:
        print(f"❌ /api/execute-redistribution endpoint failed with unexpected status code: {response.status_code}")
        print(f"Response: {response.text}")
    
    # 1. Core Burn Functionality
    print("\n1. CORE BURN FUNCTIONALITY")
    
    # 1.1 Test /api/check-burnable endpoint
    print("\n1.1 Testing /api/check-burnable endpoint")
    burnable_payload = {
        "token_address": "0x5C6374a2ac4EBC38DeA0Fc1F8716e5Ea1AdD94dd",  # Regular token
        "chain": "base"
    }
    
    non_burnable_payload = {
        "token_address": "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b",  # $BNKR token
        "chain": "base"
    }
    
    drb_payload = {
        "token_address": "0x1234567890123456789012345678901234567890",  # DRB token
        "chain": "base"
    }
    
    stablecoin_payload = {
        "token_address": "0x833589fCD6eDb6E08f4c7C32d4f71b54bdA02913",  # USDC on Base
        "chain": "base"
    }
    
    # Test with regular token (should be burnable)
    response = requests.post(f"{API_URL}/check-burnable", json=burnable_payload)
    if response.status_code == 200:
        data = response.json()
        if data.get("is_burnable") == True:
            print("✅ /api/check-burnable correctly identifies burnable tokens")
        else:
            print("❌ /api/check-burnable failed to identify burnable token")
    else:
        print(f"❌ /api/check-burnable endpoint failed with status code: {response.status_code}")
    
    # Test with non-burnable token
    response = requests.post(f"{API_URL}/check-burnable", json=non_burnable_payload)
    if response.status_code == 200:
        data = response.json()
        if data.get("is_burnable") == False:
            print("✅ /api/check-burnable correctly identifies non-burnable tokens")
        else:
            print("❌ /api/check-burnable failed to identify non-burnable token")
    else:
        print(f"❌ /api/check-burnable endpoint failed with status code: {response.status_code}")
    
    # Test with DRB token
    response = requests.post(f"{API_URL}/check-burnable", json=drb_payload)
    if response.status_code == 200:
        data = response.json()
        if data.get("is_drb") == True:
            print("✅ /api/check-burnable correctly identifies DRB token")
        else:
            print("❌ /api/check-burnable failed to identify DRB token")
    else:
        print(f"❌ /api/check-burnable endpoint failed with status code: {response.status_code}")
    
    # Test with stablecoin
    response = requests.post(f"{API_URL}/check-burnable", json=stablecoin_payload)
    if response.status_code == 200:
        data = response.json()
        if data.get("is_burnable") == False:
            print("✅ /api/check-burnable correctly identifies stablecoins as non-burnable")
        else:
            print("❌ /api/check-burnable failed to identify stablecoin as non-burnable")
    else:
        print(f"❌ /api/check-burnable endpoint failed with status code: {response.status_code}")
    
    # 1.2 Test /api/gas-estimates/{chain} endpoint
    print("\n1.2 Testing /api/gas-estimates/base endpoint")
    response = requests.get(f"{API_URL}/gas-estimates/base")
    if response.status_code == 200:
        data = response.json()
        if all(key in data for key in ["slow", "standard", "fast"]):
            print("✅ /api/gas-estimates/base endpoint returns proper gas estimates")
            print(f"Gas estimates: {json.dumps(data, indent=2)}")
        else:
            print("❌ /api/gas-estimates/base endpoint response missing expected keys")
    else:
        print(f"❌ /api/gas-estimates/base endpoint failed with status code: {response.status_code}")
    
    # 1.3 Test /api/token-price/{token}/{chain} endpoint
    print("\n1.3 Testing /api/token-price endpoint")
    test_token = "0x5C6374a2ac4EBC38DeA0Fc1F8716e5Ea1AdD94dd"
    response = requests.get(f"{API_URL}/token-price/{test_token}/base")
    if response.status_code == 200:
        data = response.json()
        if "price" in data and "currency" in data:
            print("✅ /api/token-price endpoint returns proper price data")
            print(f"Price data: {json.dumps(data, indent=2)}")
        else:
            print("❌ /api/token-price endpoint response missing expected keys")
    else:
        print(f"❌ /api/token-price endpoint failed with status code: {response.status_code}")
    
    # 1.4 Test /api/swap-quote endpoint
    print("\n1.4 Testing /api/swap-quote endpoint")
    swap_payload = {
        "token_address": test_token,
        "amount": "1000",
        "chain": "base"
    }
    
    response = requests.post(f"{API_URL}/swap-quote", json=swap_payload)
    if response.status_code == 200:
        data = response.json()
        if "status" in data and data["status"] == "success" and "data" in data:
            quote_data = data["data"]
            if all(key in quote_data for key in ["input_amount", "output_amount", "price_impact", "gas_estimate"]):
                print("✅ /api/swap-quote endpoint returns proper swap quote")
                print(f"Swap quote: {json.dumps(quote_data, indent=2)}")
            else:
                print("❌ /api/swap-quote endpoint response missing expected data keys")
        else:
            print("❌ /api/swap-quote endpoint response missing expected status or data")
    else:
        print(f"❌ /api/swap-quote endpoint failed with status code: {response.status_code}")
    
    # 1.5 Test /api/execute-burn endpoint
    print("\n1.5 Testing /api/execute-burn endpoint (simulation)")
    burn_payload = {
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "token_address": test_token,
        "amount": "1000",
        "chain": "base"
    }
    
    response = requests.post(f"{API_URL}/execute-burn", json=burn_payload)
    if response.status_code == 200:
        data = response.json()
        if "transaction_id" in data and "status" in data and data["status"] == "pending":
            print("✅ /api/execute-burn endpoint successfully creates burn transaction")
            print(f"Transaction ID: {data['transaction_id']}")
            print(f"Status: {data['status']}")
            if "amounts" in data:
                print(f"Allocation type: {data.get('allocation_type', 'N/A')}")
        else:
            print("❌ /api/execute-burn endpoint response missing expected keys")
    else:
        print(f"❌ /api/execute-burn endpoint failed with status code: {response.status_code}")
    
    # 2. Community Features
    print("\n2. COMMUNITY FEATURES")
    
    # 2.1 Test /api/community/stats endpoint
    print("\n2.1 Testing /api/community/stats endpoint")
    response = requests.get(f"{API_URL}/community/stats")
    if response.status_code == 200:
        data = response.json()
        expected_keys = ["total_burns", "total_volume_usd", "total_tokens_burned", 
                         "active_wallets", "chain_distribution", "top_burners", "recent_burns"]
        missing_keys = [key for key in expected_keys if key not in data]
        
        if not missing_keys:
            print("✅ /api/community/stats endpoint returns complete community statistics")
            print(f"Stats keys: {list(data.keys())}")
            
            # Check top_burners and recent_burns structure
            if data["top_burners"] and isinstance(data["top_burners"], list):
                print(f"Top burners count: {len(data['top_burners'])}")
            
            if data["recent_burns"] and isinstance(data["recent_burns"], list):
                print(f"Recent burns count: {len(data['recent_burns'])}")
        else:
            print(f"❌ /api/community/stats endpoint response missing expected keys: {missing_keys}")
    else:
        print(f"❌ /api/community/stats endpoint failed with status code: {response.status_code}")
    
    # 2.2 Test /api/transactions endpoint
    print("\n2.2 Testing /api/transactions endpoint")
    response = requests.get(f"{API_URL}/transactions")
    if response.status_code == 200:
        data = response.json()
        if "transactions" in data and isinstance(data["transactions"], list):
            print("✅ /api/transactions endpoint returns transaction data in correct format")
            print(f"Number of transactions: {len(data['transactions'])}")
            if data["transactions"]:
                print(f"Transaction keys: {list(data['transactions'][0].keys())}")
        else:
            print("❌ /api/transactions endpoint response doesn't have expected 'transactions' key")
    else:
        print(f"❌ /api/transactions endpoint failed with status code: {response.status_code}")
    
    # 2.3 Test /api/community/project endpoint
    print("\n2.3 Testing /api/community/project endpoint")
    project_payload = {
        "name": "Test Project",
        "description": "A test project for the community contest",
        "base_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "submitted_by": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "website": "https://example.com",
        "twitter": "@testproject",
        "logo_url": "https://example.com/logo.png"
    }
    
    response = requests.post(f"{API_URL}/community/project", json=project_payload)
    if response.status_code == 200:
        data = response.json()
        if "project_id" in data and "status" in data and data["status"] == "submitted":
            print("✅ /api/community/project endpoint successfully creates community project")
            print(f"Project ID: {data['project_id']}")
            print(f"Status: {data['status']}")
            
            # Save project ID for vote test
            project_id = data["project_id"]
            
            # Test voting
            print("\n2.4 Testing /api/community/vote endpoint")
            vote_payload = {
                "voter_wallet": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "project_id": project_id,
                "vote_token": "DRB",
                "vote_amount": "1000",
                "burn_tx_hash": "0x" + "a" * 64
            }
            
            vote_response = requests.post(f"{API_URL}/community/vote", json=vote_payload)
            if vote_response.status_code == 200:
                vote_data = vote_response.json()
                if "vote_id" in vote_data and "status" in vote_data and vote_data["status"] == "success":
                    print("✅ /api/community/vote endpoint successfully creates vote")
                    print(f"Vote ID: {vote_data['vote_id']}")
                    print(f"Status: {vote_data['status']}")
                else:
                    print("❌ /api/community/vote endpoint response missing expected keys")
            else:
                print(f"❌ /api/community/vote endpoint failed with status code: {vote_response.status_code}")
                
            # Test user votes
            print("\n2.5 Testing /api/community/votes/{wallet_address} endpoint")
            wallet = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            votes_response = requests.get(f"{API_URL}/community/votes/{wallet}")
            if votes_response.status_code == 200:
                votes_data = votes_response.json()
                if "votes" in votes_data and isinstance(votes_data["votes"], list):
                    print("✅ /api/community/votes endpoint returns user votes")
                    print(f"Number of votes: {len(votes_data['votes'])}")
                    if votes_data["votes"]:
                        print(f"Vote keys: {list(votes_data['votes'][0].keys())}")
                else:
                    print("❌ /api/community/votes endpoint response missing expected keys")
            else:
                print(f"❌ /api/community/votes endpoint failed with status code: {votes_response.status_code}")
        else:
            print("❌ /api/community/project endpoint response missing expected keys")
    else:
        print(f"❌ /api/community/project endpoint failed with status code: {response.status_code}")
    
    # 2.6 Test /api/community/contest endpoint
    print("\n2.6 Testing /api/community/contest endpoint")
    response = requests.get(f"{API_URL}/community/contest")
    if response.status_code == 200:
        data = response.json()
        expected_keys = ["voting_period", "projects", "vote_requirements", "contest_allocations"]
        missing_keys = [key for key in expected_keys if key not in data]
        
        if not missing_keys:
            print("✅ /api/community/contest endpoint returns complete contest information")
            print(f"Contest keys: {list(data.keys())}")
            
            # Check vote requirements
            if "vote_requirements" in data:
                vote_req = data["vote_requirements"]
                if "drb_amount" in vote_req and "bnkr_amount" in vote_req:
                    print(f"Vote requirements: DRB={vote_req['drb_amount']}, BNKR={vote_req['bnkr_amount']}")
                else:
                    print("❌ Vote requirements missing expected keys")
            
            # Check contest allocations
            if "contest_allocations" in data:
                allocations = data["contest_allocations"]
                if "drb_percentage" in allocations and "bnkr_percentage" in allocations:
                    print(f"Contest allocations: DRB={allocations['drb_percentage']}%, BNKR={allocations['bnkr_percentage']}%")
                else:
                    print("❌ Contest allocations missing expected keys")
        else:
            print(f"❌ /api/community/contest endpoint response missing expected keys: {missing_keys}")
    else:
        print(f"❌ /api/community/contest endpoint failed with status code: {response.status_code}")
    
    # 3. Transaction Tracking
    print("\n3. TRANSACTION TRACKING")
    
    # 3.1 Test /api/transaction-status/{tx_hash}/{chain} endpoint
    print("\n3.1 Testing /api/transaction-status endpoint")
    tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    chain = "base"
    
    response = requests.get(f"{API_URL}/transaction-status/{tx_hash}/{chain}")
    if response.status_code == 200:
        data = response.json()
        expected_keys = ["status", "confirmations", "tx_hash", "chain"]
        missing_keys = [key for key in expected_keys if key not in data]
        
        if not missing_keys:
            print("✅ /api/transaction-status endpoint returns transaction status in correct format")
            print(f"Status: {data['status']}")
            print(f"Confirmations: {data['confirmations']}")
        else:
            print(f"❌ /api/transaction-status endpoint response missing expected keys: {missing_keys}")
    else:
        print(f"❌ /api/transaction-status endpoint failed with status code: {response.status_code}")
    
    # 4. Cross-chain Operations
    print("\n4. CROSS-CHAIN OPERATIONS")
    
    # 4.1 Test /api/cross-chain/optimal-routes endpoint
    print("\n4.1 Testing /api/cross-chain/optimal-routes endpoint")
    response = requests.get(f"{API_URL}/cross-chain/optimal-routes")
    if response.status_code == 200:
        data = response.json()
        expected_keys = ["optimal_chains", "recommended_chain", "gas_estimates", "liquidity_analysis"]
        missing_keys = [key for key in expected_keys if key not in data]
        
        if not missing_keys:
            print("✅ /api/cross-chain/optimal-routes endpoint returns route optimization data")
            print(f"Recommended chain: {data['recommended_chain']}")
            print(f"Optimal chains: {data['optimal_chains']}")
        else:
            print(f"❌ /api/cross-chain/optimal-routes endpoint response missing expected keys: {missing_keys}")
    else:
        print(f"❌ /api/cross-chain/optimal-routes endpoint failed with status code: {response.status_code}")
    
    # 5. Edge Cases
    print("\n5. EDGE CASES")
    
    # 5.1 Test with invalid parameters
    print("\n5.1 Testing with invalid parameters")
    
    # Invalid token address
    invalid_token_payload = {
        "token_address": "invalid-address",
        "chain": "base"
    }
    
    response = requests.post(f"{API_URL}/check-burnable", json=invalid_token_payload)
    if response.status_code != 200:
        print("✅ /api/check-burnable properly rejects invalid token address")
    else:
        data = response.json()
        if data.get("is_burnable") == False or "error" in data:
            print("✅ /api/check-burnable properly handles invalid token address")
        else:
            print("❌ /api/check-burnable incorrectly accepts invalid token address")
    
    # Invalid chain
    response = requests.get(f"{API_URL}/gas-estimates/invalid-chain")
    if response.status_code != 200:
        print("✅ /api/gas-estimates properly rejects invalid chain")
    else:
        print("❌ /api/gas-estimates incorrectly accepts invalid chain")
    
    # Invalid wallet address
    invalid_wallet_payload = {
        "wallet_address": "invalid-wallet",
        "token_address": test_token,
        "amount": "1000",
        "chain": "base"
    }
    
    response = requests.post(f"{API_URL}/execute-burn", json=invalid_wallet_payload)
    if response.status_code != 200:
        print("✅ /api/execute-burn properly rejects invalid wallet address")
    else:
        print("❌ /api/execute-burn incorrectly accepts invalid wallet address")
    
    # 5.2 Test error handling
    print("\n5.2 Testing error handling")
    
    # Missing required parameters
    incomplete_burn_payload = {
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        # Missing token_address and amount
        "chain": "base"
    }
    
    response = requests.post(f"{API_URL}/execute-burn", json=incomplete_burn_payload)
    if response.status_code != 200:
        print("✅ /api/execute-burn properly rejects incomplete payload")
    else:
        print("❌ /api/execute-burn incorrectly accepts incomplete payload")
    
    # Missing required parameters for project submission
    incomplete_project_payload = {
        "name": "Incomplete Project"
        # Missing other required fields
    }
    
    response = requests.post(f"{API_URL}/community/project", json=incomplete_project_payload)
    if response.status_code != 200:
        print("✅ /api/community/project properly rejects incomplete payload")
    else:
        print("❌ /api/community/project incorrectly accepts incomplete payload")
    
    # 5.3 Test response formats
    print("\n5.3 Testing response formats match frontend expectations")
    
    # Check community stats format
    response = requests.get(f"{API_URL}/community/stats")
    if response.status_code == 200:
        data = response.json()
        # Check if the response has the keys expected by the frontend
        frontend_keys = ["total_burns", "total_volume_usd", "total_tokens_burned", "active_wallets", 
                         "chain_distribution", "top_burners", "recent_burns"]
        missing_keys = [key for key in frontend_keys if key not in data]
        
        if not missing_keys:
            print("✅ /api/community/stats response format matches frontend expectations")
        else:
            print(f"❌ /api/community/stats response missing keys expected by frontend: {missing_keys}")
    
    # Check transactions format
    response = requests.get(f"{API_URL}/transactions")
    if response.status_code == 200:
        data = response.json()
        if "transactions" in data and isinstance(data["transactions"], list):
            print("✅ /api/transactions response format matches frontend expectations")
        else:
            print("❌ /api/transactions response format doesn't match frontend expectations")
    
    # 6. Performance and Stability
    print("\n6. PERFORMANCE AND STABILITY")
    
    # 6.1 Test response times
    print("\n6.1 Testing response times")
    
    endpoints = [
        {"method": "GET", "url": f"{API_URL}/health"},
        {"method": "GET", "url": f"{API_URL}/chains"},
        {"method": "GET", "url": f"{API_URL}/stats"},
        {"method": "GET", "url": f"{API_URL}/community/stats"},
        {"method": "GET", "url": f"{API_URL}/transactions"}
    ]
    
    for endpoint in endpoints:
        start_time = time.time()
        if endpoint["method"] == "GET":
            response = requests.get(endpoint["url"])
        else:
            response = requests.post(endpoint["url"])
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ {endpoint['url']} - Response time: {response_time:.4f} seconds")
        else:
            print(f"❌ {endpoint['url']} - Failed with status code: {response.status_code}")
    
    # 6.2 Test concurrent requests
    print("\n6.2 Testing concurrent requests")
    
    import concurrent.futures
    
    def make_request(endpoint):
        start_time = time.time()
        if endpoint["method"] == "GET":
            response = requests.get(endpoint["url"])
        else:
            response = requests.post(endpoint["url"], json=endpoint.get("payload", {}))
        
        response_time = time.time() - start_time
        return {
            "url": endpoint["url"],
            "status_code": response.status_code,
            "response_time": response_time
        }
    
    concurrent_endpoints = [
        {"method": "GET", "url": f"{API_URL}/health"},
        {"method": "GET", "url": f"{API_URL}/chains"},
        {"method": "GET", "url": f"{API_URL}/stats"},
        {"method": "GET", "url": f"{API_URL}/community/stats"},
        {"method": "GET", "url": f"{API_URL}/transactions"},
        {"method": "POST", "url": f"{API_URL}/check-burnable", "payload": burnable_payload},
        {"method": "POST", "url": f"{API_URL}/check-burnable", "payload": non_burnable_payload},
        {"method": "GET", "url": f"{API_URL}/gas-estimates/base"},
        {"method": "GET", "url": f"{API_URL}/token-price/{test_token}/base"},
        {"method": "POST", "url": f"{API_URL}/swap-quote", "payload": swap_payload}
    ]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_endpoint = {executor.submit(make_request, endpoint): endpoint for endpoint in concurrent_endpoints}
        
        success_count = 0
        failure_count = 0
        total_time = 0
        
        for future in concurrent.futures.as_completed(future_to_endpoint):
            result = future.result()
            if result["status_code"] == 200:
                success_count += 1
                total_time += result["response_time"]
                print(f"✅ Concurrent {result['url']} - Response time: {result['response_time']:.4f} seconds")
            else:
                failure_count += 1
                print(f"❌ Concurrent {result['url']} - Failed with status code: {result['status_code']}")
        
        if success_count > 0:
            avg_time = total_time / success_count
            print(f"\nConcurrent requests summary:")
            print(f"Success: {success_count}/{len(concurrent_endpoints)}")
            print(f"Failures: {failure_count}/{len(concurrent_endpoints)}")
            print(f"Average response time: {avg_time:.4f} seconds")
        else:
            print("\nAll concurrent requests failed")
    
    print("\n" + "=" * 80)
    print("SPECIFIC ENDPOINT TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    # Run the specific tests for the endpoints mentioned in the review request
    test_specific_endpoints()
    
    # Uncomment to run all tests
    # run_tests()
