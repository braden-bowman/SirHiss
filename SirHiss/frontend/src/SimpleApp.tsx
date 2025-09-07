import React from 'react';
import { Box, Typography, Button, Container } from '@mui/material';

function SimpleApp() {
  return (
    <Container>
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Typography variant="h2" sx={{ color: '#00ff88', mb: 2 }}>
          🐍 SirHiss Trading Platform
        </Typography>
        <Typography variant="h5" sx={{ mb: 4 }}>
          System is starting up...
        </Typography>
        <Button 
          variant="contained"
          size="large"
          onClick={() => window.location.reload()}
          sx={{ backgroundColor: '#00ff88', color: '#000' }}
        >
          Refresh Application
        </Button>
      </Box>
    </Container>
  );
}

export default SimpleApp;