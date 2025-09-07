import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  Grid,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
} from '@mui/material';
import {
  Search,
  TrendingUp,
  TrendingDown,
  Add,
  Remove,
  ShowChart,
  AccountBalance,
  AttachMoney,
} from '@mui/icons-material';
import { Portfolio as PortfolioType, Holding, portfolioApi, marketApi } from '../services/api';

export function Portfolio() {
  const [portfolio, setPortfolio] = useState<PortfolioType | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [marketData, setMarketData] = useState<any[]>([]);

  // Demo market data for popular stocks
  const popularStocks = [
    { symbol: 'AAPL', name: 'Apple Inc.', price: 185.25, change: 2.15, changePercent: 1.17 },
    { symbol: 'MSFT', name: 'Microsoft Corporation', price: 365.80, change: -1.45, changePercent: -0.39 },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 142.50, change: 3.22, changePercent: 2.31 },
    { symbol: 'TSLA', name: 'Tesla, Inc.', price: 205.40, change: -8.75, changePercent: -4.08 },
    { symbol: 'AMZN', name: 'Amazon.com, Inc.', price: 155.30, change: 1.85, changePercent: 1.21 },
    { symbol: 'NVDA', name: 'NVIDIA Corporation', price: 875.45, change: 15.60, changePercent: 1.81 },
    { symbol: 'META', name: 'Meta Platforms, Inc.', price: 485.20, change: -3.15, changePercent: -0.64 },
    { symbol: 'SPY', name: 'SPDR S&P 500 ETF Trust', price: 485.75, change: 2.30, changePercent: 0.48 },
  ];

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [portfolioResponse, holdingsResponse] = await Promise.all([
          portfolioApi.getPortfolio(),
          portfolioApi.getHoldings(),
        ]);
        setPortfolio(portfolioResponse.data);
        setHoldings(holdingsResponse.data);
        setMarketData(popularStocks);
      } catch (error) {
        console.error('Error fetching portfolio data:', error);
        // Set demo data for development
        setPortfolio({
          id: 1,
          total_value: 15750.25,
          available_cash: 2250.75,
        });
        setHoldings([
          { id: 1, symbol: 'AAPL', quantity: 15, average_cost: 180.50, current_price: 185.25, market_value: 2778.75, unrealized_pl: 71.25, asset_type: 'stock' },
          { id: 2, symbol: 'MSFT', quantity: 10, average_cost: 350.00, current_price: 365.80, market_value: 3658.00, unrealized_pl: 158.00, asset_type: 'stock' },
          { id: 3, symbol: 'TSLA', quantity: 5, average_cost: 220.00, current_price: 205.40, market_value: 1027.00, unrealized_pl: -73.00, asset_type: 'stock' },
        ]);
        setMarketData(popularStocks);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      // In a real app, this would call the actual API
      const filtered = popularStocks.filter(stock => 
        stock.symbol.toLowerCase().includes(query.toLowerCase()) ||
        stock.name.toLowerCase().includes(query.toLowerCase())
      );
      setSearchResults(filtered);
    } catch (error) {
      console.error('Error searching stocks:', error);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  if (loading) {
    return <Typography>Loading portfolio...</Typography>;
  }

  const totalUnrealizedPL = holdings.reduce((sum, holding) => sum + holding.unrealized_pl, 0);

  const TabPanel = ({ children, value, index }: any) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <ShowChart sx={{ mr: 1, fontSize: 32 }} />
        <Typography variant="h4">
          Portfolio & Market
        </Typography>
      </Box>

      <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Portfolio Overview" />
        <Tab label="Market Browser" />
      </Tabs>

      <TabPanel value={activeTab} index={0}>
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            <Card sx={{ background: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <AccountBalance sx={{ mr: 1 }} />
                  <Typography variant="h6" color="primary">
                    Total Portfolio Value
                  </Typography>
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  ${portfolio?.total_value.toFixed(2) || '0.00'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <AttachMoney sx={{ mr: 1 }} />
                  <Typography variant="h6" color="primary">
                    Available Cash
                  </Typography>
                </Box>
                <Typography variant="h4">
                  ${portfolio?.available_cash.toFixed(2) || '0.00'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Ready to deploy
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  {totalUnrealizedPL >= 0 ? (
                    <TrendingUp sx={{ mr: 1, color: '#00ff88' }} />
                  ) : (
                    <TrendingDown sx={{ mr: 1, color: '#ff4444' }} />
                  )}
                  <Typography variant="h6" color={totalUnrealizedPL >= 0 ? '#00ff88' : '#ff4444'}>
                    Unrealized P&L
                  </Typography>
                </Box>
                <Typography variant="h4" color={totalUnrealizedPL >= 0 ? '#00ff88' : '#ff4444'}>
                  ${totalUnrealizedPL >= 0 ? '+' : ''}${totalUnrealizedPL.toFixed(2)}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {((totalUnrealizedPL / (portfolio?.total_value || 1)) * 100).toFixed(2)}% of portfolio
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Paper sx={{ overflow: 'hidden' }}>
          <Typography variant="h6" sx={{ p: 2, borderBottom: '1px solid #333' }}>
            Current Holdings
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: '#2a2a2a' }}>
                  <TableCell sx={{ fontWeight: 'bold' }}>Symbol</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>Quantity</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>Avg Cost</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>Current Price</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>Market Value</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>Unrealized P&L</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>Asset Type</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {holdings.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary">
                        No holdings found. Start trading with your bots to see positions here.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  holdings.map((holding) => (
                    <TableRow key={holding.id} sx={{ '&:hover': { backgroundColor: '#2a2a2a' } }}>
                      <TableCell component="th" scope="row">
                        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                          {holding.symbol}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">{holding.quantity}</TableCell>
                      <TableCell align="right">${holding.average_cost.toFixed(2)}</TableCell>
                      <TableCell align="right">${holding.current_price.toFixed(2)}</TableCell>
                      <TableCell align="right">${holding.market_value.toFixed(2)}</TableCell>
                      <TableCell 
                        align="right" 
                        sx={{ 
                          color: holding.unrealized_pl >= 0 ? '#00ff88' : '#ff4444',
                          fontWeight: 'bold'
                        }}
                      >
                        {holding.unrealized_pl >= 0 ? '+' : ''}${holding.unrealized_pl.toFixed(2)}
                      </TableCell>
                      <TableCell align="right">
                        <Chip 
                          label={holding.asset_type}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2 }}>
              <Box sx={{ mb: 3 }}>
                <TextField
                  fullWidth
                  placeholder="Search stocks, ETFs, crypto..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    handleSearch(e.target.value);
                  }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Search />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ mb: 2 }}
                />
              </Box>

              <Typography variant="h6" gutterBottom>
                {searchResults.length > 0 ? 'Search Results' : 'Popular Stocks'}
              </Typography>

              <List>
                {(searchResults.length > 0 ? searchResults : marketData).map((stock, index) => (
                  <React.Fragment key={stock.symbol}>
                    <ListItem>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Box>
                              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                {stock.symbol}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {stock.name}
                              </Typography>
                            </Box>
                            <Box sx={{ textAlign: 'right' }}>
                              <Typography variant="h6">
                                ${stock.price.toFixed(2)}
                              </Typography>
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                                {stock.change >= 0 ? (
                                  <TrendingUp sx={{ color: '#00ff88', mr: 0.5, fontSize: 16 }} />
                                ) : (
                                  <TrendingDown sx={{ color: '#ff4444', mr: 0.5, fontSize: 16 }} />
                                )}
                                <Typography 
                                  variant="body2"
                                  sx={{ 
                                    color: stock.change >= 0 ? '#00ff88' : '#ff4444',
                                    fontWeight: 'bold'
                                  }}
                                >
                                  {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                                </Typography>
                              </Box>
                            </Box>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton 
                          edge="end" 
                          color="primary"
                          onClick={() => console.log('Add to watchlist:', stock.symbol)}
                        >
                          <Add />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                    {index < (searchResults.length > 0 ? searchResults : marketData).length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Market Summary
              </Typography>
              <List>
                <ListItem>
                  <ListItemText
                    primary="S&P 500"
                    secondary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2">4,850.25</Typography>
                        <Typography variant="body2" sx={{ color: '#00ff88' }}>
                          +12.45 (0.26%)
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText
                    primary="NASDAQ"
                    secondary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2">15,180.43</Typography>
                        <Typography variant="body2" sx={{ color: '#ff4444' }}>
                          -25.67 (-0.17%)
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText
                    primary="DOW"
                    secondary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2">37,845.12</Typography>
                        <Typography variant="body2" sx={{ color: '#00ff88' }}>
                          +45.23 (0.12%)
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              </List>
            </Paper>

            <Paper sx={{ p: 2, mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Button variant="outlined" fullWidth>
                  Create New Bot
                </Button>
                <Button variant="outlined" fullWidth>
                  Rebalance Portfolio
                </Button>
                <Button variant="outlined" fullWidth>
                  View Reports
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>
    </Box>
  );
}