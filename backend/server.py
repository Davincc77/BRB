from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from web3 import Web3
from eth_utils import is_address
import requests
import asyncio

# Import blockchain service
import sys
sys.path.append('/app/backend')
from blockchain_service_simple import blockchain_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Multi-chain configurations
SUPPORTED_CHAINS = {
    "base": {
        "name": "Base",
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
        "explorer": "https://basescan.org",
        "recipient_wallet": "0xFE26d9b5853F3B652456a27A3DC33Bff72A2ca7",
        "currency": "ETH"
    },
    "solana": {
        "name": "Solana",
        "chain_id": "mainnet-beta",
        "rpc_url": "https://api.mainnet-beta.solana.com",
        "explorer": "https://solscan.io",
        "recipient_wallet": "CtFtfe2pYRiJVAUrEZtdFKZVV2UFpdaWBU1Ve7aPC",
        "currency": "SOL"
    },
    "ethereum": {
        "name": "Ethereum",
        "chain_id": 1,
        "rpc_url": "https://ethereum-rpc.publicnode.com",
        "explorer": "https://etherscan.io",
        "recipient_wallet": "0xFE26d9b5853F3B652456a27A3DC33Bff72A2ca7",
        "currency": "ETH"
    },
    "polygon": {
        "name": "Polygon",
        "chain_id": 137,
        "rpc_url": "https://polygon-rpc.com",
        "explorer": "https://polygonscan.com",
        "recipient_wallet": "0xFE26d9b5853F3B652456a27A3DC33Bff72A2ca7",
        "currency": "MATIC"
    },
    "arbitrum": {
        "name": "Arbitrum",
        "chain_id": 42161,
        "rpc_url": "https://arb1.arbitrum.io/rpc",
        "explorer": "https://arbiscan.io",
        "recipient_wallet": "0xFE26d9b5853F3B652456a27A3DC33Bff72A2ca7",
        "currency": "ETH"
    }
}

# Constants
BURN_ADDRESS = "0x000000000000000000000000000000000000dEaD"
DRB_TOKEN_CA = "0x3ec2156D4c0A9CBdAB4a016633b7BcF6a8d68Ea2"
CBBTC_TOKEN_CA = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"

# New allocation addresses
GROK_WALLET = "0xb1058c959987e3513600eb5b4fd82aeee2a0e4f9"
TEAM_WALLET = "0xFE26d9b5853F3B652456a27A3DC33Bff72A2ca7"  # Team wallet for both DRB and cbBTC
COMMUNITY_WALLET = "0xFE26d9b5853F3B652456a27A3DC33Bff72A2ca7"  # Community pools/contests wallet

# New allocation percentages
BURN_PERCENTAGE = 88.0  # 88% burned
DRB_PERCENTAGE = 8.0    # 8% total DRB allocation
DRB_GROK_PERCENTAGE = 7.0    # 7% DRB to Grok's wallet  
DRB_TEAM_PERCENTAGE = 1.0    # 1% DRB to team
CBBTC_PERCENTAGE = 4.0       # 4% total cbBTC allocation
CBBTC_COMMUNITY_PERCENTAGE = 3.0  # 3% cbBTC for community pools/contests
CBBTC_TEAM_PERCENTAGE = 1.0       # 1% cbBTC to team

# Legacy constants for backward compatibility
BASE_RECIPIENT_WALLET = SUPPORTED_CHAINS["base"]["recipient_wallet"]
SOLANA_RECIPIENT_WALLET = SUPPORTED_CHAINS["solana"]["recipient_wallet"]
BASE_RPC_URL = SUPPORTED_CHAINS["base"]["rpc_url"]
BASE_CHAIN_ID = SUPPORTED_CHAINS["base"]["chain_id"]

# Blacklisted tokens (case-insensitive)
BLACKLISTED_TOKENS = {
    DRB_TOKEN_CA.lower(),
    # ETH related
    "eth", "ethereum", "weth", 
    # BTC related  
    "btc", "bitcoin", "wbtc", "cbbtc",
    # Other blocked tokens
    "xrp", "sui", "sol", "solana"
}

