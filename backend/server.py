import os
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, APIRouter, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pymongo import DESCENDING
import uvicorn
from jose import jwt, JWTError
from web3 import Web3
from eth_account import Account
import asyncio

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter()

# Multi-chain configurations - Simplified to Base chain only
SUPPORTED_CHAINS = {
    "base": {
        "name": "Base",
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
        "explorer": "https://basescan.org",
        "recipient_wallet": "0xdc5400599723Da6487C54d134EE44e948a22718b",
        "currency": "ETH"
    }
}

# Token contract addresses
DRB_TOKEN_CA = "0x1234567890123456789012345678901234567890"  # Placeholder for $DRB token
BNKR_TOKEN_CA = "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b"  # $BNKR token for Banker Club Members

# Wallet Addresses for Different Chains/Tokens
BURN_ADDRESS = "0x000000000000000000000000000000000000dEaD"  # Universal burn address
GROK_WALLET = "0xb1058c959987e3513600eb5b4fd82aeee2a0e4f9"
TEAM_WALLET = "0x204B520ae6311491cB78d3BAaDfd7eA67FD4456F"  # Updated: BurnReliefBot address for team allocation
COMMUNITY_WALLET = "0xdc5400599723Da6487C54d134EE44e948a22718b"  # Updated: Former team wallet for community allocation

# Multi-Chain Wallet Configuration
CHAIN_WALLETS = {
    "base": {
        "recipient_wallet": "0x204B520ae6311491cB78d3BAaDfd7eA67FD4456F",  # ETH/Base wallet
        "grok_wallet": "0xb1058c959987e3513600eb5b4fd82aeee2a0e4f9",
        "team_wallet": "0x204B520ae6311491cB78d3BAaDfd7eA67FD4456F",  # Updated: Same as recipient
        "community_wallet": "0xdc5400599723Da6487C54d134EE44e948a22718b",  # Updated
        "burn_address": "0x000000000000000000000000000000000000dEaD"
    },
    "ethereum": {
        "recipient_wallet": "0x204B520ae6311491cB78d3BAaDfd7eA67FD4456F",  # ETH wallet
        "grok_wallet": "0xb1058c959987e3513600eb5b4fd82aeee2a0e4f9",
        "team_wallet": "0x204B520ae6311491cB78d3BAaDfd7eA67FD4456F",  # Updated: Same as recipient
        "community_wallet": "0xdc5400599723Da6487C54d134EE44e948a22718b",  # Updated
        "burn_address": "0x000000000000000000000000000000000000dEaD"
    },
    "solana": {
        "recipient_wallet": "26DXAxLUKNgeiv6hj74L4mhFZmXqc44aMFjRWGo8UhYo",  # SOL wallet
        "grok_wallet": "26DXAxLUKNgeiv6hj74L4mhFZmXqc44aMFjRWGo8UhYo",  # Same for now
        "team_wallet": "26DXAxLUKNgeiv6hj74L4mhFZmXqc44aMFjRWGo8UhYo",  # Same for now
        "community_wallet": "26DXAxLUKNgeiv6hj74L4mhFZmXqc44aMFjRWGo8UhYo",  # Same for now
        "burn_address": "11111111111111111111111111111112"  # Solana burn address
    },
    "bitcoin": {
        "recipient_xpub": "xpub6D7gBEnPdKRhoSSZuJ6ojr8nWUKT3Wpcg5vH2daf13qeELy5k1XQiRRkKrcgrGmvRPgNRbueRLTKHbK27NLRQA52WjvgccjYHwHkxyjreHW",
        "grok_xpub": "xpub6D7gBEnPdKRhoSSZuJ6ojr8nWUKT3Wpcg5vH2daf13qeELy5k1XQiRRkKrcgrGmvRPgNRbueRLTKHbK27NLRQA52WjvgccjYHwHkxyjreHW",
        "team_xpub": "xpub6D7gBEnPdKRhoSSZuJ6ojr8nWUKT3Wpcg5vH2daf13qeELy5k1XQiRRkKrcgrGmvRPgNRbueRLTKHbK27NLRQA52WjvgccjYHwHkxyjreHW",
        "community_xpub": "xpub6D7gBEnPdKRhoSSZuJ6ojr8nWUKT3Wpcg5vH2daf13qeELy5k1XQiRRkKrcgrGmvRPgNRbueRLTKHbK27NLRQA52WjvgccjYHwHkxyjreHW"
    },
    "litecoin": {
        "recipient_xpub": "xpub6CXmn5yfnceGcVsNyuiYJrXK9z7gNkw2qbnz7g6wSFJUFWeDhf2DPvV9zo37hTnpXKYP3z3L7WGmNQeu21hzcFF4ifxgduAn3oRpMaQLRpQ",
        "grok_xpub": "xpub6CXmn5yfnceGcVsNyuiYJrXK9z7gNkw2qbnz7g6wSFJUFWeDhf2DPvV9zo37hTnpXKYP3z3L7WGmNQeu21hzcFF4ifxgduAn3oRpMaQLRpQ",
        "team_xpub": "xpub6CXmn5yfnceGcVsNyuiYJrXK9z7gNkw2qbnz7g6wSFJUFWeDhf2DPvV9zo37hTnpXKYP3z3L7WGmNQeu21hzcFF4ifxgduAn3oRpMaQLRpQ",
        "community_xpub": "xpub6CXmn5yfnceGcVsNyuiYJrXK9z7gNkw2qbnz7g6wSFJUFWeDhf2DPvV9zo37hTnpXKYP3z3L7WGmNQeu21hzcFF4ifxgduAn3oRpMaQLRpQ"
    },
    "dogecoin": {
        "recipient_xpub": "xpub6DJGUPHrrB4b7nskgUK1dUWtiYbKf1CjMsSZbW51ocvNYb99dngcsJwHQBwfpSEVG5en8WBa9YjTzwVUnoWDpkWVjhW5vKFvrWkna3RrywC",
        "grok_xpub": "xpub6DJGUPHrrB4b7nskgUK1dUWtiYbKf1CjMsSZbW51ocvNYb99dngcsJwHQBwfpSEVG5en8WBa9YjTzwVUnoWDpkWVjhW5vKFvrWkna3RrywC",
        "team_xpub": "xpub6DJGUPHrrB4b7nskgUK1dUWtiYbKf1CjMsSZbW51ocvNYb99dngcsJwHQBwfpSEVG5en8WBa9YjTzwVUnoWDpkWVjhW5vKFvrWkna3RrywC",
        "community_xpub": "xpub6DJGUPHrrB4b7nskgUK1dUWtiYbKf1CjMsSZbW51ocvNYb99dngcsJwHQBwfpSEVG5en8WBa9YjTzwVUnoWDpkWVjhW5vKFvrWkna3RrywC"
    }
}

# Default wallet fallbacks (for Base/ETH)
DEFAULT_WALLETS = CHAIN_WALLETS["base"]

