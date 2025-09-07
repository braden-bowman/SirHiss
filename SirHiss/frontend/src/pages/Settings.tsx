import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Card,
  CardContent,
  CardActions,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { api } from '../services/api';

interface ApiCredential {
  id: string;
  platform: string;
  name: string;
  apiKey: string;
  apiSecret?: string;
  additionalFields?: Record<string, string>;
  isActive: boolean;
  lastUsed?: string;
  status: 'connected' | 'error' | 'untested';
}

const PLATFORM_CONFIGS = {
  'robinhood': {
    name: 'Robinhood',
    fields: [
      { key: 'username', label: 'Username', type: 'text', required: true },
      { key: 'password', label: 'Password', type: 'password', required: true }
    ],
    color: '#00ff88'
  },
  'yahoo_finance': {
    name: 'Yahoo Finance',
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: false }
    ],
    color: '#7b68ee',
    note: 'Yahoo Finance API is free but rate-limited. API key is optional for basic usage.'
  },
  'alpha_vantage': {
    name: 'Alpha Vantage',
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true }
    ],
    color: '#ff6b6b'
  },
  'polygon': {
    name: 'Polygon.io',
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true }
    ],
    color: '#4ecdc4'
  },
  'binance': {
    name: 'Binance',
    fields: [
      { key: 'api_key', label: 'API Key', type: 'password', required: true },
      { key: 'api_secret', label: 'API Secret', type: 'password', required: true }
    ],
    color: '#f7931a'
  }
};

