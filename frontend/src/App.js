import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import { ethers } from 'ethers';
import { Connection, PublicKey } from '@solana/web3.js';
import { Flame, Wallet, ArrowRight, CheckCircle, XCircle, Clock, Trophy, Users, TrendingUp, Award } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Chain configurations will be fetched from backend
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
  const [availableChains, setAvailableChains] = useState({});
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
  const [burnStats, setBurnStats] = useState(null);
  const [activeTab, setActiveTab] = useState('burn'); // 'burn', 'community', 'leaderboard'
  
  // Enhanced UX state
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [burnProgress, setBurnProgress] = useState(0);
  const [recentActivity, setRecentActivity] = useState([]);
  const [tooltipVisible, setTooltipVisible] = useState('');
  const [darkMode, setDarkMode] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);

  // Check if wallet is already connected
  useEffect(() => {
    fetchAvailableChains();
    checkWalletConnection();
    fetchTransactions();
    fetchBurnStats();
  }, []);

  const fetchAvailableChains = async () => {
    try {
      const response = await axios.get(`${API}/chains`);
      setAvailableChains(response.data.chains);
    } catch (error) {
      console.error('Failed to fetch chains:', error);
    }
  };

  const fetchBurnStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setBurnStats(response.data);
    } catch (error) {
      console.error('Failed to fetch burn stats:', error);
    }
  };

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    
    // Enhanced notification with sound
    if (soundEnabled) {
      try {
        const audio = new Audio(`data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgEKH/K7tiJNgcZZ7vt559NEAxQqOPwtmMcBjiS2PLNeSsFJXfH8N2QQAoUXrTq66hVFApGn+Dws2wdCkOS2eLHfCgE=`);
        audio.volume = 0.3;
        audio.play().catch(() => {}); // Ignore errors
      } catch (error) {
        console.log('Audio notification failed');
      }
    }
    
    setTimeout(() => setNotification(null), 5000);
  };

  // Enhanced refresh function
  const refreshData = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        fetchAvailableChains(),
        fetchBurnStats(),
        fetchTransactions()
      ]);
      showNotification('Data refreshed successfully!', 'success');
    } catch (error) {
      showNotification('Failed to refresh data', 'error');
    } finally {
      setIsRefreshing(false);
    }
  };

  // Copy to clipboard function
  const copyToClipboard = async (text, label = 'Text') => {
    try {
      await navigator.clipboard.writeText(text);
      showNotification(`${label} copied to clipboard!`, 'success');
    } catch (error) {
      showNotification('Failed to copy to clipboard', 'error');
    }
  };

  // Enhanced progress tracking
  const simulateBurnProgress = () => {
    setBurnProgress(0);
    const interval = setInterval(() => {
      setBurnProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + Math.random() * 15;
      });
    }, 200);
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

  const handleChainSwitch = async (newChain) => {
    setActiveChain(newChain);
    
    // If MetaMask is connected and switching to Base, ensure correct network
    if (connectedWallet === 'metamask' && newChain === 'base' && window.ethereum) {
      try {
        await window.ethereum.request({
          method: 'wallet_switchEthereumChain',
          params: [{ chainId: BASE_CHAIN_CONFIG.chainId }],
        });
      } catch (switchError) {
        if (switchError.code === 4902) {
          await window.ethereum.request({
            method: 'wallet_addEthereumChain',
            params: [BASE_CHAIN_CONFIG],
          });
        }
      }
    }
    
    // Clear validation when switching chains
    setTokenAddress('');
    setAmount('');
    setTokenValidation(null);
    
    showNotification(`Switched to ${newChain} chain`, 'info');
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
      
      // Refresh transactions and stats
      fetchTransactions();
      fetchBurnStats();
      
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
      <header className="p-6 border-b border-gray-700 backdrop-blur-md bg-gray-900 bg-opacity-50">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-3 animate-fadeInUp">
            <div className="relative">
              <Flame className="w-8 h-8 text-orange-500 animate-pulse-soft" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-bounce-soft"></div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Crypto Burn Agent</h1>
              <p className="text-xs text-gray-400">Multi-chain token burning protocol</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Settings & Controls */}
            <div className="flex items-center space-x-2">
              <button
                onClick={refreshData}
                disabled={isRefreshing}
                className={`p-2 rounded-lg transition-all duration-300 ${
                  isRefreshing 
                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed' 
                    : 'bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white transform hover:scale-105'
                }`}
                title="Refresh data"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
              
              <button
                onClick={() => setSoundEnabled(!soundEnabled)}
                className={`p-2 rounded-lg transition-all duration-300 transform hover:scale-105 ${
                  soundEnabled 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-800 hover:bg-gray-700 text-gray-300'
                }`}
                title={soundEnabled ? 'Disable sounds' : 'Enable sounds'}
              >
                <Bell className="w-4 h-4" />
              </button>
            </div>

            {/* Chain Selector */}
            <div className="chain-selector animate-slideInRight">
              {Object.entries(availableChains).map(([chainKey, chainConfig]) => (
                <button
                  key={chainKey}
                  onClick={() => handleChainSwitch(chainKey)}
                  className={`chain-option ${
                    activeChain === chainKey ? 'chain-option-active' : 'chain-option-inactive'
                  }`}
                  title={`Switch to ${chainConfig.name}`}
                >
                  {chainConfig.name}
                </button>
              ))}
            </div>

            {/* Wallet Connection */}
            {isWalletConnected ? (
              <div className="flex items-center space-x-2 animate-slideInRight">
                <div className="glass-card px-3 py-2 text-sm flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse-soft"></div>
                  <span 
                    className="text-white cursor-pointer hover:text-green-400 transition-colors"
                    onClick={() => copyToClipboard(walletAddress, 'Wallet address')}
                    title="Click to copy address"
                  >
                    {formatAddress(walletAddress)}
                  </span>
                  <span className="text-green-200 text-xs">
                    ({connectedWallet === 'metamask' ? '🦊 MetaMask' : '👻 Phantom'})
                  </span>
                </div>
                <button
                  onClick={disconnectWallet}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-all duration-300 transform hover:scale-105"
                >
                  Disconnect
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2 animate-slideInRight">
                <button
                  onClick={() => connectWallet('metamask')}
                  className="wallet-button wallet-metamask flex items-center space-x-2"
                  title="Connect MetaMask wallet"
                >
                  <Wallet className="w-4 h-4" />
                  <span>MetaMask</span>
                </button>
                <button
                  onClick={() => connectWallet('phantom')}
                  className="wallet-button wallet-phantom flex items-center space-x-2"
                  title="Connect Phantom wallet"
                >
                  <Wallet className="w-4 h-4" />
                  <span>Phantom</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-6">
        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-gray-800 rounded-lg p-1 mb-6">
          <button
            onClick={() => setActiveTab('burn')}
            className={`flex-1 py-2 px-4 rounded-md transition-colors ${
              activeTab === 'burn' 
                ? 'bg-orange-600 text-white' 
                : 'text-gray-300 hover:text-white'
            }`}
          >
            <Flame className="w-4 h-4 inline mr-2" />
            Burn Tokens
          </button>
          <button
            onClick={() => setActiveTab('community')}
            className={`flex-1 py-2 px-4 rounded-md transition-colors ${
              activeTab === 'community' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-300 hover:text-white'
            }`}
          >
            <Users className="w-4 h-4 inline mr-2" />
            Community
          </button>
          <button
            onClick={() => setActiveTab('leaderboard')}
            className={`flex-1 py-2 px-4 rounded-md transition-colors ${
              activeTab === 'leaderboard' 
                ? 'bg-purple-600 text-white' 
                : 'text-gray-300 hover:text-white'
            }`}
          >
            <Trophy className="w-4 h-4 inline mr-2" />
            Leaderboard
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'burn' && (
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
                  <p className="text-gray-400 mb-4">Connect your wallet to start burning tokens on {activeChain}</p>
                  <p className="text-gray-500 text-sm mb-6">
                    Use either MetaMask or Phantom - both work on all chains
                  </p>
                  <div className="flex justify-center space-x-4">
                    <button
                      onClick={() => connectWallet('metamask')}
                      className="bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 text-white px-6 py-3 rounded-lg flex items-center space-x-2 transition-colors"
                    >
                      <Wallet className="w-5 h-5" />
                      <span>Connect MetaMask</span>
                    </button>
                    <button
                      onClick={() => connectWallet('phantom')}
                      className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white px-6 py-3 rounded-lg flex items-center space-x-2 transition-colors"
                    >
                      <Wallet className="w-5 h-5" />
                      <span>Connect Phantom</span>
                    </button>
                  </div>
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

                  {/* Enhanced Burn Button */}
                  <button
                    onClick={() => {
                      simulateBurnProgress();
                      handleBurn();
                    }}
                    disabled={!tokenValidation?.is_valid || !amount || isLoading}
                    className="w-full btn-danger relative overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    <div className="relative z-10 flex items-center justify-center space-x-2">
                      {isLoading ? (
                        <>
                          <Clock className="w-5 h-5 animate-spin" />
                          <span>Processing...</span>
                        </>
                      ) : (
                        <>
                          <Flame className="w-5 h-5 group-hover:animate-bounce" />
                          <span>Burn Tokens</span>
                          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </>
                      )}
                    </div>
                    {isLoading && (
                      <div className="absolute bottom-0 left-0 h-1 bg-yellow-400 transition-all duration-300" 
                           style={{width: `${burnProgress}%`}}></div>
                    )}
                  </button>

                  {/* Progress indicator */}
                  {burnProgress > 0 && burnProgress < 100 && (
                    <div className="mt-4 animate-fadeInUp">
                      <div className="flex justify-between text-sm text-gray-400 mb-2">
                        <span>Burn Progress</span>
                        <span>{Math.round(burnProgress)}%</span>
                      </div>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{width: `${burnProgress}%`}}
                        ></div>
                      </div>
                    </div>
                  )}
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
        )}

        {/* Community Tab */}
        {activeTab === 'community' && (
          <div className="grid lg:grid-cols-2 gap-8">
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h2 className="text-xl font-bold text-white mb-6 flex items-center">
                <Users className="w-6 h-6 text-blue-500 mr-2" />
                Community Stats
              </h2>
              {burnStats ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-gray-700 rounded-lg">
                      <div className="text-2xl font-bold text-white">{burnStats.total_burns}</div>
                      <div className="text-gray-400 text-sm">Total Burns</div>
                    </div>
                    <div className="text-center p-4 bg-gray-700 rounded-lg">
                      <div className="text-2xl font-bold text-white">{burnStats.total_users}</div>
                      <div className="text-gray-400 text-sm">Total Users</div>
                    </div>
                  </div>
                  <div className="text-center p-4 bg-gray-700 rounded-lg">
                    <div className="text-2xl font-bold text-red-400">{parseFloat(burnStats.total_amount_burned).toLocaleString()}</div>
                    <div className="text-gray-400 text-sm">Total Tokens Burned</div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Clock className="w-16 h-16 text-gray-500 mx-auto mb-4 animate-spin" />
                  <p className="text-gray-400">Loading community stats...</p>
                </div>
              )}
            </div>
            
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h2 className="text-xl font-bold text-white mb-6 flex items-center">
                <TrendingUp className="w-6 h-6 text-green-500 mr-2" />
                Trending Tokens
              </h2>
              {burnStats && burnStats.trending_tokens.length > 0 ? (
                <div className="space-y-3">
                  {burnStats.trending_tokens.map((token, index) => (
                    <div key={index} className="bg-gray-700 rounded-lg p-3">
                      <div className="flex justify-between items-center">
                        <span className="font-mono text-sm text-white">{formatAddress(token.token_address)}</span>
                        <span className="text-blue-400 text-sm capitalize">{token.chain}</span>
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {token.burn_count} burns • {parseFloat(token.total_burned).toLocaleString()} tokens
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Flame className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400">No trending tokens yet</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Leaderboard Tab */}
        {activeTab === 'leaderboard' && (
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center">
              <Trophy className="w-6 h-6 text-yellow-500 mr-2" />
              Top Burners
            </h2>
            {burnStats && burnStats.top_burners.length > 0 ? (
              <div className="space-y-3">
                {burnStats.top_burners.map((burner, index) => (
                  <div key={index} className="bg-gray-700 rounded-lg p-4 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        index === 0 ? 'bg-yellow-600' : index === 1 ? 'bg-gray-500' : index === 2 ? 'bg-orange-600' : 'bg-gray-600'
                      }`}>
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : index + 1}
                      </div>
                      <span className="font-mono text-white">{formatAddress(burner.wallet_address)}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-white font-medium">{parseFloat(burner.total_amount).toLocaleString()}</div>
                      <div className="text-gray-400 text-sm">{burner.total_burns} burns</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Trophy className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <p className="text-gray-400">No burners yet - be the first!</p>
              </div>
            )}
          </div>
        )}

        {/* Info Section */}
        <div className="mt-8 bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-bold text-white mb-4">How It Works</h3>
          
          {/* Token Flow Information */}
          <div className="mb-6 bg-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Token Distribution</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">88% Burned to:</span>
                <span className="text-red-400 font-mono text-xs">0x000...dEaD</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">6% $DRB + 6% $cbBTC sent to:</span>
                <span className="text-blue-400 font-mono text-xs">
                  {availableChains[activeChain] ? formatAddress(availableChains[activeChain].recipient_wallet) : 'Loading...'}
                </span>
              </div>
            </div>
          </div>

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
                Automatically swapped to $DRB tokens and sent to recipient wallet
              </p>
            </div>
            <div className="text-center">
              <div className="bg-orange-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <ArrowRight className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-medium text-white mb-2">6% → $cbBTC</h4>
              <p className="text-gray-400">
                Automatically swapped to $cbBTC tokens and sent to recipient wallet
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;