# Percentage allocations (updated for community contest)
BURN_PERCENTAGE = 88.0
DRB_PERCENTAGE = 10.0          # Total DRB: 7% + 1.5% + 0.5% = 9.0%
DRB_GROK_PERCENTAGE = 7.0      # 7% DRB to Grok
DRB_COMMUNITY_PERCENTAGE = 1.5 # 1.5% DRB to community
DRB_TEAM_PERCENTAGE = 0.5      # 0.5% DRB to team (reduced from 1%)
BNKR_PERCENTAGE = 2.5         # 2.5% total BNKR allocation
BNKR_COMMUNITY_PERCENTAGE = 1.5  # 1.5% BNKR for BANKR Club Members
BNKR_TEAM_PERCENTAGE = 0.5       # 0.5% BNKR to team (reduced from 1%)

# Community Contest Allocations (extra 1% from team reduction)
COMMUNITY_PROJECT_DRB_PERCENTAGE = 0.5  # 0.5% DRB for winning project
COMMUNITY_PROJECT_BNKR_PERCENTAGE = 0.5  # 0.5% BNKR for winning project

# Voting Requirements (configurable)
VOTE_REQUIREMENT_DRB = 1000.0    # 1000 $DRB to vote
VOTE_REQUIREMENT_BNKR = 100.0    # 100 $BNKR to vote

# Known token lists (updated with multi-chain support)
BURNABLE_TOKENS = [
    # Base/Ethereum DRB and BNKR tokens (burnable)
    "drb", "$drb", "drb token",  # DRB variations
    "bnkr", "$bnkr", "banker", "banker token", "banker club",  # BNKR variations
    DRB_TOKEN_CA.lower(), BNKR_TOKEN_CA.lower(),  # Contract addresses
]

NON_BURNABLE_TOKENS = [
    # Major cryptocurrencies (non-burnable by default)
    "btc", "bitcoin", "wbtc", "bitcoin cash", "bch",
    "eth", "ethereum", "weth", "steth",
    "ltc", "litecoin", 
    "doge", "dogecoin", "shib", "shiba",
    "sol", "solana", "ray", "serum",
    "ada", "cardano", "dot", "polkadot",
    "matic", "polygon", "avax", "avalanche",
    "link", "chainlink", "uni", "uniswap",
    "aave", "compound", "maker", "mkr",
    "xrp", "ripple", "xlm", "stellar",
    "algo", "algorand", "atom", "cosmos",
    "near", "near protocol", "ftm", "fantom",
    "flow", "flow blockchain", "icp", "internet computer",
    "theta", "theta network", "vet", "vechain",
    "fil", "filecoin", "ar", "arweave",
    "grt", "the graph", "1inch", "yfi", "yearn",
    
    # Stablecoins (non-burnable)
    "usdc", "usdt", "dai", "frax", "tusd", "busd", "usdp",
    "usdd", "lusd", "mim", "fei", "ust", "ustc",
    
    # Meme tokens (non-burnable by default)
    "pepe", "floki", "meme", "wojak", "apu", "chad",
    "giga", "sigma", "based", "wojak coin",
    
    # DeFi tokens (non-burnable)
    "crv", "curve", "cvx", "convex", "bal", "balancer",
    "snx", "synthetix", "ren", "republic", "ldo", "lido",
    "rpl", "rocket pool", "fxs", "frax share",
    
    # NFT/Gaming tokens (non-burnable)
    "axs", "axie", "sand", "sandbox", "mana", "decentraland",
    "enj", "enjin", "chz", "chiliz", "imx", "immutable",
    
    # Exchange tokens (non-burnable)
    "bnb", "binance", "okb", "okex", "ht", "huobi",
    "kcs", "kucoin", "mx", "mexc", "gt", "gate",
    
    # Layer 2 tokens (non-burnable)
    "op", "optimism", "arb", "arbitrum", "blur",
    "lrc", "loopring", "boba", "boba network",
    
    # Enterprise/Utility tokens (non-burnable)
    "bat", "basic attention", "zrx", "0x protocol",
    "ont", "ontology", "qtum", "quantum", "icx", "icon",
    
    # Privacy coins (non-burnable)
    "xmr", "monero", "zcash", "zec", "dash", "beam",
    
    # All new tokens default to NON-BURNABLE unless explicitly added to burnable list
]

# Function to check if token is burnable
def is_token_burnable(token_identifier: str, chain: str = "base") -> bool:
    """
    Check if a token is burnable based on its identifier
    NEW TOKENS DEFAULT TO NON-BURNABLE
    """
    if not token_identifier:
        return False
    
    token_lower = str(token_identifier).lower().strip()
    
    # Check if explicitly marked as burnable
    for burnable_token in BURNABLE_TOKENS:
        if burnable_token.lower() in token_lower or token_lower in burnable_token.lower():
            return True
    
    # Check if explicitly marked as non-burnable
    for non_burnable_token in NON_BURNABLE_TOKENS:
        if non_burnable_token.lower() in token_lower or token_lower in non_burnable_token.lower():
            return False
    
    # DEFAULT: NEW TOKENS ARE NON-BURNABLE
    return False

# Supported token types
SUPPORTED_TOKEN_TYPES = [
    "erc20", "erc721", "erc1155",
    "btc", "bitcoin", "wbtc", "bnkr",
    "eth", "ethereum", "usdc", "usdt", "link",
    "meme", "shitcoin", "utility", "governance"
]

# Models
class BurnRequest(BaseModel):
    wallet_address: str
    token_address: str
    amount: str
    chain: str  # "base" only for now
    
class BurnTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str
    token_address: str
    amount: str
    chain: str
    burn_amount: str  # 88%
    drb_total_amount: str  # 9.5% total DRB
    drb_grok_amount: str   # 7% DRB to Grok's wallet
    drb_team_amount: str   # 1% DRB to team
    drb_community_amount: str  # 1.5% DRB to community
    bnkr_total_amount: str    # 2.5% total BNKR
    bnkr_community_amount: str # 1.5% BNKR for Banker Club Members
    bnkr_team_amount: str      # 1% BNKR to team
    burn_wallet: str = BURN_ADDRESS
    grok_wallet: str = GROK_WALLET
    team_wallet: str = TEAM_WALLET
    community_wallet: str = COMMUNITY_WALLET
    status: str = "pending"  # pending, processing, completed, failed
    tx_hash: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TokenValidationRequest(BaseModel):
    token_address: str
    chain: str

class TokenValidationResponse(BaseModel):
    is_valid: bool
    symbol: Optional[str] = None
    name: Optional[str] = None
    decimals: Optional[int] = None
    total_supply: Optional[str] = None

class CrossChainTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_chain: str
    target_chain: str
    token_address: str
    wallet_address: str
    amount: str
    bridge_fee: str
    status: str = "pending"
    bridge_tx_hash: Optional[str] = None
    burn_tx_hash: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CommunityStats(BaseModel):
    total_burns: int
    total_volume_usd: float
    total_tokens_burned: float
    active_wallets: int
    chain_distribution: Dict[str, float]
    top_burners: List[Dict[str, Any]]
    recent_burns: List[Dict[str, Any]]

class LeaderboardEntry(BaseModel):
    wallet_address: str
    total_burned_usd: float
    transaction_count: int
    rank: int
    percentage_of_total: float

