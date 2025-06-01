import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AdminProvider, useAdmin } from './contexts/AdminContext';
import { secureStorage } from './utils/secureStorage';
import AdminPanel from './components/AdminPanel';
import './App.css';
import { ethers } from 'ethers';
import { Connection, PublicKey } from '@solana/web3.js';
import { Flame, Wallet, ArrowRight, CheckCircle, XCircle, Clock, Trophy, Users, TrendingUp, Award, RefreshCw, Bell, Activity, BarChart3, Copy, Info, Star } from 'lucide-react';

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
  const [connectedWallet, setConnectedWallet] = useState(''); // 'metamask', 'phantom', or 'coinbase'
  const [showWalletMenu, setShowWalletMenu] = useState(false); // For wallet selection dropdown
  const [tokenAddress, setTokenAddress] = useState('');
  const [amount, setAmount] = useState('');
  const [tokenValidation, setTokenValidation] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [transactions, setTransactions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [notification, setNotification] = useState(null);
  const [tokenBurnability, setTokenBurnability] = useState(null); // New state for burn check
  const [burnStats, setBurnStats] = useState(null);
  const [communityStats, setCommunityStats] = useState(null);
  const [contestData, setContestData] = useState(null);
  const [activeTab, setActiveTab] = useState('burn'); // 'burn', 'community', 'leaderboard'
  const [transactionStatus, setTransactionStatus] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [projectSubmissionModal, setProjectSubmissionModal] = useState(false);
  // Admin state with secure storage
  const [adminPanelOpen, setAdminPanelOpen] = useState(false);
  const [adminToken, setAdminToken] = useState(secureStorage.getAdminToken());

  // Check for valid admin token on component mount
  useEffect(() => {
    const token = secureStorage.getAdminToken();
    if (token) {
      setAdminToken(token);
    }
  }, []);
  const [isContestMode, setIsContestMode] = useState(false);  // New state for contest mode
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    base_address: '',
    website: '',
    twitter: '',
    logo_url: ''
  });
  
  // Enhanced UX state
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Function to refresh data
  const refreshData = async () => {
    try {
      setIsRefreshing(true);
      await Promise.all([
        fetchCommunityStats(),
        fetchContestData()
      ]);
      setIsRefreshing(false);
    } catch (error) {
      console.error("Error refreshing data:", error);
      setIsRefreshing(false);
    }
  };
  
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [burnProgress, setBurnProgress] = useState(0);
  const [recentActivity, setRecentActivity] = useState([]);
  const [tooltipVisible, setTooltipVisible] = useState('');
  const [darkMode, setDarkMode] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [gasEstimates, setGasEstimates] = useState(null);
  const [swapQuotes, setSwapQuotes] = useState(null);
  const [realTimePrice, setRealTimePrice] = useState(null);
  const [crossChainMode, setCrossChainMode] = useState(false);
  const [crossChainRoute, setCrossChainRoute] = useState(null);
  const [analyzingRoute, setAnalyzingRoute] = useState(false);
  const [crossChainTransactions, setCrossChainTransactions] = useState([]);
  const [optimalRoutes, setOptimalRoutes] = useState(null);

  // Admin authentication function (simplified for demo)
  const handleAdminLogin = () => {
    const password = prompt("Enter admin password:");
    if (password === "10121277@burnreliefbot!10121277") {  // Updated admin password
      const token = "admin_token_davincc";
      
      // Use secure storage with 60-minute expiration
      if (secureStorage.setAdminToken(token, 60)) {
        setAdminToken(token);
        showNotification('Admin access granted! (60 min session)', 'success');
        setAdminPanelOpen(true);
      } else {
        showNotification('Failed to create secure session', 'error');
      }
    } else if (password) {  // Don't show error for cancelled prompt
      showNotification('Invalid admin credentials', 'error');
    }
  };

  const handleAdminLogout = () => {
    secureStorage.clearAdminToken();
    setAdminToken(null);
    setAdminPanelOpen(false);
    showNotification('Admin logged out', 'info');
  };

  // Close wallet menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showWalletMenu && !event.target.closest('.relative')) {
        setShowWalletMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showWalletMenu]);

  // Check if wallet is already connected
  useEffect(() => {
    fetchAvailableChains();
    checkWalletConnection();
    fetchTransactions();
    fetchBurnStats();
    fetchOptimalRoutes();
    fetchContestData();
    fetchCommunityStats();
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

  // Fetch community statistics
  const fetchCommunityStats = async () => {
    try {
      const response = await axios.get(`${API}/community/stats`);
      if (response.data) {
        setCommunityStats(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch community stats:', error);
    }
  };

  // Fetch contest data
  const fetchContestData = async () => {
    try {
      const response = await axios.get(`${API}/community/contest`);
      if (response.data) {
        setContestData(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch contest data:', error);
    }
  };

  // Fetch gas estimates for current chain
  const fetchGasEstimates = async (chain) => {
    try {
      const response = await axios.get(`${API}/gas-estimates/${chain}`);
      setGasEstimates(response.data);
    } catch (error) {
      console.error('Failed to fetch gas estimates:', error);
    }
  };

  // Fetch token price
  const fetchTokenPrice = async (tokenAddress, chain) => {
    try {
      const response = await axios.get(`${API}/token-price/${tokenAddress}/${chain}`);
      setRealTimePrice(response.data);
    } catch (error) {
      console.error('Failed to fetch token price:', error);
    }
  };

  // Update quotes when amount changes
  const updateSwapQuotes = async (tokenAddr, amt) => {
    if (!tokenAddr || !amt || !availableChains[activeChain]) return;
    
    try {
      const [drbQuote, bnkrQuote] = await Promise.all([
        axios.post(`${API}/swap-quote`, {
          input_token: tokenAddr,
          output_token: availableChains[activeChain]?.drb_token || '0x3ec2156D4c0A9CBdAB4a016633b7BcF6a8d68Ea2',
          amount: (parseFloat(amt) * 0.06).toString(),
          chain: activeChain
        }),
        axios.post(`${API}/swap-quote`, {
          input_token: tokenAddr,
          output_token: availableChains[activeChain]?.bnkr_token || '0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b',
          amount: (parseFloat(amt) * 0.06).toString(),
          chain: activeChain
        })
      ]);
      
      setSwapQuotes({
        drb: drbQuote.data,
        bnkr: bnkrQuote.data
      });
    } catch (error) {
      console.error('Failed to fetch swap quotes:', error);
    }
  };

  // Fetch optimal routes information
  const fetchOptimalRoutes = async () => {
    try {
      const response = await axios.get(`${API}/cross-chain/optimal-routes`);
      setOptimalRoutes(response.data);
    } catch (error) {
      console.error('Failed to fetch optimal routes:', error);
    }
  };

  // Analyze cross-chain route
  const analyzeCrossChainRoute = async (sourceChain, sourceToken, amount) => {
    if (!sourceToken || !amount) return;
    
    setAnalyzingRoute(true);
    try {
      const response = await axios.post(`${API}/cross-chain/analyze-route`, {
        source_chain: sourceChain,
        source_token: sourceToken,
        amount: amount
      });
      
      setCrossChainRoute(response.data);
      
      if (response.data.cross_chain_required) {
        showNotification(
          `Cross-chain routing required! Estimated time: ${response.data.total_estimated_time}`,
          'info'
        );
      }
    } catch (error) {
      console.error('Failed to analyze cross-chain route:', error);
      showNotification('Failed to analyze cross-chain route', 'error');
    } finally {
      setAnalyzingRoute(false);
    }
  };

  // Execute cross-chain burn
  const handleCrossChainBurn = async () => {
    if (!isWalletConnected || !tokenAddress || !amount || !tokenValidation?.is_valid) {
      showNotification('Please fill all fields and ensure token is valid', 'error');
      return;
    }

    setIsLoading(true);
    simulateBurnProgress();
    
    try {
      const response = await axios.post(`${API}/cross-chain/execute-burn`, {
        wallet_address: walletAddress,
        source_chain: activeChain,
        source_token: tokenAddress,
        amount: amount,
        approve_cross_chain: true
      });

      if (response.data.success) {
        showNotification('🌉 Cross-chain burn initiated! Multiple transactions starting...', 'success');
        
        // Show execution plan
        const plan = response.data.execution_plan;
        showNotification(
          `${plan.length} transactions created across multiple chains. Est. completion: ${response.data.estimated_completion}`,
          'info'
        );
        
        // Start monitoring cross-chain transactions
        monitorCrossChainTransaction(response.data.cross_chain_transaction_id, plan);
      } else {
        throw new Error(response.data.message || 'Cross-chain transaction failed');
      }
      
      // Reset form
      setTokenAddress('');
      setAmount('');
      setTokenValidation(null);
      setCrossChainRoute(null);
      setBurnProgress(100);
      
      // Refresh data
      setTimeout(() => {
        fetchTransactions();
        fetchBurnStats();
        setBurnProgress(0);
      }, 2000);
      
    } catch (error) {
      console.error('Cross-chain burn error:', error);
      setBurnProgress(0);
      showNotification(
        error.response?.data?.detail || error.message || 'Failed to execute cross-chain burn', 
        'error'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Monitor cross-chain transaction
  const monitorCrossChainTransaction = async (txId, executionPlan) => {
    let attempts = 0;
    const maxAttempts = 30;
    
    const checkStatus = async () => {
      try {
        const statusResponse = await axios.get(`${API}/cross-chain/transaction/${txId}`);
        const txData = statusResponse.data;
        
        showNotification(
          `Cross-chain transaction ${txData.status} - Step ${txData.current_step}/${txData.total_steps}`,
          txData.status === 'completed' ? 'success' : 'info'
        );
        
        // Monitor individual transactions
        for (const tx of executionPlan) {
          if (tx.tx_hash || tx.signature) {
            const monitorResponse = await axios.get(
              `${API}/cross-chain/monitor/${tx.tx_hash || tx.signature}/${tx.chain || activeChain}`
            );
            
            if (monitorResponse.data.status === 'confirmed') {
              showNotification(
                `✅ ${tx.type.replace('_', ' ')} confirmed on ${tx.chain || activeChain}!`,
                'success'
              );
            }
          }
        }
      } catch (error) {
        console.error('Cross-chain status check error:', error);
      }
      
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 15000); // Check every 15 seconds for cross-chain
      }
    };
    
    // Start monitoring after 5 seconds
    setTimeout(checkStatus, 5000);
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

  // Project submission function
  const submitProject = async () => {
    if (!isWalletConnected) {
      showNotification('Please connect your wallet first', 'error');
      return;
    }

    // Validate required fields
    if (!newProject.name || !newProject.description || !newProject.base_address) {
      showNotification('Please fill in all required fields (Name, Description, Base Address)', 'error');
      return;
    }

    try {
      const projectData = {
        ...newProject,
        submitted_by: walletAddress
      };

      const response = await axios.post(`${API}/community/project`, projectData);
      
      if (response.data.status === 'submitted') {
        showNotification('Project submitted successfully!', 'success');
        setProjectSubmissionModal(false);
        setNewProject({
          name: '',
          description: '',
          base_address: '',
          website: '',
          twitter: '',
          logo_url: ''
        });
        // Refresh contest data
        fetchContestData();
      }
    } catch (error) {
      console.error('Project submission error:', error);
      showNotification('Failed to submit project. Please try again.', 'error');
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
      console.log('Attempting to connect wallet:', walletType);
      setShowWalletMenu(false); // Close wallet menu
      
      if (walletType === 'metamask') {
        if (!window.ethereum) {
          console.error('MetaMask not detected');
          showNotification('MetaMask not detected. Please install MetaMask extension.', 'error');
          return;
        }

        console.log('MetaMask detected, requesting accounts...');
        // Request account access
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        console.log('Accounts received:', accounts);
        
        // If connecting to Base chain, switch to it
        if (activeChain === 'base') {
          try {
            console.log('Switching to Base chain...');
            await window.ethereum.request({
              method: 'wallet_switchEthereumChain',
              params: [{ chainId: BASE_CHAIN_CONFIG.chainId }],
            });
            console.log('Successfully switched to Base chain');
          } catch (switchError) {
            console.log('Switch error:', switchError);
            // Add Base chain if it doesn't exist
            if (switchError.code === 4902) {
              console.log('Adding Base chain...');
              await window.ethereum.request({
                method: 'wallet_addEthereumChain',
                params: [BASE_CHAIN_CONFIG],
              });
              console.log('Successfully added Base chain');
            }
          }
        }

        setWalletAddress(accounts[0]);
        setIsWalletConnected(true);
        setConnectedWallet('metamask');
        console.log('MetaMask connected successfully:', accounts[0]);
        showNotification(`MetaMask connected for ${activeChain} chain!`, 'success');
        
      } else if (walletType === 'coinbase') {
        // Check for Coinbase Wallet
        if (!window.ethereum || !window.ethereum.isCoinbaseWallet) {
          // If not detected, try to use WalletLink/Coinbase Wallet SDK
          if (!window.CoinbaseWalletSDK && !window.ethereum?.providers?.find(p => p.isCoinbaseWallet)) {
            console.error('Coinbase Wallet not detected');
            showNotification('Coinbase Wallet not detected. Please install Coinbase Wallet or use the Coinbase Wallet browser.', 'error');
            return;
          }
        }

        console.log('Coinbase Wallet detected, requesting accounts...');
        let provider = window.ethereum;
        
        // If multiple providers, find Coinbase Wallet
        if (window.ethereum.providers) {
          provider = window.ethereum.providers.find(p => p.isCoinbaseWallet) || window.ethereum;
        }

        const accounts = await provider.request({ method: 'eth_requestAccounts' });
        console.log('Coinbase accounts received:', accounts);
        
        // If connecting to Base chain, switch to it
        if (activeChain === 'base') {
          try {
            console.log('Switching to Base chain...');
            await provider.request({
              method: 'wallet_switchEthereumChain',
              params: [{ chainId: BASE_CHAIN_CONFIG.chainId }],
            });
            console.log('Successfully switched to Base chain');
          } catch (switchError) {
            console.log('Switch error:', switchError);
            // Add Base chain if it doesn't exist
            if (switchError.code === 4902) {
              console.log('Adding Base chain...');
              await provider.request({
                method: 'wallet_addEthereumChain',
                params: [BASE_CHAIN_CONFIG],
              });
              console.log('Successfully added Base chain');
            }
          }
        }

        setWalletAddress(accounts[0]);
        setIsWalletConnected(true);
        setConnectedWallet('coinbase');
        console.log('Coinbase Wallet connected successfully:', accounts[0]);
        showNotification(`Coinbase Wallet connected for ${activeChain} chain!`, 'success');
        
      } else if (walletType === 'phantom') {
        if (!window.solana) {
          console.error('Phantom wallet not detected');
          showNotification('Phantom wallet not detected. Please install Phantom.', 'error');
          return;
        }

        console.log('Phantom detected, connecting...');
        const response = await window.solana.connect();
        console.log('Phantom connected:', response.publicKey.toString());
        setWalletAddress(response.publicKey.toString());
        setIsWalletConnected(true);
        setConnectedWallet('phantom');
        showNotification(`Phantom wallet connected for ${activeChain} chain!`, 'success');
      }
    } catch (error) {
      console.error('Wallet connection error:', error);
      showNotification(`Failed to connect wallet: ${error.message}`, 'error');
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
    setSwapQuotes(null);
    setRealTimePrice(null);
    
    // Fetch gas estimates for new chain
    fetchGasEstimates(newChain);
    
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

  // Check token burnability
  const checkTokenBurnability = async (address) => {
    if (!address) {
      setTokenBurnability(null);
      return;
    }
    
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/check-burnable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token_address: address,
          chain: activeChain,
          is_contest: isContestMode  // Include contest mode
        })
      });
      
      if (response.ok) {
        const burnabilityData = await response.json();
        setTokenBurnability(burnabilityData);
      } else {
        setTokenBurnability(null);
      }
    } catch (error) {
      console.error('Failed to check token burnability:', error);
      setTokenBurnability(null);
    }
  };

  const handleTokenAddressChange = (e) => {
    const address = e.target.value;
    setTokenAddress(address);
    
    // Debounce validation and price fetching
    setTimeout(() => {
      validateToken(address);
      checkTokenBurnability(address); // Add burnability check
      if (address && amount) {
        if (crossChainMode) {
          analyzeCrossChainRoute(activeChain, address, amount);
        } else {
          updateSwapQuotes(address, amount);
        }
        fetchTokenPrice(address, activeChain);
      }
    }, 500);
  };

  const handleAmountChange = (e) => {
    const newAmount = e.target.value;
    setAmount(newAmount);
    
    // Update swap quotes or analyze cross-chain route when amount changes
    if (tokenAddress && newAmount && tokenValidation?.is_valid) {
      setTimeout(() => {
        if (crossChainMode) {
          analyzeCrossChainRoute(activeChain, tokenAddress, newAmount);
        } else {
          updateSwapQuotes(tokenAddress, newAmount);
        }
      }, 300);
    }
  };

  const handleBurn = async () => {
    if (!isWalletConnected || !tokenAddress || !amount || !tokenValidation?.is_valid) {
      showNotification('Please fill all fields and ensure token is valid', 'error');
      return;
    }

    setIsLoading(true);
    simulateBurnProgress();
    
    try {
      // First get swap quotes for transparency
      const [drbQuote, bnkrQuote] = await Promise.all([
        axios.post(`${API}/swap-quote`, {
          input_token: tokenAddress,
          output_token: availableChains[activeChain]?.drb_token || '0x3ec2156D4c0A9CBdAB4a016633b7BcF6a8d68Ea2',
          amount: (parseFloat(amount) * 0.06).toString(),
          chain: activeChain
        }),
        axios.post(`${API}/swap-quote`, {
          input_token: tokenAddress,
          output_token: availableChains[activeChain]?.bnkr_token || '0x22aF33FE49fD1Fa80c7149773dDe5890D3c76F3b',
          amount: (parseFloat(amount) * 0.06).toString(),
          chain: activeChain
        })
      ]);

      // Show quotes to user
      showNotification(
        `Swap rates: 6% → ${parseFloat(drbQuote.data.output_amount).toFixed(2)} $DRB, 6% → ${parseFloat(bnkrQuote.data.output_amount).toFixed(2)} $BNKR`,
        'info'
      );

      // Execute real blockchain transaction
      const response = await axios.post(`${API}/execute-burn`, {
        wallet_address: walletAddress,
        token_address: tokenAddress,
        amount: amount,
        chain: activeChain
      });

      if (response.data.success) {
        showNotification('🔥 Burn transaction initiated! Check your wallet for confirmations.', 'success');
        
        // Show transaction details
        const result = response.data.blockchain_result;
        showNotification(
          `${result.transactions.length} transactions created. Estimated completion: ${result.estimated_completion}`,
          'info'
        );
        
        // Start monitoring transaction status
        monitorTransactionStatus(response.data.burn_transaction_id, result.transactions);
      } else {
        throw new Error(response.data.message || 'Transaction failed');
      }
      
      // Reset form
      setTokenAddress('');
      setAmount('');
      setTokenValidation(null);
      setBurnProgress(100);
      
      // Refresh data
      setTimeout(() => {
        fetchTransactions();
        fetchBurnStats();
        setBurnProgress(0);
      }, 2000);
      
    } catch (error) {
      console.error('Burn error:', error);
      setBurnProgress(0);
      showNotification(
        error.response?.data?.detail || error.message || 'Failed to execute burn transaction', 
        'error'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Monitor transaction status
  const monitorTransactionStatus = async (burnTxId, transactions) => {
    let attempts = 0;
    const maxAttempts = 20;
    
    const checkStatus = async () => {
      try {
        for (const tx of transactions) {
          const statusResponse = await axios.get(
            `${API}/transaction-status/${tx.hash || tx.signature}/${activeChain}`
          );
          
          if (statusResponse.data.status === 'confirmed') {
            showNotification(
              `✅ ${tx.type.replace('_', ' ')} transaction confirmed!`,
              'success'
            );
          }
        }
      } catch (error) {
        console.error('Status check error:', error);
      }
      
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 10000); // Check every 10 seconds
      }
    };
    
    // Start monitoring after 5 seconds
    setTimeout(checkStatus, 5000);
  };

  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API}/transactions`);
      setTransactions(response.data.transactions?.slice(0, 10) || []); // Show last 10 transactions
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
    <div className="min-h-screen bg-gray-900 text-white relative overflow-hidden">
      {/* Retro TV Floating Icons */}
      <div className="retro-tv-icon retro-tv-smiley">
        <div style={{
          width: '60px',
          height: '45px',
          background: 'linear-gradient(135deg, #8B7355, #A0845C)',
          borderRadius: '8px',
          border: '2px solid #5D4E42',
          position: 'relative',
          boxShadow: '0 4px 8px rgba(0, 0, 0, 0.3)'
        }}>
          {/* Screen */}
          <div style={{
            position: 'absolute',
            top: '6px',
            left: '6px',
            width: '35px',
            height: '25px',
            background: '#E67E22',
            borderRadius: '4px',
            border: '1px solid #D35400',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '8px',
            color: '#F39C12'
          }}>
            😊
          </div>
          {/* Controls */}
          <div style={{
            position: 'absolute',
            right: '4px',
            top: '8px',
            width: '8px',
            height: '20px',
            background: '#34495E',
            borderRadius: '2px'
          }}>
            <div style={{
              width: '6px',
              height: '2px',
              background: '#E74C3C',
              margin: '2px 1px',
              borderRadius: '1px'
            }}></div>
            <div style={{
              width: '6px',
              height: '2px',
              background: '#27AE60',
              margin: '2px 1px',
              borderRadius: '1px'
            }}></div>
          </div>
          {/* Bottom buttons */}
          <div style={{
            position: 'absolute',
            bottom: '4px',
            left: '8px',
            display: 'flex',
            gap: '2px'
          }}>
            <div style={{ width: '4px', height: '3px', background: '#E67E22', borderRadius: '1px' }}></div>
            <div style={{ width: '4px', height: '3px', background: '#E67E22', borderRadius: '1px' }}></div>
          </div>
        </div>
      </div>

      <div className="retro-tv-icon retro-tv-drb">
        <div style={{
          width: '60px',
          height: '45px',
          background: 'linear-gradient(135deg, #BDC3C7, #95A5A6)',
          borderRadius: '8px',
          border: '2px solid #7F8C8D',
          position: 'relative',
          boxShadow: '0 4px 8px rgba(0, 0, 0, 0.3)'
        }}>
          {/* Screen */}
          <div style={{
            position: 'absolute',
            top: '6px',
            left: '6px',
            width: '35px',
            height: '25px',
            background: '#2C3E50',
            borderRadius: '4px',
            border: '1px solid #34495E',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column'
          }}>
            {/* Lightning bolt */}
            <div style={{
              fontSize: '8px',
              color: '#F39C12',
              fontWeight: 'bold',
              lineHeight: '8px'
            }}>⚡</div>
            <div style={{
              fontSize: '6px',
              color: '#ECF0F1',
              fontWeight: 'bold',
              marginTop: '1px'
            }}>DRB</div>
          </div>
          {/* Controls */}
          <div style={{
            position: 'absolute',
            right: '4px',
            top: '8px',
            width: '8px',
            height: '20px',
            background: '#34495E',
            borderRadius: '2px'
          }}>
            <div style={{
              width: '6px',
              height: '2px',
              background: '#3498DB',
              margin: '2px 1px',
              borderRadius: '1px'
            }}></div>
            <div style={{
              width: '6px',
              height: '2px',
              background: '#3498DB',
              margin: '2px 1px',
              borderRadius: '1px'
            }}></div>
          </div>
          {/* Bottom buttons */}
          <div style={{
            position: 'absolute',
            bottom: '4px',
            left: '8px',
            display: 'flex',
            gap: '2px'
          }}>
            <div style={{ width: '4px', height: '3px', background: '#E67E22', borderRadius: '1px' }}></div>
            <div style={{ width: '4px', height: '3px', background: '#E74C3C', borderRadius: '1px' }}></div>
          </div>
        </div>
      </div>
      {/* Retro TV decorative elements */}
      <div className="retro-tv retro-tv-1">
        <div style={{
          width: '120px',
          height: '90px',
          background: 'linear-gradient(135deg, #2a3441, #1e293b)',
          borderRadius: '8px',
          border: '2px solid rgba(184, 212, 227, 0.1)',
          padding: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '8px',
          color: 'rgba(184, 212, 227, 0.5)'
        }}>
          📺 DRB
        </div>
      </div>
      
      <div className="retro-tv retro-tv-2">
        <div style={{
          width: '140px',
          height: '105px',
          background: 'linear-gradient(135deg, #1e3a8a, #2563eb)',
          borderRadius: '8px',
          border: '2px solid rgba(184, 212, 227, 0.1)',
          padding: '10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '10px',
          color: 'rgba(184, 212, 227, 0.6)'
        }}>
          🔥 BURN
        </div>
      </div>
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
      <header className="nav-header p-6 border-b border-gray-700 backdrop-blur-md">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-3 animate-fadeInUp">
            <div className="relative">
              <Flame className="w-8 h-8 text-blue-500 animate-pulse-soft" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-bounce-soft"></div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Burn Relief Bot</h1>
              <p className="text-xs text-gray-400">Based burning protocol !</p>
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
                    : 'silver-glass text-gray-300 hover:text-white transform hover:scale-105'
                }`}
                title="Refresh data"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
              
              <button
                onClick={() => setSoundEnabled(!soundEnabled)}
                className={`p-2 rounded-lg transition-all duration-300 transform hover:scale-105 ${
                  soundEnabled 
                    ? 'btn-primary' 
                    : 'silver-glass text-gray-300'
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
                  className={`nav-link chain-option ${
                    activeChain === chainKey ? 'chain-option-active active' : 'chain-option-inactive'
                  }`}
                  title={`Switch to ${chainConfig.name}`}
                >
                  {chainConfig.name}
                </button>
              ))}
            </div>

            {/* Wallet Connection */}
          <div className="flex items-center gap-4">
            {/* Wallet Connection */}
            {isWalletConnected ? (
              <div className="flex items-center gap-3">
                <span className="text-green-400 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Connected: {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}
                </span>
                <button 
                  onClick={disconnectWallet} 
                  className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Disconnect
                </button>
              </div>
            ) : (
              <div className="relative">
                <button 
                  onClick={() => setShowWalletMenu(!showWalletMenu)}
                  className="btn-primary flex items-center gap-2"
                >
                  <Wallet className="w-4 h-4" />
                  Connect Wallet
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
            )}
          </div>
          </div>
        </div>

        {/* Admin Access - Centered under DRB allocation */}
        <div className="flex justify-center mt-8 mb-8">
          {adminToken ? (
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setAdminPanelOpen(true)}
                className="px-4 py-2 bg-purple-600/80 text-white rounded-lg text-sm hover:bg-purple-700/90 backdrop-blur-sm shadow-lg transition-all"
                title="Admin Panel"
              >
                ⚙️ Admin Panel
              </button>
              <button 
                onClick={handleAdminLogout}
                className="px-4 py-2 bg-gray-600/80 text-white rounded-lg text-sm hover:bg-gray-700/90 backdrop-blur-sm shadow-lg transition-all"
                title="Admin Logout"
              >
                🚪 Logout
              </button>
            </div>
          ) : (
            <button 
              onClick={handleAdminLogin}
              className="px-4 py-2 bg-purple-600/50 text-white rounded-lg text-sm hover:bg-purple-700/80 backdrop-blur-sm shadow-lg opacity-60 hover:opacity-100 transition-all"
              title="Admin Access"
            >
              ⚙️ Admin Access
            </button>
          )}
        </div>
          {adminToken ? (
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setAdminPanelOpen(true)}
                className="px-4 py-2 bg-purple-600/80 text-white rounded-lg text-sm hover:bg-purple-700/90 backdrop-blur-sm shadow-lg transition-all"
                title="Admin Panel"
              >
                ⚙️ Admin Panel
              </button>
              <button 
                onClick={handleAdminLogout}
                className="px-4 py-2 bg-gray-600/80 text-white rounded-lg text-sm hover:bg-gray-700/90 backdrop-blur-sm shadow-lg transition-all"
                title="Admin Logout"
              >
                🚪 Logout
              </button>
            </div>
          ) : (
            <button 
              onClick={handleAdminLogin}
              className="px-4 py-2 bg-purple-600/50 text-white rounded-lg text-sm hover:bg-purple-700/80 backdrop-blur-sm shadow-lg opacity-60 hover:opacity-100 transition-all"
              title="Admin Access"
            >
              ⚙️ Admin Access
            </button>
          )}
        </div>

        {/* Wallet Selection Modal Overlay */}
        {showWalletMenu && (
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setAdminPanelOpen(true)}
                className="px-4 py-2 bg-purple-600/80 text-white rounded-lg text-sm hover:bg-purple-700/90 backdrop-blur-sm shadow-lg transition-all"
                title="Admin Panel"
              >
                ⚙️ Admin Panel
              </button>
              <button 
                onClick={handleAdminLogout}
                className="px-4 py-2 bg-gray-600/80 text-white rounded-lg text-sm hover:bg-gray-700/90 backdrop-blur-sm shadow-lg transition-all"
                title="Admin Logout"
              >
                🚪 Logout
              </button>
            </div>
          ) : (
            <button 
              onClick={handleAdminLogin}
              className="px-4 py-2 bg-purple-600/50 text-white rounded-lg text-sm hover:bg-purple-700/80 backdrop-blur-sm shadow-lg opacity-60 hover:opacity-100 transition-all"
              title="Admin Access"
            >
              ⚙️ Admin Access
            </button>
          )}
        </div>
      </header>

      {/* Wallet Selection Modal Overlay */}
      {showWalletMenu && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center" style={{ zIndex: 999999 }}>
          <div className="bg-gray-900 border-2 border-gray-600 rounded-lg shadow-2xl p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white">Connect Your Wallet</h3>
              <button 
                onClick={() => setShowWalletMenu(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-3">
              {/* Coinbase Wallet */}
              <button
                onClick={() => connectWallet('coinbase')}
                className="w-full flex items-center gap-4 p-4 rounded-lg hover:bg-gray-700 transition-colors text-left border-2 border-transparent hover:border-blue-500"
              >
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-bold">CB</span>
                </div>
                <div className="flex-1">
                  <div className="text-white font-medium">Coinbase Wallet</div>
                  <div className="text-sm text-gray-400">Your keys, your crypto</div>
                </div>
                <div className="text-gray-400">→</div>
              </button>
              
              {/* MetaMask */}
              <button
                onClick={() => connectWallet('metamask')}
                className="w-full flex items-center gap-4 p-4 rounded-lg hover:bg-gray-700 transition-colors text-left border-2 border-transparent hover:border-orange-500"
              >
                <div className="w-12 h-12 bg-orange-500 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-bold">MM</span>
                </div>
                <div className="flex-1">
                  <div className="text-white font-medium">MetaMask</div>
                  <div className="text-sm text-gray-400">Browser extension wallet</div>
                </div>
                <div className="text-gray-400">→</div>
              </button>
              
              {/* Phantom Wallet */}
              <button
                onClick={() => connectWallet('phantom')}
                className="w-full flex items-center gap-4 p-4 rounded-lg hover:bg-gray-700 transition-colors text-left border-2 border-transparent hover:border-purple-500"
              >
                <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-bold">PH</span>
                </div>
                <div className="flex-1">
                  <div className="text-white font-medium">Phantom</div>
                  <div className="text-sm text-gray-400">Solana & Ethereum wallet</div>
                </div>
                <div className="text-gray-400">→</div>
              </button>
            </div>
            
            <div className="mt-6 text-center">
              <p className="text-xs text-gray-500">
                Don't have a wallet? Install one of the above to get started.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-6">
        {/* Tab Navigation */}
        <div className="flex space-x-1 silver-glass rounded-lg p-1 mb-6">
          <button
            onClick={() => setActiveTab('burn')}
            className={`nav-link flex-1 py-2 px-4 rounded-md transition-colors ${
              activeTab === 'burn' 
                ? 'bg-orange-600 text-white active' 
                : 'text-gray-300 hover:text-white'
            }`}
          >
            <Flame className="w-4 h-4 inline mr-2" />
            Burn Tokens
          </button>
          <button
            onClick={() => setActiveTab('community')}
            className={`nav-link flex-1 py-2 px-4 rounded-md transition-colors ${
              activeTab === 'community' 
                ? 'bg-blue-600 text-white active' 
                : 'text-gray-300 hover:text-white'
            }`}
          >
            <Users className="w-4 h-4 inline mr-2" />
            Community Contest
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'burn' && (
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Burn Interface */}
            <div className="card silverish-gradient">
              <h2 className="text-xl font-bold text-white mb-6 flex items-center">
                <Flame className="w-6 h-6 text-orange-500 mr-2" />
                Burn Tokens
              </h2>

              {!isWalletConnected ? (
                <div className="text-center py-12">
                  <Wallet className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400 mb-4">Connect your wallet to start burning tokens on {availableChains[activeChain]?.name || activeChain}</p>
                  <p className="text-gray-500 text-sm mb-6">
                    Burn Relief Bot supports both MetaMask and Phantom across all chains
                  </p>
                  
                  {/* Cross-chain Bridge Recommendation */}
                  <div className="silver-glass border border-blue-500 rounded-lg p-4 mb-6">
                    <div className="flex items-center justify-center mb-2">
                      <Info className="w-4 h-4 text-blue-400 mr-2" />
                      <span className="text-blue-400 text-sm font-medium">Cross-Chain Tip</span>
                    </div>
                    <p className="text-blue-300 text-xs">
                      For tokens on other chains, bridge to {activeChain} first for optimal $DRB and $BNKR swaps
                    </p>
                  </div>
                  <div className="flex justify-center space-x-4">
                    <button
                      onClick={() => connectWallet('coinbase')}
                      className="wallet-btn bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-6 py-3 rounded-lg flex items-center space-x-2 transition-colors"
                    >
                      <Wallet className="w-5 h-5" />
                      <span>Coinbase Wallet</span>
                    </button>
                    <button
                      onClick={() => connectWallet('metamask')}
                      className="wallet-btn bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 text-white px-6 py-3 rounded-lg flex items-center space-x-2 transition-colors"
                    >
                      <Wallet className="w-5 h-5" />
                      <span>MetaMask</span>
                    </button>
                    <button
                      onClick={() => connectWallet('phantom')}
                      className="wallet-btn bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white px-6 py-3 rounded-lg flex items-center space-x-2 transition-colors"
                    >
                      <Wallet className="w-5 h-5" />
                      <span>Phantom</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Cross-Chain Mode Toggle */}
                  <div className="silver-glass rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-white font-medium">🌉 Cross-Chain Mode</h4>
                        <p className="text-purple-100 text-sm">Auto-route to optimal chains for best $DRB & $BNKR liquidity</p>
                      </div>
                      <button
                        onClick={() => setCrossChainMode(!crossChainMode)}
                        className={`w-12 h-6 rounded-full transition-colors ${
                          crossChainMode ? 'bg-green-500' : 'bg-gray-400'
                        } relative`}
                      >
                        <div className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${
                          crossChainMode ? 'translate-x-7' : 'translate-x-1'
                        }`}></div>
                      </button>
                    </div>
                    {crossChainMode && optimalRoutes && (
                      <div className="mt-3 bg-black bg-opacity-30 rounded p-3 text-xs">
                        <p className="text-blue-200">
                          🎯 Optimal: $DRB on {optimalRoutes.optimal_chains.DRB}, $BNKR on {optimalRoutes.optimal_chains.BNKR}
                        </p>
                      </div>
                    )}
                  </div>
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
                      className="input-primary"
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

                  {/* Contest Mode Toggle */}
                  {adminToken && (
                    <div className="mb-4">
                      <div className="flex items-center justify-between p-4 bg-purple-800/20 rounded-lg border border-purple-600/30">
                        <div>
                          <label className="block text-sm font-medium text-purple-300 mb-1">
                            Contest Mode
                          </label>
                          <p className="text-xs text-purple-400">
                            {isContestMode ? 
                              "88% burn + 12% community pool (simplified)" : 
                              "Standard allocation (88% burn + multiple distributions)"
                            }
                          </p>
                        </div>
                        <button
                          onClick={() => {
                            setIsContestMode(!isContestMode);
                            if (tokenAddress) {
                              checkTokenBurnability(tokenAddress); // Re-validate with new mode
                            }
                          }}
                          className={`w-12 h-6 rounded-full transition-colors relative ${
                            isContestMode ? 'bg-purple-600' : 'bg-gray-600'
                          }`}
                        >
                          <div
                            className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${
                              isContestMode ? 'translate-x-6' : 'translate-x-0.5'
                            }`}
                          />
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Amount Input */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Amount to Burn
                    </label>
                    <input
                      type="number"
                      value={amount}
                      onChange={handleAmountChange}
                      placeholder="Enter amount..."
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
                    />
                  </div>

                  {/* Cross-Chain Route Display */}
                  {crossChainMode && crossChainRoute && amount && tokenValidation?.is_valid && (
                    <div className="bg-purple-600 bg-opacity-20 border border-purple-500 rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-purple-300 font-medium flex items-center">
                          {analyzingRoute ? (
                            <>
                              <Clock className="w-4 h-4 mr-2 animate-spin" />
                              Analyzing Route...
                            </>
                          ) : (
                            <>
                              🌉 Cross-Chain Route
                              {crossChainRoute.cross_chain_required && (
                                <span className="ml-2 bg-yellow-500 text-yellow-900 px-2 py-1 rounded text-xs">
                                  Multi-Chain
                                </span>
                              )}
                            </>
                          )}
                        </h4>
                        <div className="text-right text-xs">
                          <div className="text-purple-300">Est. Time: {crossChainRoute.total_estimated_time}</div>
                          <div className="text-purple-400">Est. Cost: {crossChainRoute.total_estimated_cost}</div>
                        </div>
                      </div>
                      
                      {!analyzingRoute && crossChainRoute.routes && (
                        <div className="space-y-2">
                          {crossChainRoute.routes.map((route, index) => (
                            <div key={index} className="bg-purple-700 bg-opacity-30 rounded p-2 text-xs">
                              <div className="flex items-center justify-between">
                                <span className="text-purple-200">
                                  Step {route.step}: {route.type.replace(/_/g, ' ')}
                                </span>
                                <span className="text-purple-300">
                                  {route.source_chain} {route.target_chain !== route.source_chain ? `→ ${route.target_chain}` : ''}
                                </span>
                              </div>
                              <div className="text-purple-400 mt-1">
                                Amount: {formatAmount(route.amount)} • {route.estimated_time}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Regular Burn Summary */}
                  {!crossChainMode && amount && tokenValidation?.is_valid && (
                    <div className="silver-glass rounded-lg p-4 space-y-2">
                      <h4 className="text-sm font-medium text-gray-300 flex items-center">
                        Allocation Preview
                        {tokenBurnability && (
                          <span className={`ml-2 px-2 py-1 rounded text-xs ${
                            tokenBurnability.is_drb
                              ? 'bg-blue-500 bg-opacity-20 text-blue-300'
                              : tokenBurnability.is_burnable 
                                ? 'bg-red-500 bg-opacity-20 text-red-300' 
                                : 'bg-purple-500 bg-opacity-20 text-purple-300'
                          }`}>
                            {tokenBurnability.is_drb ? 'DRB DIRECT' : (tokenBurnability.is_burnable ? 'BURNABLE' : 'SWAP ONLY')}
                          </span>
                        )}
                      </h4>
                      <div className="space-y-1 text-sm">
                        {tokenBurnability?.is_drb ? (
                          // DRB token allocations (direct allocation with minimal swapping)
                          <>
                            <div className="flex justify-between">
                              <span className="text-gray-400">0% Burned:</span>
                              <span className="text-blue-500">DRB Direct Allocation</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">95% → DRB (Grok):</span>
                              <span className="text-blue-400">{formatAmount((parseFloat(amount) * 0.95).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">1.5% → DRB (Community):</span>
                              <span className="text-blue-300">{formatAmount((parseFloat(amount) * 0.015).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">0.5% → DRB (Team):</span>
                              <span className="text-blue-300">{formatAmount((parseFloat(amount) * 0.005).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">1.5% DRB→BNKR (BANKR Club):</span>
                              <span className="bnkr-highlight">{formatAmount((parseFloat(amount) * 0.015).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">0.5% DRB→BNKR (Team):</span>
                              <span className="bnkr-highlight">{formatAmount((parseFloat(amount) * 0.005).toString())}</span>
                            </div>
                          </>
                        ) : tokenBurnability?.allocation_preview?.allocation_type === 'contest' ? (
                          // Contest allocations (simplified)
                          <>
                            <div className="mb-2 p-2 bg-purple-800/20 rounded border border-purple-600/30">
                              <span className="text-purple-300 text-sm font-medium">🏆 Contest Mode - Simplified Allocation</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">88% Burned:</span>
                              <span className="text-red-400">{formatAmount((parseFloat(amount) * 0.88).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">12% → Community Pool:</span>
                              <span className="text-green-400">{formatAmount((parseFloat(amount) * 0.12).toString())}</span>
                            </div>
                            <div className="mt-2 p-2 bg-green-800/20 rounded">
                              <span className="text-green-300 text-xs">✅ Simplified contest allocation - No complex distributions</span>
                            </div>
                          </>
                        ) : tokenBurnability?.is_burnable ? (
                          // Burnable token allocations
                          <>
                            <div className="flex justify-between">
                              <span className="text-gray-400">88% Burned:</span>
                              <span className="text-red-400">{formatAmount((parseFloat(amount) * 0.88).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">8% → $DRB (Grok):</span>
                              <span className="text-blue-400">{formatAmount((parseFloat(amount) * 0.08).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">1.5% → $DRB (Community):</span>
                              <span className="text-blue-300">{formatAmount((parseFloat(amount) * 0.015).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">0.5% → $DRB (Team):</span>
                              <span className="text-blue-300">{formatAmount((parseFloat(amount) * 0.005).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">1.5% → $BNKR (BANKR Club):</span>
                              <span className="bnkr-highlight">{formatAmount((parseFloat(amount) * 0.015).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">0.5% → $BNKR (Team):</span>
                              <span className="bnkr-highlight">{formatAmount((parseFloat(amount) * 0.005).toString())}</span>
                            </div>
                          </>
                        ) : (
                          // Non-burnable token allocations (no burning)
                          <>
                            <div className="flex justify-between">
                              <span className="text-gray-400">0% Burned:</span>
                              <span className="text-gray-500">Protected Token</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">96% → $DRB (Grok):</span>
                              <span className="text-blue-400">{formatAmount((parseFloat(amount) * 0.96).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">1.5% → $DRB (Community):</span>
                              <span className="text-blue-300">{formatAmount((parseFloat(amount) * 0.015).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">0.5% → $DRB (Team):</span>
                              <span className="text-blue-300">{formatAmount((parseFloat(amount) * 0.005).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">1.5% → $BNKR (BANKR Club):</span>
                              <span className="bnkr-highlight">{formatAmount((parseFloat(amount) * 0.015).toString())}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-400">0.5% → $BNKR (Team):</span>
                              <span className="bnkr-highlight">{formatAmount((parseFloat(amount) * 0.005).toString())}</span>
                            </div>
                          </>
                        )}
                      </div>
                      {tokenBurnability && (
                        <div className="mt-3 text-xs text-gray-400 bg-black bg-opacity-30 rounded p-2">
                          💡 {tokenBurnability.message}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Enhanced Burn Button */}
                  <button
                    onClick={() => {
                      simulateBurnProgress();
                      if (crossChainMode) {
                        handleCrossChainBurn();
                      } else {
                        handleBurn();
                      }
                    }}
                    disabled={!tokenValidation?.is_valid || !amount || isLoading}
                    className="w-full btn-danger relative overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    <div className="relative z-10 flex items-center justify-center space-x-2">
                      {isLoading ? (
                        <>
                          <Clock className="w-5 h-5 animate-spin" />
                          <span>{crossChainMode ? 'Processing Cross-Chain...' : 'Processing...'}</span>
                        </>
                      ) : (
                        <>
                          <Flame className="w-5 h-5 group-hover:animate-bounce" />
                          <span>{crossChainMode ? 'Cross-Chain Burn' : 'Burn Tokens'}</span>
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
                      <div className="progress-container">
                        <div 
                          className="progress-bar" 
                          style={{width: `${burnProgress}%`}}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Transaction History */}
            <div className="card silverish-gradient">
              <h2 className="text-xl font-bold text-white mb-6">Recent Transactions</h2>
              
              {transactions.length === 0 ? (
                <div className="text-center py-12">
                  <Clock className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400">No transactions yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {transactions.map((tx) => (
                    <div key={tx.id} className="silver-glass rounded-lg p-4">
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

        {/* Community Contest Tab */}
        {activeTab === 'community' && (
          <div className="space-y-6">
            {/* Contest Header */}
            <div className="card silverish-gradient text-center">
              <h2 className="text-2xl font-bold text-white mb-4">🏆 Community Contest</h2>
              <p className="text-gray-300 mb-6">
                Vote for Base ecosystem projects so the team of the featured project receives the allocation!
                <br/>Burn <span className="bnkr-highlight">1000 $DRB</span> or <span className="bnkr-highlight">100 $BNKR</span> to cast your vote.
                <br/><span className="text-lg font-semibold text-yellow-400">+ 0.5% $DRB + 0.5% $BNKR from normal burn</span>
              </p>
              
              {/* Contest Info */}
              <div className="grid md:grid-cols-3 gap-4 mb-6">
                <div className="silver-glass rounded-lg p-4">
                  <div className="text-2xl font-bold text-blue-400">0.5%</div>
                  <div className="text-gray-400">$DRB Allocation</div>
                </div>
                <div className="silver-glass rounded-lg p-4">
                  <div className="text-2xl font-bold text-purple-400">0.5%</div>
                  <div className="text-gray-400">$BNKR Allocation</div>
                </div>
                <div className="silver-glass rounded-lg p-4">
                  <div className="text-2xl font-bold text-green-400">
                    {contestData?.projects?.length || 0}
                  </div>
                  <div className="text-gray-400">Active Projects</div>
                </div>
              </div>
            </div>

            {/* Contest Burn Allocation */}
            <div className="card silverish-gradient">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                <Star className="w-6 h-6 text-yellow-500 mr-2" />
                Contest Token Allocation
              </h3>
              <div className="bg-purple-900/20 border border-purple-600/30 rounded-lg p-6">
                <div className="text-center mb-6">
                  <h4 className="text-lg font-bold text-purple-300 mb-2">
                    🏆 Simplified Contest Allocation
                  </h4>
                  <p className="text-gray-300 text-sm">
                    When tokens are burned for contest voting, they follow a simplified allocation:
                  </p>
                </div>
                
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Burn Allocation */}
                  <div className="flex items-center justify-between p-4 bg-red-900/20 border border-red-600/30 rounded-lg">
                    <div className="flex items-center">
                      <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center mr-4">
                        <span className="text-white font-bold text-lg">🔥</span>
                      </div>
                      <div>
                        <div className="text-red-300 font-semibold">Burned Forever</div>
                        <div className="text-gray-400 text-sm">Permanently destroyed</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-red-400">88%</div>
                    </div>
                  </div>

                  {/* Community Pool */}
                  <div className="flex items-center justify-between p-4 bg-green-900/20 border border-green-600/30 rounded-lg">
                    <div className="flex items-center">
                      <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mr-4">
                        <span className="text-white font-bold text-lg">🏆</span>
                      </div>
                      <div>
                        <div className="text-green-300 font-semibold">Community Pool</div>
                        <div className="text-gray-400 text-sm">Winning project team</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-green-400">12%</div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-blue-900/20 border border-blue-600/30 rounded-lg">
                  <div className="flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-blue-300 font-semibold mb-1">💡 How It Works</div>
                      <p className="text-gray-400 text-sm">
                        Contest burns use a simplified allocation: <span className="text-yellow-400">88% burned</span> for deflation + 
                        <span className="text-green-400"> 12% to community pool</span> for winning projects
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-4 text-center">
                  <div className="text-xs text-gray-500">
                    * Different from standard burns which have multiple allocations (Grok, Team, etc.)
                  </div>
                </div>
              </div>
            </div>

            {/* Allocation Comparison */}
            <div className="card silverish-gradient">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                <BarChart3 className="w-6 h-6 text-yellow-500 mr-2" />
                Standard vs Contest Allocations
              </h3>
              
              <div className="grid md:grid-cols-2 gap-6">
                {/* Standard Allocation */}
                <div className="bg-gray-900/20 border border-gray-600/30 rounded-lg p-4">
                  <h4 className="text-lg font-bold text-gray-300 mb-4 text-center">
                    🔄 Standard Burns
                  </h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-400">88% Burned</span>
                      <span className="text-red-400">🔥</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">8% Grok</span>
                      <span className="text-blue-400">🤖</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">1.5% Community</span>
                      <span className="text-green-400">👥</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">0.5% Team</span>
                      <span className="text-purple-400">👨‍💻</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">2% BNKR</span>
                      <span className="text-yellow-400">🏛️</span>
                    </div>
                  </div>
                  <div className="mt-3 text-xs text-gray-500 text-center">
                    Complex multi-recipient system
                  </div>
                </div>

                {/* Contest Allocation */}
                <div className="bg-purple-900/20 border border-purple-600/30 rounded-lg p-4">
                  <h4 className="text-lg font-bold text-purple-300 mb-4 text-center">
                    🏆 Contest Burns
                  </h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-400">88% Burned</span>
                      <span className="text-red-400">🔥</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">12% Community Pool</span>
                      <span className="text-green-400">🏆</span>
                    </div>
                    <div className="text-center py-4">
                      <span className="text-gray-500 text-sm">
                        All other allocations: 0%
                      </span>
                    </div>
                  </div>
                  <div className="mt-3 text-xs text-purple-400 text-center">
                    Simplified contest-focused system
                  </div>
                </div>
              </div>

              <div className="mt-6 p-4 bg-yellow-900/20 border border-yellow-600/30 rounded-lg">
                <div className="text-center">
                  <div className="text-yellow-300 font-semibold mb-2">🎯 Contest Benefits</div>
                  <p className="text-gray-400 text-sm">
                    Contest allocation puts <span className="text-green-400">more rewards directly to winning projects</span> (12% vs 1.5%), 
                    while maintaining the same <span className="text-red-400">88% burn rate</span> for token deflation.
                  </p>
                </div>
              </div>
            </div>

            {/* Current Winner */}
            {contestData?.current_winner && (
              <div className="card silverish-gradient">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                  <Trophy className="w-6 h-6 text-yellow-500 mr-2" />
                  Current Winner
                </h3>
                <div className="silver-glass rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h4 className="text-lg font-bold text-white">{contestData.current_winner.name}</h4>
                      <p className="text-gray-400">{contestData.current_winner.description}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-yellow-400 font-bold">{contestData.current_winner.total_votes} votes</div>
                      <div className="text-gray-400 text-sm">Receiving community allocation</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Project List */}
            <div className="card silverish-gradient">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-white">Active Projects</h3>
                <button 
                  className="btn-primary"
                  onClick={() => setProjectSubmissionModal(true)}
                >
                  + Submit Project
                </button>
              </div>

              {contestData?.projects && contestData.projects.length > 0 ? (
                <div className="space-y-4">
                  {contestData.projects.map((project, index) => (
                    <div key={project.id} className="silver-glass rounded-lg p-6">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                              index === 0 ? 'bg-yellow-600' : index === 1 ? 'bg-gray-500' : index === 2 ? 'bg-orange-600' : 'bg-gray-600'
                            }`}>
                              {index + 1}
                            </div>
                            <h4 className="text-lg font-bold text-white">{project.name}</h4>
                          </div>
                          <p className="text-gray-400 mb-3">{project.description}</p>
                          <div className="flex items-center space-x-4 text-sm">
                            {project.website && (
                              <a href={project.website} target="_blank" rel="noopener noreferrer" 
                                 className="text-blue-400 hover:text-blue-300">
                                🌐 Website
                              </a>
                            )}
                            {project.twitter && (
                              <a href={project.twitter} target="_blank" rel="noopener noreferrer"
                                 className="text-blue-400 hover:text-blue-300">
                                🐦 Twitter
                              </a>
                            )}
                            <span className="text-gray-500">
                              By: {formatAddress(project.submitted_by)}
                            </span>
                          </div>
                        </div>
                        
                        <div className="text-right ml-6">
                          <div className="text-white font-bold text-lg">{project.total_votes}</div>
                          <div className="text-gray-400 text-sm">votes</div>
                          <div className="mt-2 space-y-1 text-xs">
                            <div className="text-blue-300">{project.total_drb_votes} $DRB</div>
                            <div className="text-purple-300">{project.total_bnkr_votes} $BNKR</div>
                          </div>
                          
                          {isWalletConnected && (
                            <button 
                              className="btn-secondary mt-3 text-sm px-4 py-2"
                              onClick={() => {
                                // TODO: Implement vote modal
                                showNotification('Voting interface coming soon!', 'info');
                              }}
                            >
                              Vote
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Trophy className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400 mb-4">No active projects yet</p>
                  <p className="text-gray-500 text-sm">Be the first to submit a Base ecosystem project!</p>
                </div>
              )}
            </div>

            {/* Voting Rules */}
            <div className="card silverish-gradient">
              <h3 className="text-xl font-bold text-white mb-4">📋 Voting Rules</h3>
              <div className="space-y-3 text-gray-300">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span>Burn <strong>1000 $DRB</strong> or <strong>100 $BNKR</strong> to vote</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span>One vote per project per wallet</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span>Winner receives <strong>0.5% $DRB + 0.5% $BNKR</strong> allocation</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span>Voting continues until next community vote period</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span>Only Base ecosystem projects eligible</span>
                </div>
              </div>
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
            {communityStats && communityStats.top_burners && communityStats.top_burners.length > 0 ? (
              <div className="space-y-3">
                {communityStats.top_burners.map((burner, index) => (
                  <div key={index} className="silver-glass rounded-lg p-4 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        index === 0 ? 'bg-yellow-600' : index === 1 ? 'bg-gray-500' : index === 2 ? 'bg-orange-600' : 'bg-gray-600'
                      }`}>
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : index + 1}
                      </div>
                      <span className="font-mono text-white">{formatAddress(burner.wallet || burner.wallet_address)}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-white font-medium">{parseFloat(burner.total_burned || burner.total_amount || 0).toLocaleString()}</div>
                      <div className="text-gray-400 text-sm">{burner.transaction_count || burner.total_burns || 0} burns</div>
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
          <h3 className="text-lg font-bold text-white mb-6 text-center">How It Works</h3>
          
          <div className="grid md:grid-cols-7 gap-3 text-sm">
            <div className="text-center">
              <div className="bg-red-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Flame className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-medium text-white mb-2">88% Burned</h4>
              <p className="text-gray-400">
                Permanently removed from circulation
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <ArrowRight className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-medium text-white mb-2">7% → Grok</h4>
              <p className="text-gray-400">
                $DRB tokens to Grok's wallet
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-500 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Users className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-medium text-white mb-2">1.5% → DRB Community</h4>
              <p className="text-gray-400">
                $DRB tokens for community
              </p>
            </div>
            <div className="text-center">
              <div className="bg-green-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <ArrowRight className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-medium text-white mb-2">0.5% → DRB Team</h4>
              <p className="text-gray-400">
                $DRB tokens to team
              </p>
            </div>
            <div className="text-center">
              <div className="bg-purple-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Star className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-medium text-white mb-2">1.5% → BANKR Club</h4>
              <p className="text-gray-400">
                $BNKR for BANKR Club Members
              </p>
            </div>
            <div className="text-center">
              <div className="bg-purple-500 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <ArrowRight className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-medium text-white mb-2">0.5% → BNKR Team</h4>
              <p className="text-gray-400">
                $BNKR tokens to team
              </p>
            </div>
            <div className="text-center">
              <div className="bg-yellow-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <Trophy className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-medium text-white mb-2">1% → Contest Winner</h4>
              <p className="text-gray-400">
                0.5% $DRB + 0.5% $BNKR to winning project
              </p>
            </div>
          </div>
        </div>

        {/* Admin Access - Centered under DRB allocation */}
        <div className="flex justify-center mt-8 mb-8">
          {adminToken ? (
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setAdminPanelOpen(true)}
                className="px-4 py-2 bg-purple-600/80 text-white rounded-lg text-sm hover:bg-purple-700/90 backdrop-blur-sm shadow-lg transition-all"
                title="Admin Panel"
              >
                ⚙️ Admin Panel
              </button>
              <button 
                onClick={handleAdminLogout}
                className="px-4 py-2 bg-gray-600/80 text-white rounded-lg text-sm hover:bg-gray-700/90 backdrop-blur-sm shadow-lg transition-all"
                title="Admin Logout"
              >
                🚪 Logout
              </button>
            </div>
          ) : (
            <button 
              onClick={handleAdminLogin}
              className="px-4 py-2 bg-purple-600/50 text-white rounded-lg text-sm hover:bg-purple-700/80 backdrop-blur-sm shadow-lg opacity-60 hover:opacity-100 transition-all"
              title="Admin Access"
            >
              ⚙️ Admin Access
            </button>
          )}
        </div>

        {/* Project Submission Modal */}
        {projectSubmissionModal && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
            <div className="silver-glass rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-white">Submit Project</h3>
                <button 
                  onClick={() => setProjectSubmissionModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-gray-300 mb-1">Project Name *</label>
                  <input
                    type="text"
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600"
                    value={newProject.name}
                    onChange={(e) => setNewProject({...newProject, name: e.target.value})}
                    placeholder="Enter project name"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-300 mb-1">Description *</label>
                  <textarea
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600 h-20"
                    value={newProject.description}
                    onChange={(e) => setNewProject({...newProject, description: e.target.value})}
                    placeholder="Describe your project"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-300 mb-1">Base Address *</label>
                  <input
                    type="text"
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600"
                    value={newProject.base_address}
                    onChange={(e) => setNewProject({...newProject, base_address: e.target.value})}
                    placeholder="0x..."
                  />
                </div>
                
                <div>
                  <label className="block text-gray-300 mb-1">Website</label>
                  <input
                    type="url"
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600"
                    value={newProject.website}
                    onChange={(e) => setNewProject({...newProject, website: e.target.value})}
                    placeholder="https://..."
                  />
                </div>
                
                <div>
                  <label className="block text-gray-300 mb-1">Twitter</label>
                  <input
                    type="text"
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600"
                    value={newProject.twitter}
                    onChange={(e) => setNewProject({...newProject, twitter: e.target.value})}
                    placeholder="@username"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-300 mb-1">Logo URL</label>
                  <input
                    type="url"
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600"
                    value={newProject.logo_url}
                    onChange={(e) => setNewProject({...newProject, logo_url: e.target.value})}
                    placeholder="https://..."
                  />
                </div>
              </div>
              
              <div className="flex gap-3 mt-6">
                <button 
                  onClick={() => setProjectSubmissionModal(false)}
                  className="flex-1 py-2 px-4 bg-gray-600 text-white rounded hover:bg-gray-700 transition"
                >
                  Cancel
                </button>
                <button 
                  onClick={submitProject}
                  className="flex-1 py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                >
                  Submit Project
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Project Submission Modal */}
        {projectSubmissionModal && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
            <div className="silver-glass rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-white">Submit Project</h3>
                <button 
                  onClick={() => setProjectSubmissionModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-gray-300 mb-1">Project Name *</label>
                  <input
                    type="text"
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600"
                    value={newProject.name}
                    onChange={(e) => setNewProject({...newProject, name: e.target.value})}
                    placeholder="Enter project name"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-300 mb-1">Description *</label>
                  <textarea
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600 h-20"
                    value={newProject.description}
                    onChange={(e) => setNewProject({...newProject, description: e.target.value})}
                    placeholder="Describe your project"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-300 mb-1">Base Address *</label>
                  <input
                    type="text"
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600"
                    value={newProject.base_address}
                    onChange={(e) => setNewProject({...newProject, base_address: e.target.value})}
                    placeholder="0x..."
                  />
                </div>
                
                <div>
                  <label className="block text-gray-300 mb-1">Website</label>
                  <input
                    type="url"
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600"
                    value={newProject.website}
                    onChange={(e) => setNewProject({...newProject, website: e.target.value})}
                    placeholder="https://..."
                  />
                </div>
                
                <div>
                  <label className="block text-gray-300 mb-1">Twitter</label>
                  <input
                    type="text"
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600"
                    value={newProject.twitter}
                    onChange={(e) => setNewProject({...newProject, twitter: e.target.value})}
                    placeholder="@username"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-300 mb-1">Logo URL</label>
                  <input
                    type="url"
                    className="w-full p-2 rounded bg-gray-800 text-white border border-gray-600"
                    value={newProject.logo_url}
                    onChange={(e) => setNewProject({...newProject, logo_url: e.target.value})}
                    placeholder="https://..."
                  />
                </div>
              </div>
              
              <div className="flex gap-3 mt-6">
                <button 
                  onClick={() => setProjectSubmissionModal(false)}
                  className="flex-1 py-2 px-4 bg-gray-600 text-white rounded hover:bg-gray-700 transition"
                >
                  Cancel
                </button>
                <button 
                  onClick={submitProject}
                  className="flex-1 py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                >
                  Submit Project
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Admin Panel */}
        {adminPanelOpen && adminToken && (
          <AdminPanel onClose={() => setAdminPanelOpen(false)} />
        )}

        {/* Discrete Admin Access - Bottom Right Corner */}
        <div className="fixed bottom-4 right-4 z-40">
          {adminToken ? (
            <div className="flex flex-col gap-2">
              <button 
                onClick={() => setAdminPanelOpen(true)}
                className="px-2 py-1 bg-purple-600/80 text-white rounded text-xs hover:bg-purple-700/90 backdrop-blur-sm shadow-lg"
                title="Admin Panel"
              >
                ⚙️
              </button>
              <button 
                onClick={handleAdminLogout}
                className="px-2 py-1 bg-gray-600/80 text-white rounded text-xs hover:bg-gray-700/90 backdrop-blur-sm shadow-lg"
                title="Admin Logout"
              >
                🚪
              </button>
            </div>
          ) : (
            <button 
              onClick={handleAdminLogin}
              className="px-2 py-1 bg-purple-600/80 text-white rounded text-xs hover:bg-purple-700/90 backdrop-blur-sm shadow-lg opacity-30 hover:opacity-100 transition-opacity"
              title="Admin Access"
            >
              ⚙️
            </button>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;