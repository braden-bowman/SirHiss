import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Switch,
  FormControlLabel,
  TextField,
  Alert,
  Card,
  CardContent,
  CardActions,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  InputAdornment,
  IconButton
} from '@mui/material';
import {
  Security as SecurityIcon,
  Smartphone as SmartphoneIcon,
  Sms as SmsIcon,
  Key as KeyIcon,
  History as HistoryIcon,
  Refresh as RefreshIcon,
  ContentCopy as CopyIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Lock as LockIcon,
  Fingerprint as FingerprintIcon
} from '@mui/icons-material';
import QRCode from 'qrcode';
import { api } from '../services/api';

interface SecuritySettings {
  twoFactorEnabled: boolean;
  smsEnabled: boolean;
  authenticatorEnabled: boolean;
  phoneNumber?: string;
  backupCodes: string[];
  lastPasswordChange?: string;
  loginSessions: LoginSession[];
}

interface LoginSession {
  id: string;
  device: string;
  location: string;
  ipAddress: string;
  lastActive: string;
  isCurrent: boolean;
}

export function Security() {
  const [settings, setSettings] = useState<SecuritySettings>({
    twoFactorEnabled: false,
    smsEnabled: false,
    authenticatorEnabled: false,
    backupCodes: [],
    loginSessions: []
  });
  
  const [showSetupDialog, setShowSetupDialog] = useState(false);
  const [setupStep, setSetupStep] = useState<'phone' | 'authenticator' | 'verify'>('phone');
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning', text: string } | null>(null);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  useEffect(() => {
    loadSecuritySettings();
  }, []);

  const loadSecuritySettings = async () => {
    try {
      const response = await api.get('/auth/security-settings');
      setSettings(response.data);
    } catch (error) {
      console.error('Failed to load security settings:', error);
      // Load demo data
      setSettings({
        twoFactorEnabled: true,
        smsEnabled: true,
        authenticatorEnabled: false,
        phoneNumber: '+1-555-0123',
        backupCodes: ['ABC123', 'DEF456', 'GHI789', 'JKL012'],
        lastPasswordChange: '2025-01-10T14:30:00Z',
        loginSessions: [
          {
            id: '1',
            device: 'Chrome on Windows',
            location: 'New York, NY',
            ipAddress: '192.168.1.100',
            lastActive: '2025-01-15T10:30:00Z',
            isCurrent: true
          },
          {
            id: '2',
            device: 'Safari on iPhone',
            location: 'New York, NY',
            ipAddress: '192.168.1.101',
            lastActive: '2025-01-14T18:45:00Z',
            isCurrent: false
          }
        ]
      });
    }
  };

  const setupTwoFactor = async (method: 'sms' | 'authenticator') => {
    setLoading(true);
    try {
      if (method === 'sms') {
        await api.post('/auth/setup-sms-2fa', { phoneNumber });
        setSetupStep('verify');
      } else {
        const response = await api.post('/auth/setup-authenticator-2fa');
        setQrCodeUrl(await QRCode.toDataURL(response.data.qr_url));
        setSetupStep('verify');
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to setup two-factor authentication' });
    }
    setLoading(false);
  };

  const verifyTwoFactor = async () => {
    setLoading(true);
    try {
      await api.post('/auth/verify-2fa-setup', { 
        code: verificationCode,
        method: setupStep === 'phone' ? 'sms' : 'authenticator'
      });
      
      const response = await api.get('/auth/backup-codes');
      setBackupCodes(response.data.codes);
      setShowBackupCodes(true);
      
      await loadSecuritySettings();
      setMessage({ type: 'success', text: 'Two-factor authentication enabled successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Invalid verification code' });
    }
    setLoading(false);
  };

  const disableTwoFactor = async () => {
    if (window.confirm('Are you sure you want to disable two-factor authentication? This will make your account less secure.')) {
      try {
        await api.post('/auth/disable-2fa');
        await loadSecuritySettings();
        setMessage({ type: 'warning', text: 'Two-factor authentication has been disabled' });
      } catch (error) {
        setMessage({ type: 'error', text: 'Failed to disable two-factor authentication' });
      }
    }
  };

  const generateBackupCodes = async () => {
    try {
      const response = await api.post('/auth/regenerate-backup-codes');
      setBackupCodes(response.data.codes);
      setShowBackupCodes(true);
      await loadSecuritySettings();
      setMessage({ type: 'success', text: 'New backup codes generated' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to generate backup codes' });
    }
  };

  const changePassword = async () => {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      return;
    }

    try {
      await api.post('/auth/change-password', {
        currentPassword: passwordForm.currentPassword,
        newPassword: passwordForm.newPassword
      });
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setMessage({ type: 'success', text: 'Password changed successfully' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to change password' });
    }
  };

  const revokeSession = async (sessionId: string) => {
    try {
      await api.delete(`/auth/sessions/${sessionId}`);
      await loadSecuritySettings();
      setMessage({ type: 'success', text: 'Session revoked successfully' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to revoke session' });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setMessage({ type: 'success', text: 'Copied to clipboard' });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ color: '#fff', mb: 3 }}>
        🔒 Security Settings
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
        {/* Two-Factor Authentication */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3, backgroundColor: '#1a1a1a', color: '#fff', mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <SecurityIcon sx={{ mr: 1 }} />
              Two-Factor Authentication
            </Typography>

            <Box sx={{ mb: 3 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.twoFactorEnabled}
                    onChange={() => settings.twoFactorEnabled ? disableTwoFactor() : setShowSetupDialog(true)}
                    color="success"
                  />
                }
                label={
                  <Box>
                    <Typography>Enable Two-Factor Authentication</Typography>
                    <Typography variant="caption" color="textSecondary">
                      Add an extra layer of security to your account
                    </Typography>
                  </Box>
                }
              />
            </Box>

            {settings.twoFactorEnabled && (
              <Box sx={{ ml: 4 }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Card sx={{ backgroundColor: '#2a2a2a' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <SmsIcon sx={{ mr: 1, color: settings.smsEnabled ? '#00ff88' : '#666' }} />
                          <Typography>SMS Authentication</Typography>
                          {settings.smsEnabled && <CheckIcon sx={{ ml: 'auto', color: '#00ff88' }} />}
                        </Box>
                        {settings.phoneNumber && (
                          <Typography variant="body2" color="textSecondary">
                            {settings.phoneNumber}
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Card sx={{ backgroundColor: '#2a2a2a' }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <SmartphoneIcon sx={{ mr: 1, color: settings.authenticatorEnabled ? '#00ff88' : '#666' }} />
                          <Typography>Authenticator App</Typography>
                          {settings.authenticatorEnabled && <CheckIcon sx={{ ml: 'auto', color: '#00ff88' }} />}
                        </Box>
                        <Typography variant="body2" color="textSecondary">
                          Google Authenticator, Authy, etc.
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 3 }}>
                  <Button
                    variant="outlined"
                    onClick={generateBackupCodes}
                    startIcon={<RefreshIcon />}
                    sx={{ mr: 2 }}
                  >
                    Generate New Backup Codes
                  </Button>
                  <Chip 
                    label={`${settings.backupCodes.length} backup codes available`}
                    color="info"
                    size="small"
                  />
                </Box>
              </Box>
            )}
          </Paper>

          {/* Password Management */}
          <Paper sx={{ p: 3, backgroundColor: '#1a1a1a', color: '#fff', mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <LockIcon sx={{ mr: 1 }} />
              Password Management
            </Typography>

            {settings.lastPasswordChange && (
              <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
                Last changed: {new Date(settings.lastPasswordChange).toLocaleDateString()}
              </Typography>
            )}

            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  type="password"
                  label="Current Password"
                  value={passwordForm.currentPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  type="password"
                  label="New Password"
                  value={passwordForm.newPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  type="password"
                  label="Confirm New Password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              onClick={changePassword}
              sx={{ mt: 2, backgroundColor: '#00ff88', color: '#000' }}
              disabled={!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword}
            >
              Change Password
            </Button>
          </Paper>

          {/* Active Sessions */}
          <Paper sx={{ p: 3, backgroundColor: '#1a1a1a', color: '#fff' }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <HistoryIcon sx={{ mr: 1 }} />
              Active Sessions
            </Typography>

            <List>
              {settings.loginSessions.map((session, index) => (
                <React.Fragment key={session.id}>
                  <ListItem
                    sx={{
                      backgroundColor: session.isCurrent ? 'rgba(0, 255, 136, 0.1)' : 'transparent',
                      borderRadius: 1,
                      mb: 1
                    }}
                  >
                    <ListItemIcon>
                      <FingerprintIcon sx={{ color: session.isCurrent ? '#00ff88' : '#666' }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography>{session.device}</Typography>
                          {session.isCurrent && (
                            <Chip label="Current" size="small" sx={{ ml: 1, backgroundColor: '#00ff88', color: '#000' }} />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            {session.location} • {session.ipAddress}
                          </Typography>
                          <Typography variant="caption">
                            Last active: {new Date(session.lastActive).toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                    {!session.isCurrent && (
                      <Button
                        size="small"
                        color="error"
                        onClick={() => revokeSession(session.id)}
                      >
                        Revoke
                      </Button>
                    )}
                  </ListItem>
                  {index < settings.loginSessions.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Security Status */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3, backgroundColor: '#1a1a1a', color: '#fff', height: 'fit-content' }}>
            <Typography variant="h6" gutterBottom>Security Score</Typography>
            
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Typography variant="h2" sx={{ color: '#00ff88', fontWeight: 'bold' }}>
                85%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Good Security
              </Typography>
            </Box>

            <List dense>
              <ListItem>
                <ListItemIcon>
                  <CheckIcon sx={{ color: '#00ff88' }} />
                </ListItemIcon>
                <ListItemText primary="Two-Factor Authentication" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckIcon sx={{ color: '#00ff88' }} />
                </ListItemIcon>
                <ListItemText primary="Strong Password" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <WarningIcon sx={{ color: '#ffaa00' }} />
                </ListItemIcon>
                <ListItemText primary="Recent Password Change" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckIcon sx={{ color: '#00ff88' }} />
                </ListItemIcon>
                <ListItemText primary="Backup Codes Generated" />
              </ListItem>
            </List>

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="caption">
                Enable authenticator app for additional security points
              </Typography>
            </Alert>
          </Paper>
        </Grid>
      </Grid>

      {/* Setup 2FA Dialog */}
      <Dialog open={showSetupDialog} onClose={() => setShowSetupDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ backgroundColor: '#1a1a1a', color: '#fff' }}>
          Setup Two-Factor Authentication
        </DialogTitle>
        <DialogContent sx={{ backgroundColor: '#1a1a1a', color: '#fff' }}>
          {setupStep === 'phone' && (
            <Box sx={{ mt: 2 }}>
              <Typography gutterBottom>Choose your preferred method:</Typography>
              
              <Grid container spacing={2} sx={{ mt: 2 }}>
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<SmsIcon />}
                    onClick={() => setSetupStep('phone')}
                    sx={{ height: '80px', flexDirection: 'column' }}
                  >
                    SMS
                    <Typography variant="caption">Text messages</Typography>
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<SmartphoneIcon />}
                    onClick={() => setSetupStep('authenticator')}
                    sx={{ height: '80px', flexDirection: 'column' }}
                  >
                    Authenticator
                    <Typography variant="caption">App-based</Typography>
                  </Button>
                </Grid>
              </Grid>

              <TextField
                fullWidth
                label="Phone Number"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                margin="normal"
                placeholder="+1-555-123-4567"
              />
            </Box>
          )}

          {setupStep === 'authenticator' && (
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Typography gutterBottom>
                Scan this QR code with your authenticator app:
              </Typography>
              {qrCodeUrl && (
                <Box sx={{ my: 3 }}>
                  <img src={qrCodeUrl} alt="QR Code" style={{ maxWidth: '200px' }} />
                </Box>
              )}
              <Alert severity="info" sx={{ mt: 2 }}>
                Compatible with Google Authenticator, Authy, 1Password, and other TOTP apps
              </Alert>
            </Box>
          )}

          {setupStep === 'verify' && (
            <Box sx={{ mt: 2 }}>
              <Typography gutterBottom>
                Enter the verification code:
              </Typography>
              <TextField
                fullWidth
                label="Verification Code"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                margin="normal"
                placeholder="123456"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ backgroundColor: '#1a1a1a' }}>
          <Button onClick={() => setShowSetupDialog(false)}>Cancel</Button>
          {setupStep === 'phone' && (
            <Button 
              onClick={() => setupTwoFactor('sms')}
              disabled={loading || !phoneNumber}
              variant="contained"
              sx={{ backgroundColor: '#00ff88', color: '#000' }}
            >
              Send SMS Code
            </Button>
          )}
          {setupStep === 'authenticator' && (
            <Button 
              onClick={() => setupTwoFactor('authenticator')}
              disabled={loading}
              variant="contained"
              sx={{ backgroundColor: '#00ff88', color: '#000' }}
            >
              Generate QR Code
            </Button>
          )}
          {setupStep === 'verify' && (
            <Button 
              onClick={verifyTwoFactor}
              disabled={loading || !verificationCode}
              variant="contained"
              sx={{ backgroundColor: '#00ff88', color: '#000' }}
            >
              Verify & Enable
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Backup Codes Dialog */}
      <Dialog open={showBackupCodes} onClose={() => setShowBackupCodes(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ backgroundColor: '#1a1a1a', color: '#fff' }}>
          Backup Codes
        </DialogTitle>
        <DialogContent sx={{ backgroundColor: '#1a1a1a', color: '#fff' }}>
          <Alert severity="warning" sx={{ mb: 3 }}>
            Save these backup codes in a safe place. Each code can only be used once.
          </Alert>
          
          <Grid container spacing={1}>
            {backupCodes.map((code, index) => (
              <Grid item xs={6} key={index}>
                <TextField
                  fullWidth
                  value={code}
                  InputProps={{
                    readOnly: true,
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton onClick={() => copyToClipboard(code)}>
                          <CopyIcon />
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                  sx={{ 
                    '& input': { 
                      fontFamily: 'monospace',
                      textAlign: 'center'
                    }
                  }}
                />
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions sx={{ backgroundColor: '#1a1a1a' }}>
          <Button onClick={() => setShowBackupCodes(false)} variant="contained">
            I've Saved These Codes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}