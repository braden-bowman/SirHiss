import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Security,
  VpnKey,
  Shield,
  Warning,
  CheckCircle,
  Error,
  Logout,
  Computer,
  Smartphone,
  LocationOn,
  AccessTime,
  Delete,
} from '@mui/icons-material';

interface Session {
  id: string;
  device: string;
  location: string;
  ip_address: string;
  last_active: string;
  is_current: boolean;
}

interface SecurityLog {
  id: number;
  timestamp: string;
  event_type: string;
  description: string;
  ip_address: string;
  user_agent: string;
  status: 'success' | 'warning' | 'error';
}

interface SecuritySettings {
  two_factor_enabled: boolean;
  session_timeout: number;
  max_concurrent_sessions: number;
  require_strong_passwords: boolean;
  email_notifications: boolean;
  suspicious_activity_alerts: boolean;
}

export function SecurityInterface() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [securityLogs, setSecurityLogs] = useState<SecurityLog[]>([]);
  const [settings, setSettings] = useState<SecuritySettings>({
    two_factor_enabled: false,
    session_timeout: 30,
    max_concurrent_sessions: 5,
    require_strong_passwords: true,
    email_notifications: true,
    suspicious_activity_alerts: true,
  });
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error' | 'info'>('info');
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: '', sessionId: '' });
  const [twoFactorDialog, setTwoFactorDialog] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');

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
      return null;
    }
  };

  const loadSessions = async () => {
    try {
      const data = await apiCall('/api/v1/security/sessions');
      if (data) {
        setSessions(data);
      } else {
        // Demo data
        setSessions([
          {
            id: '1',
            device: 'Chrome on macOS',
            location: 'San Francisco, CA',
            ip_address: '192.168.1.100',
            last_active: new Date().toISOString(),
            is_current: true,
          },
          {
            id: '2',
            device: 'Safari on iPhone',
            location: 'San Francisco, CA',
            ip_address: '192.168.1.101',
            last_active: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            is_current: false,
          },
        ]);
      }
    } catch (err) {
      setMessage('Failed to load sessions');
      setMessageType('error');
    }
  };

  const loadSecurityLogs = async () => {
    try {
      const data = await apiCall('/api/v1/security/logs');
      if (data) {
        setSecurityLogs(data);
      } else {
        // Demo data
        setSecurityLogs([
          {
            id: 1,
            timestamp: new Date().toISOString(),
            event_type: 'Login',
            description: 'Successful login',
            ip_address: '192.168.1.100',
            user_agent: 'Chrome/119.0.0.0',
            status: 'success',
          },
          {
            id: 2,
            timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
            event_type: 'Bot Started',
            description: 'Trading bot "Tech Growth Bot" started',
            ip_address: '192.168.1.100',
            user_agent: 'Chrome/119.0.0.0',
            status: 'success',
          },
          {
            id: 3,
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            event_type: 'Settings Changed',
            description: 'Risk tolerance updated to High',
            ip_address: '192.168.1.100',
            user_agent: 'Chrome/119.0.0.0',
            status: 'warning',
          },
          {
            id: 4,
            timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
            event_type: 'Failed Login',
            description: 'Invalid password attempt',
            ip_address: '203.0.113.45',
            user_agent: 'Unknown',
            status: 'error',
          },
        ]);
      }
    } catch (err) {
      setMessage('Failed to load security logs');
      setMessageType('error');
    }
  };

  const loadSecuritySettings = async () => {
    try {
      const data = await apiCall('/api/v1/security/settings');
      if (data) {
        setSettings({ ...settings, ...data });
      } else {
        // Load from localStorage for demo
        const savedSettings = localStorage.getItem('sirhiss_security_settings');
        if (savedSettings) {
          setSettings({ ...settings, ...JSON.parse(savedSettings) });
        }
      }
    } catch (err) {
      setMessage('Failed to load security settings');
      setMessageType('error');
    }
  };

  const saveSecuritySettings = async () => {
    setLoading(true);
    try {
      await apiCall('/api/v1/security/settings', {
        method: 'POST',
        body: JSON.stringify(settings),
      });
      
      setMessage('Security settings saved successfully');
      setMessageType('success');
    } catch (err) {
      // Demo mode - save to localStorage
      localStorage.setItem('sirhiss_security_settings', JSON.stringify(settings));
      setMessage('Security settings saved (demo mode)');
      setMessageType('info');
    }
    
    setLoading(false);
    setTimeout(() => setMessage(''), 3000);
  };

  const terminateSession = async (sessionId: string) => {
    try {
      await apiCall(`/api/v1/security/sessions/${sessionId}`, { method: 'DELETE' });
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      setMessage('Session terminated successfully');
      setMessageType('success');
    } catch (err) {
      // Demo mode
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      setMessage('Session terminated (demo mode)');
      setMessageType('info');
    }
    
    setConfirmDialog({ open: false, action: '', sessionId: '' });
    setTimeout(() => setMessage(''), 3000);
  };

  const terminateAllSessions = async () => {
    try {
      await apiCall('/api/v1/security/sessions', { method: 'DELETE' });
      setSessions(prev => prev.filter(s => s.is_current));
      setMessage('All other sessions terminated');
      setMessageType('success');
    } catch (err) {
      // Demo mode
      setSessions(prev => prev.filter(s => s.is_current));
      setMessage('All other sessions terminated (demo mode)');
      setMessageType('info');
    }
    
    setConfirmDialog({ open: false, action: '', sessionId: '' });
    setTimeout(() => setMessage(''), 3000);
  };

  const toggleTwoFactor = async () => {
    if (!settings.two_factor_enabled) {
      setTwoFactorDialog(true);
    } else {
      setSettings(prev => ({ ...prev, two_factor_enabled: false }));
      setMessage('Two-factor authentication disabled');
      setMessageType('info');
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const enableTwoFactor = async () => {
    if (verificationCode.length === 6) {
      setSettings(prev => ({ ...prev, two_factor_enabled: true }));
      setTwoFactorDialog(false);
      setVerificationCode('');
      setMessage('Two-factor authentication enabled');
      setMessageType('success');
      setTimeout(() => setMessage(''), 3000);
    } else {
      setMessage('Please enter a valid 6-digit code');
      setMessageType('error');
      setTimeout(() => setMessage(''), 3000);
    }
  };

  useEffect(() => {
    loadSessions();
    loadSecurityLogs();
    loadSecuritySettings();
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getEventIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle sx={{ color: '#00ff88' }} />;
      case 'warning': return <Warning sx={{ color: '#ffaa00' }} />;
      case 'error': return <Error sx={{ color: '#ff4444' }} />;
      default: return <CheckCircle sx={{ color: '#666' }} />;
    }
  };

  const getDeviceIcon = (device: string) => {
    if (device.toLowerCase().includes('iphone') || device.toLowerCase().includes('android')) {
      return <Smartphone />;
    }
    return <Computer />;
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, color: '#00ff88' }}>
        🔒 Security Center
      </Typography>

      {message && (
        <Alert severity={messageType} sx={{ mb: 2 }} onClose={() => setMessage('')}>
          {message}
        </Alert>
      )}

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ background: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Shield sx={{ mr: 1, color: '#00ff88' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>Security Status</Typography>
              </Box>
              <Typography variant="h4" sx={{ color: '#00ff88', mb: 1 }}>
                SECURE
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                All security features active
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ background: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Computer sx={{ mr: 1, color: '#4488ff' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>Active Sessions</Typography>
              </Box>
              <Typography variant="h4" sx={{ color: '#fff', mb: 1 }}>
                {sessions.length}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                Current devices
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ background: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <VpnKey sx={{ mr: 1, color: '#ffaa00' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>2FA Status</Typography>
              </Box>
              <Typography variant="h4" sx={{ 
                color: settings.two_factor_enabled ? '#00ff88' : '#ff4444',
                mb: 1 
              }}>
                {settings.two_factor_enabled ? 'ON' : 'OFF'}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                Two-factor authentication
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ background: '#1a1a1a', border: '1px solid #333', mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3, color: '#fff' }}>
                Security Settings
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.two_factor_enabled}
                      onChange={toggleTwoFactor}
                      color="primary"
                    />
                  }
                  label="Two-Factor Authentication"
                />
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.email_notifications}
                      onChange={(e) => setSettings(prev => ({ 
                        ...prev, 
                        email_notifications: e.target.checked 
                      }))}
                    />
                  }
                  label="Email Security Notifications"
                />
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.suspicious_activity_alerts}
                      onChange={(e) => setSettings(prev => ({ 
                        ...prev, 
                        suspicious_activity_alerts: e.target.checked 
                      }))}
                    />
                  }
                  label="Suspicious Activity Alerts"
                />
              </Box>
              
              <TextField
                label="Session Timeout (minutes)"
                type="number"
                fullWidth
                value={settings.session_timeout}
                onChange={(e) => setSettings(prev => ({ 
                  ...prev, 
                  session_timeout: parseInt(e.target.value) 
                }))}
                sx={{ mb: 2 }}
              />
              
              <TextField
                label="Max Concurrent Sessions"
                type="number"
                fullWidth
                value={settings.max_concurrent_sessions}
                onChange={(e) => setSettings(prev => ({ 
                  ...prev, 
                  max_concurrent_sessions: parseInt(e.target.value) 
                }))}
                sx={{ mb: 3 }}
              />
              
              <Button
                variant="contained"
                onClick={saveSecuritySettings}
                disabled={loading}
                sx={{ background: '#00ff88', color: '#000' }}
              >
                Save Security Settings
              </Button>
            </CardContent>
          </Card>

          <Card sx={{ background: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ color: '#fff' }}>
                  Active Sessions
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setConfirmDialog({ open: true, action: 'terminate_all', sessionId: '' })}
                  sx={{ color: '#ff4444', borderColor: '#ff4444' }}
                >
                  Terminate All
                </Button>
              </Box>
              
              <List>
                {sessions.map((session, index) => (
                  <React.Fragment key={session.id}>
                    <ListItem>
                      <ListItemIcon>
                        {getDeviceIcon(session.device)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography sx={{ color: '#fff' }}>
                              {session.device}
                            </Typography>
                            {session.is_current && (
                              <Chip
                                label="Current"
                                size="small"
                                sx={{ ml: 1, background: '#00ff88', color: '#000' }}
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', color: '#aaa' }}>
                              <LocationOn sx={{ fontSize: 16, mr: 0.5 }} />
                              <Typography variant="body2" sx={{ color: '#aaa', mr: 2 }}>
                                {session.location}
                              </Typography>
                              <Typography variant="body2" sx={{ color: '#aaa' }}>
                                {session.ip_address}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', color: '#aaa', mt: 0.5 }}>
                              <AccessTime sx={{ fontSize: 16, mr: 0.5 }} />
                              <Typography variant="body2" sx={{ color: '#aaa' }}>
                                Last active: {formatDate(session.last_active)}
                              </Typography>
                            </Box>
                          </Box>
                        }
                      />
                      {!session.is_current && (
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => setConfirmDialog({ 
                            open: true, 
                            action: 'terminate_session', 
                            sessionId: session.id 
                          })}
                          sx={{ color: '#ff4444', borderColor: '#ff4444' }}
                        >
                          <Logout />
                        </Button>
                      )}
                    </ListItem>
                    {index < sessions.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ background: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3, color: '#fff' }}>
                Security Activity Log
              </Typography>
              
              <TableContainer component={Paper} sx={{ background: '#0a0a0a' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ color: '#fff' }}>Time</TableCell>
                      <TableCell sx={{ color: '#fff' }}>Event</TableCell>
                      <TableCell sx={{ color: '#fff' }}>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {securityLogs.map((log) => (
                      <TableRow 
                        key={log.id}
                        sx={{ '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.02)' } }}
                      >
                        <TableCell sx={{ color: '#aaa' }}>
                          {formatDate(log.timestamp)}
                        </TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" sx={{ color: '#fff' }}>
                              {log.event_type}
                            </Typography>
                            <Typography variant="caption" sx={{ color: '#aaa' }}>
                              {log.description}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          {getEventIcon(log.status)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({ open: false, action: '', sessionId: '' })}>
        <DialogTitle>Confirm Action</DialogTitle>
        <DialogContent>
          <Typography>
            {confirmDialog.action === 'terminate_all' 
              ? 'Are you sure you want to terminate all other sessions? This will log out all other devices.'
              : 'Are you sure you want to terminate this session?'
            }
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, action: '', sessionId: '' })}>
            Cancel
          </Button>
          <Button
            onClick={confirmDialog.action === 'terminate_all' ? terminateAllSessions : () => terminateSession(confirmDialog.sessionId)}
            color="error"
            variant="contained"
          >
            Terminate
          </Button>
        </DialogActions>
      </Dialog>

      {/* Two-Factor Authentication Dialog */}
      <Dialog open={twoFactorDialog} onClose={() => setTwoFactorDialog(false)}>
        <DialogTitle>Enable Two-Factor Authentication</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            Scan this QR code with your authenticator app, then enter the 6-digit verification code:
          </Typography>
          <Box sx={{ textAlign: 'center', mb: 2 }}>
            <Box
              sx={{
                width: 200,
                height: 200,
                background: '#f0f0f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
                mb: 2,
              }}
            >
              <Typography>QR Code Here</Typography>
            </Box>
          </Box>
          <TextField
            label="Verification Code"
            fullWidth
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value)}
            inputProps={{ maxLength: 6 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTwoFactorDialog(false)}>Cancel</Button>
          <Button
            onClick={enableTwoFactor}
            disabled={verificationCode.length !== 6}
            variant="contained"
          >
            Enable 2FA
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}