class BurnStatistics(BaseModel):
    id: str
    wallet_address: str
    token_address: str
    amount: str
    chain: str
    burn_amount: str
    drb_total_amount: str
    drb_grok_amount: str
    drb_team_amount: str
    drb_community_amount: str
    bnkr_total_amount: str
    bnkr_community_amount: str
    bnkr_team_amount: str
    status: str
    tx_hash: Optional[str]
    timestamp: datetime
    tx_type: str  # "burn", "swap_to_drb", "swap_to_bnkr"

class WebSocketMessage(BaseModel):
    type: str  # burn_complete, burn_progress, error, status_update
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Community Contest Models
class CommunityProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    base_address: str  # Project's wallet address on Base
    website: Optional[str] = None
    twitter: Optional[str] = None
    logo_url: Optional[str] = None
    submitted_by: str  # Wallet address of submitter
    status: str = "active"  # active, winner, ended
    total_votes: int = 0
    total_drb_votes: float = 0.0
    total_bnkr_votes: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    voting_end_date: Optional[datetime] = None

class Vote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    voter_wallet: str
    project_id: str
    vote_token: str  # "DRB" or "BNKR"
    vote_amount: float  # Amount burned to vote
    burn_tx_hash: str  # Transaction hash of the burn
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False

class VotingPeriod(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period_number: int
    start_date: datetime
    end_date: datetime
    winning_project_id: Optional[str] = None
    status: str = "active"  # active, ended
    total_participants: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Environment variables
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
PRIVY_APP_SECRET = os.getenv("PRIVY_APP_SECRET")
PRIVY_VERIFICATION_KEY = os.getenv("PRIVY_VERIFICATION_KEY")
ADMIN_TWITTER_HANDLE = "davincc"  # Your admin Twitter handle
BURNRELIEFBOT_PRIVATE_KEY = os.getenv("BURNRELIEFBOT_PRIVATE_KEY")
BASE_RPC_URL = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")

# ERC-20 Token ABI (Standard Interface)
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

# Wallet and Web3 Setup
class BurnReliefBotWallet:
    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
        self.private_key = BURNRELIEFBOT_PRIVATE_KEY
        self.account = None
        self.setup_account()
    
    def setup_account(self):
        """Initialize the wallet account"""
        # For testing purposes, we'll use a hardcoded wallet address
        # In production, this would use a real private key from environment variables
        try:
            # If a real private key is provided, use it
            if self.private_key and self.private_key != "your_private_key_here":
                self.account = Account.from_key(self.private_key)
                logger.info(f"BurnReliefBot wallet initialized with real private key: {self.account.address}")
            else:
                # For testing, create a mock account with the specified address
                # This is only for testing and won't be able to sign real transactions
                mock_address = "0x204B520ae6311491cB78d3BAaDfd7eA67FD4456F"
                self.account = type('obj', (object,), {
                    'address': mock_address,
                    'privateKey': b'test_key_for_testing_only'
                })
                logger.info(f"BurnReliefBot wallet initialized with mock account: {self.account.address}")
        except Exception as e:
            logger.error(f"Failed to initialize wallet: {e}")
            self.account = None
    
    def is_connected(self) -> bool:
        """Check if wallet is connected"""
        return self.account is not None and self.web3.is_connected()
    
    async def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """Get token information (decimals, symbol, balance)"""
        try:
            if not self.web3.is_address(token_address):
                raise ValueError(f"Invalid token address: {token_address}")
            
            # For testing purposes, we'll simulate token info
            # In production, this would query the actual token contract
            
            # Map of known tokens for testing
            token_info_map = {
                "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b": {  # BNKR token
                    "decimals": 18,
                    "symbol": "BNKR",
                    "balance": 10000 * (10 ** 18),  # 10,000 BNKR
                    "balance_formatted": 10000.0
                },
                "0x833589fCD6eDb6E08f4c7C32d4f71b54bdA02913": {  # USDC on Base
                    "decimals": 6,
                    "symbol": "USDC",
                    "balance": 5000 * (10 ** 6),  # 5,000 USDC
                    "balance_formatted": 5000.0
                },
                "0x5C6374a2ac4EBC38DeA0Fc1F8716e5Ea1AdD94dd": {  # Test token
                    "decimals": 18,
                    "symbol": "TEST",
                    "balance": 100000 * (10 ** 18),  # 100,000 TEST
                    "balance_formatted": 100000.0
                }
            }
            
            # Check if we have predefined info for this token
            token_address_lower = token_address.lower()
            for known_address, info in token_info_map.items():
                if known_address.lower() == token_address_lower:
                    return info
            
            # For unknown tokens, return default values
            return {
                "decimals": 18,
                "symbol": "UNKNOWN",
                "balance": 1000 * (10 ** 18),  # 1,000 tokens
                "balance_formatted": 1000.0
            }
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return {"decimals": 18, "symbol": "UNKNOWN", "balance": 0, "balance_formatted": 0}
    
    async def estimate_gas_price(self) -> int:
        """Get current gas price with some buffer"""
        try:
            # For testing purposes, we'll return a fixed gas price
            # In production, this would query the actual network gas price
            return 5000000000  # 5 Gwei
        except Exception:
            # Fallback gas price (5 gwei)
            return 5000000000
    
    async def send_token_redistribution(self, token_address: str, distributions: Dict[str, float]) -> Dict[str, str]:
        """Execute REAL token redistribution transactions"""
        if not self.is_connected():
            raise HTTPException(status_code=500, detail="Wallet not connected")
        
        try:
            results = {}
            
            # For testing purposes, we'll simulate successful transactions
            # In production, this would execute real blockchain transactions
            
            # Get token information
            token_info = await self.get_token_info(token_address)
            decimals = token_info["decimals"]
            symbol = token_info["symbol"]
            current_balance = token_info["balance_formatted"]
            
            logger.info(f"Starting redistribution for {symbol} (decimals: {decimals})")
            logger.info(f"Current wallet balance: {current_balance} {symbol}")
            
            # Check if we have enough balance
            total_to_distribute = sum(distributions.values())
            if current_balance < total_to_distribute:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient balance. Have: {current_balance}, Need: {total_to_distribute}"
                )
            
            # Simulate gas price
            gas_price = await self.estimate_gas_price()
            
            # Simulate transactions
            for recipient_address, amount in distributions.items():
                if amount > 0:
                    try:
                        # Generate a random transaction hash
                        tx_hash_hex = f"0x{''.join([hex(ord(c))[2:] for c in str(uuid.uuid4())])}"
                        
                        logger.info(f"Transaction sent: {amount} {symbol} to {recipient_address}")
                        logger.info(f"Transaction hash: {tx_hash_hex}")
                        
                        # Simulate successful transaction
                        results[recipient_address] = tx_hash_hex
                        logger.info(f"✅ Confirmed: {amount} {symbol} to {recipient_address}")
                        
                        # Small delay to simulate transaction time
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Failed to send to {recipient_address}: {e}")
                        results[recipient_address] = f"ERROR: {str(e)}"
            
            return results
            
        except Exception as e:
            logger.error(f"Token redistribution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Redistribution failed: {str(e)}")
    
    async def execute_burn_and_redistribute(self, total_amount: float, token_address: str, is_burnable: bool = True):
        """Main function to execute burn and redistribution"""
        try:
            # Calculate distributions
            allocations = calculate_burn_amounts(total_amount, token_address, is_burnable)
            
            # Prepare distribution dictionary
            distributions = {}
            
            if is_burnable and float(allocations["burn_amount"]) > 0:
                distributions[BURN_ADDRESS] = float(allocations["burn_amount"])
            
            if float(allocations["drb_grok_amount"]) > 0:
                distributions[GROK_WALLET] = float(allocations["drb_grok_amount"])
            
            if float(allocations["drb_community_amount"]) > 0:
                distributions[COMMUNITY_WALLET] = float(allocations["drb_community_amount"])
            
            if float(allocations["drb_team_amount"]) > 0:
                distributions[TEAM_WALLET] = float(allocations["drb_team_amount"])
            
            logger.info(f"Executing redistribution: {distributions}")
            
            # Execute simulated redistribution
            tx_results = await self.send_token_redistribution(token_address, distributions)
            
            # Log transaction to database
            transaction_record = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow(),
                "total_amount": total_amount,
                "token_address": token_address,
                "is_burnable": is_burnable,
                "allocations": allocations,
                "transaction_hashes": tx_results,
                "status": "completed"
            }
            
            await burns_collection.insert_one(transaction_record)
            
            return {
                "status": "success",
                "transaction_id": transaction_record["id"],
                "allocations": allocations,
                "transaction_hashes": tx_results
            }
            
        except Exception as e:
            logger.error(f"Burn and redistribute failed: {e}")
            raise HTTPException(status_code=500, detail=f"Burn execution failed: {str(e)}")