# Models
class BurnRequest(BaseModel):
    wallet_address: str
    token_address: str
    amount: str
    chain: str  # "base" or "solana"
    
class BurnTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str
    token_address: str
    amount: str
    chain: str
    burn_amount: str  # 88%
    drb_total_amount: str  # 8% total DRB
    drb_grok_amount: str   # 7% DRB to Grok's wallet
    drb_team_amount: str   # 1% DRB to team
    cbbtc_total_amount: str    # 4% total cbBTC
    cbbtc_community_amount: str # 3% cbBTC for community
    cbbtc_team_amount: str      # 1% cbBTC to team
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
    reason: Optional[str] = None
    token_name: Optional[str] = None
    token_symbol: Optional[str] = None

# Community models
class BurnStats(BaseModel):
    total_burns: int
    total_amount_burned: str
    total_users: int
    trending_tokens: List[dict]
    top_burners: List[dict]

class Achievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_address: str
    achievement_type: str  # "first_burn", "big_burner", "multi_chain", etc.
    title: str
    description: str
    icon: str
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    chain: str
    amount: Optional[str] = None

class Challenge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    target_amount: str
    current_amount: str = "0"
    participants: int = 0
    start_date: datetime
    end_date: datetime
    reward_description: str
    status: str = "active"  # active, completed, expired

# Real blockchain transaction models
class SwapQuoteRequest(BaseModel):
    input_token: str
    output_token: str
    amount: str
    chain: str

class SwapQuoteResponse(BaseModel):
    input_amount: str
    output_amount: str
    price_impact: str
    gas_estimate: str
    route: Optional[dict] = None
    error: Optional[str] = None

class ExecuteBurnRequest(BaseModel):
    wallet_address: str
    token_address: str
    amount: str
    chain: str
    slippage_tolerance: float = 3.0  # 3% default

class BlockchainTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    burn_transaction_id: str
    tx_type: str  # "burn", "swap_to_drb", "swap_to_cbbtc"
    tx_hash: str
    chain: str
    status: str = "pending"  # pending, confirmed, failed
    confirmations: int = 0
    gas_used: Optional[str] = None
    gas_price: Optional[str] = None
    block_number: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GasEstimate(BaseModel):
    chain: str
    slow: dict
    standard: dict
    fast: dict
    currency: str

# Utility functions
def is_token_blacklisted(token_address: str, token_symbol: str = None) -> bool:
    """Check if token is blacklisted"""
    # Check by address
    if token_address.lower() in BLACKLISTED_TOKENS:
        return True
    
    # Check by symbol if provided
    if token_symbol and token_symbol.lower() in BLACKLISTED_TOKENS:
        return True
        
    return False

def calculate_amounts(total_amount: str):
    """Calculate burn and distribution amounts based on new 88/8/4 split"""
    total = float(total_amount)
    
    # 88% burned
    burn_amount = total * (BURN_PERCENTAGE / 100)
    
    # 8% DRB allocation (7% to Grok, 1% to team)
    drb_total_amount = total * (DRB_PERCENTAGE / 100)
    drb_grok_amount = total * (DRB_GROK_PERCENTAGE / 100)
    drb_team_amount = total * (DRB_TEAM_PERCENTAGE / 100)
    
    # 4% cbBTC allocation (3% to community, 1% to team)
    cbbtc_total_amount = total * (CBBTC_PERCENTAGE / 100)
    cbbtc_community_amount = total * (CBBTC_COMMUNITY_PERCENTAGE / 100)
    cbbtc_team_amount = total * (CBBTC_TEAM_PERCENTAGE / 100)
    
    return {
        "burn_amount": str(burn_amount),
        "drb_total_amount": str(drb_total_amount),
        "drb_grok_amount": str(drb_grok_amount),
        "drb_team_amount": str(drb_team_amount),
        "cbbtc_total_amount": str(cbbtc_total_amount),
        "cbbtc_community_amount": str(cbbtc_community_amount),
        "cbbtc_team_amount": str(cbbtc_team_amount)
    }