export function Settings() {
  const [credentials, setCredentials] = useState<ApiCredential[]>([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingCredential, setEditingCredential] = useState<ApiCredential | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState('');
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    try {
      const response = await api.get('/settings/credentials');
      setCredentials(response.data);
    } catch (error) {
      console.error('Failed to load credentials:', error);
      // Load demo data for development
      setCredentials([
        {
          id: '1',
          platform: 'robinhood',
          name: 'Robinhood Trading',
          apiKey: 'demo_user',
          isActive: true,
          status: 'connected',
          lastUsed: '2025-01-15T10:30:00Z'
        },
        {
          id: '2',
          platform: 'yahoo_finance',
          name: 'Yahoo Finance Data',
          apiKey: '',
          isActive: true,
          status: 'connected',
          lastUsed: '2025-01-15T09:15:00Z'
        }
      ]);
    }
  };

  const handleOpenDialog = (credential?: ApiCredential) => {
    if (credential) {
      setEditingCredential(credential);
      setSelectedPlatform(credential.platform);
      setFormData({
        name: credential.name,
        ...credential.additionalFields,
        api_key: credential.apiKey,
        api_secret: credential.apiSecret || ''
      });
    } else {
      setEditingCredential(null);
      setSelectedPlatform('');
      setFormData({});
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingCredential(null);
    setSelectedPlatform('');
    setFormData({});
  };

  const handleSave = async () => {
    if (!selectedPlatform) return;

    setLoading(true);
    try {
      const payload = {
        platform: selectedPlatform,
        name: formData.name || PLATFORM_CONFIGS[selectedPlatform as keyof typeof PLATFORM_CONFIGS].name,
        ...formData
      };

      if (editingCredential) {
        await api.put(`/settings/credentials/${editingCredential.id}`, payload);
      } else {
        await api.post('/settings/credentials', payload);
      }

      await loadCredentials();
      handleCloseDialog();
      setMessage({ type: 'success', text: 'Credentials saved successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save credentials' });
    }
    setLoading(false);
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this credential?')) {
      try {
        await api.delete(`/settings/credentials/${id}`);
        await loadCredentials();
        setMessage({ type: 'success', text: 'Credentials deleted successfully!' });
      } catch (error) {
        setMessage({ type: 'error', text: 'Failed to delete credentials' });
      }
    }
  };

  const handleToggleActive = async (id: string, isActive: boolean) => {
    try {
      await api.patch(`/settings/credentials/${id}`, { isActive: !isActive });
      await loadCredentials();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update credential status' });
    }
  };

  const testConnection = async (credential: ApiCredential) => {
    try {
      setLoading(true);
      await api.post(`/settings/credentials/${credential.id}/test`);
      setMessage({ type: 'success', text: `${credential.name} connection successful!` });
      await loadCredentials();
    } catch (error) {
      setMessage({ type: 'error', text: `${credential.name} connection failed` });
    }
    setLoading(false);
  };

  const togglePasswordVisibility = (credentialId: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [credentialId]: !prev[credentialId]
    }));
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ color: '#fff', mb: 3 }}>
        ⚙️ Settings & API Configuration
      </Typography>

      {message && (
        <Alert 
          severity={message.type} 
          onClose={() => setMessage(null)}
          sx={{ mb: 3 }}
        >
          {message.text}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3, backgroundColor: '#1a1a1a', color: '#fff' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">API Credentials</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog()}
                sx={{ backgroundColor: '#00ff88', color: '#000' }}
              >
                Add Credential
              </Button>
            </Box>

            <Grid container spacing={2}>
              {credentials.map((credential) => {
                const platformConfig = PLATFORM_CONFIGS[credential.platform as keyof typeof PLATFORM_CONFIGS];
                return (
                  <Grid item xs={12} md={6} lg={4} key={credential.id}>
                    <Card sx={{ backgroundColor: '#2a2a2a', color: '#fff', height: '100%' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                          <Box>
                            <Typography variant="h6" sx={{ color: platformConfig?.color || '#fff' }}>
                              {credential.name}
                            </Typography>
                            <Chip 
                              label={platformConfig?.name || credential.platform}
                              size="small"
                              sx={{ backgroundColor: platformConfig?.color || '#666', color: '#000', mt: 1 }}
                            />
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {credential.status === 'connected' && (
                              <CheckCircleIcon sx={{ color: '#00ff88', mr: 1 }} />
                            )}
                            {credential.status === 'error' && (
                              <ErrorIcon sx={{ color: '#ff6b6b', mr: 1 }} />
                            )}
                            <FormControlLabel
                              control={
                                <Switch
                                  checked={credential.isActive}
                                  onChange={() => handleToggleActive(credential.id, credential.isActive)}
                                  color="success"
                                />
                              }
                              label=""
                            />
                          </Box>
                        </Box>

                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" color="textSecondary" gutterBottom>
                            API Key:
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                fontFamily: 'monospace',
                                backgroundColor: '#333',
                                p: 1,
                                borderRadius: 1,
                                flex: 1,
                                mr: 1
                              }}
                            >
                              {showPasswords[credential.id] ? credential.apiKey : '••••••••••••••••'}
                            </Typography>
                            <IconButton
                              size="small"
                              onClick={() => togglePasswordVisibility(credential.id)}
                            >
                              {showPasswords[credential.id] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                            </IconButton>
                          </Box>
                        </Box>

                        {credential.lastUsed && (
                          <Typography variant="caption" color="textSecondary">
                            Last used: {new Date(credential.lastUsed).toLocaleDateString()}
                          </Typography>
                        )}
                      </CardContent>

                      <CardActions>
                        <Button
                          size="small"
                          onClick={() => testConnection(credential)}
                          disabled={loading}
                        >
                          Test Connection
                        </Button>
                        <Button
                          size="small"
                          onClick={() => handleOpenDialog(credential)}
                          startIcon={<EditIcon />}
                        >
                          Edit
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => handleDelete(credential.id)}
                          startIcon={<DeleteIcon />}
                        >
                          Delete
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>

            {credentials.length === 0 && (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="textSecondary">
                  No API credentials configured. Add your first credential to get started.
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Add/Edit Credential Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ backgroundColor: '#1a1a1a', color: '#fff' }}>
          {editingCredential ? 'Edit Credential' : 'Add New Credential'}
        </DialogTitle>
        <DialogContent sx={{ backgroundColor: '#1a1a1a', color: '#fff' }}>
          {!editingCredential && (
            <Box sx={{ mb: 3, mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Select Platform:
              </Typography>
              <Grid container spacing={1}>
                {Object.entries(PLATFORM_CONFIGS).map(([key, config]) => (
                  <Grid item key={key}>
                    <Chip
                      label={config.name}
                      onClick={() => setSelectedPlatform(key)}
                      variant={selectedPlatform === key ? 'filled' : 'outlined'}
                      sx={{
                        backgroundColor: selectedPlatform === key ? config.color : 'transparent',
                        color: selectedPlatform === key ? '#000' : config.color,
                        borderColor: config.color
                      }}
                    />
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}

          {selectedPlatform && (
            <Box>
              <TextField
                fullWidth
                label="Display Name"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                margin="normal"
                sx={{ mb: 2 }}
              />

              {PLATFORM_CONFIGS[selectedPlatform as keyof typeof PLATFORM_CONFIGS]?.fields.map((field) => (
                <TextField
                  key={field.key}
                  fullWidth
                  label={field.label}
                  type={field.type}
                  value={formData[field.key] || ''}
                  onChange={(e) => setFormData({ ...formData, [field.key]: e.target.value })}
                  margin="normal"
                  required={field.required}
                />
              ))}

              {PLATFORM_CONFIGS[selectedPlatform as keyof typeof PLATFORM_CONFIGS]?.note && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  {PLATFORM_CONFIGS[selectedPlatform as keyof typeof PLATFORM_CONFIGS].note}
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ backgroundColor: '#1a1a1a' }}>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleSave}
            variant="contained"
            disabled={loading || !selectedPlatform}
            sx={{ backgroundColor: '#00ff88', color: '#000' }}
          >
            {loading ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}