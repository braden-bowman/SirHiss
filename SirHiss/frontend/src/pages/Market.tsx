import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tabs,
  Tab,
  InputAdornment,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Alert
} from '@mui/material';
import {
  Search as SearchIcon,
  TrendingUp,
  TrendingDown,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { api } from '../services/api';
import { yahooFinanceService } from '../services/yahooFinance';

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap?: number;
  pe?: number;
  dividend?: number;
  isWatchlist?: boolean;
}

interface MarketData {
  symbol: string;
  timestamp: string;
  price: number;
  volume: number;
}

interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  publishedAt: string;
  symbols: string[];
}

export function Market() {
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Stock[]>([]);
  const [popularStocks, setPopularStocks] = useState<Stock[]>([]);
  const [watchlist, setWatchlist] = useState<Stock[]>([]);
  const [marketIndices, setMarketIndices] = useState<Stock[]>([]);
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [chartData, setChartData] = useState<MarketData[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMarketData();
  }, []);

  const loadMarketData = async () => {
    try {
      setLoading(true);
      
      // Try to load real data from Yahoo Finance
      try {
        console.log('Loading real market data from Yahoo Finance...');
        
        const [popularStocksData, indicesData, newsData] = await Promise.all([
          yahooFinanceService.getTrendingStocks(),
          yahooFinanceService.getMarketIndices(),
          yahooFinanceService.getMarketNews()
        ]);

        if (popularStocksData && popularStocksData.length > 0) {
          setPopularStocks(popularStocksData as Stock[]);
          setSelectedStock(popularStocksData[0] as Stock);
          
          // Load historical data for the first stock
          try {
            const historical = await yahooFinanceService.getHistoricalData(popularStocksData[0].symbol, '1mo');
            setChartData(historical.map(item => ({
              symbol: popularStocksData[0].symbol,
              timestamp: item.timestamp,
              price: item.price,
              volume: item.volume
            })));
          } catch (error) {
            console.warn('Failed to load historical data:', error);
          }
        }

        if (indicesData && indicesData.length > 0) {
          setMarketIndices(indicesData as Stock[]);
        }

        if (newsData && newsData.length > 0) {
          setNews(newsData);
        }

        console.log('Successfully loaded real market data!');

      } catch (yahooError) {
        console.warn('Yahoo Finance API failed, using demo data:', yahooError);
        
        // Fallback to demo data
        const demoPopularStocks: Stock[] = [
          { symbol: 'AAPL', name: 'Apple Inc.', price: 185.25, change: 2.15, changePercent: 1.17, volume: 45236789, marketCap: 2850000000000, pe: 28.5, dividend: 0.94 },
          { symbol: 'MSFT', name: 'Microsoft Corporation', price: 365.80, change: -1.45, changePercent: -0.39, volume: 32145678, marketCap: 2720000000000, pe: 32.1, dividend: 2.68 },
          { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 142.35, change: 3.28, changePercent: 2.36, volume: 28456789, marketCap: 1800000000000, pe: 25.8, dividend: 0 },
          { symbol: 'AMZN', name: 'Amazon.com Inc.', price: 151.94, change: -0.87, changePercent: -0.57, volume: 38765432, marketCap: 1570000000000, pe: 45.2, dividend: 0 },
          { symbol: 'TSLA', name: 'Tesla Inc.', price: 248.50, change: 12.35, changePercent: 5.23, volume: 67890123, marketCap: 790000000000, pe: 78.9, dividend: 0 },
          { symbol: 'NVDA', name: 'NVIDIA Corporation', price: 875.30, change: 25.40, changePercent: 2.99, volume: 23456789, marketCap: 2160000000000, pe: 65.4, dividend: 0.16 },
        ];

        const demoIndices: Stock[] = [
          { symbol: 'SPY', name: 'SPDR S&P 500 ETF', price: 485.72, change: 2.34, changePercent: 0.48, volume: 45789123 },
          { symbol: 'QQQ', name: 'Invesco QQQ ETF', price: 398.45, change: 1.87, changePercent: 0.47, volume: 32145678 },
          { symbol: 'DIA', name: 'SPDR Dow Jones ETF', price: 356.89, change: -0.92, changePercent: -0.26, volume: 12345678 },
          { symbol: 'VTI', name: 'Vanguard Total Stock Market ETF', price: 241.56, change: 1.23, changePercent: 0.51, volume: 23456789 }
        ];

        const demoNews: NewsItem[] = [
          {
            id: '1',
            title: 'Market Data: Using Demo Data (Yahoo Finance Connection Failed)',
            summary: 'Real-time data from Yahoo Finance is currently unavailable. Displaying demo data for interface testing.',
            source: 'SirHiss System',
            publishedAt: new Date().toISOString(),
            symbols: ['DEMO']
          },
          {
            id: '2',
            title: 'Yahoo Finance Integration Ready',
            summary: 'The system is configured to use Yahoo Finance API for real market data when available.',
            source: 'SirHiss System',
            publishedAt: new Date().toISOString(),
            symbols: ['INFO']
          }
        ];

        setPopularStocks(demoPopularStocks);
        setMarketIndices(demoIndices);
        setNews(demoNews);
        setSelectedStock(demoPopularStocks[0]);
        
        // Generate demo chart data
        const chartData = Array.from({ length: 30 }, (_, i) => ({
          symbol: 'AAPL',
          timestamp: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString(),
          price: 180 + Math.random() * 20,
          volume: 40000000 + Math.random() * 20000000
        }));
        setChartData(chartData);
      }

      // Load watchlist from local storage or API
      try {
        const savedWatchlist = localStorage.getItem('watchlist');
        if (savedWatchlist) {
          const watchlistSymbols = JSON.parse(savedWatchlist);
          const watchlistData = await yahooFinanceService.getQuotes(watchlistSymbols);
          setWatchlist(watchlistData.map(stock => ({ ...stock, isWatchlist: true })) as Stock[]);
        }
      } catch (error) {
        console.warn('Failed to load watchlist:', error);
        // Set demo watchlist
        setWatchlist([
          { ...popularStocks[0], isWatchlist: true },
          { symbol: 'AMD', name: 'Advanced Micro Devices', price: 142.78, change: 4.25, changePercent: 3.07, volume: 34567890, isWatchlist: true }
        ]);
      }

    } catch (error) {
      console.error('Failed to load market data:', error);
    }
    setLoading(false);
  };

  const searchStocks = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      // Try Yahoo Finance search first
      const searchResults = await yahooFinanceService.searchStocks(query, 8);
      
      if (searchResults && searchResults.length > 0) {
        // Get quotes for search results
        const symbols = searchResults.map((result: any) => result.symbol);
        const quotes = await yahooFinanceService.getQuotes(symbols);
        
        const stockData = quotes.map((quote: any) => {
          const searchResult = searchResults.find((result: any) => result.symbol === quote.symbol);
          return {
            ...quote,
            name: searchResult?.name || quote.name
          };
        });
        
        setSearchResults(stockData as Stock[]);
      } else {
        setSearchResults([]);
      }
    } catch (error) {
      console.warn('Yahoo Finance search failed, trying local search:', error);
      
      try {
        // Fallback to backend search
        const response = await api.get(`/market/search?q=${query}`);
        setSearchResults(response.data);
      } catch (apiError) {
        console.warn('API search also failed, using local filter:', apiError);
        
        // Final fallback - filter from existing stocks
        const allStocks = [...popularStocks, ...marketIndices];
        const filtered = allStocks.filter(stock => 
          stock.symbol.toLowerCase().includes(query.toLowerCase()) ||
          stock.name.toLowerCase().includes(query.toLowerCase())
        );
        setSearchResults(filtered);
      }
    }
  };

  const toggleWatchlist = async (stock: Stock) => {
    try {
      let updatedWatchlist: Stock[];
      
      if (stock.isWatchlist) {
        // Remove from watchlist
        updatedWatchlist = watchlist.filter(s => s.symbol !== stock.symbol);
        setWatchlist(updatedWatchlist);
        
        // Try to remove from backend
        try {
          await api.delete(`/market/watchlist/${stock.symbol}`);
        } catch (error) {
          console.warn('Backend watchlist removal failed, using local storage:', error);
        }
        
        // Update local storage
        const symbols = updatedWatchlist.map(s => s.symbol);
        localStorage.setItem('watchlist', JSON.stringify(symbols));
        
      } else {
        // Add to watchlist
        const newStock = { ...stock, isWatchlist: true };
        updatedWatchlist = [...watchlist, newStock];
        setWatchlist(updatedWatchlist);
        
        // Try to add to backend
        try {
          await api.post('/market/watchlist', { symbol: stock.symbol });
        } catch (error) {
          console.warn('Backend watchlist addition failed, using local storage:', error);
        }
        
        // Update local storage
        const symbols = updatedWatchlist.map(s => s.symbol);
        localStorage.setItem('watchlist', JSON.stringify(symbols));
      }
      
      // Update stock in all lists
      const updateStock = (stocks: Stock[]) => 
        stocks.map(s => s.symbol === stock.symbol ? { ...s, isWatchlist: !s.isWatchlist } : s);
      
      setPopularStocks(updateStock);
      setSearchResults(updateStock);
      
    } catch (error) {
      console.error('Failed to update watchlist:', error);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatVolume = (value: number) => {
    if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
    return value.toString();
  };

  const StockCard = ({ stock }: { stock: Stock }) => (
    <Card 
      sx={{ 
        backgroundColor: '#2a2a2a', 
        cursor: 'pointer',
        '&:hover': { backgroundColor: '#3a3a3a' }
      }}
      onClick={() => setSelectedStock(stock)}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Box>
            <Typography variant="h6" sx={{ color: '#fff' }}>{stock.symbol}</Typography>
            <Typography variant="body2" sx={{ color: '#aaa' }} noWrap>
              {stock.name}
            </Typography>
          </Box>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              toggleWatchlist(stock);
            }}
          >
            {stock.isWatchlist ? 
              <StarIcon sx={{ color: '#ffaa00' }} /> : 
              <StarBorderIcon sx={{ color: '#666' }} />
            }
          </IconButton>
        </Box>
        
        <Typography variant="h5" sx={{ color: '#fff', mb: 1 }}>
          {formatCurrency(stock.price)}
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {stock.change >= 0 ? 
            <TrendingUp sx={{ color: '#00ff88', mr: 0.5 }} /> :
            <TrendingDown sx={{ color: '#ff6b6b', mr: 0.5 }} />
          }
          <Typography 
            variant="body2" 
            sx={{ color: stock.change >= 0 ? '#00ff88' : '#ff6b6b' }}
          >
            {formatCurrency(stock.change)} ({formatPercent(stock.changePercent)})
          </Typography>
        </Box>
        
        <Typography variant="caption" sx={{ color: '#666', display: 'block', mt: 1 }}>
          Vol: {formatVolume(stock.volume)}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ color: '#fff', mb: 3 }}>
        📈 Market Data & Analysis
      </Typography>

      <Grid container spacing={3}>
        {/* Search and Navigation */}
        <Grid item xs={12}>
          <Paper sx={{ backgroundColor: '#1a1a1a', color: '#fff' }}>
            <Tabs 
              value={activeTab} 
              onChange={(_, newValue) => setActiveTab(newValue)}
              sx={{ borderBottom: '1px solid #333' }}
            >
              <Tab label="Popular Stocks" />
              <Tab label="Market Indices" />
              <Tab label="My Watchlist" />
              <Tab label="Market News" />
            </Tabs>
            
            <Box sx={{ p: 2 }}>
              <TextField
                fullWidth
                placeholder="Search stocks, ETFs, or cryptocurrencies..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  searchStocks(e.target.value);
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton onClick={() => searchStocks(searchQuery)}>
                        <RefreshIcon />
                      </IconButton>
                    </InputAdornment>
                  )
                }}
                sx={{ mb: 2 }}
              />

              {/* Search Results */}
              {searchResults.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6" gutterBottom>Search Results</Typography>
                  <Grid container spacing={2}>
                    {searchResults.map((stock) => (
                      <Grid item xs={12} sm={6} md={4} lg={3} key={stock.symbol}>
                        <StockCard stock={stock} />
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Main Content */}
        <Grid item xs={12} lg={8}>
          {/* Tab Content */}
          {activeTab === 0 && (
            <Paper sx={{ p: 3, backgroundColor: '#1a1a1a', color: '#fff' }}>
              <Typography variant="h6" gutterBottom>Popular Stocks</Typography>
              <Grid container spacing={2}>
                {popularStocks.map((stock) => (
                  <Grid item xs={12} sm={6} md={4} key={stock.symbol}>
                    <StockCard stock={stock} />
                  </Grid>
                ))}
              </Grid>
            </Paper>
          )}

          {activeTab === 1 && (
            <Paper sx={{ p: 3, backgroundColor: '#1a1a1a', color: '#fff' }}>
              <Typography variant="h6" gutterBottom>Market Indices & ETFs</Typography>
              <Grid container spacing={2}>
                {marketIndices.map((index) => (
                  <Grid item xs={12} sm={6} md={4} key={index.symbol}>
                    <StockCard stock={index} />
                  </Grid>
                ))}
              </Grid>
            </Paper>
          )}

          {activeTab === 2 && (
            <Paper sx={{ p: 3, backgroundColor: '#1a1a1a', color: '#fff' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">My Watchlist</Typography>
                <Button
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={() => setActiveTab(0)}
                >
                  Add Stocks
                </Button>
              </Box>
              
              {watchlist.length > 0 ? (
                <Grid container spacing={2}>
                  {watchlist.map((stock) => (
                    <Grid item xs={12} sm={6} md={4} key={stock.symbol}>
                      <StockCard stock={stock} />
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography color="textSecondary">
                    Your watchlist is empty. Add some stocks to track them here.
                  </Typography>
                </Box>
              )}
            </Paper>
          )}

          {activeTab === 3 && (
            <Paper sx={{ p: 3, backgroundColor: '#1a1a1a', color: '#fff' }}>
              <Typography variant="h6" gutterBottom>Market News</Typography>
              <List>
                {news.map((item, index) => (
                  <React.Fragment key={item.id}>
                    <ListItem alignItems="flex-start">
                      <ListItemText
                        primary={item.title}
                        secondary={
                          <Box>
                            <Typography variant="body2" sx={{ color: '#aaa', mb: 1 }}>
                              {item.summary}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                              <Typography variant="caption" sx={{ color: '#666' }}>
                                {item.source} • {new Date(item.publishedAt).toLocaleDateString()}
                              </Typography>
                              {item.symbols.map(symbol => (
                                <Chip
                                  key={symbol}
                                  label={symbol}
                                  size="small"
                                  sx={{ backgroundColor: '#00ff8844', color: '#00ff88' }}
                                />
                              ))}
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < news.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </Paper>
          )}
        </Grid>

        {/* Stock Details Sidebar */}
        <Grid item xs={12} lg={4}>
          {selectedStock && (
            <Paper sx={{ p: 3, backgroundColor: '#1a1a1a', color: '#fff', mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box>
                  <Typography variant="h5">{selectedStock.symbol}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {selectedStock.name}
                  </Typography>
                </Box>
                <IconButton onClick={() => toggleWatchlist(selectedStock)}>
                  {selectedStock.isWatchlist ? 
                    <StarIcon sx={{ color: '#ffaa00' }} /> : 
                    <StarBorderIcon sx={{ color: '#666' }} />
                  }
                </IconButton>
              </Box>

              <Typography variant="h4" sx={{ mb: 1 }}>
                {formatCurrency(selectedStock.price)}
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                {selectedStock.change >= 0 ? 
                  <TrendingUp sx={{ color: '#00ff88', mr: 0.5 }} /> :
                  <TrendingDown sx={{ color: '#ff6b6b', mr: 0.5 }} />
                }
                <Typography 
                  variant="h6" 
                  sx={{ color: selectedStock.change >= 0 ? '#00ff88' : '#ff6b6b' }}
                >
                  {formatCurrency(selectedStock.change)} ({formatPercent(selectedStock.changePercent)})
                </Typography>
              </Box>

              {/* Stock Metrics */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>Key Metrics</Typography>
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="textSecondary">Volume</Typography>
                    <Typography variant="body2">{formatVolume(selectedStock.volume)}</Typography>
                  </Grid>
                  {selectedStock.marketCap && (
                    <Grid item xs={6}>
                      <Typography variant="caption" color="textSecondary">Market Cap</Typography>
                      <Typography variant="body2">{formatVolume(selectedStock.marketCap)}</Typography>
                    </Grid>
                  )}
                  {selectedStock.pe && (
                    <Grid item xs={6}>
                      <Typography variant="caption" color="textSecondary">P/E Ratio</Typography>
                      <Typography variant="body2">{selectedStock.pe}</Typography>
                    </Grid>
                  )}
                  {selectedStock.dividend && (
                    <Grid item xs={6}>
                      <Typography variant="caption" color="textSecondary">Dividend Yield</Typography>
                      <Typography variant="body2">{selectedStock.dividend}%</Typography>
                    </Grid>
                  )}
                </Grid>
              </Box>

              {/* Price Chart */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <TimelineIcon sx={{ mr: 1 }} />
                  30-Day Price Chart
                </Typography>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#00ff88" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 10, fill: '#666' }}
                    />
                    <YAxis 
                      domain={['dataMin - 5', 'dataMax + 5']}
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 10, fill: '#666' }}
                    />
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#2a2a2a', 
                        border: '1px solid #666',
                        color: '#fff'
                      }}
                      labelFormatter={(value) => new Date(value).toLocaleDateString()}
                      formatter={(value: number) => [formatCurrency(value), 'Price']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="price" 
                      stroke="#00ff88" 
                      fillOpacity={1} 
                      fill="url(#colorPrice)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>

              <Button
                fullWidth
                variant="contained"
                sx={{ backgroundColor: '#00ff88', color: '#000', fontWeight: 'bold' }}
              >
                Create Trading Bot for {selectedStock.symbol}
              </Button>
            </Paper>
          )}

          {/* Market Summary */}
          <Paper sx={{ p: 3, backgroundColor: '#1a1a1a', color: '#fff' }}>
            <Typography variant="h6" gutterBottom>Market Summary</Typography>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              Market data provided by Yahoo Finance and other sources. Prices may be delayed up to 20 minutes.
            </Alert>

            <List dense>
              <ListItem>
                <ListItemText 
                  primary="Market Status" 
                  secondary="Open • NYSE & NASDAQ"
                />
                <ListItemSecondaryAction>
                  <Chip label="OPEN" color="success" size="small" />
                </ListItemSecondaryAction>
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Stocks Tracked" 
                  secondary="Popular US equities"
                />
                <ListItemSecondaryAction>
                  <Typography variant="body2">{popularStocks.length}</Typography>
                </ListItemSecondaryAction>
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Watchlist Items" 
                  secondary="Your tracked stocks"
                />
                <ListItemSecondaryAction>
                  <Typography variant="body2">{watchlist.length}</Typography>
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}