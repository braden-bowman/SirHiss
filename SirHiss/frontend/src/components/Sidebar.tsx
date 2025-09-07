import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Box,
  Toolbar
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  SmartToy as BotIcon,
  AccountBalance as PortfolioIcon,
  TrendingUp as MarketIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../services/auth';

const drawerWidth = 240;

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, user } = useAuth();

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'Portfolio', icon: <PortfolioIcon />, path: '/portfolio' },
    { text: 'Market Data', icon: <MarketIcon />, path: '/market' },
    { text: 'Trading Bots', icon: <BotIcon />, path: '/bots' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
    { text: 'Security', icon: <SecurityIcon />, path: '/security' }
  ];

  const handleItemClick = (path: string) => {
    navigate(path);
    onClose();
  };

  const handleLogout = () => {
    logout();
    onClose();
  };

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          background: 'linear-gradient(180deg, #1a1a1a 0%, #0a0a0a 100%)',
          borderRight: '1px solid #333',
          color: '#fff'
        }
      }}
    >
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="h6" sx={{ color: '#00ff88', fontWeight: 'bold' }}>
            🐍 SirHiss
          </Typography>
        </Box>
      </Toolbar>
      
      <Divider sx={{ borderColor: '#333' }} />
      
      <Box sx={{ p: 2, textAlign: 'center', bgcolor: '#2a2a2a', m: 1, borderRadius: 1 }}>
        <Typography variant="body2" sx={{ color: '#aaa', mb: 0.5 }}>
          Logged in as
        </Typography>
        <Typography variant="body1" sx={{ color: '#00ff88', fontWeight: 'bold' }}>
          {user?.username || 'User'}
        </Typography>
      </Box>

      <List sx={{ px: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              onClick={() => handleItemClick(item.path)}
              selected={location.pathname === item.path}
              sx={{
                borderRadius: 1,
                '&.Mui-selected': {
                  backgroundColor: 'rgba(0, 255, 136, 0.1)',
                  borderLeft: '3px solid #00ff88',
                  '& .MuiListItemIcon-root': {
                    color: '#00ff88'
                  },
                  '& .MuiListItemText-primary': {
                    color: '#00ff88',
                    fontWeight: 'bold'
                  }
                },
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.05)'
                }
              }}
            >
              <ListItemIcon sx={{ color: '#ccc', minWidth: 40 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '0.9rem'
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Box sx={{ flexGrow: 1 }} />
      
      <Divider sx={{ borderColor: '#333', mx: 1 }} />
      
      <List sx={{ px: 1, pb: 2 }}>
        <ListItem disablePadding>
          <ListItemButton
            onClick={handleLogout}
            sx={{
              borderRadius: 1,
              '&:hover': {
                backgroundColor: 'rgba(255, 0, 0, 0.1)'
              }
            }}
          >
            <ListItemIcon sx={{ color: '#ff6b6b', minWidth: 40 }}>
              <LogoutIcon />
            </ListItemIcon>
            <ListItemText 
              primary="Logout"
              primaryTypographyProps={{
                fontSize: '0.9rem',
                color: '#ff6b6b'
              }}
            />
          </ListItemButton>
        </ListItem>
      </List>
    </Drawer>
  );
}