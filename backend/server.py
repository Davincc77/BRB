from fastapi import FastAPI, HTTPException, APIRouter, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import logging
import asyncio
import aiohttp
import uuid
import json
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, DESCENDING
import time
from web3 import Web3
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.system_program import TransferParams, transfer
from solders.rpc.responses import SendTransactionResp
import websockets
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Multi-chain configurations - Simplified to Base chain only
SUPPORTED_CHAINS = {
    "base": {
        "name": "Base",
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
        "explorer": "https://basescan.org",
        "recipient_wallet": "0xFE26d9b5853F3B652456a27A3DC33Bff72A2ca7",
        "currency": "ETH"
    }
}

# Token contract addresses
DRB_TOKEN_CA = "0x1234567890123456789012345678901234567890"  # Placeholder for $DRB token
BNKR_TOKEN_CA = "0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b"  # $BNKR token for Banker Club Members

# Wallet addresses
BURN_ADDRESS = "0x000000000000000000000000000000000000dEaD"
GROK_WALLET = "0x742d35Cc6634C0532925a3b8D0d67c58C95B4b1a"
TEAM_WALLET = "0x742d35Cc6634C0532925a3b8D0d67c58C95B4b1b"
COMMUNITY_WALLET = "0x742d35Cc6634C0532925a3b8D0d67c58C95B4b1c"

# Percentage allocations (simplified for Base chain only)
BURN_PERCENTAGE = 88.0
DRB_PERCENTAGE = 9.5
DRB_GROK_PERCENTAGE = 7.0      # 7% DRB to Grok
DRB_TEAM_PERCENTAGE = 1.0      # 1% DRB to team
DRB_COMMUNITY_PERCENTAGE = 1.5 # 1.5% DRB to community
BNKR_PERCENTAGE = 2.5         # 2.5% total BNKR allocation (1.5% community + 1% team)
BNKR_COMMUNITY_PERCENTAGE = 1.5  # 1.5% BNKR for Banker Club Members and OK Computers holders
BNKR_TEAM_PERCENTAGE = 1.0       # 1% BNKR to team

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

# Database setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/burn_relief_bot')
client = AsyncIOMotorClient(MONGO_URL)
db = client.burn_relief_bot

# Collections
burns_collection = db.burns
stats_collection = db.stats
community_collection = db.community
leaderboard_collection = db.leaderboard
crosschain_collection = db.crosschain
websocket_collection = db.websockets

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
        if chain == "base":
            # Use Web3 to validate contract
            web3 = Web3(Web3.HTTPProvider(SUPPORTED_CHAINS["base"]["rpc_url"]))
            code = web3.eth.get_code(token_address)
            return len(code) > 0
        return False
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return False

def calculate_burn_amounts(total_amount: float) -> Dict[str, str]:
    """Calculate distribution amounts for burn transaction"""
    total = float(total_amount)
    
    burn_amount = total * (BURN_PERCENTAGE / 100)
    drb_total_amount = total * (DRB_PERCENTAGE / 100)
    drb_grok_amount = total * (DRB_GROK_PERCENTAGE / 100)
    drb_team_amount = total * (DRB_TEAM_PERCENTAGE / 100)
    drb_community_amount = total * (DRB_COMMUNITY_PERCENTAGE / 100)
    bnkr_total_amount = total * (BNKR_PERCENTAGE / 100)
    bnkr_community_amount = total * (BNKR_COMMUNITY_PERCENTAGE / 100)
    bnkr_team_amount = total * (BNKR_TEAM_PERCENTAGE / 100)
    
    return {
        "burn_amount": str(burn_amount),
        "drb_total_amount": str(drb_total_amount),
        "drb_grok_amount": str(drb_grok_amount),
        "drb_team_amount": str(drb_team_amount),
        "drb_community_amount": str(drb_community_amount),
        "bnkr_total_amount": str(bnkr_total_amount),
        "bnkr_community_amount": str(bnkr_community_amount),
        "bnkr_team_amount": str(bnkr_team_amount)
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

@api_router.post("/burn")
async def create_burn_transaction(request: BurnRequest, background_tasks: BackgroundTasks):
    """Create a new burn transaction"""
    try:
        # Validate token
        is_valid = await validate_token_contract(request.token_address, request.chain)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid token contract")
        
        # Calculate amounts
        amounts = calculate_burn_amounts(float(request.amount))
        
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
        
        return {
            "transaction_id": transaction.id,
            "status": "pending",
            "amounts": amounts,
            "message": "Burn transaction created successfully"
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

# Include the API router
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Burn Relief Bot API - Base Chain Only", "version": "2.0", "chains": ["base"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
