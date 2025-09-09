import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  ShowChart,
} from '@mui/icons-material';

interface Holding {
  id: number;
  symbol: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  bot_name?: string;
}

interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  total_pnl: number;
  total_pnl_percent: number;
  available_cash: number;
  number_of_positions: number;
}

function TabPanel({ children, value, index }: any) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export function PortfolioInterface() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState(0);

  const API_BASE = 'http://localhost:9002';

  const apiCall = async (endpoint: string) => {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`);
      if (!response.ok) throw new Error(`API error: ${response.status}`);
      return await response.json();
    } catch (err) {
      console.error(`API call failed for ${endpoint}:`, err);
      return null;
    }
  };

  const loadPortfolioData = async () => {
    setLoading(true);
    
    // Load portfolio summary
    const summaryData = await apiCall('/api/v1/portfolio/summary');
    if (summaryData) {
      setSummary(summaryData);
    } else {
      // Demo data
      setSummary({
        total_value: 15750.25,
        total_cost: 15379.00,
        total_pnl: 371.25,
        total_pnl_percent: 2.41,
        available_cash: 2250.75,
        number_of_positions: 5
      });
    }

    // Load holdings
    const holdingsData = await apiCall('/api/v1/portfolio/positions');
    if (holdingsData) {
      setHoldings(holdingsData);
    } else {
      // Demo data
      setHoldings([
        {
          id: 1,
          symbol: 'AAPL',
          quantity: 15,
          average_cost: 178.50,
          current_price: 185.20,
          market_value: 2778.00,
          unrealized_pnl: 100.50,
          unrealized_pnl_percent: 3.75,
          bot_name: 'Tech Growth Bot'
        },
        {
          id: 2,
          symbol: 'MSFT',
          quantity: 12,
          average_cost: 345.00,
          current_price: 352.75,
          market_value: 4233.00,
          unrealized_pnl: 93.00,
          unrealized_pnl_percent: 2.25,
          bot_name: 'Tech Growth Bot'
        },
        {
          id: 3,
          symbol: 'GOOGL',
          quantity: 8,
          average_cost: 142.30,
          current_price: 139.85,
          market_value: 1118.80,
          unrealized_pnl: -19.60,
          unrealized_pnl_percent: -1.72,
          bot_name: 'Tech Growth Bot'
        },
        {
          id: 4,
          symbol: 'JNJ',
          quantity: 25,
          average_cost: 165.80,
          current_price: 167.45,
          market_value: 4186.25,
          unrealized_pnl: 41.25,
          unrealized_pnl_percent: 0.99,
          bot_name: 'Dividend Hunter'
        },
        {
          id: 5,
          symbol: 'KO',
          quantity: 40,
          average_cost: 58.75,
          current_price: 59.20,
          market_value: 2368.00,
          unrealized_pnl: 18.00,
          unrealized_pnl_percent: 0.77,
          bot_name: 'Dividend Hunter'
        }
      ]);
    }
    
    setLoading(false);
  };

  useEffect(() => {
    loadPortfolioData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadPortfolioData, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const renderOverview = () => (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, color: '#fff' }}>
        Portfolio Overview
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1a1a1a 0%, #2a4a2a 100%)', border: '1px solid #00ff8844' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AccountBalance sx={{ mr: 1, color: '#00ff88' }} />
                <Typography variant="h6" sx={{ color: '#00ff88' }}>Total Value</Typography>
              </Box>
              <Typography variant="h4" sx={{ color: '#fff', mb: 1 }}>
                {summary ? formatCurrency(summary.total_value) : '$0.00'}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                Portfolio market value
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ShowChart sx={{ mr: 1, color: summary?.total_pnl >= 0 ? '#00ff88' : '#ff4444' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>Total P&L</Typography>
              </Box>
              <Typography variant="h4" sx={{ 
                color: summary?.total_pnl >= 0 ? '#00ff88' : '#ff4444',
                mb: 1 
              }}>
                {summary ? formatCurrency(summary.total_pnl) : '$0.00'}
              </Typography>
              <Typography variant="body2" sx={{ 
                color: summary?.total_pnl >= 0 ? '#00ff88' : '#ff4444' 
              }}>
                {summary ? formatPercent(summary.total_pnl_percent) : '0.00%'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUp sx={{ mr: 1, color: '#4488ff' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>Available Cash</Typography>
              </Box>
              <Typography variant="h4" sx={{ color: '#fff', mb: 1 }}>
                {summary ? formatCurrency(summary.available_cash) : '$0.00'}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                Ready to invest
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingDown sx={{ mr: 1, color: '#ffaa00' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>Positions</Typography>
              </Box>
              <Typography variant="h4" sx={{ color: '#fff', mb: 1 }}>
                {summary ? summary.number_of_positions : 0}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                Active holdings
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {loading && (
        <Box sx={{ width: '100%', mb: 2 }}>
          <LinearProgress sx={{ 
            backgroundColor: '#333',
            '& .MuiLinearProgress-bar': { backgroundColor: '#00ff88' }
          }} />
        </Box>
      )}

      {error && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );

  const renderHoldings = () => (
    <TableContainer component={Paper} sx={{ background: '#1a1a1a' }}>
      <Table>
        <TableHead>
          <TableRow sx={{ '& th': { borderBottom: '1px solid #333', color: '#fff' } }}>
            <TableCell>Symbol</TableCell>
            <TableCell align="right">Quantity</TableCell>
            <TableCell align="right">Avg Cost</TableCell>
            <TableCell align="right">Current Price</TableCell>
            <TableCell align="right">Market Value</TableCell>
            <TableCell align="right">P&L</TableCell>
            <TableCell align="right">P&L %</TableCell>
            <TableCell>Bot</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {holdings.map((holding) => (
            <TableRow 
              key={holding.id}
              sx={{ 
                '& td': { borderBottom: '1px solid #333', color: '#fff' },
                '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.02)' }
              }}
            >
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="body1" sx={{ fontWeight: 'bold', color: '#00ff88' }}>
                    {holding.symbol}
                  </Typography>
                </Box>
              </TableCell>
              <TableCell align="right">{holding.quantity}</TableCell>
              <TableCell align="right">{formatCurrency(holding.average_cost)}</TableCell>
              <TableCell align="right">{formatCurrency(holding.current_price)}</TableCell>
              <TableCell align="right">{formatCurrency(holding.market_value)}</TableCell>
              <TableCell align="right">
                <Typography sx={{ 
                  color: holding.unrealized_pnl >= 0 ? '#00ff88' : '#ff4444',
                  fontWeight: 'bold'
                }}>
                  {formatCurrency(holding.unrealized_pnl)}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography sx={{ 
                  color: holding.unrealized_pnl_percent >= 0 ? '#00ff88' : '#ff4444',
                  fontWeight: 'bold'
                }}>
                  {formatPercent(holding.unrealized_pnl_percent)}
                </Typography>
              </TableCell>
              <TableCell>
                <Chip 
                  label={holding.bot_name || 'Manual'} 
                  size="small"
                  sx={{ backgroundColor: '#333', color: '#fff' }}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const renderPerformance = () => (
    <Box>
      <Typography variant="h6" sx={{ mb: 3, color: '#fff' }}>
        Performance Analytics
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ background: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                Asset Allocation
              </Typography>
              {holdings.map((holding, index) => {
                const percentage = summary ? (holding.market_value / summary.total_value) * 100 : 0;
                return (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" sx={{ color: '#fff' }}>
                        {holding.symbol}
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#aaa' }}>
                        {percentage.toFixed(1)}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={percentage}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: '#333',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: `hsl(${120 - index * 30}, 70%, 50%)`
                        }
                      }}
                    />
                  </Box>
                );
              })}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card sx={{ background: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                Performance Metrics
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" sx={{ color: '#aaa', mb: 1 }}>
                  Total Return
                </Typography>
                <Typography variant="h4" sx={{ 
                  color: summary?.total_pnl >= 0 ? '#00ff88' : '#ff4444' 
                }}>
                  {summary ? formatPercent(summary.total_pnl_percent) : '0.00%'}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" sx={{ color: '#aaa', mb: 1 }}>
                  Best Performer
                </Typography>
                {holdings.length > 0 && (
                  <Box>
                    {(() => {
                      const best = holdings.reduce((prev, current) => 
                        prev.unrealized_pnl_percent > current.unrealized_pnl_percent ? prev : current
                      );
                      return (
                        <Typography variant="h6" sx={{ color: '#00ff88' }}>
                          {best.symbol} ({formatPercent(best.unrealized_pnl_percent)})
                        </Typography>
                      );
                    })()}
                  </Box>
                )}
              </Box>
              
              <Box>
                <Typography variant="body2" sx={{ color: '#aaa', mb: 1 }}>
                  Worst Performer
                </Typography>
                {holdings.length > 0 && (
                  <Box>
                    {(() => {
                      const worst = holdings.reduce((prev, current) => 
                        prev.unrealized_pnl_percent < current.unrealized_pnl_percent ? prev : current
                      );
                      return (
                        <Typography variant="h6" sx={{ color: '#ff4444' }}>
                          {worst.symbol} ({formatPercent(worst.unrealized_pnl_percent)})
                        </Typography>
                      );
                    })()}
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  return (
    <Box>
      {renderOverview()}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab label="Holdings" />
          <Tab label="Performance" />
        </Tabs>
      </Box>

      <TabPanel value={activeTab} index={0}>
        {renderHoldings()}
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        {renderPerformance()}
      </TabPanel>
    </Box>
  );
}