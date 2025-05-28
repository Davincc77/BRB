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
    drb_swap_amount: str  # 6% 
    cbbtc_swap_amount: str  # 6%
    recipient_wallet: str  # Where swapped tokens are sent
    burn_wallet: str = BURN_ADDRESS  # Where burned tokens are sent
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
    """Calculate burn and swap amounts based on 88/6/6 split"""
    total = float(total_amount)
    burn_amount = total * 0.88
    drb_amount = total * 0.06
    cbbtc_amount = total * 0.06
    
    return {
        "burn_amount": str(burn_amount),
        "drb_swap_amount": str(drb_amount), 
        "cbbtc_swap_amount": str(cbbtc_amount)
    }

async def get_token_info(token_address: str, chain: str):
    """Get token information from blockchain"""
    if chain == "base":
        try:
            web3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
            
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
            logger.error(f"Error getting token info: {e}")
            return None
    
    # For Solana, we'd need to implement similar logic
    # For now, return None
    return None

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Crypto Burn Agent API"}

@api_router.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "burn_address": BURN_ADDRESS,
        "drb_token_address": DRB_TOKEN_CA,
        "cbbtc_token_address": CBBTC_TOKEN_CA,
        "base_recipient_wallet": BASE_RECIPIENT_WALLET,
        "solana_recipient_wallet": SOLANA_RECIPIENT_WALLET,
        "supported_chains": ["base", "solana"],
        "burn_percentage": 88,
        "drb_swap_percentage": 6,
        "cbbtc_swap_percentage": 6
    }

@api_router.post("/validate-token", response_model=TokenValidationResponse)
async def validate_token(request: TokenValidationRequest):
    """Validate if a token can be burned"""
    try:
        # Basic address validation
        if request.chain == "base":
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
        if request.chain == "base":
            recipient_wallet = BASE_RECIPIENT_WALLET
        elif request.chain == "solana":
            if SOLANA_RECIPIENT_WALLET is None:
                raise HTTPException(status_code=400, detail="Solana recipient wallet not configured")
            recipient_wallet = SOLANA_RECIPIENT_WALLET
        else:
            raise HTTPException(status_code=400, detail="Unsupported chain")
        
        # Create transaction record
        burn_tx = BurnTransaction(
            wallet_address=request.wallet_address,
            token_address=request.token_address,
            amount=request.amount,
            chain=request.chain,
            burn_amount=amounts["burn_amount"],
            drb_swap_amount=amounts["drb_swap_amount"],
            cbbtc_swap_amount=amounts["cbbtc_swap_amount"],
            recipient_wallet=recipient_wallet
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