async def get_token_info(token_address: str, chain: str):
    """Get token information from blockchain"""
    if chain in ["base", "ethereum", "polygon", "arbitrum"]:
        try:
            chain_config = SUPPORTED_CHAINS[chain]
            web3 = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
            
            # ERC-20 ABI for name and symbol
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "name",
                    "outputs": [{"name": "", "type": "string"}],
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
            
            contract = web3.eth.contract(address=token_address, abi=erc20_abi)
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            
            return {"name": name, "symbol": symbol}
        except Exception as e:
            logger.error(f"Error getting token info for {chain}: {e}")
            return None
    
    # For Solana, we'd need to implement similar logic
    # For now, return None
    return None

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Burn Relief Bot API", "version": "1.0.0", "status": "active"}

@api_router.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "burn_address": BURN_ADDRESS,
        "drb_token_address": DRB_TOKEN_CA,
        "cbbtc_token_address": CBBTC_TOKEN_CA,
        "supported_chains": SUPPORTED_CHAINS,
        "burn_percentage": 88,
        "drb_swap_percentage": 6,
        "cbbtc_swap_percentage": 6
    }

@api_router.get("/chains")
async def get_supported_chains():
    """Get all supported chains"""
    return {"chains": SUPPORTED_CHAINS}

@api_router.get("/stats", response_model=BurnStats)
async def get_burn_stats():
    """Get community burn statistics"""
    try:
        # Get total burns and users
        total_burns = await db.burn_transactions.count_documents({})
        total_users = len(await db.burn_transactions.distinct("wallet_address"))
        
        # Calculate total amount burned across all chains
        pipeline = [
            {"$group": {
                "_id": None,
                "total_burned": {"$sum": {"$toDouble": "$burn_amount"}}
            }}
        ]
        result = await db.burn_transactions.aggregate(pipeline).to_list(1)
        total_amount_burned = str(result[0]["total_burned"]) if result else "0"
        
        # Get trending tokens (most burned)
        trending_pipeline = [
            {"$group": {
                "_id": {"token_address": "$token_address", "chain": "$chain"},
                "burn_count": {"$sum": 1},
                "total_burned": {"$sum": {"$toDouble": "$burn_amount"}}
            }},
            {"$sort": {"burn_count": -1}},
            {"$limit": 5}
        ]
        trending_result = await db.burn_transactions.aggregate(trending_pipeline).to_list(5)
        trending_tokens = [
            {
                "token_address": item["_id"]["token_address"],
                "chain": item["_id"]["chain"],
                "burn_count": item["burn_count"],
                "total_burned": str(item["total_burned"])
            }
            for item in trending_result
        ]
        
        # Get top burners
        burners_pipeline = [
            {"$group": {
                "_id": "$wallet_address",
                "total_burns": {"$sum": 1},
                "total_amount": {"$sum": {"$toDouble": "$burn_amount"}}
            }},
            {"$sort": {"total_amount": -1}},
            {"$limit": 10}
        ]
        burners_result = await db.burn_transactions.aggregate(burners_pipeline).to_list(10)
        top_burners = [
            {
                "wallet_address": item["_id"],
                "total_burns": item["total_burns"],
                "total_amount": str(item["total_amount"])
            }
            for item in burners_result
        ]
        
        return BurnStats(
            total_burns=total_burns,
            total_amount_burned=total_amount_burned,
            total_users=total_users,
            trending_tokens=trending_tokens,
            top_burners=top_burners
        )
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return BurnStats(
            total_burns=0,
            total_amount_burned="0",
            total_users=0,
            trending_tokens=[],
            top_burners=[]
        )

