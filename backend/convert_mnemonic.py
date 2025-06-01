#!/usr/bin/env python3

from mnemonic import Mnemonic
from eth_account import Account
import os

def mnemonic_to_private_key(mnemonic_phrase: str, account_index: int = 0) -> str:
    """Convert mnemonic phrase to private key"""
    
    # Enable unaudited HD wallet features
    Account.enable_unaudited_hdwallet_features()
    
    # Create account from mnemonic
    account = Account.from_mnemonic(mnemonic_phrase, account_path=f"m/44'/60'/0'/0/{account_index}")
    
    return account.key.hex()

if __name__ == "__main__":
    # Your mnemonic phrase
    mnemonic = "symptom grace spider pumpkin rain pulp antenna wage kid season surround shoot"
    
    try:
        # Convert to private key (account index 0)
        private_key = mnemonic_to_private_key(mnemonic)
        
        print(f"Wallet Address: {Account.from_key(private_key).address}")
        print(f"Private Key: {private_key}")
        
    except Exception as e:
        print(f"Error: {e}")