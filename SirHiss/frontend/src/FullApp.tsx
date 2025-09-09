import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  AppBar,
  Toolbar,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CssBaseline,
  Chip,
  IconButton,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  SmartToy,
  TrendingUp,
  AccountBalanceWallet,
  Settings,
  Security,
  Menu as MenuIcon,
  PlayArrow,
  Stop,
} from '@mui/icons-material';
import { PortfolioInterface } from './components/PortfolioInterface.tsx';
import { SettingsInterface } from './components/SettingsInterface.tsx';
import { MarketDataInterface } from './components/MarketDataInterface.tsx';
import { SecurityInterface } from './components/SecurityInterface.tsx';
import { BotManagement } from './pages/BotManagement.tsx';
import { useWebSocket } from './hooks/useWebSocket.ts';

const API_BASE = 'http://localhost:9002';

interface Bot {
  id: number;
  name: string;
  description: string;
  status: string;
  allocated_percentage: number;
  current_value: number;
  allocated_amount: number;
}

interface Algorithm {
  id: number;
  algorithm_name: string;
  algorithm_type: string;
  enabled: boolean;
  position_size: number;
  total_trades: number;
  win_rate: number;
  total_return: number;
}

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
}

interface FullAppProps {
  user: User;
  authToken: string;
  onLogout: () => void;
}

