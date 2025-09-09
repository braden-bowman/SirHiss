import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Alert,
  Paper,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  LinearProgress,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Delete,
  Edit,
  SmartToy,
  TrendingUp,
  Code,
  Settings,
  ExpandMore,
  Assessment,
  Timeline,
  MonetizationOn,
  Speed,
} from '@mui/icons-material';
import { TradingBot, botApi } from '../services/api.ts';
import { AlgorithmManager } from '../components/AlgorithmManager.tsx';

export function BotManagement() {
  const [bots, setBots] = useState<TradingBot[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editBot, setEditBot] = useState<TradingBot | null>(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [selectedBot, setSelectedBot] = useState<TradingBot | null>(null);
  const [algorithmDialogOpen, setAlgorithmDialogOpen] = useState(false);

  const [newBot, setNewBot] = useState({
    name: '',
    description: '',
    allocated_percentage: 0,
    strategy_type: '',
    parameters: {},
  });

  // Strategy templates
  const strategyTemplates = {
    'momentum': {
      name: 'Momentum Trading',
      description: 'Buys stocks showing upward momentum and sells on downward momentum',
      code: `# Momentum Trading Strategy
def should_buy(symbol, price_data, indicators):
    # Buy if RSI < 30 and price is above 20-day MA
    rsi = indicators['rsi']
    ma_20 = indicators['ma_20']
    current_price = price_data['close']
    
    return rsi < 30 and current_price > ma_20

def should_sell(symbol, position, price_data, indicators):
    # Sell if RSI > 70 or price drops 5% below purchase price
    rsi = indicators['rsi']
    current_price = price_data['close']
    purchase_price = position['average_cost']
    
    return rsi > 70 or current_price < purchase_price * 0.95`,
      parameters: { 'rsi_buy_threshold': 30, 'rsi_sell_threshold': 70, 'stop_loss_percent': 5 }
    },
    'mean_reversion': {
      name: 'Mean Reversion',
      description: 'Buys oversold stocks and sells overbought ones',
      code: `# Mean Reversion Strategy
def should_buy(symbol, price_data, indicators):
    # Buy when price is significantly below moving average
    current_price = price_data['close']
    ma_50 = indicators['ma_50']
    bollinger_lower = indicators['bb_lower']
    
    return current_price < bollinger_lower and current_price < ma_50 * 0.95

def should_sell(symbol, position, price_data, indicators):
    # Sell when price returns to mean or hits stop loss
    current_price = price_data['close']
    ma_50 = indicators['ma_50']
    purchase_price = position['average_cost']
    
    return current_price > ma_50 or current_price < purchase_price * 0.92`,
      parameters: { 'ma_period': 50, 'deviation_threshold': 0.95, 'stop_loss_percent': 8 }
    },
    'dividend_growth': {
      name: 'Dividend Growth',
      description: 'Focuses on dividend-paying stocks with consistent growth',
      code: `# Dividend Growth Strategy
def should_buy(symbol, price_data, indicators):
    # Buy dividend stocks with yield > 3% and consistent growth
    dividend_yield = indicators.get('dividend_yield', 0)
    dividend_growth = indicators.get('dividend_growth_rate', 0)
    pe_ratio = indicators.get('pe_ratio', 100)
    
    return dividend_yield > 3.0 and dividend_growth > 5.0 and pe_ratio < 25

def should_sell(symbol, position, price_data, indicators):
    # Sell if dividend is cut or stock becomes overvalued
    dividend_yield = indicators.get('dividend_yield', 0)
    pe_ratio = indicators.get('pe_ratio', 0)
    current_price = price_data['close']
    purchase_price = position['average_cost']
    
    return dividend_yield < 2.0 or pe_ratio > 30 or current_price < purchase_price * 0.85`,
      parameters: { 'min_dividend_yield': 3.0, 'min_growth_rate': 5.0, 'max_pe_ratio': 25 }
    }
  };

  useEffect(() => {
    fetchBots();
  }, []);

  const fetchBots = async () => {
    try {
      const response = await botApi.getBots();
      setBots(response.data);
    } catch (error) {
      console.error('Error fetching bots:', error);
      // Set demo data for development
      setBots([
        {
          id: 1,
          name: 'Tech Growth Bot',
          description: 'Focuses on technology growth stocks with high momentum',
          allocated_percentage: 40,
          allocated_amount: 6300,
          current_value: 6450.20,
          status: 'running',
          parameters: { risk_level: 'medium', strategy: 'growth' },
          created_at: '2024-01-01',
          updated_at: '2024-01-07',
        },
        {
          id: 2,
          name: 'Dividend Hunter',
          description: 'High dividend yield stocks with consistent payouts',
          allocated_percentage: 30,
          allocated_amount: 4725,
          current_value: 4680.50,
          status: 'running',
          parameters: { min_dividend_yield: 3.5, strategy: 'dividend' },
          created_at: '2024-01-01',
          updated_at: '2024-01-07',
        },
        {
          id: 3,
          name: 'Crypto Swing',
          description: 'Cryptocurrency swing trading with technical analysis',
          allocated_percentage: 20,
          allocated_amount: 3150,
          current_value: 2369.55,
          status: 'stopped',
          parameters: { asset_type: 'crypto', strategy: 'swing' },
          created_at: '2024-01-01',
          updated_at: '2024-01-07',
        },
      ]);
      setError('Using demo data - backend connection failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBot = async () => {
    try {
      await botApi.createBot(newBot);
      setCreateDialogOpen(false);
      setNewBot({
        name: '',
        description: '',
        allocated_percentage: 0,
        strategy_type: '',
        parameters: {},
      });
      fetchBots();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to create bot');
    }
  };

  const handleStartBot = async (id: number) => {
    try {
      await botApi.startBot(id);
      fetchBots();
    } catch (error: any) {
      // Demo: Update local state
      setBots(prev => prev.map(bot => 
        bot.id === id ? { ...bot, status: 'running' as any } : bot
      ));
    }
  };

  const handleStopBot = async (id: number) => {
    try {
      await botApi.stopBot(id);
      fetchBots();
    } catch (error: any) {
      // Demo: Update local state
      setBots(prev => prev.map(bot => 
        bot.id === id ? { ...bot, status: 'stopped' as any } : bot
      ));
    }
  };

  const handleDeleteBot = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this bot? This action cannot be undone.')) {
      try {
        await botApi.deleteBot(id);
        fetchBots();
      } catch (error: any) {
        // Demo: Update local state
        setBots(prev => prev.filter(bot => bot.id !== id));
      }
    }
  };

  const handleSelectTemplate = (templateKey: string) => {
    const template = strategyTemplates[templateKey as keyof typeof strategyTemplates];
    setNewBot({
      ...newBot,
      strategy_type: templateKey,
      name: template.name,
      description: template.description,
      parameters: template.parameters,
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 4 }}>
        <LinearProgress sx={{ width: '100%', mb: 2 }} />
        <Typography>Loading trading bots...</Typography>
      </Box>
    );
  }

  const runningBots = bots.filter(bot => bot.status === 'running').length;
  const totalAllocated = bots.reduce((sum, bot) => sum + bot.allocated_percentage, 0);

  const TabPanel = ({ children, value, index }: any) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <SmartToy sx={{ mr: 1, fontSize: 32 }} />
        <Typography variant="h4">
          🤖 Bot Management
        </Typography>
      </Box>


      {/* Bot Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Assessment sx={{ mr: 1, color: '#00ff88' }} />
                <Typography variant="h6">Active Bots</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {runningBots} / {bots.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Timeline sx={{ mr: 1, color: '#ffaa00' }} />
                <Typography variant="h6">Total Allocated</Typography>
              </Box>
              <Typography variant="h4" color="secondary">
                {totalAllocated.toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <MonetizationOn sx={{ mr: 1, color: '#4488ff' }} />
                <Typography variant="h6">Total Value</Typography>
              </Box>
              <Typography variant="h4">
                ${bots.reduce((sum, bot) => sum + bot.current_value, 0).toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Speed sx={{ mr: 1, color: '#ff4444' }} />
                <Typography variant="h6">Performance</Typography>
              </Box>
              <Typography variant="h4" sx={{ color: '#00ff88' }}>
                +2.45%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 3 }}>
        <Tab label="My Bots" />
        <Tab label="Strategy Templates" />
        <Tab label="Algorithm Manager" />
      </Tabs>

      <TabPanel value={activeTab} index={0}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5">
            Your Trading Bots ({bots.length})
          </Typography>
          <Button
            variant="contained"
            startIcon={<SmartToy />}
            onClick={() => setCreateDialogOpen(true)}
            sx={{ background: 'linear-gradient(45deg, #00ff88 30%, #4488ff 90%)' }}
          >
            Create New Bot
          </Button>
        </Box>

        <Grid container spacing={3}>
          {bots.map((bot) => (
            <Grid item xs={12} md={6} lg={4} key={bot.id}>
              <Card sx={{ 
                height: '100%',
                background: bot.status === 'running' 
                  ? 'linear-gradient(135deg, #1a1a1a 0%, #2a4a2a 100%)'
                  : 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)',
                border: bot.status === 'running' ? '1px solid #00ff8844' : '1px solid #333'
              }}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {bot.name}
                    </Typography>
                    <Chip
                      label={bot.status}
                      icon={bot.status === 'running' ? <PlayArrow /> : <Stop />}
                      color={
                        bot.status === 'running'
                          ? 'success'
                          : bot.status === 'error'
                          ? 'error'
                          : 'default'
                      }
                      size="small"
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: 40 }}>
                    {bot.description || 'No description provided'}
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      Portfolio Allocation: {bot.allocated_percentage}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={bot.allocated_percentage}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: '#333',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: bot.status === 'running' ? '#00ff88' : '#666',
                        },
                      }}
                    />
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Current Value:
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      ${bot.current_value.toFixed(2)}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Allocated:
                    </Typography>
                    <Typography variant="body2">
                      ${bot.allocated_amount.toFixed(2)}
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      P&L:
                    </Typography>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontWeight: 'bold',
                        color: bot.current_value > bot.allocated_amount ? '#00ff88' : '#ff4444'
                      }}
                    >
                      {bot.current_value > bot.allocated_amount ? '+' : ''}
                      ${(bot.current_value - bot.allocated_amount).toFixed(2)}
                    </Typography>
                  </Box>
                </CardContent>
                
                <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                  <Box>
                    {bot.status === 'running' ? (
                      <IconButton
                        color="secondary"
                        onClick={() => handleStopBot(bot.id)}
                        title="Stop Bot"
                        sx={{ 
                          backgroundColor: '#ff444444',
                          '&:hover': { backgroundColor: '#ff444466' }
                        }}
                      >
                        <Stop />
                      </IconButton>
                    ) : (
                      <IconButton
                        color="primary"
                        onClick={() => handleStartBot(bot.id)}
                        title="Start Bot"
                        sx={{ 
                          backgroundColor: '#00ff8844',
                          '&:hover': { backgroundColor: '#00ff8866' }
                        }}
                      >
                        <PlayArrow />
                      </IconButton>
                    )}
                  </Box>
                  
                  <Box>
                    <IconButton
                      onClick={() => setEditBot(bot)}
                      title="Configure Bot"
                      size="small"
                    >
                      <Settings />
                    </IconButton>
                    <IconButton
                      onClick={() => {
                        setSelectedBot(bot);
                        setAlgorithmDialogOpen(true);
                      }}
                      title="Manage Algorithms"
                      size="small"
                      sx={{ color: '#00ff88' }}
                    >
                      <Code />
                    </IconButton>
                    <IconButton
                      color="error"
                      onClick={() => handleDeleteBot(bot.id)}
                      title="Delete Bot"
                      size="small"
                    >
                      <Delete />
                    </IconButton>
                  </Box>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <Typography variant="h5" gutterBottom>
          Strategy Templates
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Choose from proven trading strategies and customize them for your needs.
        </Typography>

        <Grid container spacing={3}>
          {Object.entries(strategyTemplates).map(([key, template]) => (
            <Grid item xs={12} md={6} key={key}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                    {template.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {template.description}
                  </Typography>
                  
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography variant="body2">
                        <Code sx={{ mr: 1, fontSize: 16, verticalAlign: 'middle' }} />
                        View Strategy Code
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <pre style={{ 
                        backgroundColor: '#0a0a0a', 
                        padding: '12px', 
                        borderRadius: '4px',
                        fontSize: '12px',
                        overflow: 'auto',
                        fontFamily: 'monospace'
                      }}>
                        {template.code}
                      </pre>
                    </AccordionDetails>
                  </Accordion>
                </CardContent>
                <CardActions>
                  <Button
                    variant="outlined"
                    startIcon={<TrendingUp />}
                    onClick={() => {
                      handleSelectTemplate(key);
                      setCreateDialogOpen(true);
                    }}
                  >
                    Use This Strategy
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <Typography variant="h5" gutterBottom>
          Algorithm Manager
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Configure advanced trading algorithms for your bots. Select a bot to manage its algorithms.
        </Typography>
        
        {selectedBot ? (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <SmartToy sx={{ color: '#00ff88' }} />
              <Typography variant="h6">
                Managing algorithms for: {selectedBot.name}
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => setSelectedBot(null)}
              >
                Select Different Bot
              </Button>
            </Box>
            <AlgorithmManager 
              botId={selectedBot.id} 
              onAlgorithmsChange={() => fetchBots()}
            />
          </Box>
        ) : (
          <Box>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Select a bot to manage its algorithms:
            </Typography>
            <Grid container spacing={2}>
              {bots.map((bot) => (
                <Grid item xs={12} md={6} lg={4} key={bot.id}>
                  <Card 
                    sx={{ 
                      cursor: 'pointer',
                      transition: 'all 0.3s',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 4
                      }
                    }}
                    onClick={() => setSelectedBot(bot)}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <SmartToy sx={{ color: bot.status === 'running' ? '#00ff88' : '#666' }} />
                        <Box>
                          <Typography variant="h6">
                            {bot.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {bot.status} • {bot.allocated_percentage}% allocated
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}
      </TabPanel>

      {/* Algorithm Management Dialog */}
      <Dialog 
        open={algorithmDialogOpen} 
        onClose={() => setAlgorithmDialogOpen(false)} 
        maxWidth="lg" 
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Code sx={{ mr: 1, color: '#00ff88' }} />
            Algorithm Manager - {selectedBot?.name}
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedBot && (
            <AlgorithmManager 
              botId={selectedBot.id} 
              onAlgorithmsChange={() => fetchBots()}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAlgorithmDialogOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Bot Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <SmartToy sx={{ mr: 1 }} />
            Create New Trading Bot
          </Box>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                autoFocus
                margin="dense"
                label="Bot Name"
                fullWidth
                variant="outlined"
                value={newBot.name}
                onChange={(e) => setNewBot({ ...newBot, name: e.target.value })}
                sx={{ mb: 2 }}
              />
              <TextField
                margin="dense"
                label="Description"
                fullWidth
                multiline
                rows={2}
                variant="outlined"
                value={newBot.description}
                onChange={(e) => setNewBot({ ...newBot, description: e.target.value })}
                sx={{ mb: 2 }}
              />
              <TextField
                margin="dense"
                label="Portfolio Allocation (%)"
                type="number"
                fullWidth
                variant="outlined"
                value={newBot.allocated_percentage}
                onChange={(e) => setNewBot({ ...newBot, allocated_percentage: parseFloat(e.target.value) || 0 })}
                inputProps={{ min: 0, max: 100 - totalAllocated, step: 0.1 }}
                helperText={`Available: ${(100 - totalAllocated).toFixed(1)}%`}
                sx={{ mb: 2 }}
              />
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Strategy Type</InputLabel>
                <Select
                  value={newBot.strategy_type}
                  label="Strategy Type"
                  onChange={(e) => handleSelectTemplate(e.target.value)}
                >
                  <MenuItem value="">Custom Strategy</MenuItem>
                  {Object.entries(strategyTemplates).map(([key, template]) => (
                    <MenuItem key={key} value={key}>{template.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Parameters
              </Typography>
              {Object.entries(newBot.parameters).map(([key, value]) => (
                <TextField
                  key={key}
                  margin="dense"
                  label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  fullWidth
                  variant="outlined"
                  type="number"
                  value={value as number}
                  onChange={(e) => setNewBot({
                    ...newBot,
                    parameters: { ...newBot.parameters, [key]: parseFloat(e.target.value) || 0 }
                  })}
                  sx={{ mb: 1 }}
                />
              ))}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateBot} 
            variant="contained"
            disabled={!newBot.name || !newBot.allocated_percentage}
            sx={{ background: 'linear-gradient(45deg, #00ff88 30%, #4488ff 90%)' }}
          >
            Create Bot
          </Button>
        </DialogActions>
      </Dialog>
      
      {error && (
        <Alert severity="warning" sx={{ mt: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
    </Box>
  );
}