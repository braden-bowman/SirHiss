import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, CircularProgress, Typography } from '@mui/material';
import { AuthPage } from './components/AuthPage.tsx';
import FullApp from './FullApp.tsx';

// Create dark theme for the application
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00ff88',
    },
    secondary: {
      main: '#ff4444',
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
    text: {
      primary: '#ffffff',
      secondary: '#aaaaaa',
    },
  },
  components: {
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '& fieldset': {
              borderColor: '#333',
            },
            '&:hover fieldset': {
              borderColor: '#555',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#00ff88',
            },
          },
          '& .MuiInputLabel-root': {
            color: '#aaa',
          },
          '& .MuiInputLabel-root.Mui-focused': {
            color: '#00ff88',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Check for existing authentication on startup
  useEffect(() => {
    const checkAuth = async () => {
      // Check for stored JWT token authentication
      const token = localStorage.getItem('auth_token') || localStorage.getItem('token');
      const userData = localStorage.getItem('user_data');
      
      if (token && userData) {
        try {
          // First, optimistically set user data from localStorage to reduce flashing
          const cachedUser = JSON.parse(userData);
          setUser(cachedUser);
          setAuthToken(token);
          
          // Then verify token is still valid in the background
          const response = await fetch('http://localhost:9002/api/v1/auth/me', {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
          
          if (response.ok) {
            const userInfo = await response.json();
            setUser(userInfo); // Update with fresh data
          } else {
            // Token is invalid, clear storage and reset state
            localStorage.removeItem('auth_token');
            localStorage.removeItem('token');
            localStorage.removeItem('user_data');
            setUser(null);
            setAuthToken(null);
          }
        } catch (error) {
          // Network error or server down - keep cached user for now
          console.warn('Failed to verify token, using cached user data:', error);
          try {
            const cachedUser = JSON.parse(userData);
            setUser(cachedUser);
            setAuthToken(token);
          } catch (parseError) {
            // If cached data is corrupted, clear everything
            localStorage.removeItem('auth_token');
            localStorage.removeItem('token');
            localStorage.removeItem('user_data');
            setUser(null);
            setAuthToken(null);
          }
        }
      }
      
      setLoading(false);
    };

    checkAuth();
  }, []);

  const handleLogin = (userData: User, token: string) => {
    setUser(userData);
    setAuthToken(token);
    localStorage.setItem('auth_token', token);
    localStorage.setItem('token', token); // Also save as 'token' for compatibility
    localStorage.setItem('user_data', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    setAuthToken(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('token');
    localStorage.removeItem('user_data');
  };

  // Security: Clear session when tab/window closes
  useEffect(() => {
    const handleBeforeUnload = () => {
      // Clear authentication data when tab closes for security
      localStorage.removeItem('auth_token');
      localStorage.removeItem('token');
      localStorage.removeItem('user_data');
    };

    const handleVisibilityChange = () => {
      // Optional: Clear session when page becomes hidden for extended period
      if (document.hidden) {
        // Set a timeout to clear session if hidden for more than 30 minutes
        setTimeout(() => {
          if (document.hidden) {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('token');
            localStorage.removeItem('user_data');
            setUser(null);
            setAuthToken(null);
          }
        }, 30 * 60 * 1000); // 30 minutes
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <CircularProgress sx={{ color: '#00ff88', mb: 2 }} size={60} />
          <Typography variant="h6" sx={{ color: '#00ff88' }}>
            SirHiss
          </Typography>
          <Typography variant="body2" sx={{ color: '#aaa' }}>
            Loading...
          </Typography>
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {user && authToken ? (
        <FullApp user={user} authToken={authToken} onLogout={handleLogout} />
      ) : (
        <AuthPage onLogin={handleLogin} />
      )}
    </ThemeProvider>
  );
}

export default App;