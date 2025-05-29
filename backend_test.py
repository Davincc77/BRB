
import requests
import unittest
import json
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://3a95f327-f436-45cf-b1c0-6652d03679be.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BurnReliefBotAPITests(unittest.TestCase):
    """Test suite for Burn Relief Bot API endpoints"""

    def setUp(self):
        """Setup for each test"""
        self.test_wallet = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        self.test_token = "0xa0b86a33e6441838c1f8b8dd52b0b8b37c5bc75f"  # USDC
        self.test_amount = "1000"
        self.test_chains = ["base", "ethereum", "polygon", "arbitrum"]

    def test_01_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{API_URL}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "active")
        self.assertEqual(data["version"], "1.0.0")
        print("✅ API health check passed")

    def test_02_config_endpoint(self):
        """Test config endpoint"""
        response = requests.get(f"{API_URL}/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify config data
        self.assertIn("burn_address", data)
        self.assertIn("drb_token_address", data)
        self.assertIn("cbbtc_token_address", data)
        self.assertIn("supported_chains", data)
        self.assertIn("allocation", data)
        self.assertIn("wallets", data)
        
        # Verify allocation percentages
        allocation = data["allocation"]
        self.assertEqual(allocation["burn_percentage"], 88.0)
        self.assertEqual(allocation["drb_total_percentage"], 9.5)
        self.assertEqual(allocation["cbbtc_total_percentage"], 2.5)
        
        print("✅ Config endpoint verified")

    def test_03_stats_endpoint(self):
        """Test stats endpoint"""
        response = requests.get(f"{API_URL}/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify stats data structure
        self.assertIn("total_burns", data)
        self.assertIn("total_amount_burned", data)
        self.assertIn("total_users", data)
        self.assertIn("trending_tokens", data)
        self.assertIn("top_burners", data)
        
        # Verify data types
        self.assertIsInstance(data["total_burns"], int)
        self.assertIsInstance(data["total_amount_burned"], str)
        self.assertIsInstance(data["total_users"], int)
        self.assertIsInstance(data["trending_tokens"], list)
        self.assertIsInstance(data["top_burners"], list)
        
        print(f"✅ Stats endpoint: {data['total_burns']} burns, {data['total_users']} users")

    def test_04_chains_endpoint(self):
        """Test chains endpoint"""
        response = requests.get(f"{API_URL}/chains")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("chains", data)
        
        chains = data["chains"]
        # Verify required chains are present
        required_chains = ["base", "solana", "ethereum", "polygon", "sui", "bitcoin"]
        for chain in required_chains:
            self.assertIn(chain, chains)
            
        # Verify chain data structure
        for chain_id, chain_data in chains.items():
            self.assertIn("name", chain_data)
            self.assertIn("chain_id", chain_data)
            self.assertIn("rpc_url", chain_data)
            self.assertIn("explorer", chain_data)
            self.assertIn("recipient_wallet", chain_data)
            self.assertIn("currency", chain_data)
            
        print(f"✅ Chains endpoint returned {len(chains)} chains")

    def test_05_optimal_routes_endpoint(self):
        """Test optimal routes endpoint"""
        response = requests.get(f"{API_URL}/cross-chain/optimal-routes")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify optimal chains data
        self.assertIn("optimal_chains", data)
        self.assertIn("DRB", data["optimal_chains"])
        self.assertIn("cbBTC", data["optimal_chains"])
        
        # Verify supported bridges
        self.assertIn("supported_bridges", data)
        self.assertGreater(len(data["supported_bridges"]), 0)
        
        # Verify supported chains
        self.assertIn("supported_chains", data)
        self.assertGreater(len(data["supported_chains"]), 0)
        
        # Verify routing strategy
        self.assertIn("routing_strategy", data)
        
        # Verify last updated timestamp
        self.assertIn("last_updated", data)
        
        print(f"✅ Optimal routes: $DRB on {data['optimal_chains']['DRB']}, $cbBTC on {data['optimal_chains']['cbBTC']}")

    def test_06_cross_chain_supported_tokens(self):
        """Test supported tokens endpoint"""
        for chain in self.test_chains:
            response = requests.get(f"{API_URL}/cross-chain/supported-tokens/{chain}")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("chain", data)
            self.assertIn("supported_tokens", data)
            self.assertGreater(len(data["supported_tokens"]), 0)
            
        print(f"✅ Supported tokens endpoint tested for {len(self.test_chains)} chains")

    def test_07_analyze_cross_chain_route(self):
        """Test cross-chain route analysis"""
        for chain in self.test_chains:
            payload = {
                "source_chain": chain,
                "source_token": self.test_token,
                "amount": self.test_amount
            }
            
            response = requests.post(f"{API_URL}/cross-chain/analyze-route", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Verify route analysis response
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("routes", data)
            self.assertGreater(len(data["routes"]), 0)
            self.assertIn("total_estimated_time", data)
            self.assertIn("total_estimated_cost", data)
            
            # Verify route steps
            routes = data["routes"]
            self.assertEqual(routes[0]["type"], "burn")  # First step should always be burn
            
            # Check if DRB and cbBTC routes are present
            route_types = [route["type"] for route in routes]
            self.assertTrue(any("drb" in route_type for route_type in route_types))
            self.assertTrue(any("cbbtc" in route_type for route_type in route_types))
            
        print(f"✅ Cross-chain route analysis tested for {len(self.test_chains)} chains")

    def test_08_token_validation(self):
        """Test token validation endpoint"""
        for chain in self.test_chains:
            payload = {
                "token_address": self.test_token,
                "chain": chain
            }
            
            response = requests.post(f"{API_URL}/validate-token", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Verify validation response
            self.assertIn("is_valid", data)
            if data["is_valid"]:
                self.assertIn("token_name", data)
                self.assertIn("token_symbol", data)
            else:
                self.assertIn("reason", data)
                
        print(f"✅ Token validation endpoint tested for {len(self.test_chains)} chains")

    def test_09_gas_estimates(self):
        """Test gas estimates endpoint"""
        for chain in self.test_chains:
            response = requests.get(f"{API_URL}/gas-estimates/{chain}")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Verify gas estimate data
            self.assertEqual(data["chain"], chain)
            self.assertIn("slow", data)
            self.assertIn("standard", data)
            self.assertIn("fast", data)
            self.assertIn("currency", data)
            
        print(f"✅ Gas estimates tested for {len(self.test_chains)} chains")

    def test_10_swap_quote(self):
        """Test swap quote functionality"""
        for chain in self.test_chains:
            payload = {
                "input_token": self.test_token,
                "output_token": "0x3ec2156D4c0A9CBdAB4a016633b7BcF6a8d68Ea2",  # DRB token
                "amount": self.test_amount,
                "chain": chain
            }
            
            response = requests.post(f"{API_URL}/swap-quote", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Verify quote data
            self.assertEqual(data["input_amount"], self.test_amount)
            self.assertIn("output_amount", data)
            self.assertIn("price_impact", data)
            self.assertIn("gas_estimate", data)
            
        print(f"✅ Swap quote functionality tested for {len(self.test_chains)} chains")

    def test_11_execute_cross_chain_burn(self):
        """Test cross-chain burn execution"""
        payload = {
            "wallet_address": self.test_wallet,
            "source_chain": "polygon",  # Test with a non-optimal chain to trigger cross-chain
            "source_token": self.test_token,
            "amount": self.test_amount,
            "approve_cross_chain": True
        }
        
        response = requests.post(f"{API_URL}/cross-chain/execute-burn", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify execution response
        self.assertTrue(data["success"])
        self.assertIn("cross_chain_transaction_id", data)
        self.assertIn("execution_plan", data)
        self.assertIn("total_transactions", data)
        self.assertGreater(data["total_transactions"], 0)
        
        # Store transaction ID for monitoring test
        self.transaction_id = data["cross_chain_transaction_id"]
        
        print(f"✅ Cross-chain burn execution successful with {data['total_transactions']} transactions")
        return data["cross_chain_transaction_id"]

    def test_12_get_cross_chain_transaction(self):
        """Test retrieving cross-chain transaction"""
        # First execute a transaction to get an ID
        tx_id = self.test_11_execute_cross_chain_burn()
        
        # Wait a moment for transaction to be processed
        time.sleep(2)
        
        # Get transaction details
        response = requests.get(f"{API_URL}/cross-chain/transaction/{tx_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify transaction data
        self.assertEqual(data["id"], tx_id)
        self.assertEqual(data["user_address"], self.test_wallet)
        self.assertEqual(data["source_chain"], "polygon")
        self.assertEqual(data["source_token"], self.test_token)
        self.assertEqual(data["amount"], self.test_amount)
        self.assertIn("execution_plan", data)
        self.assertGreater(len(data["execution_plan"]), 0)
        
        print(f"✅ Cross-chain transaction retrieval successful")

    def test_13_monitor_cross_chain_transaction(self):
        """Test monitoring cross-chain transaction"""
        # Use a mock transaction hash for testing
        tx_hash = "0xbridge1234567890123456789012345678901234567890123456789012345678"
        chain = "ethereum"
        
        response = requests.get(f"{API_URL}/cross-chain/monitor/{tx_hash}/{chain}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify monitoring data
        self.assertEqual(data["tx_hash"], tx_hash)
        self.assertEqual(data["chain"], chain)
        self.assertIn("status", data)
        self.assertIn("confirmations", data)
        self.assertIn("estimated_completion", data)
        
        print(f"✅ Cross-chain transaction monitoring successful")

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
