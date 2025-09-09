import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Box,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  SmartToy,
  AttachMoney,
  ShowChart,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { TradingBot, Portfolio, Holding, botApi, portfolioApi } from '../services/api';

export function Dashboard() {
  const [bots, setBots] = useState<TradingBot[]>([]);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock market data for demonstration (in real app, this would come from API)
  const portfolioHistory = [
    { date: '2024-01-01', value: 10000 },
    { date: '2024-01-02', value: 10250 },
    { date: '2024-01-03', value: 10100 },
    { date: '2024-01-04', value: 10400 },
    { date: '2024-01-05', value: 10650 },
    { date: '2024-01-06', value: 10500 },
    { date: '2024-01-07', value: 10800 },
  ];

  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        const [botsResponse, portfolioResponse, holdingsResponse] = await Promise.all([
          botApi.getBots(),
          portfolioApi.getPortfolio(),
          portfolioApi.getHoldings(),
        ]);
        setBots(botsResponse.data);
        setPortfolio(portfolioResponse.data);
        setHoldings(holdingsResponse.data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setError('Failed to load dashboard data. Using demo data.');
        // Set demo data for development
        setPortfolio({
          id: 1,
          total_value: 15750.25,
          available_cash: 2250.75,
        });
        setBots([
          {
            id: 1,
            name: 'Tech Growth Bot',
            description: 'Focuses on technology growth stocks',
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
            description: 'High dividend yield stocks',
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
            description: 'Cryptocurrency swing trading',
            allocated_percentage: 20,
            allocated_amount: 3150,
            current_value: 2369.55,
            status: 'stopped',
            parameters: { asset_type: 'crypto', strategy: 'swing' },
            created_at: '2024-01-01',
            updated_at: '2024-01-07',
          },
        ]);
        setHoldings([
          { id: 1, symbol: 'AAPL', quantity: 15, average_cost: 180.50, current_price: 185.25, market_value: 2778.75, unrealized_pl: 71.25, asset_type: 'stock' },
          { id: 2, symbol: 'MSFT', quantity: 10, average_cost: 350.00, current_price: 365.80, market_value: 3658.00, unrealized_pl: 158.00, asset_type: 'stock' },
          { id: 3, symbol: 'TSLA', quantity: 5, average_cost: 220.00, current_price: 205.40, market_value: 1027.00, unrealized_pl: -73.00, asset_type: 'stock' },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 4 }}>
        <LinearProgress sx={{ width: '100%', mb: 2 }} />
        <Typography>Loading dashboard...</Typography>
      </Box>
    );
  }

  const runningBots = bots.filter(bot => bot.status === 'running').length;
  const totalBots = bots.length;
  const totalPnL = holdings.reduce((sum, holding) => sum + holding.unrealized_pl, 0);
  const totalChange = totalPnL / (portfolio?.total_value || 1) * 100;

  // Data for bot allocation pie chart
  const botAllocationData = bots.map(bot => ({
    name: bot.name,
    value: bot.allocated_percentage,
    amount: bot.current_value,
  }));

  const COLORS = ['#00ff88', '#ff4444', '#ffaa00', '#4488ff', '#ff44aa'];

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <SmartToy sx={{ mr: 1, fontSize: 32 }} />
        <Typography variant="h4">
          🐍 Trading Dashboard
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Portfolio Overview */}
        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AccountBalance sx={{ mr: 1 }} />
                <Typography variant="h6">Portfolio Value</Typography>
              </Box>
              <Typography variant="h3" color="primary" sx={{ fontWeight: 'bold' }}>
                ${portfolio?.total_value.toFixed(2) || '0.00'}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {totalChange >= 0 ? (
                  <TrendingUp sx={{ color: '#00ff88', mr: 0.5 }} />
                ) : (
                  <TrendingDown sx={{ color: '#ff4444', mr: 0.5 }} />
                )}
                <Typography 
                  variant="body1" 
                  sx={{ 
                    color: totalChange >= 0 ? '#00ff88' : '#ff4444',
                    fontWeight: 'bold'
                  }}
                >
                  {totalChange >= 0 ? '+' : ''}{totalChange.toFixed(2)}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                P&L: ${totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Available Cash */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AttachMoney sx={{ mr: 1 }} />
                <Typography variant="h6">Available Cash</Typography>
              </Box>
              <Typography variant="h4" color="secondary">
                ${portfolio?.available_cash.toFixed(2) || '0.00'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Ready to deploy
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Bots */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <SmartToy sx={{ mr: 1 }} />
                <Typography variant="h6">Trading Bots</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {runningBots} / {totalBots}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {runningBots} running, {totalBots - runningBots} stopped
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Total Holdings */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ShowChart sx={{ mr: 1 }} />
                <Typography variant="h6">Holdings</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {holdings.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Positions active
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Portfolio Performance Chart */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Portfolio Performance
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={portfolioHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis 
                  dataKey="date" 
                  stroke="#888"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#888"
                  fontSize={12}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1a1a1a', 
                    border: '1px solid #333',
                    borderRadius: '8px'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#00ff88" 
                  strokeWidth={2}
                  dot={{ fill: '#00ff88', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Bot Allocation */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Bot Allocation
            </Typography>
            {botAllocationData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={botAllocationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    dataKey="value"
                  >
                    {botAllocationData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: any, name: string) => [`${value}%`, name]}
                    contentStyle={{ 
                      backgroundColor: '#1a1a1a', 
                      border: '1px solid #333',
                      borderRadius: '8px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                No bots configured
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Current Holdings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Current Holdings
            </Typography>
            {holdings.length > 0 ? (
              <List>
                {holdings.map((holding, index) => (
                  <React.Fragment key={holding.id}>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography variant="h6">{holding.symbol}</Typography>
                            <Typography variant="h6">${holding.current_price.toFixed(2)}</Typography>
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                              <Typography variant="body2" color="text.secondary">
                                {holding.quantity} shares @ ${holding.average_cost.toFixed(2)}
                              </Typography>
                              <Typography 
                                variant="body2"
                                sx={{ 
                                  color: holding.unrealized_pl >= 0 ? '#00ff88' : '#ff4444',
                                  fontWeight: 'bold'
                                }}
                              >
                                {holding.unrealized_pl >= 0 ? '+' : ''}${holding.unrealized_pl.toFixed(2)}
                              </Typography>
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                              Market Value: ${holding.market_value.toFixed(2)}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < holdings.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                No holdings found
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Active Trading Bots */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Trading Bots
            </Typography>
            {bots.length === 0 ? (
              <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                No trading bots configured. Create your first bot in the Bot Management section.
              </Typography>
            ) : (
              <List>
                {bots.map((bot, index) => (
                  <React.Fragment key={bot.id}>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography variant="h6">{bot.name}</Typography>
                            <Chip
                              label={bot.status}
                              color={bot.status === 'running' ? 'success' : 'default'}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              {bot.description || 'No description'}
                            </Typography>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                              <Typography variant="body2">
                                Allocation: {bot.allocated_percentage}%
                              </Typography>
                              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                ${bot.current_value.toFixed(2)}
                              </Typography>
                            </Box>
                            <Box sx={{ mt: 1 }}>
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
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < bots.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      {error && (
        <Alert severity="warning" sx={{ mt: 3 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
}