@api_router.post("/validate-token", response_model=TokenValidationResponse)
async def validate_token(request: TokenValidationRequest):
    """Validate if a token can be burned"""
    try:
        # Check if chain is supported
        if request.chain not in SUPPORTED_CHAINS:
            return TokenValidationResponse(
                is_valid=False,
                reason=f"Unsupported chain: {request.chain}"
            )
        
        # Basic address validation for EVM chains
        if request.chain in ["base", "ethereum", "polygon", "arbitrum"]:
            if not is_address(request.token_address):
                return TokenValidationResponse(
                    is_valid=False,
                    reason="Invalid token address format"
                )
        
        # Get token info
        token_info = await get_token_info(request.token_address, request.chain)
        
        if not token_info:
            return TokenValidationResponse(
                is_valid=False,
                reason="Could not fetch token information"
            )
        
        # Check if token is blacklisted
        if is_token_blacklisted(request.token_address, token_info.get("symbol")):
            return TokenValidationResponse(
                is_valid=False,
                reason=f"Token {token_info.get('symbol', 'Unknown')} is not allowed for burning",
                token_name=token_info.get("name"),
                token_symbol=token_info.get("symbol")
            )
        
        return TokenValidationResponse(
            is_valid=True,
            token_name=token_info.get("name"),
            token_symbol=token_info.get("symbol")
        )
        
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return TokenValidationResponse(
            is_valid=False,
            reason="Token validation failed"
        )

@api_router.post("/burn", response_model=BurnTransaction)
async def create_burn_transaction(request: BurnRequest):
    """Create a burn transaction"""
    try:
        # Validate token first
        validation = await validate_token(TokenValidationRequest(
            token_address=request.token_address,
            chain=request.chain
        ))
        
        if not validation.is_valid:
            raise HTTPException(status_code=400, detail=validation.reason)
        
        # Calculate amounts
        amounts = calculate_amounts(request.amount)
        
        # Determine recipient wallet based on chain
        if request.chain in SUPPORTED_CHAINS:
            recipient_wallet = SUPPORTED_CHAINS[request.chain]["recipient_wallet"]
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported chain: {request.chain}")
        
        # Create transaction record with new allocation structure
        burn_tx = BurnTransaction(
            wallet_address=request.wallet_address,
            token_address=request.token_address,
            amount=request.amount,
            chain=request.chain,
            burn_amount=amounts["burn_amount"],
            drb_total_amount=amounts["drb_total_amount"],
            drb_grok_amount=amounts["drb_grok_amount"],
            drb_team_amount=amounts["drb_team_amount"],
            cbbtc_total_amount=amounts["cbbtc_total_amount"],
            cbbtc_community_amount=amounts["cbbtc_community_amount"],
            cbbtc_team_amount=amounts["cbbtc_team_amount"]
        )
        
        # Save to database
        await db.burn_transactions.insert_one(burn_tx.dict())
        
        return burn_tx
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Burn transaction creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create burn transaction")

@api_router.get("/transactions", response_model=List[BurnTransaction])
async def get_transactions(wallet_address: Optional[str] = None):
    """Get burn transactions"""
    try:
        query = {}
        if wallet_address:
            query["wallet_address"] = wallet_address
            
        transactions = await db.burn_transactions.find(query).sort("timestamp", -1).to_list(100)
        return [BurnTransaction(**tx) for tx in transactions]
        
    except Exception as e:
        logger.error(f"Get transactions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")

@api_router.get("/transaction/{transaction_id}", response_model=BurnTransaction)
async def get_transaction(transaction_id: str):
    """Get specific transaction"""
    try:
        transaction = await db.burn_transactions.find_one({"id": transaction_id})
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return BurnTransaction(**transaction)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get transaction error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch transaction")

# Real blockchain endpoints
@api_router.post("/swap-quote", response_model=SwapQuoteResponse)
async def get_swap_quote(request: SwapQuoteRequest):
    """Get real-time swap quote from DEX"""
    try:
        quote = await blockchain_service.get_swap_quote(
            request.input_token,
            request.output_token, 
            request.amount,
            request.chain
        )
        
        if "error" in quote:
            return SwapQuoteResponse(
                input_amount=request.amount,
                output_amount="0",
                price_impact="0%",
                gas_estimate="0",
                error=quote["error"]
            )
        
        return SwapQuoteResponse(
            input_amount=request.amount,
            output_amount=quote.get("outputAmount", "0"),
            price_impact=quote.get("slippage", "0%"),
            gas_estimate=quote.get("gasEstimate", "0"),
            route=quote.get("route")
        )
        
    except Exception as e:
        logger.error(f"Swap quote error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get swap quote")

