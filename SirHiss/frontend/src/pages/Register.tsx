import React, { useState } from 'react';
import {
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  Container,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Grid,
  Chip,
  FormControlLabel,
  Checkbox,
  IconButton,
  InputAdornment
} from '@mui/material';
import { 
  PersonAdd as RegisterIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
import { api } from '../services/api';
import { useAuth } from '../services/auth';

interface PlatformConfig {
  id: string;
  name: string;
  description: string;
  color: string;
  required: boolean;
  fields: {
    key: string;
    label: string;
    type: string;
    required: boolean;
    placeholder?: string;
  }[];
}

const TRADING_PLATFORMS: PlatformConfig[] = [
  {
    id: 'robinhood',
    name: 'Robinhood',
    description: 'Commission-free stock and crypto trading',
    color: '#00ff88',
    required: true,
    fields: [
      { key: 'username', label: 'Username', type: 'text', required: true },
      { key: 'password', label: 'Password', type: 'password', required: true }
    ]
  },
  {
    id: 'yahoo_finance',
    name: 'Yahoo Finance',
    description: 'Free market data and financial information',
    color: '#7b68ee',
    required: false,
    fields: [
      { key: 'api_key', label: 'API Key (Optional)', type: 'password', required: false, placeholder: 'Leave blank for free tier' }
    ]
  }
];

const steps = ['Account Details', 'Trading Platforms', 'Confirmation'];

export function Register() {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const { login } = useAuth();
  
  // Step 1: Account Details
  const [accountData, setAccountData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [showPasswords, setShowPasswords] = useState({
    password: false,
    confirmPassword: false
  });

  // Step 2: Trading Platforms
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(['robinhood']);
  const [platformCredentials, setPlatformCredentials] = useState<Record<string, Record<string, string>>>({});
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const validateStep1 = () => {
    if (!accountData.username || !accountData.email || !accountData.password || !accountData.confirmPassword) {
      setError('All fields are required');
      return false;
    }
    if (accountData.password !== accountData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    if (accountData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (!selectedPlatforms.includes('robinhood')) {
      setError('Robinhood connection is required for trading functionality');
      return false;
    }
    
    for (const platformId of selectedPlatforms) {
      const platform = TRADING_PLATFORMS.find(p => p.id === platformId);
      if (!platform) continue;
      
      const credentials = platformCredentials[platformId] || {};
      for (const field of platform.fields) {
        if (field.required && !credentials[field.key]) {
          setError(`${field.label} is required for ${platform.name}`);
          return false;
        }
      }
    }
    
    if (!agreedToTerms) {
      setError('You must agree to the Terms of Service');
      return false;
    }
    
    return true;
  };

  const handleNext = () => {
    setError('');
    
    if (activeStep === 0 && !validateStep1()) return;
    if (activeStep === 1 && !validateStep2()) return;
    
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    
    try {
      // Step 1: Create user account
      const userResponse = await api.post('/auth/register', {
        username: accountData.username,
        email: accountData.email,
        password: accountData.password
      });

      // Step 2: Login to get auth token
      await login(accountData.username, accountData.password);

      // Step 3: Add trading platform credentials
      for (const platformId of selectedPlatforms) {
        const credentials = platformCredentials[platformId];
        if (credentials && Object.keys(credentials).length > 0) {
          const platform = TRADING_PLATFORMS.find(p => p.id === platformId);
          await api.post('/settings/credentials', {
            platform: platformId,
            name: platform?.name || platformId,
            ...credentials
          });
        }
      }

      setSuccess(true);
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 2000);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const togglePlatformSelection = (platformId: string) => {
    if (platformId === 'robinhood') return; // Required platform
    
    setSelectedPlatforms(prev => 
      prev.includes(platformId) 
        ? prev.filter(id => id !== platformId)
        : [...prev, platformId]
    );
  };

  const updatePlatformCredentials = (platformId: string, field: string, value: string) => {
    setPlatformCredentials(prev => ({
      ...prev,
      [platformId]: {
        ...prev[platformId],
        [field]: value
      }
    }));
  };

  if (success) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <Container maxWidth="sm">
          <Paper sx={{ p: 4, backgroundColor: '#1a1a1a', textAlign: 'center' }}>
            <CheckIcon sx={{ fontSize: 64, color: '#00ff88', mb: 2 }} />
            <Typography variant="h4" sx={{ color: '#fff', mb: 2 }}>
              Welcome to SirHiss! 🐍
            </Typography>
            <Typography variant="body1" sx={{ color: '#ccc', mb: 3 }}>
              Your account has been created successfully. Redirecting to dashboard...
            </Typography>
          </Paper>
        </Container>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%)',
        py: 4
      }}
    >
      <Container maxWidth="md">
        <Paper sx={{ p: 4, backgroundColor: '#1a1a1a', color: '#fff' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 4 }}>
            <RegisterIcon sx={{ mr: 2, color: '#00ff88', fontSize: 32 }} />
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              Join SirHiss Trading Platform
            </Typography>
          </Box>

          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel sx={{ '& .MuiStepLabel-label': { color: '#ccc' } }}>
                  {label}
                </StepLabel>
              </Step>
            ))}
          </Stepper>


          {/* Step 1: Account Details */}
          {activeStep === 0 && (
            <Box>
              <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
                Create Your Account
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Username"
                    value={accountData.username}
                    onChange={(e) => setAccountData({ ...accountData, username: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    value={accountData.email}
                    onChange={(e) => setAccountData({ ...accountData, email: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Password"
                    type={showPasswords.password ? 'text' : 'password'}
                    value={accountData.password}
                    onChange={(e) => setAccountData({ ...accountData, password: e.target.value })}
                    required
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setShowPasswords({ ...showPasswords, password: !showPasswords.password })}
                          >
                            {showPasswords.password ? <VisibilityOffIcon /> : <VisibilityIcon />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Confirm Password"
                    type={showPasswords.confirmPassword ? 'text' : 'password'}
                    value={accountData.confirmPassword}
                    onChange={(e) => setAccountData({ ...accountData, confirmPassword: e.target.value })}
                    required
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setShowPasswords({ ...showPasswords, confirmPassword: !showPasswords.confirmPassword })}
                          >
                            {showPasswords.confirmPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
              </Grid>
            </Box>
          )}

          {/* Step 2: Trading Platforms */}
          {activeStep === 1 && (
            <Box>
              <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
                Connect Trading Platforms
              </Typography>
              
              <Grid container spacing={3}>
                {TRADING_PLATFORMS.map((platform) => (
                  <Grid item xs={12} key={platform.id}>
                    <Card 
                      sx={{ 
                        backgroundColor: selectedPlatforms.includes(platform.id) ? '#2a2a2a' : '#1a1a1a',
                        border: selectedPlatforms.includes(platform.id) ? `2px solid ${platform.color}` : '1px solid #333',
                        cursor: platform.required ? 'default' : 'pointer'
                      }}
                      onClick={() => !platform.required && togglePlatformSelection(platform.id)}
                    >
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography variant="h6" sx={{ color: platform.color, mr: 2 }}>
                              {platform.name}
                            </Typography>
                            {platform.required && (
                              <Chip label="Required" size="small" sx={{ backgroundColor: platform.color, color: '#000' }} />
                            )}
                          </Box>
                          {!platform.required && (
                            <Checkbox
                              checked={selectedPlatforms.includes(platform.id)}
                              sx={{ color: platform.color }}
                            />
                          )}
                        </Box>
                        
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                          {platform.description}
                        </Typography>

                        {selectedPlatforms.includes(platform.id) && (
                          <Grid container spacing={2}>
                            {platform.fields.map((field) => (
                              <Grid item xs={12} sm={6} key={field.key}>
                                <TextField
                                  fullWidth
                                  label={field.label}
                                  type={field.type}
                                  placeholder={field.placeholder}
                                  required={field.required}
                                  value={platformCredentials[platform.id]?.[field.key] || ''}
                                  onChange={(e) => updatePlatformCredentials(platform.id, field.key, e.target.value)}
                                  onClick={(e) => e.stopPropagation()}
                                />
                              </Grid>
                            ))}
                          </Grid>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>

              <FormControlLabel
                control={
                  <Checkbox
                    checked={agreedToTerms}
                    onChange={(e) => setAgreedToTerms(e.target.checked)}
                    sx={{ color: '#00ff88' }}
                  />
                }
                label={
                  <Typography variant="body2">
                    I agree to the Terms of Service and understand that trading involves risk
                  </Typography>
                }
                sx={{ mt: 3 }}
              />
            </Box>
          )}

          {/* Step 3: Confirmation */}
          {activeStep === 2 && (
            <Box>
              <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
                Review & Confirm
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Account Information</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Username: {accountData.username}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Email: {accountData.email}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Connected Platforms</Typography>
                  {selectedPlatforms.map(platformId => {
                    const platform = TRADING_PLATFORMS.find(p => p.id === platformId);
                    return (
                      <Chip
                        key={platformId}
                        label={platform?.name}
                        sx={{ backgroundColor: platform?.color, color: '#000', mr: 1, mb: 1 }}
                      />
                    );
                  })}
                </Grid>
              </Grid>
            </Box>
          )}

          {/* Navigation Buttons */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
            <Button
              onClick={activeStep === 0 ? () => window.location.href = '/login' : handleBack}
              startIcon={<ArrowBackIcon />}
              sx={{ color: '#ccc' }}
            >
              {activeStep === 0 ? 'Back to Login' : 'Back'}
            </Button>
            
            <Button
              onClick={activeStep === steps.length - 1 ? handleSubmit : handleNext}
              endIcon={activeStep === steps.length - 1 ? <CheckIcon /> : <ArrowForwardIcon />}
              variant="contained"
              disabled={loading}
              sx={{ backgroundColor: '#00ff88', color: '#000' }}
            >
              {loading ? 'Creating Account...' : activeStep === steps.length - 1 ? 'Create Account' : 'Next'}
            </Button>
          </Box>
        </Paper>
        
        {error && (
          <Alert severity="error" sx={{ mt: 3 }}>
            {error}
          </Alert>
        )}
      </Container>
    </Box>
  );
}