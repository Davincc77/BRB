import requests
import json
import unittest
import os

# Get backend URL from frontend .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1]
            break
    else:
        BACKEND_URL = "https://da1071c2-49d0-40cd-a59e-7eddc2918c8b.preview.emergentagent.com"

API_URL = f"{BACKEND_URL}/api"

class TestMultiChainWalletSystem(unittest.TestCase):
    """Test the multi-chain wallet system and token classification"""

    def test_01_check_burnable_with_different_chains(self):
        """Test /api/check-burnable with different chains"""
        chains = ["base", "ethereum", "solana", "bitcoin", "litecoin", "dogecoin"]
        
        for chain in chains:
            # Test with DRB token (should be burnable)
            payload = {
                "token_address": "0x1234567890123456789012345678901234567890",  # DRB token
                "chain": chain
            }
            response = requests.post(f"{API_URL}/check-burnable", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print(f"\nTesting chain: {chain} with DRB token")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify correct wallet addresses are returned for each chain
            self.assertIn("recipient_wallet", data)
            self.assertIn("chain_wallets", data)
            
            # Verify chain-specific addresses
            if chain == "ethereum":
                self.assertEqual(data["recipient_wallet"], "0x204B520ae6311491cB78d3BAaDfd7eA67FD4456F")
            elif chain == "solana":
                self.assertEqual(data["recipient_wallet"], "26DXAxLUKNgeiv6hj74L4mhFZmXqc44aMFjRWGo8UhYo")
            elif chain in ["bitcoin", "litecoin", "dogecoin"]:
                self.assertTrue("xpub" in data["recipient_wallet"])
            
            # Verify DRB is marked as burnable
            self.assertTrue(data["is_burnable"])
            
            # Test with BNKR token (should be burnable)
            payload = {
                "token_address": "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b",  # BNKR token
                "chain": chain
            }
            response = requests.post(f"{API_URL}/check-burnable", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print(f"\nTesting chain: {chain} with BNKR token")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify BNKR is marked as burnable
            self.assertTrue(data["is_burnable"])
            
            # Test with a non-burnable token (BTC)
            payload = {
                "token_address": "bitcoin",  # BTC token
                "chain": chain
            }
            response = requests.post(f"{API_URL}/check-burnable", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print(f"\nTesting chain: {chain} with BTC token")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify BTC is marked as non-burnable
            self.assertFalse(data["is_burnable"])
            
            # Test with a new token (should default to non-burnable)
            payload = {
                "token_address": "0xabcdef1234567890abcdef1234567890abcdef12",  # New token
                "chain": chain
            }
            response = requests.post(f"{API_URL}/check-burnable", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print(f"\nTesting chain: {chain} with new token")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify new token defaults to non-burnable
            self.assertFalse(data["is_burnable"])
    
    def test_02_token_classification(self):
        """Test token classification for various tokens"""
        
        # Test that DRB token is marked as burnable
        payload = {
            "token_address": "0x1234567890123456789012345678901234567890",  # DRB token
            "chain": "base"
        }
        response = requests.post(f"{API_URL}/check-burnable", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_burnable"])
        
        # Test that BNKR token is marked as burnable
        payload = {
            "token_address": "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b",  # BNKR token
            "chain": "base"
        }
        response = requests.post(f"{API_URL}/check-burnable", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_burnable"])
        
        # Test that major cryptocurrencies are marked as non-burnable
        non_burnable_tokens = [
            "btc", "bitcoin", "eth", "ethereum", "sol", "solana", 
            "usdc", "usdt", "dai", "link", "matic", "polygon"
        ]
        
        for token in non_burnable_tokens:
            payload = {
                "token_address": token,
                "chain": "base"
            }
            response = requests.post(f"{API_URL}/check-burnable", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print(f"\nTesting token: {token}")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify token is marked as non-burnable
            self.assertFalse(data["is_burnable"])
        
        # Test that NEW tokens default to NON-BURNABLE
        new_tokens = [
            "0xabcdef1234567890abcdef1234567890abcdef12",
            "0x9876543210fedcba9876543210fedcba98765432",
            "0x1111111111222222222233333333334444444444"
        ]
        
        for token in new_tokens:
            payload = {
                "token_address": token,
                "chain": "base"
            }
            response = requests.post(f"{API_URL}/check-burnable", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print(f"\nTesting new token: {token}")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify new token defaults to non-burnable
            self.assertFalse(data["is_burnable"])
    
    def test_03_wallet_status(self):
        """Test wallet status endpoint"""
        response = requests.get(f"{API_URL}/wallet/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        print(f"\nWallet Status Response: {json.dumps(data, indent=2)}")
        
        # Verify BurnReliefBot wallet is connected
        self.assertIn("connected", data)
        self.assertIn("wallet_address", data)
        
        # Verify wallet address is correct
        if data["wallet_address"]:
            self.assertEqual(data["wallet_address"], "0x204B520ae6311491cB78d3BAaDfd7eA67FD4456F")

def run_tests():
    """Run all tests"""
    print(f"🧪 Testing Multi-Chain Wallet System and Token Classification at {API_URL}")
    print("=" * 80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestMultiChainWalletSystem)
    
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