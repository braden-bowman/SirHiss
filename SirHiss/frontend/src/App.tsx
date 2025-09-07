import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography, IconButton, Box, CssBaseline } from '@mui/material';
import { Menu as MenuIcon } from '@mui/icons-material';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { BotManagement } from './pages/BotManagement';
import { Portfolio } from './pages/Portfolio';
import { Settings } from './pages/Settings';
import { Security } from './pages/Security';
import { Market } from './pages/Market';
import { Sidebar } from './components/Sidebar';
import { AuthProvider, useAuth } from './services/auth';

function AppContent() {
  const { user, loading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleDrawerToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: '#0a0a0a' }}>
        <Typography sx={{ color: '#00ff88' }}>Loading...</Typography>
      </Box>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={!user ? <Login /> : <Navigate to="/dashboard" />} />
      <Route path="/register" element={!user ? <Register /> : <Navigate to="/dashboard" />} />
      <Route path="/*" element={user ? <AuthenticatedApp sidebarOpen={sidebarOpen} onDrawerToggle={handleDrawerToggle} /> : <Navigate to="/login" />} />
    </Routes>
  );
}

function AuthenticatedApp({ sidebarOpen, onDrawerToggle }: { sidebarOpen: boolean, onDrawerToggle: () => void }) {
  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar 
        position="fixed" 
        sx={{ 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: '#1a1a1a',
          borderBottom: '1px solid #333'
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={onDrawerToggle}
            edge="start"
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ color: '#00ff88' }}>
            SirHiss Trading Platform
          </Typography>
        </Toolbar>
      </AppBar>

      <Sidebar open={sidebarOpen} onClose={() => onDrawerToggle()} />

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          marginLeft: sidebarOpen ? '240px' : 0,
          transition: 'margin-left 0.2s',
          backgroundColor: '#0a0a0a',
          minHeight: '100vh'
        }}
      >
        <Toolbar />
        
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/market" element={<Market />} />
          <Route path="/bots" element={<BotManagement />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/security" element={<Security />} />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </Box>
    </Box>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;