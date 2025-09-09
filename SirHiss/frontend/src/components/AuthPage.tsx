import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Tab,
  Tabs,
  Alert,
  InputAdornment,
  IconButton,
  Divider,
  Container,
  Grid,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Login,
  PersonAdd,
  Security,
  TrendingUp,
  SmartToy,
} from '@mui/icons-material';

interface AuthPageProps {
  onLogin: (user: any, token: string) => void;
}

interface LoginForm {
  username: string;
  password: string;
}

interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

function TabPanel({ children, value, index }: any) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export function AuthPage({ onLogin }: AuthPageProps) {
  const [activeTab, setActiveTab] = useState(0);
  const [loginForm, setLoginForm] = useState<LoginForm>({
    username: '',
    password: '',
  });
  const [registerForm, setRegisterForm] = useState<RegisterForm>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (err) {
      throw err;
    }
  };

  const handleLogin = async () => {
    if (!loginForm.username || !loginForm.password) {
      setError('Please enter both username and password');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await apiCall('/api/v1/auth/login/simple', {
        method: 'POST',
        body: JSON.stringify(loginForm),
      });
      
      // Store authentication data
      localStorage.setItem('auth_token', response.access_token);
      localStorage.setItem('user_data', JSON.stringify(response.user));
      
      // Call parent callback
      onLogin(response.user, response.access_token);
      
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
    
    setLoading(false);
  };

  const handleRegister = async () => {
    if (!registerForm.username || !registerForm.email || !registerForm.password || !registerForm.confirmPassword) {
      setError('Please fill in all fields');
      return;
    }

    if (registerForm.password !== registerForm.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (registerForm.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (!registerForm.email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      await apiCall('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password,
        }),
      });
      
      setSuccess('Account created successfully! Please log in.');
      setActiveTab(0); // Switch to login tab
      setRegisterForm({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
      });
      
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    }
    
    setLoading(false);
  };

  const handleKeyPress = (event: React.KeyboardEvent, action: () => void) => {
    if (event.key === 'Enter') {
      action();
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Container maxWidth="sm">
        <Card
          sx={{
            background: 'rgba(26, 26, 26, 0.95)',
            border: '1px solid #333',
            borderRadius: 4,
            backdropFilter: 'blur(10px)',
            boxShadow: '0 8px 32px rgba(0, 255, 136, 0.1)',
          }}
        >
          <CardContent sx={{ p: 4 }}>
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                <SmartToy sx={{ fontSize: 40, color: '#00ff88', mr: 1 }} />
                <Typography
                  variant="h3"
                  sx={{
                    color: '#00ff88',
                    fontWeight: 'bold',
                    textShadow: '0 0 20px rgba(0, 255, 136, 0.3)',
                  }}
                >
                  SirHiss
                </Typography>
              </Box>
              <Typography variant="h6" sx={{ color: '#aaa', mb: 1 }}>
                Automated Trading Bot Platform
              </Typography>
              <Typography variant="body2" sx={{ color: '#666' }}>
                Professional algorithmic trading made simple
              </Typography>
            </Box>

            {/* Features Preview */}
            <Box sx={{ mb: 4 }}>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <TrendingUp sx={{ color: '#00ff88', mb: 1 }} />
                    <Typography variant="caption" sx={{ color: '#aaa', display: 'block' }}>
                      Advanced Algorithms
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Security sx={{ color: '#4488ff', mb: 1 }} />
                    <Typography variant="caption" sx={{ color: '#aaa', display: 'block' }}>
                      Bank-Level Security
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <SmartToy sx={{ color: '#ffaa00', mb: 1 }} />
                    <Typography variant="caption" sx={{ color: '#aaa', display: 'block' }}>
                      Multi-Bot Management
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>

            <Divider sx={{ mb: 3, borderColor: '#333' }} />

            {/* Auth Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: '#333', mb: 3 }}>
              <Tabs
                value={activeTab}
                onChange={(_, v) => setActiveTab(v)}
                centered
                sx={{
                  '& .MuiTab-root': { color: '#aaa' },
                  '& .Mui-selected': { color: '#00ff88' },
                  '& .MuiTabs-indicator': { backgroundColor: '#00ff88' },
                }}
              >
                <Tab label="Login" icon={<Login />} iconPosition="start" />
                <Tab label="Register" icon={<PersonAdd />} iconPosition="start" />
              </Tabs>
            </Box>

            {/* Error/Success Messages */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                {error}
              </Alert>
            )}
            {success && (
              <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
                {success}
              </Alert>
            )}

            {/* Login Form */}
            <TabPanel value={activeTab} index={0}>
              <Box>
                <TextField
                  label="Username"
                  fullWidth
                  value={loginForm.username}
                  onChange={(e) => setLoginForm(prev => ({ ...prev, username: e.target.value }))}
                  onKeyPress={(e) => handleKeyPress(e, handleLogin)}
                  sx={{ mb: 2 }}
                  autoComplete="username"
                />
                <TextField
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  fullWidth
                  value={loginForm.password}
                  onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
                  onKeyPress={(e) => handleKeyPress(e, handleLogin)}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPassword(!showPassword)}
                          edge="end"
                          sx={{ color: '#aaa' }}
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 3 }}
                  autoComplete="current-password"
                />
                <Button
                  variant="contained"
                  fullWidth
                  size="large"
                  onClick={handleLogin}
                  disabled={loading || !loginForm.username || !loginForm.password}
                  startIcon={<Login />}
                  sx={{
                    background: 'linear-gradient(45deg, #00ff88 0%, #00cc6a 100%)',
                    color: '#000',
                    py: 1.5,
                    '&:hover': {
                      background: 'linear-gradient(45deg, #00cc6a 0%, #00aa55 100%)',
                    },
                    '&:disabled': {
                      background: '#333',
                      color: '#666',
                    },
                  }}
                >
                  {loading ? 'Signing In...' : 'Sign In'}
                </Button>
              </Box>
            </TabPanel>

            {/* Register Form */}
            <TabPanel value={activeTab} index={1}>
              <Box>
                <TextField
                  label="Username"
                  fullWidth
                  value={registerForm.username}
                  onChange={(e) => setRegisterForm(prev => ({ ...prev, username: e.target.value }))}
                  sx={{ mb: 2 }}
                  autoComplete="username"
                  helperText="Choose a unique username"
                />
                <TextField
                  label="Email Address"
                  type="email"
                  fullWidth
                  value={registerForm.email}
                  onChange={(e) => setRegisterForm(prev => ({ ...prev, email: e.target.value }))}
                  sx={{ mb: 2 }}
                  autoComplete="email"
                  helperText="We'll use this for security notifications"
                />
                <TextField
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  fullWidth
                  value={registerForm.password}
                  onChange={(e) => setRegisterForm(prev => ({ ...prev, password: e.target.value }))}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPassword(!showPassword)}
                          edge="end"
                          sx={{ color: '#aaa' }}
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 2 }}
                  autoComplete="new-password"
                  helperText="Minimum 8 characters"
                />
                <TextField
                  label="Confirm Password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  fullWidth
                  value={registerForm.confirmPassword}
                  onChange={(e) => setRegisterForm(prev => ({ ...prev, confirmPassword: e.target.value }))}
                  onKeyPress={(e) => handleKeyPress(e, handleRegister)}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          edge="end"
                          sx={{ color: '#aaa' }}
                        >
                          {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 3 }}
                  autoComplete="new-password"
                  error={registerForm.confirmPassword !== '' && registerForm.password !== registerForm.confirmPassword}
                  helperText={
                    registerForm.confirmPassword !== '' && registerForm.password !== registerForm.confirmPassword
                      ? 'Passwords do not match'
                      : 'Re-enter your password'
                  }
                />
                <Button
                  variant="contained"
                  fullWidth
                  size="large"
                  onClick={handleRegister}
                  disabled={loading || !registerForm.username || !registerForm.email || !registerForm.password || !registerForm.confirmPassword}
                  startIcon={<PersonAdd />}
                  sx={{
                    background: 'linear-gradient(45deg, #4488ff 0%, #3366cc 100%)',
                    color: '#fff',
                    py: 1.5,
                    '&:hover': {
                      background: 'linear-gradient(45deg, #3366cc 0%, #2255aa 100%)',
                    },
                    '&:disabled': {
                      background: '#333',
                      color: '#666',
                    },
                  }}
                >
                  {loading ? 'Creating Account...' : 'Create Account'}
                </Button>
              </Box>
            </TabPanel>

            {/* Footer */}
            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Typography variant="body2" sx={{ color: '#666' }}>
                By signing up, you agree to our Terms of Service and Privacy Policy
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}