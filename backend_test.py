
import requests
import unittest
import json
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://3a95f327-f436-45cf-b1c0-6652d03679be.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BurnReliefBotAPITests(unittest.TestCase):
    """Test suite for Burn Relief Bot API endpoints after Base-only simplification"""

    def setUp(self):
        """Setup for each test"""
        self.test_wallet = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        self.test_token = "0xA0b86A33E6441838c1f8B8Dd52B0B8b37c5Bc75F"  # Regular token
        self.bnkr_token = "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b"  # $BNKR token
        self.drb_token = "0x1234567890123456789012345678901234567890"  # DRB token
        self.usdc_token = "0x833589fCD6eDb6E08f4c7C32d4f71b54bdA02913"  # USDC on Base
        self.test_amount = "1000"
        self.chain = "base"  # Only Base chain is supported now

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
        """Test chains endpoint for Base-only setup"""
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
        
        # Verify allocations
        self.assertIn("allocations", data)
        allocations = data["allocations"]
        self.assertEqual(allocations["burn_percentage"], 88.0)
        self.assertEqual(allocations["drb_total_percentage"], 10.0)
        self.assertEqual(allocations["bnkr_total_percentage"], 2.5)
        self.assertEqual(allocations["bnkr_community_percentage"], 1.5)
        self.assertEqual(allocations["bnkr_team_percentage"], 1.0)
        
        print("✅ Chains endpoint verified - Base-only setup confirmed")

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
        """Test burn endpoint"""
        payload = {
            "wallet_address": self.test_wallet,
            "token_address": self.test_token,
            "amount": self.test_amount,
            "chain": self.chain
        }
        
        response = requests.post(f"{API_URL}/burn", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify burn response
        self.assertIn("transaction_id", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "pending")
        self.assertIn("amounts", data)
        self.assertIn("is_burnable", data)
        self.assertIn("allocation_type", data)
        
        # Verify amounts
        amounts = data["amounts"]
        self.assertIn("burn_amount", amounts)
        self.assertIn("drb_total_amount", amounts)
        self.assertIn("drb_grok_amount", amounts)
        self.assertIn("drb_team_amount", amounts)
        self.assertIn("drb_community_amount", amounts)
        self.assertIn("bnkr_total_amount", amounts)
        self.assertIn("bnkr_community_amount", amounts)
        self.assertIn("bnkr_team_amount", amounts)
        
        print("✅ Burn endpoint verified")

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