@api_router.post("/execute-burn", response_model=dict)
async def execute_real_burn(request: ExecuteBurnRequest):
    """Execute real blockchain burn transaction"""
    try:
        # Validate token first
        validation = await validate_token(TokenValidationRequest(
            token_address=request.token_address,
            chain=request.chain
        ))
        
        if not validation.is_valid:
            raise HTTPException(status_code=400, detail=validation.reason)
        
        # Get recipient wallet for chain
        if request.chain not in SUPPORTED_CHAINS:
            raise HTTPException(status_code=400, detail=f"Unsupported chain: {request.chain}")
        
        recipient_wallet = SUPPORTED_CHAINS[request.chain]["recipient_wallet"]
        
        # Execute blockchain transaction
        result = await blockchain_service.execute_burn_transaction(
            request.token_address,
            request.amount,
            request.wallet_address,
            request.chain,
            recipient_wallet
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Transaction failed"))
        
        # Calculate amounts for database record
        amounts = calculate_amounts(request.amount)
        
        # Create burn transaction record with new allocation structure
        burn_tx = BurnTransaction(
            wallet_address=request.wallet_address,
            token_address=request.token_address,
            amount=request.amount,
            chain=request.chain,
            burn_amount=amounts["burn_amount"],
            drb_total_amount=amounts["drb_total_amount"],
            drb_grok_amount=amounts["drb_grok_amount"],
            drb_team_amount=amounts["drb_team_amount"],
            cbbtc_total_amount=amounts["cbbtc_total_amount"],
            cbbtc_community_amount=amounts["cbbtc_community_amount"],
            cbbtc_team_amount=amounts["cbbtc_team_amount"],
            status="processing"
        )
        
        # Save burn transaction
        await db.burn_transactions.insert_one(burn_tx.dict())
        
        # Save individual blockchain transactions
        for tx in result.get("transactions", []):
            blockchain_tx = BlockchainTransaction(
                burn_transaction_id=burn_tx.id,
                tx_type=tx["type"],
                tx_hash=tx.get("hash", tx.get("signature", "")),
                chain=request.chain,
                status="pending"
            )
            await db.blockchain_transactions.insert_one(blockchain_tx.dict())
        
        return {
            "success": True,
            "burn_transaction_id": burn_tx.id,
            "blockchain_result": result,
            "message": "Burn transaction initiated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute burn error: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute burn transaction")

@api_router.get("/gas-estimates/{chain}", response_model=GasEstimate)
async def get_gas_estimates(chain: str):
    """Get current gas estimates for chain"""
    try:
        estimates = await blockchain_service.estimate_gas_fees(chain)
        
        if "error" in estimates:
            raise HTTPException(status_code=400, detail=estimates["error"])
        
        return GasEstimate(
            chain=chain,
            slow={"price": estimates.get("base_fee", "0"), "time": "2-5 minutes"},
            standard={"price": str(float(estimates.get("base_fee", "0")) * 1.2), "time": "1-2 minutes"},
            fast={"price": str(float(estimates.get("base_fee", "0")) * 1.5), "time": "30 seconds"},
            currency=estimates.get("currency", "Gwei")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gas estimates error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get gas estimates")

@api_router.get("/transaction-status/{tx_hash}/{chain}")
async def get_transaction_status(tx_hash: str, chain: str):
    """Get real-time transaction status from blockchain"""
    try:
        status = await blockchain_service.get_transaction_status(tx_hash, chain)
        return status
        
    except Exception as e:
        logger.error(f"Transaction status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get transaction status")

@api_router.get("/token-price/{token_address}/{chain}")
async def get_token_price(token_address: str, chain: str):
    """Get current token price"""
    try:
        price = await blockchain_service.get_token_price(token_address, chain)
        
        if price is None:
            raise HTTPException(status_code=404, detail="Token price not found")
        
        return {"token_address": token_address, "chain": chain, "price_usd": price}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token price error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get token price")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()