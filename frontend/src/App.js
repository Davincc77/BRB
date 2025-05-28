import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import { ethers } from 'ethers';
import { Connection, PublicKey } from '@solana/web3.js';
import { Flame, Wallet, ArrowRight, CheckCircle, XCircle, Clock } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Chain configurations
const BASE_CHAIN_CONFIG = {
  chainId: '0x2105', // 8453 in hex
  chainName: 'Base',
  nativeCurrency: { name: 'ETH', symbol: 'ETH', decimals: 18 },
  rpcUrls: ['https://mainnet.base.org'],
  blockExplorerUrls: ['https://basescan.org/']
};

const SOLANA_RPC = 'https://api.mainnet-beta.solana.com';

function App() {
  // State management
  const [activeChain, setActiveChain] = useState('base');
  const [walletAddress, setWalletAddress] = useState('');
  const [isWalletConnected, setIsWalletConnected] = useState(false);
  const [connectedWallet, setConnectedWallet] = useState(''); // 'metamask' or 'phantom'
  const [tokenAddress, setTokenAddress] = useState('');
  const [amount, setAmount] = useState('');
  const [tokenValidation, setTokenValidation] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [transactions, setTransactions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // Check if wallet is already connected
  useEffect(() => {
    checkWalletConnection();
    fetchTransactions();
  }, []);

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  const checkWalletConnection = async () => {
    // Check MetaMask connection
    if (window.ethereum) {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_accounts' });
        if (accounts.length > 0) {
          setWalletAddress(accounts[0]);
          setIsWalletConnected(true);
          setConnectedWallet('metamask');
          return;
        }
      } catch (error) {
        console.error('Error checking MetaMask connection:', error);
      }
    }

    // Check Phantom connection  
    if (window.solana) {
      try {
        const response = await window.solana.connect({ onlyIfTrusted: true });
        setWalletAddress(response.publicKey.toString());
        setIsWalletConnected(true);
        setConnectedWallet('phantom');
      } catch (error) {
        console.error('Error checking Phantom wallet:', error);
      }
    }
  };

  const connectWallet = async (walletType) => {
    try {
      if (walletType === 'metamask') {
        if (!window.ethereum) {
          showNotification('MetaMask not detected. Please install MetaMask.', 'error');
          return;
        }

        // Request account access
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        
        // If connecting to Base chain, switch to it
        if (activeChain === 'base') {
          try {
            await window.ethereum.request({
              method: 'wallet_switchEthereumChain',
              params: [{ chainId: BASE_CHAIN_CONFIG.chainId }],
            });
          } catch (switchError) {
            // Add Base chain if it doesn't exist
            if (switchError.code === 4902) {
              await window.ethereum.request({
                method: 'wallet_addEthereumChain',
                params: [BASE_CHAIN_CONFIG],
              });
            }
          }
        }

        setWalletAddress(accounts[0]);
        setIsWalletConnected(true);
        setConnectedWallet('metamask');
        showNotification(`MetaMask connected for ${activeChain} chain!`, 'success');
        
      } else if (walletType === 'phantom') {
        if (!window.solana) {
          showNotification('Phantom wallet not detected. Please install Phantom.', 'error');
          return;
        }

        const response = await window.solana.connect();
        setWalletAddress(response.publicKey.toString());
        setIsWalletConnected(true);
        setConnectedWallet('phantom');
        showNotification(`Phantom wallet connected for ${activeChain} chain!`, 'success');
      }
    } catch (error) {
      console.error('Wallet connection error:', error);
      showNotification('Failed to connect wallet. Please try again.', 'error');
    }
  };

  const disconnectWallet = () => {
    setWalletAddress('');
    setIsWalletConnected(false);
    setConnectedWallet('');
    setTokenAddress('');
    setAmount('');
    setTokenValidation(null);
    showNotification('Wallet disconnected', 'info');
  };

  const validateToken = async (address) => {
    if (!address) {
      setTokenValidation(null);
      return;
    }

    setIsValidating(true);
    try {
      const response = await axios.post(`${API}/validate-token`, {
        token_address: address,
        chain: activeChain
      });
      setTokenValidation(response.data);
    } catch (error) {
      console.error('Token validation error:', error);
      setTokenValidation({
        is_valid: false,
        reason: 'Failed to validate token'
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleTokenAddressChange = (e) => {
    const address = e.target.value;
    setTokenAddress(address);
    
    // Debounce validation
    setTimeout(() => validateToken(address), 500);
  };

  const handleBurn = async () => {
    if (!isWalletConnected || !tokenAddress || !amount || !tokenValidation?.is_valid) {
      showNotification('Please fill all fields and ensure token is valid', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/burn`, {
        wallet_address: walletAddress,
        token_address: tokenAddress,
        amount: amount,
        chain: activeChain
      });

      showNotification('Burn transaction created! Please confirm in your wallet.', 'success');
      
      // Reset form
      setTokenAddress('');
      setAmount('');
      setTokenValidation(null);
      
      // Refresh transactions
      fetchTransactions();
      
    } catch (error) {
      console.error('Burn error:', error);
      showNotification(error.response?.data?.detail || 'Failed to create burn transaction', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API}/transactions`);
      setTransactions(response.data.slice(0, 10)); // Show last 10 transactions
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed': return <XCircle className="w-5 h-5 text-red-500" />;
      default: return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const formatAmount = (amount) => {
    return parseFloat(amount).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg ${
          notification.type === 'success' ? 'bg-green-600' : 
          notification.type === 'error' ? 'bg-red-600' : 'bg-blue-600'
        } text-white`}>
          {notification.message}
        </div>
      )}

      {/* Header */}
      <header className="p-6 border-b border-gray-700">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <Flame className="w-8 h-8 text-orange-500" />
            <h1 className="text-2xl font-bold text-white">Crypto Burn Agent</h1>
          </div>
          
          {/* Chain Selector */}
          <div className="flex items-center space-x-4">
            <div className="flex bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => setActiveChain('base')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  activeChain === 'base' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                Base
              </button>
              <button
                onClick={() => setActiveChain('solana')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  activeChain === 'solana' 
                    ? 'bg-purple-600 text-white' 
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                Solana
              </button>
            </div>

            {/* Wallet Connection */}
            {isWalletConnected ? (
              <div className="flex items-center space-x-2">
                <div className="bg-green-600 text-white px-3 py-2 rounded-lg text-sm">
                  {formatAddress(walletAddress)}
                </div>
                <button
                  onClick={disconnectWallet}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Disconnect
                </button>
              </div>
            ) : (
              <button
                onClick={connectWallet}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-2 rounded-lg flex items-center space-x-2 transition-colors"
              >
                <Wallet className="w-5 h-5" />
                <span>Connect {activeChain === 'base' ? 'MetaMask' : 'Phantom'}</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-8">
          
          {/* Burn Interface */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center">
              <Flame className="w-6 h-6 text-orange-500 mr-2" />
              Burn Tokens
            </h2>

            {!isWalletConnected ? (
              <div className="text-center py-12">
                <Wallet className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <p className="text-gray-400 mb-4">Connect your wallet to start burning tokens</p>
                <button
                  onClick={connectWallet}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-lg transition-colors"
                >
                  Connect {activeChain === 'base' ? 'MetaMask' : 'Phantom'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Token Address Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Token Contract Address
                  </label>
                  <input
                    type="text"
                    value={tokenAddress}
                    onChange={handleTokenAddressChange}
                    placeholder={`Enter ${activeChain} token address...`}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
                  />
                  
                  {/* Token Validation Status */}
                  {isValidating && (
                    <div className="mt-2 flex items-center text-yellow-500">
                      <Clock className="w-4 h-4 mr-2 animate-spin" />
                      <span className="text-sm">Validating token...</span>
                    </div>
                  )}
                  
                  {tokenValidation && (
                    <div className={`mt-2 flex items-center ${tokenValidation.is_valid ? 'text-green-500' : 'text-red-500'}`}>
                      {tokenValidation.is_valid ? 
                        <CheckCircle className="w-4 h-4 mr-2" /> : 
                        <XCircle className="w-4 h-4 mr-2" />
                      }
                      <span className="text-sm">
                        {tokenValidation.is_valid 
                          ? `Valid token: ${tokenValidation.token_symbol} (${tokenValidation.token_name})`
                          : tokenValidation.reason
                        }
                      </span>
                    </div>
                  )}
                </div>

                {/* Amount Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Amount to Burn
                  </label>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="Enter amount..."
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
                  />
                </div>

                {/* Burn Summary */}
                {amount && tokenValidation?.is_valid && (
                  <div className="bg-gray-700 rounded-lg p-4 space-y-2">
                    <h4 className="text-sm font-medium text-gray-300">Burn Summary</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">88% Burned:</span>
                        <span className="text-red-400">{formatAmount((parseFloat(amount) * 0.88).toString())}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">6% → $DRB:</span>
                        <span className="text-blue-400">{formatAmount((parseFloat(amount) * 0.06).toString())}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">6% → $cbBTC:</span>
                        <span className="text-orange-400">{formatAmount((parseFloat(amount) * 0.06).toString())}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Burn Button */}
                <button
                  onClick={handleBurn}
                  disabled={!tokenValidation?.is_valid || !amount || isLoading}
                  className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white py-3 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
                >
                  {isLoading ? (
                    <>
                      <Clock className="w-5 h-5 animate-spin" />
                      <span>Processing...</span>
                    </>
                  ) : (
                    <>
                      <Flame className="w-5 h-5" />
                      <span>Burn Tokens</span>
                      <ArrowRight className="w-5 h-5" />
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Transaction History */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-6">Recent Transactions</h2>
            
            {transactions.length === 0 ? (
              <div className="text-center py-12">
                <Clock className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <p className="text-gray-400">No transactions yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {transactions.map((tx) => (
                  <div key={tx.id} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(tx.status)}
                        <span className="text-sm font-medium text-white capitalize">
                          {tx.status}
                        </span>
                      </div>
                      <span className="text-xs text-gray-400">
                        {new Date(tx.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                    
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Wallet:</span>
                        <span className="text-white">{formatAddress(tx.wallet_address)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Amount:</span>
                        <span className="text-white">{formatAmount(tx.amount)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Chain:</span>
                        <span className="text-white capitalize">{tx.chain}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-8 bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-bold text-white mb-4">How It Works</h3>
          <div className="grid md:grid-cols-3 gap-6 text-sm">
            <div className="text-center">
              <div className="bg-red-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Flame className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-medium text-white mb-2">88% Burned</h4>
              <p className="text-gray-400">
                Tokens are sent to the burn address and permanently removed from circulation
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <ArrowRight className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-medium text-white mb-2">6% → $DRB</h4>
              <p className="text-gray-400">
                Automatically swapped to $DRB tokens via DEX
              </p>
            </div>
            <div className="text-center">
              <div className="bg-orange-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <ArrowRight className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-medium text-white mb-2">6% → $cbBTC</h4>
              <p className="text-gray-400">
                Automatically swapped to $cbBTC tokens via DEX
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;