function TabPanel({ children, value, index }: any) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function FullApp({ user, authToken, onLogout }: FullAppProps) {
  const [currentView, setCurrentView] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Data states
  const [bots, setBots] = useState<Bot[]>([]);
  const [portfolioData, setPortfolioData] = useState({
    totalValue: 0,
    totalPnL: 0,
    availableCash: 0,
    activeBots: 0
  });
  const [algorithms, setAlgorithms] = useState<Algorithm[]>([]);
  const [selectedBotId, setSelectedBotId] = useState<number | null>(null);
  const [algorithmTab, setAlgorithmTab] = useState(0);

  // WebSocket connection
  const websocketUrl = `ws://localhost:9002/ws/client_${user?.id || 'guest'}`;
  const { lastMessage, connectionStatus, sendMessage } = useWebSocket(websocketUrl, !!authToken);
  
  // Process WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      switch (lastMessage.type) {
        case 'portfolio_update':
          setPortfolioData(prev => ({ ...prev, ...lastMessage.data }));
          break;
        case 'bots_update':
          setBots(lastMessage.data || []);
          break;
        default:
          console.log('Unhandled WebSocket message:', lastMessage);
      }
    }
  }, [lastMessage]);

  // API Helper with authentication
  const apiCall = useCallback(async (endpoint: string, options: any = {}) => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...options.headers,
      };

      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers,
        ...options,
      });
      
      if (response.status === 401) {
        // Authentication failed, logout user
        onLogout();
        throw new Error('Authentication required');
      }
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      return await response.json();
    } catch (err) {
      console.error(`API call failed for ${endpoint}:`, err);
      throw err;
    }
  }, [authToken, onLogout]);

  // Data loading functions
  const loadBots = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/v1/bots/');
      setBots(data || []);
    } catch (err) {
      console.error('Failed to load bots:', err);
      setBots([]);
      setError('Failed to load trading bots');
    }
    setLoading(false);
  }, [apiCall]);

  const loadPortfolioData = useCallback(async () => {
    try {
      const data = await apiCall('/api/v1/portfolio/summary');
      setPortfolioData({
        totalValue: parseFloat(data?.total_value || 0),
        totalPnL: parseFloat(data?.total_pnl || 0),
        availableCash: parseFloat(data?.available_cash || 0),
        activeBots: data?.active_bots || 0
      });
    } catch (err) {
      console.error('Failed to load portfolio data:', err);
      setPortfolioData({
        totalValue: 0,
        totalPnL: 0,
        availableCash: 0,
        activeBots: 0
      });
    }
  }, [apiCall]);

  // Load data and set up auto-refresh
  useEffect(() => {
    if (!user || !user.username) return; // Don't load if user not ready
    
    loadBots();
    loadPortfolioData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      if (currentView === 'dashboard') {
        loadPortfolioData();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [currentView, user, loadBots, loadPortfolioData]);

  // Safety check for user (after all hooks)
  if (!user || !user.username) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%)'
      }}>
        <CircularProgress sx={{ color: '#00ff88' }} />
        <Typography variant="h6" sx={{ ml: 2, color: '#00ff88' }}>
          Loading user data...
        </Typography>
      </Box>
    );
  }

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
    { id: 'bots', label: 'Trading Bots', icon: <SmartToy /> },
    { id: 'algorithms', label: 'Algorithms', icon: <TrendingUp /> },
    { id: 'portfolio', label: 'Portfolio', icon: <AccountBalanceWallet /> },
    { id: 'market', label: 'Market Data', icon: <TrendingUp /> },
    { id: 'security', label: 'Security', icon: <Security /> },
    { id: 'settings', label: 'Settings', icon: <Settings /> },
  ];

  const loadAlgorithms = async (botId: number) => {
    try {
      const data = await apiCall(`/api/v1/algorithms/bots/${botId}/algorithms`);
      setAlgorithms(data || []);
    } catch (err) {
      console.error('Failed to load algorithms:', err);
      setAlgorithms([]);
    }
  };

  // Bot control functions
  const toggleBot = async (botId: number, action: 'start' | 'stop') => {
    setError('');
    try {
      await apiCall(`/api/v1/bots/${botId}/${action}`, { method: 'POST' });
      await loadBots();
      setError(`Bot ${action}ed successfully`);
    } catch (err) {
      setError(`Failed to ${action} bot`);
    }
    
    setTimeout(() => setError(''), 3000);
  };

  const createBot = async (botData: any) => {
    try {
      await apiCall('/api/v1/bots/', {
        method: 'POST',
        body: JSON.stringify(botData)
      });
      await loadBots();
    } catch (err) {
      console.error('Failed to create bot:', err);
      setError('Failed to create bot');
    }
  };


  const renderDashboard = () => (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, color: '#00ff88' }}>
        📊 Trading Dashboard
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#00ff88' }}>Portfolio Value</Typography>
              <Typography variant="h4" sx={{ color: '#fff' }}>
                ${(portfolioData.totalValue || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </Typography>
              <Typography variant="body2" sx={{ color: portfolioData.totalPnL >= 0 ? '#00ff88' : '#ff4444' }}>
                {portfolioData.totalPnL >= 0 ? '+' : ''}${(portfolioData.totalPnL || 0).toFixed(2)} Total P&L
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#4488ff' }}>Available Cash</Typography>
              <Typography variant="h4" sx={{ color: '#fff' }}>
                ${(portfolioData.availableCash || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>Ready to deploy</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#ffaa00' }}>Active Bots</Typography>
              <Typography variant="h4" sx={{ color: '#fff' }}>
                {bots.filter(b => b.status === 'running').length} / {bots.length}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                {bots.filter(b => b.status === 'running').length} running
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#ff6b6b' }}>Performance</Typography>
              <Typography variant="h4" sx={{ color: '#00ff88' }}>+2.45%</Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>Overall return</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card sx={{ background: '#1a1a1a', border: '1px solid #333' }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, color: '#fff' }}>Trading Bots</Typography>
          {bots.map(bot => (
            <Box key={bot.id} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2, border: '1px solid #333', borderRadius: 2, mb: 1 }}>
              <Box>
                <Typography variant="h6" sx={{ color: '#fff' }}>{bot.name}</Typography>
                <Typography variant="body2" sx={{ color: '#aaa' }}>
                  {bot.description} • {bot.allocated_percentage}% allocation • ${bot.current_value.toFixed(2)} value
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip 
                  label={bot.status} 
                  color={bot.status === 'running' ? 'success' : 'default'}
                  size="small"
                />
                <Button
                  size="small"
                  variant={bot.status === 'running' ? 'outlined' : 'contained'}
                  color={bot.status === 'running' ? 'secondary' : 'primary'}
                  onClick={() => toggleBot(bot.id, bot.status === 'running' ? 'stop' : 'start')}
                  startIcon={bot.status === 'running' ? <Stop /> : <PlayArrow />}
                >
                  {bot.status === 'running' ? 'Stop' : 'Start'}
                </Button>
              </Box>
            </Box>
          ))}
        </CardContent>
      </Card>
    </Box>
  );

  const renderBots = () => (
    <Box>
      <BotManagement />
    </Box>
  );

  const renderAlgorithms = () => (
    <Box>
      <BotManagement />
    </Box>
  );

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard': return renderDashboard();
      case 'bots': return renderBots();
      case 'algorithms': return renderAlgorithms();
      case 'portfolio': return (
        <Box>
          <Typography variant="h4" sx={{ mb: 3, color: '#00ff88' }}>💼 Portfolio</Typography>
          <PortfolioInterface />
        </Box>
      );
      case 'market': return (
        <Box>
          <Typography variant="h4" sx={{ mb: 3, color: '#00ff88' }}>📈 Market Data</Typography>
          <MarketDataInterface />
        </Box>
      );
      case 'security': return (
        <Box>
          <SecurityInterface />
        </Box>
      );
      case 'settings': return (
        <Box>
          <Typography variant="h4" sx={{ mb: 3, color: '#00ff88' }}>⚙️ Settings</Typography>
          <SettingsInterface />
        </Box>
      );
      default: return renderDashboard();
    }
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      <AppBar position="fixed" sx={{ zIndex: 1201, backgroundColor: '#1a1a1a' }}>
        <Toolbar>
          <IconButton
            color="inherit"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            edge="start"
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" sx={{ color: '#00ff88', flexGrow: 1 }}>
            🐍 SirHiss Trading Platform
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ color: '#aaa' }}>
              Welcome, {user.username}
            </Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={onLogout}
              sx={{ color: '#ff4444', borderColor: '#ff4444' }}
            >
              Logout
            </Button>
            {loading && <CircularProgress size={24} sx={{ color: '#00ff88' }} />}
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="persistent"
        anchor="left"
        open={sidebarOpen}
        sx={{
          width: 240,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 240,
            boxSizing: 'border-box',
            backgroundColor: '#1a1a1a',
            borderRight: '1px solid #333',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto', p: 2 }}>
          <List>
            {menuItems.map((item) => (
              <ListItem 
                button 
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                sx={{ 
                  borderRadius: 2,
                  mb: 1,
                  backgroundColor: currentView === item.id ? 'rgba(0, 255, 136, 0.1)' : 'transparent',
                  '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.05)' }
                }}
              >
                <ListItemIcon sx={{ color: currentView === item.id ? '#00ff88' : '#aaa' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.label} 
                  sx={{ color: currentView === item.id ? '#00ff88' : '#fff' }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          marginLeft: sidebarOpen ? 0 : '-240px',
          transition: 'margin-left 0.2s',
          backgroundColor: '#0a0a0a',
          minHeight: '100vh'
        }}
      >
        <Toolbar />
        
        {error && (
          <Alert severity="info" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}
        
        {renderCurrentView()}
      </Box>
    </Box>
  );
}

export default FullApp;