import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
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
  IconButton,
  InputAdornment,
  List,
  ListItem,
  ListItemText,
  Tabs,
  Tab,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Search,
  Add,
  Remove,
  TrendingUp,
  TrendingDown,
  Star,
  StarBorder,
  Refresh,
} from '@mui/icons-material';

interface MarketData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap?: number;
  pe_ratio?: number;
  dividend_yield?: number;
}

interface Watchlist {
  id: number;
  name: string;
  symbols: string[];
}

function TabPanel({ children, value, index }: any) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export function MarketDataInterface() {
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<MarketData[]>([]);
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [selectedWatchlist, setSelectedWatchlist] = useState<number>(0);
  const [watchlistData, setWatchlistData] = useState<MarketData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [newWatchlistName, setNewWatchlistName] = useState('');

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

  const searchStocks = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setLoading(true);
    try {
      const data = await apiCall(`/api/v1/market/search?q=${encodeURIComponent(query)}`);
      if (data) {
        setSearchResults(data);
      } else {
        // Demo data
        setSearchResults([
          {
            symbol: 'AAPL',
            name: 'Apple Inc.',
            price: 185.20,
            change: 2.15,
            change_percent: 1.17,
            volume: 45678901,
            market_cap: 2876000000000,
            pe_ratio: 29.2,
          },
          {
            symbol: 'MSFT',
            name: 'Microsoft Corporation',
            price: 352.75,
            change: -1.25,
            change_percent: -0.35,
            volume: 23456789,
            market_cap: 2634000000000,
            pe_ratio: 32.1,
          },
          {
            symbol: 'GOOGL',
            name: 'Alphabet Inc.',
            price: 139.85,
            change: 0.95,
            change_percent: 0.68,
            volume: 18765432,
            market_cap: 1789000000000,
            pe_ratio: 25.8,
          },
        ].filter(stock => 
          stock.symbol.toLowerCase().includes(query.toLowerCase()) ||
          stock.name.toLowerCase().includes(query.toLowerCase())
        ));
      }
    } catch (err) {
      setError('Failed to search stocks');
    }
    setLoading(false);
  };

  const loadWatchlists = async () => {
    try {
      const data = await apiCall('/api/v1/market/watchlists');
      if (data) {
        setWatchlists(data);
      } else {
        // Demo data
        const savedWatchlists = localStorage.getItem('sirhiss_watchlists');
        if (savedWatchlists) {
          setWatchlists(JSON.parse(savedWatchlists));
        } else {
          const defaultWatchlists = [
            { id: 1, name: 'My Portfolio', symbols: ['AAPL', 'MSFT', 'GOOGL'] },
            { id: 2, name: 'Tech Stocks', symbols: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'] },
            { id: 3, name: 'Dividend Stocks', symbols: ['JNJ', 'KO', 'PG', 'XOM'] },
          ];
          setWatchlists(defaultWatchlists);
          localStorage.setItem('sirhiss_watchlists', JSON.stringify(defaultWatchlists));
        }
      }
    } catch (err) {
      setError('Failed to load watchlists');
    }
  };

  const loadWatchlistData = async (watchlistId: number) => {
    const watchlist = watchlists.find(w => w.id === watchlistId);
    if (!watchlist) return;

    setLoading(true);
    try {
      const data = await apiCall(`/api/v1/market/quotes?symbols=${watchlist.symbols.join(',')}`);
      if (data) {
        setWatchlistData(data);
      } else {
        // Demo data
        const demoData: MarketData[] = [
          {
            symbol: 'AAPL',
            name: 'Apple Inc.',
            price: 185.20,
            change: 2.15,
            change_percent: 1.17,
            volume: 45678901,
            market_cap: 2876000000000,
            pe_ratio: 29.2,
            dividend_yield: 0.52,
          },
          {
            symbol: 'MSFT',
            name: 'Microsoft Corporation',
            price: 352.75,
            change: -1.25,
            change_percent: -0.35,
            volume: 23456789,
            market_cap: 2634000000000,
            pe_ratio: 32.1,
            dividend_yield: 0.68,
          },
          {
            symbol: 'GOOGL',
            name: 'Alphabet Inc.',
            price: 139.85,
            change: 0.95,
            change_percent: 0.68,
            volume: 18765432,
            market_cap: 1789000000000,
            pe_ratio: 25.8,
            dividend_yield: 0,
          },
          {
            symbol: 'JNJ',
            name: 'Johnson & Johnson',
            price: 167.45,
            change: 0.85,
            change_percent: 0.51,
            volume: 12345678,
            market_cap: 450000000000,
            pe_ratio: 15.2,
            dividend_yield: 2.95,
          },
          {
            symbol: 'KO',
            name: 'The Coca-Cola Company',
            price: 59.20,
            change: -0.15,
            change_percent: -0.25,
            volume: 8765432,
            market_cap: 256000000000,
            pe_ratio: 24.8,
            dividend_yield: 3.12,
          },
        ];
        
        setWatchlistData(demoData.filter(stock => watchlist.symbols.includes(stock.symbol)));
      }
    } catch (err) {
      setError('Failed to load market data');
    }
    setLoading(false);
  };

  const addToWatchlist = async (symbol: string, watchlistId: number) => {
    const watchlist = watchlists.find(w => w.id === watchlistId);
    if (!watchlist || watchlist.symbols.includes(symbol)) return;

    const updatedWatchlists = watchlists.map(w => 
      w.id === watchlistId 
        ? { ...w, symbols: [...w.symbols, symbol] }
        : w
    );

    setWatchlists(updatedWatchlists);
    localStorage.setItem('sirhiss_watchlists', JSON.stringify(updatedWatchlists));
    
    if (selectedWatchlist === watchlistId) {
      await loadWatchlistData(watchlistId);
    }
  };

  const removeFromWatchlist = async (symbol: string, watchlistId: number) => {
    const updatedWatchlists = watchlists.map(w => 
      w.id === watchlistId 
        ? { ...w, symbols: w.symbols.filter(s => s !== symbol) }
        : w
    );

    setWatchlists(updatedWatchlists);
    localStorage.setItem('sirhiss_watchlists', JSON.stringify(updatedWatchlists));
    
    if (selectedWatchlist === watchlistId) {
      await loadWatchlistData(watchlistId);
    }
  };

  const createWatchlist = () => {
    if (!newWatchlistName.trim()) return;

    const newWatchlist = {
      id: Math.max(0, ...watchlists.map(w => w.id)) + 1,
      name: newWatchlistName,
      symbols: [],
    };

    const updatedWatchlists = [...watchlists, newWatchlist];
    setWatchlists(updatedWatchlists);
    localStorage.setItem('sirhiss_watchlists', JSON.stringify(updatedWatchlists));
    setNewWatchlistName('');
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(1)}B`;
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(1)}M`;
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(1)}K`;
    return volume.toString();
  };

  const formatMarketCap = (marketCap: number) => {
    if (marketCap >= 1e12) return `${(marketCap / 1e12).toFixed(1)}T`;
    if (marketCap >= 1e9) return `${(marketCap / 1e9).toFixed(1)}B`;
    if (marketCap >= 1e6) return `${(marketCap / 1e6).toFixed(1)}M`;
    return marketCap.toString();
  };

  useEffect(() => {
    loadWatchlists();
  }, []);

  useEffect(() => {
    if (watchlists.length > 0 && selectedWatchlist >= 0) {
      loadWatchlistData(selectedWatchlist);
    }
  }, [watchlists, selectedWatchlist]);

  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      if (searchQuery) {
        searchStocks(searchQuery);
      } else {
        setSearchResults([]);
      }
    }, 500);

    return () => clearTimeout(delayedSearch);
  }, [searchQuery]);

  const renderSearch = () => (
    <Box>
      <Typography variant="h6" sx={{ mb: 3, color: '#fff' }}>
        Stock Search
      </Typography>
      
      <TextField
        fullWidth
        placeholder="Search stocks by symbol or name..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search />
            </InputAdornment>
          ),
        }}
        sx={{ mb: 3 }}
      />

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {searchResults.length > 0 && (
        <TableContainer component={Paper} sx={{ background: '#1a1a1a' }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: '#fff' }}>Symbol</TableCell>
                <TableCell sx={{ color: '#fff' }}>Name</TableCell>
                <TableCell align="right" sx={{ color: '#fff' }}>Price</TableCell>
                <TableCell align="right" sx={{ color: '#fff' }}>Change</TableCell>
                <TableCell align="right" sx={{ color: '#fff' }}>Volume</TableCell>
                <TableCell align="center" sx={{ color: '#fff' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {searchResults.map((stock) => (
                <TableRow key={stock.symbol} sx={{ '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.02)' } }}>
                  <TableCell sx={{ color: '#00ff88', fontWeight: 'bold' }}>
                    {stock.symbol}
                  </TableCell>
                  <TableCell sx={{ color: '#fff' }}>{stock.name}</TableCell>
                  <TableCell align="right" sx={{ color: '#fff' }}>
                    {formatCurrency(stock.price)}
                  </TableCell>
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                      {stock.change >= 0 ? <TrendingUp sx={{ mr: 0.5, color: '#00ff88' }} /> : <TrendingDown sx={{ mr: 0.5, color: '#ff4444' }} />}
                      <Typography sx={{ color: stock.change >= 0 ? '#00ff88' : '#ff4444' }}>
                        {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)} ({stock.change_percent.toFixed(2)}%)
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="right" sx={{ color: '#aaa' }}>
                    {formatVolume(stock.volume)}
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      onClick={() => addToWatchlist(stock.symbol, selectedWatchlist || 1)}
                      sx={{ color: '#00ff88' }}
                    >
                      <Add />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );

  const renderWatchlists = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ color: '#fff' }}>
          Watchlists
        </Typography>
        <Button
          startIcon={<Refresh />}
          onClick={() => loadWatchlistData(selectedWatchlist)}
          sx={{ color: '#00ff88' }}
        >
          Refresh
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <Card sx={{ background: '#1a1a1a', border: '1px solid #333', mb: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                My Watchlists
              </Typography>
              <List dense>
                {watchlists.map((watchlist) => (
                  <ListItem
                    key={watchlist.id}
                    button
                    selected={selectedWatchlist === watchlist.id}
                    onClick={() => setSelectedWatchlist(watchlist.id)}
                    sx={{
                      borderRadius: 1,
                      mb: 0.5,
                      backgroundColor: selectedWatchlist === watchlist.id ? 'rgba(0, 255, 136, 0.1)' : 'transparent',
                    }}
                  >
                    <ListItemText
                      primary={watchlist.name}
                      secondary={`${watchlist.symbols.length} symbols`}
                      primaryTypographyProps={{ color: selectedWatchlist === watchlist.id ? '#00ff88' : '#fff' }}
                      secondaryTypographyProps={{ color: '#aaa' }}
                    />
                  </ListItem>
                ))}
              </List>
              
              <Box sx={{ mt: 2 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="New watchlist name"
                  value={newWatchlistName}
                  onChange={(e) => setNewWatchlistName(e.target.value)}
                  sx={{ mb: 1 }}
                />
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Add />}
                  onClick={createWatchlist}
                  disabled={!newWatchlistName.trim()}
                  sx={{ color: '#00ff88', borderColor: '#00ff88' }}
                >
                  Create
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={9}>
          {loading && <LinearProgress sx={{ mb: 2 }} />}
          
          {watchlistData.length > 0 ? (
            <TableContainer component={Paper} sx={{ background: '#1a1a1a' }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ color: '#fff' }}>Symbol</TableCell>
                    <TableCell sx={{ color: '#fff' }}>Name</TableCell>
                    <TableCell align="right" sx={{ color: '#fff' }}>Price</TableCell>
                    <TableCell align="right" sx={{ color: '#fff' }}>Change</TableCell>
                    <TableCell align="right" sx={{ color: '#fff' }}>Volume</TableCell>
                    <TableCell align="right" sx={{ color: '#fff' }}>P/E</TableCell>
                    <TableCell align="right" sx={{ color: '#fff' }}>Yield</TableCell>
                    <TableCell align="center" sx={{ color: '#fff' }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {watchlistData.map((stock) => (
                    <TableRow key={stock.symbol} sx={{ '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.02)' } }}>
                      <TableCell sx={{ color: '#00ff88', fontWeight: 'bold' }}>
                        {stock.symbol}
                      </TableCell>
                      <TableCell sx={{ color: '#fff' }}>{stock.name}</TableCell>
                      <TableCell align="right" sx={{ color: '#fff' }}>
                        {formatCurrency(stock.price)}
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                          {stock.change >= 0 ? <TrendingUp sx={{ mr: 0.5, color: '#00ff88' }} /> : <TrendingDown sx={{ mr: 0.5, color: '#ff4444' }} />}
                          <Typography sx={{ color: stock.change >= 0 ? '#00ff88' : '#ff4444' }}>
                            {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)} ({stock.change_percent.toFixed(2)}%)
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right" sx={{ color: '#aaa' }}>
                        {formatVolume(stock.volume)}
                      </TableCell>
                      <TableCell align="right" sx={{ color: '#aaa' }}>
                        {stock.pe_ratio ? stock.pe_ratio.toFixed(1) : 'N/A'}
                      </TableCell>
                      <TableCell align="right" sx={{ color: '#aaa' }}>
                        {stock.dividend_yield ? `${stock.dividend_yield.toFixed(2)}%` : '0%'}
                      </TableCell>
                      <TableCell align="center">
                        <IconButton
                          onClick={() => removeFromWatchlist(stock.symbol, selectedWatchlist)}
                          sx={{ color: '#ff4444' }}
                        >
                          <Remove />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Card sx={{ background: '#1a1a1a', border: '1px solid #333', p: 4, textAlign: 'center' }}>
              <Typography variant="h6" sx={{ color: '#aaa', mb: 2 }}>
                No stocks in this watchlist
              </Typography>
              <Typography variant="body2" sx={{ color: '#666' }}>
                Use the search tab to find and add stocks to your watchlist
              </Typography>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab label="Search Stocks" />
          <Tab label="Watchlists" />
        </Tabs>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <TabPanel value={activeTab} index={0}>
        {renderSearch()}
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        {renderWatchlists()}
      </TabPanel>
    </Box>
  );
}