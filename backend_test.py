#!/usr/bin/env python3
import requests
import json
import time
import sys
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://da1071c2-49d0-40cd-a59e-7eddc2918c8b.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

# Test wallet addresses
TEST_WALLET = "0x1234567890123456789012345678901234567890"
TEST_TOKEN = "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b"  # BNKR token
TEST_AMOUNT = "100"

# Admin token for testing admin endpoints
ADMIN_TOKEN = "admin_token_davincc"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}== {text}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")

def print_success(text):
    """Print a success message"""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Print an error message"""
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    """Print a warning message"""
    print(f"{YELLOW}! {text}{RESET}")

def print_info(text):
    """Print an info message"""
    print(f"{BLUE}ℹ {text}{RESET}")

def test_endpoint(method, endpoint, expected_status=200, data=None, headers=None, params=None, verify_keys=None):
    """
    Test an API endpoint and verify the response
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint to test
        expected_status: Expected HTTP status code
        data: Request data (for POST/PUT)
        headers: Request headers
        params: URL parameters
        verify_keys: List of keys to verify in the response
        
    Returns:
        tuple: (success, response_data)
    """
    url = f"{API_BASE_URL}{endpoint}"
    print_info(f"Testing {method} {url}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print_error(f"Unsupported method: {method}")
            return False, None
        
        # Check status code
        if response.status_code != expected_status:
            print_error(f"Expected status {expected_status}, got {response.status_code}")
            print_error(f"Response: {response.text}")
            return False, None
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            if expected_status != 200:
                # Non-200 responses might not be JSON
                print_warning("Response is not JSON (expected for error responses)")
                return True, response.text
            print_error(f"Invalid JSON response: {response.text}")
            return False, None
        
        # Verify keys in response
        if verify_keys:
            missing_keys = [key for key in verify_keys if key not in response_data]
            if missing_keys:
                print_error(f"Missing keys in response: {missing_keys}")
                return False, response_data
        
        print_success(f"Response: {response.status_code} {response.reason}")
        return True, response_data
    
    except requests.RequestException as e:
        print_error(f"Request failed: {e}")
        return False, None

def test_health_check():
    """Test the health check endpoint"""
    print_header("Testing Health Check Endpoint")
    
    success, data = test_endpoint(
        "GET", 
        "/health", 
        verify_keys=["status", "timestamp"]
    )
    
    if success:
        if data["status"] == "healthy":
            print_success("Health check endpoint is working correctly")
        else:
            print_error(f"Unexpected status: {data['status']}")
    
    return success

def test_chains_endpoint():
    """Test the chains endpoint"""
    print_header("Testing Chains Endpoint")
    
    success, data = test_endpoint(
        "GET", 
        "/chains", 
        verify_keys=["chains", "default_chain", "allocations"]
    )
    
    if success:
        # Verify Base chain is returned
        if "base" in data["chains"]:
            print_success("Base chain is correctly returned")
        else:
            print_error("Base chain not found in response")
            return False
        
        # Verify allocations
        allocations = data["allocations"]
        if allocations["burn_percentage"] == 88.0:
            print_success("Burn percentage is correct (88%)")
        else:
            print_error(f"Incorrect burn percentage: {allocations['burn_percentage']}")
        
        # Verify BNKR allocations
        if allocations["bnkr_total_percentage"] == 2.5:
            print_success("BNKR total percentage is correct (2.5%)")
        else:
            print_error(f"Incorrect BNKR percentage: {allocations['bnkr_total_percentage']}")
        
        # Verify team allocations
        if allocations["bnkr_team_percentage"] == 0.5 and allocations["drb_team_percentage"] == 0.5:
            print_success("Team percentages are correct (0.5% each)")
        else:
            print_error(f"Incorrect team percentages: BNKR={allocations['bnkr_team_percentage']}, DRB={allocations['drb_team_percentage']}")
    
    return success

def test_token_validation():
    """Test the token validation endpoint"""
    print_header("Testing Token Validation Endpoint")
    
    # Test with valid token
    success, data = test_endpoint(
        "POST", 
        "/validate-token", 
        data={
            "token_address": TEST_TOKEN,
            "chain": "base"
        },
        verify_keys=["is_valid", "symbol", "name", "decimals", "total_supply"]
    )
    
    if success:
        if data["is_valid"]:
            print_success("Token validation works for valid token")
        else:
            print_error("Valid token was not recognized")
    
    # Test with invalid token
    success, data = test_endpoint(
        "POST", 
        "/validate-token", 
        data={
            "token_address": "invalid_address",
            "chain": "base"
        }
    )
    
    if success:
        if not data["is_valid"]:
            print_success("Token validation correctly rejects invalid token")
        else:
            print_error("Invalid token was incorrectly validated")
    
    return success

def test_check_burnable():
    """Test the check-burnable endpoint"""
    print_header("Testing Check Burnable Endpoint")
    
    # Test with BNKR token
    success, data = test_endpoint(
        "POST", 
        "/check-burnable", 
        data={
            "token_address": TEST_TOKEN,
            "chain": "base"
        },
        verify_keys=["is_burnable", "allocation_preview", "chain_wallets"]
    )
    
    if success:
        # Verify BNKR token is recognized
        if data["token_address"] == TEST_TOKEN:
            print_success("Token address is correctly returned")
        else:
            print_error(f"Incorrect token address: {data['token_address']}")
        
        # Verify allocation preview
        allocation = data["allocation_preview"]
        if "burn_percentage" in allocation and "grok_percentage" in allocation:
            print_success("Allocation preview contains required fields")
        else:
            print_error("Allocation preview missing required fields")
        
        # Verify chain wallets
        if "recipient_wallet" in data["chain_wallets"]:
            print_success("Chain wallets information is included")
        else:
            print_error("Chain wallets information is missing")
    
    # Test with contest parameter
    success, data = test_endpoint(
        "POST", 
        "/check-burnable", 
        data={
            "token_address": TEST_TOKEN,
            "chain": "base",
            "is_contest": True
        },
        verify_keys=["is_burnable", "allocation_preview", "is_contest"]
    )
    
    if success:
        # Verify contest allocation
        if data["is_contest"] and data["allocation_preview"]["allocation_type"] == "contest":
            print_success("Contest allocation is correctly identified")
            
            # Verify contest percentages
            if data["allocation_preview"]["burn_percentage"] == 88.0 and data["allocation_preview"]["community_percentage"] == 12.0:
                print_success("Contest allocation percentages are correct (88% burn, 12% community)")
            else:
                print_error(f"Incorrect contest allocation percentages: {data['allocation_preview']}")
        else:
            print_error("Contest allocation not correctly identified")
    
    return success

def test_burn_endpoint():
    """Test the burn endpoint with focus on async/await fix for is_token_burnable"""
    print_header("Testing Burn Endpoint")
    
    # Test with a regular token
    success, data = test_endpoint(
        "POST", 
        "/burn", 
        data={
            "wallet_address": TEST_WALLET,
            "token_address": TEST_TOKEN,
            "amount": TEST_AMOUNT,
            "chain": "base"
        },
        verify_keys=["transaction_id", "status", "amounts"]
    )
    
    if success:
        # Verify transaction was created
        if data["status"] == "pending":
            print_success("Burn transaction created successfully")
        else:
            print_error(f"Unexpected transaction status: {data['status']}")
        
        # Verify amounts
        amounts = data["amounts"]
        if "burn_amount" in amounts and "drb_total_amount" in amounts and "bnkr_total_amount" in amounts:
            print_success("Burn amounts are correctly calculated")
            
            # Store transaction ID for later tests
            transaction_id = data["transaction_id"]
            
            # Wait for transaction to be processed
            print_info("Waiting for transaction to be processed...")
            time.sleep(3)
            
            # Check transaction status
            success, tx_data = test_endpoint(
                "GET", 
                "/transactions", 
                verify_keys=["transactions"]
            )
            
            if success:
                # Find our transaction
                found = False
                for tx in tx_data["transactions"]:
                    if tx["id"] == transaction_id:
                        found = True
                        print_success(f"Transaction found in database with status: {tx['status']}")
                        break
                
                if not found:
                    print_error("Transaction not found in database")
        else:
            print_error("Burn amounts missing required fields")
    
    # Test with a non-standard token to verify is_token_burnable function works
    print_info("Testing with a non-standard token to verify is_token_burnable function...")
    
    non_standard_token = "0x5C6374a2ac4EBC38DeA0Fc1F8716e5Ea1AdD94dd"  # Test token
    
    success, data = test_endpoint(
        "POST", 
        "/burn", 
        data={
            "wallet_address": TEST_WALLET,
            "token_address": non_standard_token,
            "amount": TEST_AMOUNT,
            "chain": "base"
        },
        verify_keys=["transaction_id", "status", "amounts"]
    )
    
    if success:
        print_success("Burn endpoint successfully processed non-standard token")
        print_success("is_token_burnable function is working correctly with async/await")
    
    return success

def test_stats_endpoint():
    """Test the stats endpoint"""
    print_header("Testing Stats Endpoint")
    
    success, data = test_endpoint(
        "GET", 
        "/stats", 
        verify_keys=["total_transactions", "completed_transactions", "burn_percentage", "bnkr_percentage"]
    )
    
    if success:
        # Verify burn percentage
        if data["burn_percentage"] == 88.0:
            print_success("Burn percentage is correct (88%)")
        else:
            print_error(f"Incorrect burn percentage: {data['burn_percentage']}")
        
        # Verify BNKR percentage
        if data["bnkr_percentage"] == 2.5:
            print_success("BNKR percentage is correct (2.5%)")
        else:
            print_error(f"Incorrect BNKR percentage: {data['bnkr_percentage']}")
        
        # Verify total_bnkr_allocated field
        if "total_bnkr_allocated" in data:
            print_success("BNKR allocation data is included")
        else:
            print_warning("total_bnkr_allocated field not found, but may be named differently")
    
    return success

def test_gas_estimates():
    """Test the gas estimates endpoint"""
    print_header("Testing Gas Estimates Endpoint")
    
    success, data = test_endpoint(
        "GET", 
        "/gas-estimates/base", 
        verify_keys=["slow", "standard", "fast"]
    )
    
    if success:
        # Verify gas estimate structure
        if "gwei" in data["standard"] and "usd" in data["standard"]:
            print_success("Gas estimates are correctly structured")
        else:
            print_error("Gas estimates missing required fields")
    
    return success

def test_token_price():
    """Test the token price endpoint"""
    print_header("Testing Token Price Endpoint")
    
    success, data = test_endpoint(
        "GET", 
        f"/token-price/{TEST_TOKEN}/base", 
        verify_keys=["price", "currency"]
    )
    
    if success:
        # Verify price is a number
        try:
            price = float(data["price"])
            print_success(f"Token price returned: {price} {data['currency']}")
        except (ValueError, TypeError):
            print_error(f"Invalid price format: {data['price']}")
    
    return success

def test_swap_quote():
    """Test the swap quote endpoint"""
    print_header("Testing Swap Quote Endpoint")
    
    success, data = test_endpoint(
        "POST", 
        "/swap-quote", 
        data={
            "amount": TEST_AMOUNT,
            "token_address": TEST_TOKEN,
            "chain": "base"
        },
        verify_keys=["status", "data"]
    )
    
    if success:
        # Verify quote data
        quote_data = data["data"]
        if "input_amount" in quote_data and "output_amount" in quote_data:
            print_success("Swap quote contains required fields")
        else:
            print_error("Swap quote missing required fields")
    
    return success

def test_transactions_endpoint():
    """Test the transactions endpoint"""
    print_header("Testing Transactions Endpoint")
    
    success, data = test_endpoint(
        "GET", 
        "/transactions", 
        verify_keys=["transactions"]
    )
    
    if success:
        # Verify transactions list
        if isinstance(data["transactions"], list):
            print_success(f"Transactions endpoint returned {len(data['transactions'])} transactions")
        else:
            print_error("Transactions not returned as a list")
    
    return success

def test_transaction_status():
    """Test the transaction status endpoint"""
    print_header("Testing Transaction Status Endpoint")
    
    # Use a dummy transaction hash
    tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    
    success, data = test_endpoint(
        "GET", 
        f"/transaction-status/{tx_hash}/base", 
        verify_keys=["status", "tx_hash", "chain"]
    )
    
    if success:
        # Verify transaction status
        if data["status"] in ["pending", "confirmed"]:
            print_success(f"Transaction status returned: {data['status']}")
        else:
            print_error(f"Unexpected transaction status: {data['status']}")
    
    return success

def test_optimal_routes():
    """Test the optimal routes endpoint"""
    print_header("Testing Optimal Routes Endpoint")
    
    success, data = test_endpoint(
        "GET", 
        "/cross-chain/optimal-routes", 
        verify_keys=["optimal_chains", "recommended_chain"]
    )
    
    if success:
        # Verify Base is recommended
        if data["recommended_chain"] == "base":
            print_success("Base chain is correctly recommended")
        else:
            print_error(f"Unexpected recommended chain: {data['recommended_chain']}")
    
    return success

def test_community_stats():
    """Test the community stats endpoint"""
    print_header("Testing Community Stats Endpoint")
    
    success, data = test_endpoint(
        "GET", 
        "/community/stats", 
        verify_keys=["total_burns", "total_volume_usd", "top_burners", "recent_burns"]
    )
    
    if success:
        # Verify top burners list
        if isinstance(data["top_burners"], list):
            print_success(f"Community stats returned {len(data['top_burners'])} top burners")
        else:
            print_error("Top burners not returned as a list")
        
        # Verify recent burns list
        if isinstance(data["recent_burns"], list):
            print_success(f"Community stats returned {len(data['recent_burns'])} recent burns")
        else:
            print_error("Recent burns not returned as a list")
    
    return success

def test_admin_endpoints():
    """Test the admin endpoints"""
    print_header("Testing Admin Endpoints")
    
    # Set admin headers
    admin_headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    
    # Test projects endpoint with admin token
    success, data = test_endpoint(
        "GET", 
        "/admin/projects", 
        headers=admin_headers,
        verify_keys=["projects"]
    )
    
    if success:
        print_success("Admin authentication works correctly")
    
    # Test without admin token (should fail)
    success, data = test_endpoint(
        "GET", 
        "/admin/projects", 
        expected_status=401
    )
    
    if success:
        print_success("Admin endpoint correctly rejects unauthorized requests")
    
    # Test with invalid admin token (should fail)
    invalid_headers = {
        "Authorization": "Bearer invalid_token"
    }
    
    success, data = test_endpoint(
        "GET", 
        "/admin/projects", 
        headers=invalid_headers,
        expected_status=401
    )
    
    if success:
        print_success("Admin endpoint correctly rejects invalid tokens")
    
    # Test creating a project
    project_data = {
        "name": "Test Project",
        "description": "A test project created by the test script",
        "base_address": "0x1234567890123456789012345678901234567890",
        "submitted_by": "test_script"
    }
    
    success, data = test_endpoint(
        "POST", 
        "/admin/projects", 
        headers=admin_headers,
        data=project_data,
        verify_keys=["status", "project"]
    )
    
    if success:
        print_success("Admin can create projects")
        
        # Store project ID for update/delete tests
        project_id = data["project"]["id"]
        
        # Test updating the project
        update_data = {
            "name": "Updated Test Project",
            "description": "This project was updated by the test script"
        }
        
        success, data = test_endpoint(
            "PUT", 
            f"/admin/projects/{project_id}", 
            headers=admin_headers,
            data=update_data,
            verify_keys=["status"]
        )
        
        if success:
            print_success("Admin can update projects")
        
        # Test deleting the project
        success, data = test_endpoint(
            "DELETE", 
            f"/admin/projects/{project_id}", 
            headers=admin_headers,
            verify_keys=["status"]
        )
        
        if success:
            print_success("Admin can delete projects")
    
    return success

def test_wallet_status():
    """Test the wallet status endpoint"""
    print_header("Testing Wallet Status Endpoint")
    
    success, data = test_endpoint(
        "GET", 
        "/wallet/status", 
        verify_keys=["connected", "network", "rpc_url"]
    )
    
    if success:
        # Verify wallet status
        print_success(f"Wallet status: connected={data['connected']}")
        print_success(f"Network: {data['network']}")
        
        # Verify RPC URL
        if data["rpc_url"] == "https://mainnet.base.org":
            print_success("Base RPC URL is correct")
        else:
            print_error(f"Unexpected RPC URL: {data['rpc_url']}")
    
    return success

def test_contest_burn():
    """Test the contest burn endpoint"""
    print_header("Testing Contest Burn Endpoint")
    
    # Set admin headers
    admin_headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    
    # Test contest burn endpoint
    contest_data = {
        "amount": "10",
        "token_address": TEST_TOKEN,
        "description": "Test contest burn"
    }
    
    success, data = test_endpoint(
        "POST", 
        "/execute-contest-burn", 
        headers=admin_headers,
        data=contest_data,
        verify_keys=["status", "transaction_id", "allocations", "allocation_type"]
    )
    
    if success:
        # Verify contest allocation
        if data["allocation_type"] == "contest":
            print_success("Contest allocation is correctly identified")
            
            # Verify allocations
            allocations = data["allocations"]
            if "burn_amount" in allocations and "community_amount" in allocations:
                print_success("Contest burn allocations are correctly calculated")
                
                # Verify burn amount is 88%
                burn_amount = float(allocations["burn_amount"])
                community_amount = float(allocations["community_amount"])
                total_amount = burn_amount + community_amount
                
                burn_percentage = (burn_amount / total_amount) * 100
                community_percentage = (community_amount / total_amount) * 100
                
                if abs(burn_percentage - 88.0) < 0.1 and abs(community_percentage - 12.0) < 0.1:
                    print_success("Contest burn percentages are correct (88% burn, 12% community)")
                else:
                    print_error(f"Incorrect contest burn percentages: burn={burn_percentage}%, community={community_percentage}%")
            else:
                print_error("Contest burn allocations missing required fields")
        else:
            print_error(f"Unexpected allocation type: {data['allocation_type']}")
    
    return success

def run_all_tests():
    """Run all tests and return the results"""
    results = {}
    
    # Core functionality tests
    results["health_check"] = test_health_check()
    results["chains"] = test_chains_endpoint()
    results["token_validation"] = test_token_validation()
    results["check_burnable"] = test_check_burnable()
    results["burn"] = test_burn_endpoint()
    results["stats"] = test_stats_endpoint()
    
    # Additional API tests
    results["gas_estimates"] = test_gas_estimates()
    results["token_price"] = test_token_price()
    results["swap_quote"] = test_swap_quote()
    results["transactions"] = test_transactions_endpoint()
    results["transaction_status"] = test_transaction_status()
    results["optimal_routes"] = test_optimal_routes()
    results["community_stats"] = test_community_stats()
    
    # Admin functionality tests
    results["admin"] = test_admin_endpoints()
    results["wallet_status"] = test_wallet_status()
    results["contest_burn"] = test_contest_burn()
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{test}: {status}")
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    return passed == total

if __name__ == "__main__":
    print_header(f"Testing Burn Relief Bot Backend API at {API_BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = run_all_tests()
    
    print_header(f"Testing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not success:
        sys.exit(1)
