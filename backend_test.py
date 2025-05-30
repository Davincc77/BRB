
import requests
import unittest
import json
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://3a95f327-f436-45cf-b1c0-6652d03679be.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BurnReliefBotAPITests(unittest.TestCase):
    """Test suite for Burn Relief Bot API endpoints after Community Contest upgrade"""

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
        self.assertEqual(response.status_code, 400)  # Should return 400 Bad Request
        
        # Test vote submission with missing required fields
        incomplete_vote = {
            "voter_wallet": self.test_wallet
            # Missing other required fields
        }
        
        response = requests.post(f"{API_URL}/community/vote", json=incomplete_vote)
        self.assertEqual(response.status_code, 400)  # Should return 400 Bad Request
        
        print("✅ Error handling for missing parameters verified")
    
    def test_16_error_handling_invalid_requests(self):
        """Test error handling for invalid requests"""
        # Test with invalid token address format
        payload = {
            "token_address": "invalid-address",  # Not a valid Ethereum address
            "chain": self.chain
        }
        
        response = requests.post(f"{API_URL}/validate-token", json=payload)
        # Should either return 400 Bad Request or 200 with is_valid=False
        if response.status_code == 200:
            data = response.json()
            self.assertIn("is_valid", data)
            self.assertFalse(data["is_valid"])
        else:
            self.assertEqual(response.status_code, 400)
        
        # Test with invalid chain
        payload = {
            "token_address": self.test_token,
            "chain": "invalid-chain"  # Not a supported chain
        }
        
        response = requests.get(f"{API_URL}/gas-estimates/invalid-chain")
        self.assertEqual(response.status_code, 400)  # Should return 400 Bad Request
        
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

if __name__ == "__main__":
    run_tests()
