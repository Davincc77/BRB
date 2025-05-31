
import requests
import sys
import json
import time
from datetime import datetime

class BurnReliefBotPhase3Tester:
    def __init__(self, base_url="https://2da4bb13-3091-4413-9807-6a6cfcfa1853.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # Constants for testing
        self.valid_base_token = "0x4200000000000000000000000000000000000006"  # Example token on Base
        self.valid_eth_token = "0xdAC17F958D2ee523a2206206994597C13D831ec7"  # USDT on Ethereum
        self.valid_polygon_token = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC on Polygon
        self.valid_arbitrum_token = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"  # USDC on Arbitrum
        self.valid_solana_token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC on Solana
        
        self.drb_token = "0x3ec2156D4c0A9CBdAB4a016633b7BcF6a8d68Ea2"  # DRB token
        self.cbbtc_token = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"  # cbBTC token
        
        # Test wallet addresses
        self.test_wallet = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Test EVM wallet
        self.test_solana_wallet = "CtFtfe2pYRiJVAUrEZtdFKZVV2UFpdaWBU1Ve7aPC"  # Test Solana wallet
        
        # Supported chains
        self.chains = ["base", "ethereum", "polygon", "arbitrum", "solana"]
        
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
    
    # PHASE 3 REAL BLOCKCHAIN TESTS
    
    def test_swap_quote(self, chain, input_token, output_token, amount):
        """Test the swap quote API endpoint"""
        data = {
            "input_token": input_token,
            "output_token": output_token,
            "amount": amount,
            "chain": chain
        }
        
        success, response = self.run_test(
            f"Swap Quote ({chain}): {amount} {input_token} → {output_token}", 
            "POST", 
            "swap-quote", 
            data=data
        )
        
        if success and response:
            # Verify response structure
            required_fields = ["input_amount", "output_amount", "price_impact", "gas_estimate"]
            all_fields_present = all(field in response for field in required_fields)
            
            if all_fields_present:
                print(f"✅ Swap quote contains all required fields")
                print(f"   Input: {response['input_amount']} → Output: {response['output_amount']}")
                print(f"   Price Impact: {response['price_impact']}, Gas Estimate: {response['gas_estimate']}")
                return True, response
            else:
                missing_fields = [field for field in required_fields if field not in response]
                print(f"❌ Missing swap quote fields: {', '.join(missing_fields)}")
                return False, response
        
        return success, response
    
    def test_gas_estimates(self, chain):
        """Test gas estimation for a specific chain"""
        success, response = self.run_test(
            f"Gas Estimates for {chain}", 
            "GET", 
            f"gas-estimates/{chain}"
        )
        
        if success and response:
            # Verify response structure
            required_fields = ["chain", "slow", "standard", "fast", "currency"]
            all_fields_present = all(field in response for field in required_fields)
            
            if all_fields_present:
                print(f"✅ Gas estimates contain all required fields")
                print(f"   Slow: {response['slow']['price']} {response['currency']}")
                print(f"   Standard: {response['standard']['price']} {response['currency']}")
                print(f"   Fast: {response['fast']['price']} {response['currency']}")
                return True, response
            else:
                missing_fields = [field for field in required_fields if field not in response]
                print(f"❌ Missing gas estimate fields: {', '.join(missing_fields)}")
                return False, response
        
        return success, response
    
    def test_token_price(self, chain, token_address):
        """Test token price fetching"""
        success, response = self.run_test(
            f"Token Price for {token_address} on {chain}", 
            "GET", 
            f"token-price/{token_address}/{chain}"
        )
        
        if success and response:
            # Verify response structure
            required_fields = ["token_address", "chain", "price_usd"]
            all_fields_present = all(field in response for field in required_fields)
            
            if all_fields_present:
                print(f"✅ Token price response contains all required fields")
                print(f"   Price: ${response['price_usd']}")
                return True, response
            else:
                missing_fields = [field for field in required_fields if field not in response]
                print(f"❌ Missing token price fields: {', '.join(missing_fields)}")
                return False, response
        
        return success, response
    
    def test_execute_burn(self, chain, token_address, amount):
        """Test the execute-burn endpoint"""
        data = {
            "wallet_address": self.test_wallet if chain != "solana" else self.test_solana_wallet,
            "token_address": token_address,
            "amount": amount,
            "chain": chain,
            "slippage_tolerance": 3.0
        }
        
        success, response = self.run_test(
            f"Execute Burn on {chain}: {amount} {token_address}", 
            "POST", 
            "execute-burn", 
            data=data
        )
        
        if success and response:
            # Verify response structure
            required_fields = ["success", "burn_transaction_id", "blockchain_result", "message"]
            all_fields_present = all(field in response for field in required_fields)
            
            if all_fields_present and response["success"]:
                print(f"✅ Execute burn response contains all required fields")
                print(f"   Burn Transaction ID: {response['burn_transaction_id']}")
                print(f"   Message: {response['message']}")
                
                # Check blockchain result
                blockchain_result = response["blockchain_result"]
                if "transactions" in blockchain_result and len(blockchain_result["transactions"]) > 0:
                    print(f"✅ Contains {len(blockchain_result['transactions'])} transactions")
                    
                    # Test transaction status monitoring
                    burn_tx_id = response['burn_transaction_id']
                    for tx in blockchain_result["transactions"]:
                        tx_hash = tx.get("hash") or tx.get("signature", "")
                        if tx_hash:
                            self.test_transaction_status(chain, tx_hash)
                    
                    return True, response
                else:
                    print("❌ No transactions in blockchain result")
                    return False, response
            else:
                missing_fields = [field for field in required_fields if field not in response]
                if missing_fields:
                    print(f"❌ Missing execute burn fields: {', '.join(missing_fields)}")
                else:
                    print(f"❌ Execute burn failed: {response.get('message', 'Unknown error')}")
                return False, response
        
        return success, response
    
    def test_transaction_status(self, chain, tx_hash):
        """Test transaction status monitoring"""
        success, response = self.run_test(
            f"Transaction Status for {tx_hash} on {chain}", 
            "GET", 
            f"transaction-status/{tx_hash}/{chain}"
        )
        
        if success and response:
            # Verify response structure
            if "status" in response:
                print(f"✅ Transaction status: {response['status']}")
                if "confirmations" in response:
                    print(f"   Confirmations: {response['confirmations']}")
                return True, response
            else:
                print("❌ Missing status field in transaction status response")
                return False, response
        
        return success, response
    
    def test_full_burn_flow(self, chain, token_address, amount):
        """Test the full burn flow from quote to execution to monitoring"""
        print(f"\n{'=' * 50}")
        print(f"TESTING FULL BURN FLOW ON {chain.upper()}")
        print(f"{'=' * 50}")
        
        # Step 1: Get token price
        print("\nStep 1: Get token price")
        price_success, price_response = self.test_token_price(chain, token_address)
        
        # Step 2: Get gas estimates
        print("\nStep 2: Get gas estimates")
        gas_success, gas_response = self.test_gas_estimates(chain)
        
        # Step 3: Get swap quotes
        print("\nStep 3: Get swap quotes for DRB")
        drb_quote_success, drb_quote_response = self.test_swap_quote(
            chain, token_address, self.drb_token, str(float(amount) * 0.06)
        )
        
        print("\nStep 4: Get swap quotes for cbBTC")
        cbbtc_quote_success, cbbtc_quote_response = self.test_swap_quote(
            chain, token_address, self.cbbtc_token, str(float(amount) * 0.06)
        )
        
        # Step 5: Execute burn
        print("\nStep 5: Execute burn transaction")
        burn_success, burn_response = self.test_execute_burn(chain, token_address, amount)
        
        # Overall success
        all_steps_success = price_success and gas_success and drb_quote_success and cbbtc_quote_success and burn_success
        
        print(f"\n{'=' * 50}")
        print(f"FULL BURN FLOW ON {chain.upper()}: {'✅ SUCCESS' if all_steps_success else '❌ FAILED'}")
        print(f"{'=' * 50}")
        
        return all_steps_success

def main():
    print("=" * 50)
    print("Burn Relief Bot - Phase 3 Real Blockchain Test Suite")
    print("=" * 50)
    
    tester = BurnReliefBotPhase3Tester()
    
    # Test all chains for gas estimates
    for chain in tester.chains:
        tester.test_gas_estimates(chain)
    
    # Test token prices
    tester.test_token_price("base", tester.valid_base_token)
    tester.test_token_price("ethereum", tester.valid_eth_token)
    tester.test_token_price("polygon", tester.valid_polygon_token)
    tester.test_token_price("arbitrum", tester.valid_arbitrum_token)
    
    # Test swap quotes
    tester.test_swap_quote("base", tester.valid_base_token, tester.drb_token, "100")
    tester.test_swap_quote("ethereum", tester.valid_eth_token, tester.drb_token, "100")
    tester.test_swap_quote("polygon", tester.valid_polygon_token, tester.drb_token, "100")
    tester.test_swap_quote("arbitrum", tester.valid_arbitrum_token, tester.drb_token, "100")
    
    # Test full burn flow on each chain
    tester.test_full_burn_flow("base", tester.valid_base_token, "1000")
    tester.test_full_burn_flow("ethereum", tester.valid_eth_token, "1000")
    tester.test_full_burn_flow("polygon", tester.valid_polygon_token, "1000")
    tester.test_full_burn_flow("arbitrum", tester.valid_arbitrum_token, "1000")
    
    # Print results
    print("\n" + "=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
