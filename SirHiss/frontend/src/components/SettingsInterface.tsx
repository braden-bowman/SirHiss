import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Alert,
  Tabs,
  Tab,
  Switch,
  FormControlLabel,
  Divider,
  IconButton,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Key,
  Security,
  Visibility,
  VisibilityOff,
  Save,
  Logout,
  Login,
  AccountCircle,
  Settings as SettingsIcon,
} from '@mui/icons-material';

interface UserSettings {
  robinhood_username: string;
  robinhood_password: string;
  robinhood_mfa_code?: string;
  risk_tolerance: string;
  max_position_size: number;
  enable_notifications: boolean;
  auto_rebalance: boolean;
  dark_mode: boolean;
}

interface AuthState {
  isAuthenticated: boolean;
  user: {
    id: number;
    username: string;
    email?: string;
  } | null;
  robinhoodConnected: boolean;
}

function TabPanel({ children, value, index }: any) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export function SettingsInterface() {
  const [activeTab, setActiveTab] = useState(0);
  const [settings, setSettings] = useState<UserSettings>({
    robinhood_username: '',
    robinhood_password: '',
    robinhood_mfa_code: '',
    risk_tolerance: 'medium',
    max_position_size: 0.1,
    enable_notifications: true,
    auto_rebalance: false,
    dark_mode: true,
  });
  
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    robinhoodConnected: false,
  });
  
  const [showPasswords, setShowPasswords] = useState({
    robinhood: false,
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error' | 'info'>('info');
  const [loginDialog, setLoginDialog] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });

  const API_BASE = 'http://localhost:9002';

  const apiCall = async (endpoint: string, options: any = {}) => {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      return await response.json();
    } catch (err) {
      console.error(`API call failed for ${endpoint}:`, err);
      throw err;
    }
  };

  const loadSettings = async () => {
    try {
      const data = await apiCall('/api/v1/settings/user');
      setSettings({ ...settings, ...data });
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  const loadAuthState = async () => {
    try {
      const data = await apiCall('/api/v1/auth/me');
      setAuthState({
        isAuthenticated: true,
        user: data,
        robinhoodConnected: false, // TODO: Get actual Robinhood status
      });
    } catch (err) {
      console.error('Failed to load auth state:', err);
      setAuthState({
        isAuthenticated: false,
        user: null,
        robinhoodConnected: false,
      });
    }
  };

  const saveSettings = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      await apiCall('/api/v1/settings/user', {
        method: 'POST',
        body: JSON.stringify(settings),
      });
      
      setMessage('Settings saved successfully');
      setMessageType('success');
    } catch (err) {
      setMessage('Failed to save settings');
      setMessageType('error');
    }
    
    setLoading(false);
    setTimeout(() => setMessage(''), 3000);
  };

  const connectRobinhood = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      const response = await apiCall('/api/v1/auth/robinhood/connect', {
        method: 'POST',
        body: JSON.stringify({
          username: settings.robinhood_username,
          password: settings.robinhood_password,
          mfa_code: settings.robinhood_mfa_code,
        }),
      });
      
      setAuthState(prev => ({ ...prev, robinhoodConnected: true }));
      setMessage('Robinhood connected successfully');
      setMessageType('success');
    } catch (err) {
      setMessage('Failed to connect Robinhood account');
      setMessageType('error');
    }
    
    setLoading(false);
    setTimeout(() => setMessage(''), 3000);
  };

  const disconnectRobinhood = async () => {
    try {
      await apiCall('/api/v1/auth/robinhood/disconnect', { method: 'POST' });
      setAuthState(prev => ({ ...prev, robinhoodConnected: false }));
      setMessage('Robinhood disconnected');
      setMessageType('info');
    } catch (err) {
      setMessage('Failed to disconnect Robinhood account');
      setMessageType('error');
    }
    
    setTimeout(() => setMessage(''), 3000);
  };

  const handleLogin = async () => {
    setLoading(true);
    
    try {
      const response = await apiCall('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify(loginForm),
      });
      
      setAuthState({
        isAuthenticated: true,
        user: response.user,
        robinhoodConnected: response.robinhood_connected || false,
      });
      
      setLoginDialog(false);
      setMessage('Logged in successfully');
      setMessageType('success');
    } catch (err) {
      setMessage('Login failed');
      setMessageType('error');
    }
    
    setLoading(false);
    setTimeout(() => setMessage(''), 3000);
  };

  const handleLogout = () => {
    setAuthState({
      isAuthenticated: false,
      user: null,
      robinhoodConnected: false,
    });
    
    setMessage('Logged out successfully');
    setMessageType('info');
    setTimeout(() => setMessage(''), 3000);
  };

  useEffect(() => {
    loadSettings();
    loadAuthState();
  }, []);

  const renderAccount = () => (
    <Box>
      <Typography variant="h6" sx={{ mb: 3, color: '#fff' }}>
        Account Management
      </Typography>
      
      {!authState.isAuthenticated ? (
        <Card sx={{ background: '#1a1a1a', border: '1px solid #333', mb: 3 }}>
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 2 }}>
              <AccountCircle sx={{ fontSize: 64, color: '#666', mb: 2 }} />
              <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                Not logged in
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa', mb: 3 }}>
                Log in to access all features and save your settings
              </Typography>
              <Button
                variant="contained"
                startIcon={<Login />}
                onClick={() => setLoginDialog(true)}
                sx={{ background: '#00ff88', color: '#000' }}
              >
                Login
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Card sx={{ background: '#1a1a1a', border: '1px solid #333', mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h6" sx={{ color: '#00ff88' }}>
                  Welcome, {authState.user?.username}
                </Typography>
                <Typography variant="body2" sx={{ color: '#aaa' }}>
                  {authState.user?.email}
                </Typography>
              </Box>
              <Button
                variant="outlined"
                startIcon={<Logout />}
                onClick={handleLogout}
                sx={{ color: '#ff4444', borderColor: '#ff4444' }}
              >
                Logout
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );

  const renderRobinhoodSettings = () => (
    <Box>
      <Typography variant="h6" sx={{ mb: 3, color: '#fff' }}>
        Robinhood Integration
      </Typography>
      
      <Card sx={{ background: '#1a1a1a', border: '1px solid #333', mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Box>
              <Typography variant="h6" sx={{ color: '#fff' }}>
                Connection Status
              </Typography>
              <Typography variant="body2" sx={{ color: authState.robinhoodConnected ? '#00ff88' : '#ff4444' }}>
                {authState.robinhoodConnected ? 'Connected' : 'Not connected'}
              </Typography>
            </Box>
            {authState.robinhoodConnected ? (
              <Button
                variant="outlined"
                onClick={disconnectRobinhood}
                sx={{ color: '#ff4444', borderColor: '#ff4444' }}
              >
                Disconnect
              </Button>
            ) : null}
          </Box>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Robinhood Username"
                fullWidth
                value={settings.robinhood_username}
                onChange={(e) => setSettings(prev => ({ ...prev, robinhood_username: e.target.value }))}
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Robinhood Password"
                type={showPasswords.robinhood ? 'text' : 'password'}
                fullWidth
                value={settings.robinhood_password}
                onChange={(e) => setSettings(prev => ({ ...prev, robinhood_password: e.target.value }))}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPasswords(prev => ({ ...prev, robinhood: !prev.robinhood }))}
                        edge="end"
                      >
                        {showPasswords.robinhood ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="MFA Code (if enabled)"
                fullWidth
                value={settings.robinhood_mfa_code}
                onChange={(e) => setSettings(prev => ({ ...prev, robinhood_mfa_code: e.target.value }))}
                sx={{ mb: 2 }}
              />
            </Grid>
          </Grid>
          
          {!authState.robinhoodConnected && (
            <Button
              variant="contained"
              startIcon={<Key />}
              onClick={connectRobinhood}
              disabled={loading || !settings.robinhood_username || !settings.robinhood_password}
              sx={{ background: '#00ff88', color: '#000', mt: 2 }}
            >
              Connect Robinhood
            </Button>
          )}
        </CardContent>
      </Card>
    </Box>
  );

  const renderTradingSettings = () => (
    <Box>
      <Typography variant="h6" sx={{ mb: 3, color: '#fff' }}>
        Trading Settings
      </Typography>
      
      <Card sx={{ background: '#1a1a1a', border: '1px solid #333' }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                select
                label="Risk Tolerance"
                fullWidth
                value={settings.risk_tolerance}
                onChange={(e) => setSettings(prev => ({ ...prev, risk_tolerance: e.target.value }))}
                SelectProps={{ native: true }}
                sx={{ mb: 2 }}
              >
                <option value="low">Low Risk</option>
                <option value="medium">Medium Risk</option>
                <option value="high">High Risk</option>
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Max Position Size (%)"
                type="number"
                fullWidth
                value={settings.max_position_size * 100}
                onChange={(e) => setSettings(prev => ({ 
                  ...prev, 
                  max_position_size: parseFloat(e.target.value) / 100 
                }))}
                inputProps={{ min: 1, max: 100 }}
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enable_notifications}
                    onChange={(e) => setSettings(prev => ({ ...prev, enable_notifications: e.target.checked }))}
                  />
                }
                label="Enable Notifications"
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.auto_rebalance}
                    onChange={(e) => setSettings(prev => ({ ...prev, auto_rebalance: e.target.checked }))}
                  />
                }
                label="Auto Rebalance Portfolio"
                sx={{ mb: 2 }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab label="Account" />
          <Tab label="Robinhood" />
          <Tab label="Trading" />
        </Tabs>
      </Box>

      {message && (
        <Alert severity={messageType} sx={{ mb: 2 }} onClose={() => setMessage('')}>
          {message}
        </Alert>
      )}

      <TabPanel value={activeTab} index={0}>
        {renderAccount()}
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        {renderRobinhoodSettings()}
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        {renderTradingSettings()}
      </TabPanel>

      <Box sx={{ position: 'fixed', bottom: 20, right: 20 }}>
        <Button
          variant="contained"
          startIcon={<Save />}
          onClick={saveSettings}
          disabled={loading}
          sx={{ background: '#00ff88', color: '#000' }}
        >
          Save Settings
        </Button>
      </Box>

      {/* Login Dialog */}
      <Dialog open={loginDialog} onClose={() => setLoginDialog(false)}>
        <DialogTitle>Login to SirHiss</DialogTitle>
        <DialogContent>
          <TextField
            label="Username"
            fullWidth
            value={loginForm.username}
            onChange={(e) => setLoginForm(prev => ({ ...prev, username: e.target.value }))}
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            value={loginForm.password}
            onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLoginDialog(false)}>Cancel</Button>
          <Button
            onClick={handleLogin}
            disabled={loading || !loginForm.username || !loginForm.password}
            variant="contained"
          >
            Login
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}