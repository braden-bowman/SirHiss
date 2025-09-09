import React, { useState } from 'react';
import {
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  Divider,
  Container,
  Card,
  CardContent,
  Grid
} from '@mui/material';
import { 
  LoginRounded as LoginIcon,
  SmartToy as BotIcon,
  TrendingUp as TrendingIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import { useAuth } from '../services/auth';

export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(username, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setUsername('admin');
    setPassword('admin123');
    setLoading(true);
    setError('');

    try {
      await login('admin', 'admin123');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%)',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* Header Section */}
      <Box sx={{ py: 4 }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 6 }}>
            <Typography 
              variant="h2" 
              sx={{ 
                fontWeight: 'bold', 
                color: '#00ff88', 
                mb: 2,
                textShadow: '0 0 20px rgba(0, 255, 136, 0.3)'
              }}
            >
              🐍 SirHiss Trading Platform
            </Typography>
            <Typography variant="h5" sx={{ color: '#cccccc', mb: 4 }}>
              Advanced AI-Powered Trading Bot Management
            </Typography>
            
            <Grid container spacing={3} justifyContent="center" sx={{ mb: 4 }}>
              <Grid item xs={12} sm={4}>
                <Card sx={{ backgroundColor: '#2a2a2a', height: '100%' }}>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <BotIcon sx={{ fontSize: 48, color: '#00ff88', mb: 2 }} />
                    <Typography variant="h6" gutterBottom>Automated Trading</Typography>
                    <Typography variant="body2" color="textSecondary">
                      Create and manage multiple trading bots with custom strategies
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Card sx={{ backgroundColor: '#2a2a2a', height: '100%' }}>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <TrendingIcon sx={{ fontSize: 48, color: '#4488ff', mb: 2 }} />
                    <Typography variant="h6" gutterBottom>Real-Time Data</Typography>
                    <Typography variant="body2" color="textSecondary">
                      Live market data and portfolio tracking with interactive charts
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Card sx={{ backgroundColor: '#2a2a2a', height: '100%' }}>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <SecurityIcon sx={{ fontSize: 48, color: '#ffaa00', mb: 2 }} />
                    <Typography variant="h6" gutterBottom>Enterprise Security</Typography>
                    <Typography variant="body2" color="textSecondary">
                      Two-factor authentication and encrypted credential storage
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </Container>
      </Box>

      {/* Login Section */}
      <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', py: 4 }}>
        <Container maxWidth="sm">
          <Paper 
            sx={{ 
              p: 4, 
              backgroundColor: '#1a1a1a',
              border: '1px solid #00ff8844',
              boxShadow: '0 4px 20px rgba(0, 255, 136, 0.1)'
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 3 }}>
              <LoginIcon sx={{ mr: 1, color: '#00ff88' }} />
              <Typography variant="h5" sx={{ color: '#fff', fontWeight: 'bold' }}>
                Login to Dashboard
              </Typography>
            </Box>


            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                margin="normal"
                required
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                margin="normal"
                required
                sx={{ mb: 3 }}
              />
              
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                sx={{ 
                  mb: 2,
                  backgroundColor: '#00ff88',
                  color: '#000',
                  fontWeight: 'bold',
                  '&:hover': {
                    backgroundColor: '#00dd77'
                  }
                }}
                disabled={loading}
              >
                {loading ? 'Logging in...' : 'Login to Dashboard'}
              </Button>
            </form>

            <Divider sx={{ my: 3, borderColor: '#333' }}>
              <Typography variant="body2" sx={{ color: '#666' }}>
                or
              </Typography>
            </Divider>

            <Button
              fullWidth
              variant="outlined"
              size="large"
              onClick={handleDemoLogin}
              disabled={loading}
              sx={{ 
                borderColor: '#4488ff',
                color: '#4488ff',
                '&:hover': {
                  borderColor: '#6699ff',
                  backgroundColor: 'rgba(68, 136, 255, 0.1)'
                }
              }}
            >
              Try Demo Account
            </Button>

            <Divider sx={{ my: 3, borderColor: '#333' }}>
              <Typography variant="body2" sx={{ color: '#666' }}>
                or
              </Typography>
            </Divider>

            <Button
              fullWidth
              variant="outlined"
              size="large"
              onClick={() => window.location.href = '/register'}
              disabled={loading}
              sx={{ 
                borderColor: '#ffaa00',
                color: '#ffaa00',
                '&:hover': {
                  borderColor: '#ffcc44',
                  backgroundColor: 'rgba(255, 170, 0, 0.1)'
                }
              }}
            >
              Create New Account
            </Button>

            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                Demo Credentials:
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa', fontFamily: 'monospace' }}>
                Username: <strong>admin</strong> | Password: <strong>admin123</strong>
              </Typography>
            </Box>
          </Paper>
          
          {error && (
            <Alert severity="error" sx={{ mt: 3 }}>
              {error}
            </Alert>
          )}
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ py: 3, borderTop: '1px solid #333' }}>
        <Container>
          <Typography variant="body2" align="center" sx={{ color: '#666' }}>
            © 2025 SirHiss Trading Platform - Secure • Automated • Professional
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}