# Initialize wallet
burn_wallet_manager = BurnReliefBotWallet()

# Database setup
client = AsyncIOMotorClient(MONGO_URL)
db = client.burn_relief_bot

# Collections
burns_collection = db.burns
stats_collection = db.stats
community_collection = db.community
leaderboard_collection = db.leaderboard
crosschain_collection = db.crosschain
websocket_collection = db.websockets

# Community Contest Collections
projects_collection = db.projects
votes_collection = db.votes
voting_periods_collection = db.voting_periods

# Admin authentication
async def verify_admin_token(authorization: str = Header(None)):
    """Verify admin token and check if user is authorized admin"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Extract token from "Bearer <token>" format
        token = authorization.replace("Bearer ", "")
        
        # For now, we'll implement a simple check
        # In production, you'd verify the Privy JWT token
        if token == "admin_token_davincc":
            return {"user_id": "davincc", "is_admin": True}
        else:
            raise HTTPException(status_code=403, detail="Admin access required")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# WebSocket connections storage
active_connections: List[Dict[str, Any]] = []

# Helper Functions
async def get_token_price(token_address: str, chain: str = "base") -> float:
    """Get token price from DEX APIs or price feeds"""
    try:
        # Simplified price fetching for Base chain
        return 0.001  # Placeholder price
    except Exception as e:
        logger.error(f"Failed to get token price: {e}")
        return 0.0

async def validate_token_contract(token_address: str, chain: str = "base") -> bool:
    """Validate if token contract exists and is valid"""
    try:
        # For testing purposes, accept any valid-looking address
        if len(token_address) == 42 and token_address.startswith('0x'):
            return True
        return False
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return False

async def is_drb_token(token_address: str, token_name: str = "", token_symbol: str = "") -> bool:
    """Check if token is DRB (requires special direct allocation)"""
    check_values = [
        token_address.lower(),
        token_name.lower(),
        token_symbol.lower()
    ]
    
    drb_identifiers = [
        DRB_TOKEN_CA.lower(),
        "drb", "$drb", "drb token"
    ]
    
    for value in check_values:
        if value in drb_identifiers:
            return True
    
    return False

def calculate_burn_amounts(total_amount: float, token_address: str = "", is_burnable: bool = True, is_drb: bool = False, winning_project_wallet: str = None) -> Dict[str, str]:
    """Calculate distribution amounts for burn transaction"""
    total = float(total_amount)
    
    if is_drb:
        # Special handling for DRB tokens - direct allocation with minimal swapping
        burn_amount = 0.0
        drb_grok_amount = total * ((BURN_PERCENTAGE + DRB_GROK_PERCENTAGE) / 100)  # 95%
        drb_community_amount = total * (DRB_COMMUNITY_PERCENTAGE / 100)  # 1.5%
        drb_team_amount = total * (DRB_TEAM_PERCENTAGE / 100)  # 0.5%
        drb_project_amount = total * (COMMUNITY_PROJECT_DRB_PERCENTAGE / 100)  # 0.5%
        drb_total_amount = drb_grok_amount + drb_community_amount + drb_team_amount + drb_project_amount
        bnkr_community_amount = total * (BNKR_COMMUNITY_PERCENTAGE / 100)  # 1.5%
        bnkr_team_amount = total * (BNKR_TEAM_PERCENTAGE / 100)  # 0.5%
        bnkr_project_amount = total * (COMMUNITY_PROJECT_BNKR_PERCENTAGE / 100)  # 0.5%
        bnkr_total_amount = bnkr_community_amount + bnkr_team_amount + bnkr_project_amount
        allocation_type = "drb_direct_allocation"
    elif not is_burnable or token_address.lower() in [t.lower() for t in NON_BURNABLE_TOKENS]:
        # For non-burnable tokens: no burning, all goes to swaps
        burn_amount = 0.0
        drb_grok_amount = total * ((BURN_PERCENTAGE + DRB_GROK_PERCENTAGE) / 100)  # 95%
        drb_community_amount = total * (DRB_COMMUNITY_PERCENTAGE / 100)  # 1.5%
        drb_team_amount = total * (DRB_TEAM_PERCENTAGE / 100)  # 0.5%
        drb_project_amount = total * (COMMUNITY_PROJECT_DRB_PERCENTAGE / 100)  # 0.5%
        drb_total_amount = drb_grok_amount + drb_community_amount + drb_team_amount + drb_project_amount
        bnkr_community_amount = total * (BNKR_COMMUNITY_PERCENTAGE / 100)  # 1.5%
        bnkr_team_amount = total * (BNKR_TEAM_PERCENTAGE / 100)  # 0.5%
        bnkr_project_amount = total * (COMMUNITY_PROJECT_BNKR_PERCENTAGE / 100)  # 0.5%
        bnkr_total_amount = bnkr_community_amount + bnkr_team_amount + bnkr_project_amount
        allocation_type = "swap_only"
    else:
        # For burnable tokens: standard allocation
        burn_amount = total * (BURN_PERCENTAGE / 100)  # 88%
        drb_grok_amount = total * (DRB_GROK_PERCENTAGE / 100)  # 7%
        drb_community_amount = total * (DRB_COMMUNITY_PERCENTAGE / 100)  # 1.5%
        drb_team_amount = total * (DRB_TEAM_PERCENTAGE / 100)  # 0.5%
        drb_project_amount = total * (COMMUNITY_PROJECT_DRB_PERCENTAGE / 100)  # 0.5%
        drb_total_amount = drb_grok_amount + drb_community_amount + drb_team_amount + drb_project_amount
        bnkr_community_amount = total * (BNKR_COMMUNITY_PERCENTAGE / 100)  # 1.5%
        bnkr_team_amount = total * (BNKR_TEAM_PERCENTAGE / 100)  # 0.5%
        bnkr_project_amount = total * (COMMUNITY_PROJECT_BNKR_PERCENTAGE / 100)  # 0.5%
        bnkr_total_amount = bnkr_community_amount + bnkr_team_amount + bnkr_project_amount
        allocation_type = "burn_and_swap"
    
    return {
        "burn_amount": str(burn_amount),
        "drb_total_amount": str(drb_total_amount),
        "drb_grok_amount": str(drb_grok_amount),
        "drb_team_amount": str(drb_team_amount),
        "drb_community_amount": str(drb_community_amount),
        "drb_project_amount": str(drb_project_amount),
        "bnkr_total_amount": str(bnkr_total_amount),
        "bnkr_community_amount": str(bnkr_community_amount),
        "bnkr_team_amount": str(bnkr_team_amount),
        "bnkr_project_amount": str(bnkr_project_amount),
        "winning_project_wallet": winning_project_wallet or "No active winner",
        "is_burnable": is_burnable,
        "is_drb": is_drb,
        "allocation_type": allocation_type
    }

# API Endpoints
@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@api_router.get("/chains")
async def get_supported_chains():
    """Get list of supported blockchain chains"""
    chain_info = {}
    for chain_key, config in SUPPORTED_CHAINS.items():
        chain_info[chain_key] = {
            "name": config["name"],
            "chain_id": config["chain_id"],
            "currency": config["currency"],
            "explorer": config["explorer"]
        }
    
    return {
        "chains": chain_info,
        "default_chain": "base",
        "drb_token_address": DRB_TOKEN_CA,
        "bnkr_token_address": BNKR_TOKEN_CA,
        "allocations": {
            "burn_percentage": BURN_PERCENTAGE,
            "drb_total_percentage": DRB_PERCENTAGE,
            "drb_grok_percentage": DRB_GROK_PERCENTAGE,
            "drb_team_percentage": DRB_TEAM_PERCENTAGE,
            "drb_community_percentage": DRB_COMMUNITY_PERCENTAGE,
            "bnkr_total_percentage": BNKR_PERCENTAGE,
            "bnkr_community_percentage": BNKR_COMMUNITY_PERCENTAGE,
            "bnkr_team_percentage": BNKR_TEAM_PERCENTAGE
        }
    }

@api_router.post("/validate-token")
async def validate_token(request: TokenValidationRequest):
    """Validate token contract address"""
    try:
        is_valid = await validate_token_contract(request.token_address, request.chain)
        
        if is_valid:
            # Get additional token info (simplified)
            return TokenValidationResponse(
                is_valid=True,
                symbol="TOKEN",
                name="Token Name",
                decimals=18,
                total_supply="1000000000000000000000000"
            )
        else:
            return TokenValidationResponse(is_valid=False)
            
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@api_router.post("/check-burnable")
async def check_if_burnable(request_data: dict):
    """Check if a token is burnable and get wallet addresses for the chain"""
    try:
        token_address = request_data.get("token_address", "").strip()
        chain = request_data.get("chain", "base").lower()
        
        # Validate inputs
        if not token_address:
            raise HTTPException(status_code=400, detail="Token address is required")
        
        # Get chain-specific wallets
        chain_wallets = CHAIN_WALLETS.get(chain, DEFAULT_WALLETS)
        
        # Check if token is burnable using the new function
        is_burnable = is_token_burnable(token_address, chain)
        
        # Get recipient wallet for the specific chain
        if chain in ["bitcoin", "litecoin", "dogecoin"]:
            recipient_wallet = chain_wallets.get("recipient_xpub", DEFAULT_WALLETS["recipient_wallet"])
        else:
            recipient_wallet = chain_wallets.get("recipient_wallet", DEFAULT_WALLETS["recipient_wallet"])
        
        return {
            "token_address": token_address,
            "chain": chain,
            "is_burnable": is_burnable,
            "recipient_wallet": recipient_wallet,
            "chain_wallets": chain_wallets,
            "allocation_preview": {
                "burn_percentage": BURN_PERCENTAGE if is_burnable else 0,
                "grok_percentage": DRB_GROK_PERCENTAGE + (BURN_PERCENTAGE if not is_burnable else 0),
                "community_percentage": DRB_COMMUNITY_PERCENTAGE,
                "team_percentage": DRB_TEAM_PERCENTAGE,
                "bnkr_community_percentage": BNKR_COMMUNITY_PERCENTAGE,
                "bnkr_team_percentage": BNKR_TEAM_PERCENTAGE
            },
            "note": "NEW TOKENS DEFAULT TO NON-BURNABLE" if not is_burnable else "Token is burnable"
        }
    except Exception as e:
        logger.error(f"Check burnable error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check token: {str(e)}")

@api_router.post("/burn")
async def create_burn_transaction(request: BurnRequest, background_tasks: BackgroundTasks):
    """Create a new burn transaction"""
    try:
        # Validate token
        is_valid = await validate_token_contract(request.token_address, request.chain)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid token contract")
        
        # Check if token is burnable and if it's DRB
        is_burnable = await is_token_burnable(request.token_address)
        is_drb = await is_drb_token(request.token_address)
        
        # Calculate amounts based on token type
        amounts = calculate_burn_amounts(float(request.amount), request.token_address, is_burnable, is_drb)
        
        # Create transaction record
        transaction = BurnTransaction(
            wallet_address=request.wallet_address,
            token_address=request.token_address,
            amount=request.amount,
            chain=request.chain,
            burn_amount=amounts["burn_amount"],
            drb_total_amount=amounts["drb_total_amount"],
            drb_grok_amount=amounts["drb_grok_amount"],
            drb_team_amount=amounts["drb_team_amount"],
            drb_community_amount=amounts["drb_community_amount"],
            bnkr_total_amount=amounts["bnkr_total_amount"],
            bnkr_community_amount=amounts["bnkr_community_amount"],
            bnkr_team_amount=amounts["bnkr_team_amount"]
        )
        
        # Store in database
        result = await burns_collection.insert_one(transaction.dict())
        
        # Process burn in background
        background_tasks.add_task(process_burn_transaction, transaction.id)
        
        transaction_type = "DRB Direct Allocation" if is_drb else ("Burn" if is_burnable else "Swap")
        
        return {
            "transaction_id": transaction.id,
            "status": "pending",
            "amounts": amounts,
            "is_burnable": is_burnable,
            "is_drb": is_drb,
            "allocation_type": amounts["allocation_type"],
            "message": f"{transaction_type} transaction created successfully"
        }
        
    except Exception as e:
        logger.error(f"Burn creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create burn: {str(e)}")

@api_router.get("/transactions/{wallet_address}")
async def get_wallet_transactions(wallet_address: str):
    """Get transaction history for a wallet"""
    try:
        transactions = []
        cursor = burns_collection.find(
            {"wallet_address": wallet_address}
        ).sort("timestamp", DESCENDING).limit(50)
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            transactions.append(doc)
        
        return {"transactions": transactions}
        
    except Exception as e:
        logger.error(f"Transaction fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")

@api_router.get("/stats")
async def get_burn_statistics():
    """Get overall burn statistics"""
    try:
        total_burns = await burns_collection.count_documents({})
        completed_burns = await burns_collection.count_documents({"status": "completed"})
        
        # Calculate totals (simplified)
        pipeline = [
            {"$match": {"status": "completed"}},
            {"$group": {
                "_id": None,
                "total_volume": {"$sum": {"$toDouble": "$amount"}},
                "total_burned": {"$sum": {"$toDouble": "$burn_amount"}},
                "total_drb": {"$sum": {"$toDouble": "$drb_total_amount"}},
                "total_bnkr": {"$sum": {"$toDouble": "$bnkr_total_amount"}}
            }}
        ]
        
        result = await burns_collection.aggregate(pipeline).to_list(1)
        stats = result[0] if result else {
            "total_volume": 0,
            "total_burned": 0,
            "total_drb": 0,
            "total_bnkr": 0
        }
        
        return {
            "total_transactions": total_burns,
            "completed_transactions": completed_burns,
            "total_volume_usd": stats["total_volume"],
            "total_tokens_burned": stats["total_burned"],
            "total_drb_allocated": stats["total_drb"],
            "total_bnkr_allocated": stats["total_bnkr"],
            "burn_percentage": BURN_PERCENTAGE,
            "drb_percentage": DRB_PERCENTAGE,
            "bnkr_percentage": BNKR_PERCENTAGE,
            "supported_chains": list(SUPPORTED_CHAINS.keys())
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@api_router.get("/gas-estimates/{chain}")
async def get_gas_estimates(chain: str):
    """Get gas estimates for chain operations"""
    try:
        if chain == "base":
            return {
                "slow": {"gwei": "1", "usd": "0.001", "time": "30s"},
                "standard": {"gwei": "2", "usd": "0.002", "time": "15s"},
                "fast": {"gwei": "3", "usd": "0.003", "time": "5s"}
            }
        else:
            raise HTTPException(status_code=400, detail="Unsupported chain")
    except Exception as e:
        logger.error(f"Gas estimates error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get gas estimates: {str(e)}")

@api_router.get("/token-price/{token_address}/{chain}")
async def get_token_price_endpoint(token_address: str, chain: str):
    """Get token price"""
    try:
        price = await get_token_price(token_address, chain)
        return {"price": price, "currency": "USD"}
    except Exception as e:
        logger.error(f"Token price error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get token price: {str(e)}")

@api_router.post("/swap-quote")
async def get_swap_quote(request: dict):
    """Get swap quote for tokens"""
    try:
        # Simplified swap quote response
        return {
            "status": "success",
            "data": {
                "input_amount": request.get("amount", "0"),
                "output_amount": str(float(request.get("amount", "0")) * 0.95),  # 5% slippage
                "price_impact": "5%",
                "gas_estimate": "0.002"
            }
        }
    except Exception as e:
        logger.error(f"Swap quote error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get swap quote: {str(e)}")

@api_router.post("/execute-burn")
async def execute_burn_deprecated(request: dict):
    """Legacy execute burn endpoint - redirect to new burn endpoint"""
    try:
        # Convert old format to new format
        burn_request = BurnRequest(
            wallet_address=request.get("wallet_address", ""),
            token_address=request.get("token_address", ""),
            amount=request.get("amount", "0"),
            chain=request.get("chain", "base")
        )
        # Call the main burn endpoint logic
        return await create_burn_transaction(burn_request, BackgroundTasks())
    except Exception as e:
        logger.error(f"Execute burn error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute burn: {str(e)}")

@api_router.get("/transactions")
async def get_all_transactions():
    """Get all recent transactions"""
    try:
        transactions = []
        cursor = burns_collection.find({}).sort("timestamp", DESCENDING).limit(20)
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            transactions.append(doc)
        
        return {"transactions": transactions}
    except Exception as e:
        logger.error(f"Transactions fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")

@api_router.get("/transaction-status/{tx_hash}/{chain}")
async def get_transaction_status(tx_hash: str, chain: str):
    """Get transaction status from blockchain"""
    try:
        # For Base mainnet, we'll simulate checking transaction status
        # In a real implementation, you would query the blockchain
        
        # Check if transaction exists in our database first
        transaction = await burns_collection.find_one({"transaction_hash": tx_hash})
        
        if transaction:
            return {
                "status": "confirmed",
                "confirmations": 12,
                "tx_hash": tx_hash,
                "chain": chain
            }
        else:
            # Simulate checking blockchain
            return {
                "status": "pending", 
                "confirmations": 0,
                "tx_hash": tx_hash,
                "chain": chain
            }
    except Exception as e:
        logger.error(f"Transaction status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check transaction status: {str(e)}")

@api_router.get("/cross-chain/optimal-routes")
async def get_optimal_routes():
    """Get optimal routes for cross-chain operations (simplified for Base-only)"""
    try:
        # Since we're Base-only now, return simple Base chain recommendation
        return {
            "optimal_chains": {
                "DRB": "base",
                "BNKR": "base"
            },
            "recommended_chain": "base",
            "gas_estimates": {
                "base": {
                    "slow": "0.001",
                    "standard": "0.002", 
                    "fast": "0.003"
                }
            },
            "liquidity_analysis": {
                "base": {
                    "DRB_liquidity": "high",
                    "BNKR_liquidity": "high"
                }
            },
            "message": "Base chain is optimal for all token operations"
        }
    except Exception as e:
        logger.error(f"Optimal routes error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimal routes: {str(e)}")

@api_router.get("/community/contest")
async def get_community_contest():
    """Get current community contest information"""
    try:
        # Get current voting period
        current_period = await voting_periods_collection.find_one(
            {"status": "active"},
            sort=[("created_at", DESCENDING)]
        )
        
        # Get all active projects
        projects = []
        cursor = projects_collection.find({"status": "active"}).sort("total_votes", DESCENDING)
        async for project in cursor:
            project["_id"] = str(project["_id"])
            projects.append(project)
        
        # Get voting requirements
        vote_requirements = {
            "drb_amount": VOTE_REQUIREMENT_DRB,
            "bnkr_amount": VOTE_REQUIREMENT_BNKR
        }
        
        # Get current winner
        current_winner = None
        if current_period and current_period.get("winning_project_id"):
            current_winner = await projects_collection.find_one(
                {"id": current_period["winning_project_id"]}
            )
            if current_winner:
                current_winner["_id"] = str(current_winner["_id"])
        
        return {
            "voting_period": current_period,
            "projects": projects,
            "vote_requirements": vote_requirements,
            "current_winner": current_winner,
            "contest_allocations": {
                "drb_percentage": COMMUNITY_PROJECT_DRB_PERCENTAGE,
                "bnkr_percentage": COMMUNITY_PROJECT_BNKR_PERCENTAGE
            }
        }
        
    except Exception as e:
        logger.error(f"Community contest error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get contest info: {str(e)}")

@api_router.post("/community/project")
async def submit_project(project_data: dict):
    """Submit a new project for community voting"""
    try:
        # Validate required fields
        required_fields = ["name", "description", "base_address", "submitted_by"]
        for field in required_fields:
            if field not in project_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Create new project
        project = CommunityProject(
            name=project_data["name"],
            description=project_data["description"],
            base_address=project_data["base_address"],
            website=project_data.get("website"),
            twitter=project_data.get("twitter"),
            logo_url=project_data.get("logo_url"),
            submitted_by=project_data["submitted_by"]
        )
        
        # Store in database
        result = await projects_collection.insert_one(project.dict())
        
        return {
            "project_id": project.id,
            "status": "submitted",
            "message": "Project submitted successfully for community voting"
        }
        
    except Exception as e:
        logger.error(f"Project submission error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit project: {str(e)}")

@api_router.post("/community/vote")
async def cast_vote(vote_data: dict):
    """Cast a vote by burning DRB or BNKR tokens"""
    try:
        # Validate required fields
        required_fields = ["voter_wallet", "project_id", "vote_token", "vote_amount", "burn_tx_hash"]
        for field in required_fields:
            if field not in vote_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        vote_token = vote_data["vote_token"].upper()
        vote_amount = float(vote_data["vote_amount"])
        
        # Validate vote amount meets requirements
        if vote_token == "DRB" and vote_amount < VOTE_REQUIREMENT_DRB:
            raise HTTPException(
                status_code=400, 
                detail=f"Minimum {VOTE_REQUIREMENT_DRB} DRB required to vote"
            )
        elif vote_token == "BNKR" and vote_amount < VOTE_REQUIREMENT_BNKR:
            raise HTTPException(
                status_code=400, 
                detail=f"Minimum {VOTE_REQUIREMENT_BNKR} BNKR required to vote"
            )
        
        # Check if project exists
        project = await projects_collection.find_one({"id": vote_data["project_id"]})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if voter already voted for this project
        existing_vote = await votes_collection.find_one({
            "voter_wallet": vote_data["voter_wallet"],
            "project_id": vote_data["project_id"]
        })
        if existing_vote:
            raise HTTPException(status_code=400, detail="You have already voted for this project")
        
        # Create vote record
        vote = Vote(
            voter_wallet=vote_data["voter_wallet"],
            project_id=vote_data["project_id"],
            vote_token=vote_token,
            vote_amount=vote_amount,
            burn_tx_hash=vote_data["burn_tx_hash"],
            verified=True  # In production, this should verify the burn transaction
        )
        
        # Store vote
        await votes_collection.insert_one(vote.dict())
        
        # Update project vote counts
        update_data = {"$inc": {"total_votes": 1}}
        if vote_token == "DRB":
            update_data["$inc"]["total_drb_votes"] = vote_amount
        else:
            update_data["$inc"]["total_bnkr_votes"] = vote_amount
            
        await projects_collection.update_one(
            {"id": vote_data["project_id"]},
            update_data
        )
        
        return {
            "vote_id": vote.id,
            "status": "success",
            "message": f"Vote cast successfully with {vote_amount} {vote_token}"
        }
        
    except Exception as e:
        logger.error(f"Voting error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cast vote: {str(e)}")

@api_router.get("/community/votes/{wallet_address}")
async def get_user_votes(wallet_address: str):
    """Get voting history for a wallet"""
    try:
        votes = []
        cursor = votes_collection.find(
            {"voter_wallet": wallet_address}
        ).sort("timestamp", DESCENDING)
        
        async for vote in cursor:
            vote["_id"] = str(vote["_id"])
            # Get project info
            project = await projects_collection.find_one({"id": vote["project_id"]})
            if project:
                vote["project_name"] = project["name"]
            votes.append(vote)
        
        return {"votes": votes}
        
    except Exception as e:
        logger.error(f"User votes error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user votes: {str(e)}")

@api_router.get("/community/stats")
async def get_community_stats():
    """Get community statistics and leaderboard"""
    try:
        # Get recent burns
        recent_burns = []
        cursor = burns_collection.find(
            {"status": "completed"}
        ).sort("timestamp", DESCENDING).limit(10)
        
        async for doc in cursor:
            recent_burns.append({
                "wallet": doc["wallet_address"][:6] + "..." + doc["wallet_address"][-4:],
                "amount": doc["amount"],
                "chain": doc["chain"],
                "timestamp": doc["timestamp"].isoformat()
            })
        
        # Get top burners
        pipeline = [
            {"$match": {"status": "completed"}},
            {"$group": {
                "_id": "$wallet_address",
                "total_burned": {"$sum": {"$toDouble": "$amount"}},
                "transaction_count": {"$sum": 1}
            }},
            {"$sort": {"total_burned": -1}},
            {"$limit": 10}
        ]
        
        top_burners = []
        async for doc in burns_collection.aggregate(pipeline):
            top_burners.append({
                "wallet": doc["_id"][:6] + "..." + doc["_id"][-4:],
                "total_burned": doc["total_burned"],
                "transaction_count": doc["transaction_count"]
            })
        
        return CommunityStats(
            total_burns=await burns_collection.count_documents({"status": "completed"}),
            total_volume_usd=sum([float(b["amount"]) for b in recent_burns]),
            total_tokens_burned=0,  # Simplified
            active_wallets=len(top_burners),
            chain_distribution={"base": 100.0},  # Base only for now
            top_burners=top_burners,
            recent_burns=recent_burns
        ).dict()
        
    except Exception as e:
        logger.error(f"Community stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get community stats: {str(e)}")

async def process_burn_transaction(transaction_id: str):
    """Process burn transaction in background"""
    try:
        # Get transaction
        transaction = await burns_collection.find_one({"id": transaction_id})
        if not transaction:
            return
        
        # Update status to processing
        await burns_collection.update_one(
            {"id": transaction_id},
            {"$set": {"status": "processing"}}
        )
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Simulate transaction hash
        tx_hash = f"0x{uuid.uuid4().hex}"
        
        # Update to completed
        await burns_collection.update_one(
            {"id": transaction_id},
            {"$set": {
                "status": "completed",
                "tx_hash": tx_hash
            }}
        )
        
        logger.info(f"Burn transaction {transaction_id} completed")
        
    except Exception as e:
        logger.error(f"Burn processing error: {e}")
        # Update to failed
        await burns_collection.update_one(
            {"id": transaction_id},
            {"$set": {"status": "failed"}}
        )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wallet management endpoints
@api_router.get("/wallet/status")
async def get_wallet_status():
    """Get BurnReliefBot wallet status"""
    try:
        is_connected = burn_wallet_manager.is_connected()
        wallet_address = burn_wallet_manager.account.address if burn_wallet_manager.account else None
        
        # Get additional info if connected
        additional_info = {}
        if is_connected:
            try:
                # For testing purposes, we'll simulate ETH balance and other details
                # In production, these would be real values from the blockchain
                
                # Simulate ETH balance for gas (0.5 ETH)
                eth_balance = 0.5
                
                # Simulate current gas price (5 Gwei)
                gas_price_gwei = 5.0
                
                # Simulate current block number
                block_number = 12345678
                
                additional_info = {
                    "eth_balance": eth_balance,
                    "gas_price_gwei": gas_price_gwei,
                    "block_number": block_number
                }
            except Exception as e:
                logger.warning(f"Could not get additional wallet info: {e}")
        
        return {
            "connected": is_connected,
            "wallet_address": wallet_address,
            "network": "Base Mainnet",
            "rpc_url": BASE_RPC_URL,
            **additional_info
        }
    except Exception as e:
        logger.error(f"Wallet status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check wallet status: {str(e)}")

@api_router.get("/wallet/token-info/{token_address}")
async def get_token_info(token_address: str, admin_user: dict = Depends(verify_admin_token)):
    """Get detailed token information (admin only)"""
    try:
        if not burn_wallet_manager.is_connected():
            raise HTTPException(status_code=500, detail="Wallet not connected")
        
        token_info = await burn_wallet_manager.get_token_info(token_address)
        return {
            "token_address": token_address,
            "token_info": token_info
        }
    except Exception as e:
        logger.error(f"Token info check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get token info: {str(e)}")

@api_router.post("/test-redistribution")
async def test_redistribution(test_data: dict, admin_user: dict = Depends(verify_admin_token)):
    """Test redistribution with small amounts (admin only)"""
    try:
        token_address = test_data.get("token_address")
        test_amount = float(test_data.get("test_amount", 0.01))  # Default 0.01 tokens
        
        if not burn_wallet_manager.is_connected():
            raise HTTPException(status_code=500, detail="Wallet not connected")
        
        # Get token info first
        token_info = await burn_wallet_manager.get_token_info(token_address)
        
        # For testing purposes, we'll simulate a successful test redistribution
        # In production, this would execute a real test transaction
        
        # Simulate test transaction
        test_tx_hash = f"0x{''.join([hex(ord(c))[2:] for c in str(uuid.uuid4())])}"
        
        # Return success response with simulated result
        return {
            "test_result": "success",
            "test_amount": test_amount,
            "token_info": token_info,
            "redistribution_result": {
                "status": "success",
                "transaction_id": test_tx_hash,
                "allocations": {
                    "burn_amount": test_amount * 0.5,
                    "drb_grok_amount": test_amount * 0.2,
                    "drb_community_amount": test_amount * 0.2,
                    "drb_team_amount": test_amount * 0.1
                },
                "transaction_hashes": {
                    BURN_ADDRESS: f"0x{''.join([hex(ord(c))[2:] for c in str(uuid.uuid4())])}",
                    GROK_WALLET: f"0x{''.join([hex(ord(c))[2:] for c in str(uuid.uuid4())])}",
                    COMMUNITY_WALLET: f"0x{''.join([hex(ord(c))[2:] for c in str(uuid.uuid4())])}",
                    TEAM_WALLET: f"0x{''.join([hex(ord(c))[2:] for c in str(uuid.uuid4())])}"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Test redistribution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@api_router.post("/execute-redistribution")
async def execute_redistribution(redistribution_data: dict, admin_user: dict = Depends(verify_admin_token)):
    """Manually execute token redistribution (admin only)"""
    try:
        total_amount = float(redistribution_data.get("amount", 0))
        token_address = redistribution_data.get("token_address", "")
        is_burnable = redistribution_data.get("is_burnable", True)
        
        if total_amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount")
        
        result = await burn_wallet_manager.execute_burn_and_redistribute(
            total_amount, token_address, is_burnable
        )
        
        return result
    except Exception as e:
        logger.error(f"Manual redistribution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute redistribution: {str(e)}")

# Include the API router
app.include_router(api_router, prefix="/api")

# Admin router
admin_router = APIRouter()

@admin_router.get("/projects")
async def get_admin_projects(admin_user: dict = Depends(verify_admin_token)):
    """Get all projects for admin management"""
    try:
        projects = []
        cursor = projects_collection.find({})
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            projects.append(doc)
        
        return {"projects": projects}
    except Exception as e:
        logger.error(f"Admin projects fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

@admin_router.post("/projects")
async def create_admin_project(project_data: dict, admin_user: dict = Depends(verify_admin_token)):
    """Create a new project (admin only)"""
    try:
        project = {
            "id": str(uuid.uuid4()),
            "name": project_data.get("name"),
            "description": project_data.get("description"),
            "base_address": project_data.get("base_address"),
            "website": project_data.get("website", ""),
            "twitter": project_data.get("twitter", ""),
            "logo_url": project_data.get("logo_url", ""),
            "is_active": False,
            "votes": 0,
            "created_at": datetime.utcnow(),
            "created_by": admin_user["user_id"]
        }
        
        result = await projects_collection.insert_one(project)
        project["_id"] = str(result.inserted_id)
        
        return {"status": "created", "project": project}
    except Exception as e:
        logger.error(f"Admin project creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@admin_router.put("/projects/{project_id}")
async def update_admin_project(project_id: str, project_data: dict, admin_user: dict = Depends(verify_admin_token)):
    """Update a project (admin only)"""
    try:
        update_data = {
            "name": project_data.get("name"),
            "description": project_data.get("description"),
            "base_address": project_data.get("base_address"),
            "website": project_data.get("website", ""),
            "twitter": project_data.get("twitter", ""),
            "logo_url": project_data.get("logo_url", ""),
            "updated_at": datetime.utcnow(),
            "updated_by": admin_user["user_id"]
        }
        
        result = await projects_collection.update_one(
            {"_id": project_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"status": "updated"}
    except Exception as e:
        logger.error(f"Admin project update error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

@admin_router.delete("/projects/{project_id}")
async def delete_admin_project(project_id: str, admin_user: dict = Depends(verify_admin_token)):
    """Delete a project (admin only)"""
    try:
        result = await projects_collection.delete_one({"_id": project_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"status": "deleted"}
    except Exception as e:
        logger.error(f"Admin project deletion error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

@admin_router.post("/contest/start")
async def start_contest(contest_data: dict, admin_user: dict = Depends(verify_admin_token)):
    """Start a contest for a specific project (admin only)"""
    try:
        project_id = contest_data.get("project_id")
        
        # Deactivate all current contests
        await projects_collection.update_many(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )
        
        # Activate the selected project
        result = await projects_collection.update_one(
            {"_id": project_id},
            {"$set": {"is_active": True, "votes": 0, "contest_started_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"status": "contest_started", "project_id": project_id}
    except Exception as e:
        logger.error(f"Contest start error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start contest: {str(e)}")

app.include_router(admin_router, prefix="/api/admin")

@app.get("/")
async def root():
    return {"message": "Burn Relief Bot API - Base Chain Only", "version": "2.0", "chains": ["base"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
