import axios from 'axios';

interface YahooFinanceQuote {
  symbol: string;
  regularMarketPrice: number;
  regularMarketChange: number;
  regularMarketChangePercent: number;
  regularMarketVolume: number;
  marketCap?: number;
  trailingPE?: number;
  dividendYield?: number;
  shortName: string;
  longName?: string;
}

interface YahooFinanceSearchResult {
  symbol: string;
  name: string;
  exch: string;
  type: string;
  exchDisp: string;
  typeDisp: string;
}

interface YahooFinanceHistoricalData {
  timestamp: number[];
  indicators: {
    quote: Array<{
      open: number[];
      high: number[];
      low: number[];
      close: number[];
      volume: number[];
    }>;
  };
}

class YahooFinanceService {
  private baseUrl = 'https://query1.finance.yahoo.com/v8/finance/chart';
  private searchUrl = 'https://query2.finance.yahoo.com/v1/finance/search';
  private proxyUrl = '/api/v1/market/proxy'; // Use our backend as proxy to avoid CORS
  
  // Convert Yahoo Finance quote to our Stock interface
  private convertQuoteToStock(quote: YahooFinanceQuote) {
    return {
      symbol: quote.symbol,
      name: quote.shortName || quote.longName || quote.symbol,
      price: quote.regularMarketPrice || 0,
      change: quote.regularMarketChange || 0,
      changePercent: quote.regularMarketChangePercent || 0,
      volume: quote.regularMarketVolume || 0,
      marketCap: quote.marketCap,
      pe: quote.trailingPE,
      dividend: quote.dividendYield
    };
  }

  // Get real-time quote for a symbol
  async getQuote(symbol: string) {
    try {
      // Try direct Yahoo Finance API first
      const response = await axios.get(`${this.baseUrl}/${symbol}`, {
        params: {
          range: '1d',
          interval: '1m',
          includePrePost: false
        }
      });
      
      const result = response.data.chart.result[0];
      const quote = result.meta;
      
      return {
        symbol: quote.symbol,
        name: quote.symbol, // Yahoo doesn't always provide company name in this endpoint
        price: quote.regularMarketPrice,
        change: quote.regularMarketPrice - quote.previousClose,
        changePercent: ((quote.regularMarketPrice - quote.previousClose) / quote.previousClose) * 100,
        volume: quote.regularMarketVolume,
        marketCap: quote.marketCap,
        pe: quote.trailingPE,
        dividend: quote.dividendYield
      };
    } catch (error) {
      console.warn('Direct Yahoo Finance API failed, trying proxy:', error);
      
      try {
        // Fallback to our backend proxy
        const response = await axios.get(`${this.proxyUrl}/quote/${symbol}`);
        return this.convertQuoteToStock(response.data);
      } catch (proxyError) {
        console.error('Proxy also failed:', proxyError);
        throw new Error(`Failed to fetch quote for ${symbol}`);
      }
    }
  }

  // Get multiple quotes at once
  async getQuotes(symbols: string[]) {
    const promises = symbols.map(symbol => this.getQuote(symbol));
    const results = await Promise.allSettled(promises);
    
    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        console.error(`Failed to fetch quote for ${symbols[index]}:`, result.reason);
        return null;
      }
    }).filter(Boolean);
  }

  // Search for stocks by query
  async searchStocks(query: string, limit: number = 10) {
    try {
      // Try direct Yahoo Finance search
      const response = await axios.get(this.searchUrl, {
        params: { q: query, quotesCount: limit, newsCount: 0 }
      });
      
      return response.data.quotes.map((quote: YahooFinanceSearchResult) => ({
        symbol: quote.symbol,
        name: quote.name,
        exchange: quote.exch,
        type: quote.type
      }));
    } catch (error) {
      console.warn('Direct Yahoo Finance search failed, trying proxy:', error);
      
      try {
        // Fallback to our backend proxy
        const response = await axios.get(`${this.proxyUrl}/search`, {
          params: { q: query, limit }
        });
        return response.data;
      } catch (proxyError) {
        console.error('Search proxy also failed:', proxyError);
        throw new Error(`Failed to search for "${query}"`);
      }
    }
  }

  // Get historical price data
  async getHistoricalData(symbol: string, period: string = '1mo', interval: string = '1d') {
    try {
      const response = await axios.get(`${this.baseUrl}/${symbol}`, {
        params: { range: period, interval }
      });
      
      const result = response.data.chart.result[0];
      const timestamps = result.timestamp;
      const prices = result.indicators.quote[0];
      
      return timestamps.map((timestamp: number, index: number) => ({
        timestamp: new Date(timestamp * 1000).toISOString(),
        open: prices.open[index],
        high: prices.high[index],
        low: prices.low[index],
        close: prices.close[index],
        volume: prices.volume[index],
        price: prices.close[index] // Alias for compatibility
      }));
    } catch (error) {
      console.warn('Direct Yahoo Finance historical data failed, trying proxy:', error);
      
      try {
        const response = await axios.get(`${this.proxyUrl}/historical/${symbol}`, {
          params: { period, interval }
        });
        return response.data;
      } catch (proxyError) {
        console.error('Historical data proxy also failed:', proxyError);
        throw new Error(`Failed to fetch historical data for ${symbol}`);
      }
    }
  }

  // Get popular/trending stocks
  async getTrendingStocks() {
    const popularSymbols = [
      'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 
      'META', 'NFLX', 'AMD', 'CRM', 'ORCL', 'ADBE'
    ];
    
    return this.getQuotes(popularSymbols);
  }

  // Get major market indices
  async getMarketIndices() {
    const indexSymbols = ['SPY', 'QQQ', 'DIA', 'VTI', 'IWM', 'EFA'];
    return this.getQuotes(indexSymbols);
  }

  // Get crypto prices (Yahoo Finance supports major cryptocurrencies)
  async getCryptoPrices() {
    const cryptoSymbols = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'SOL-USD', 'DOT-USD'];
    return this.getQuotes(cryptoSymbols);
  }

  // Get market news (basic implementation - would need news API for full functionality)
  async getMarketNews(symbols?: string[]) {
    try {
      const response = await axios.get(`${this.proxyUrl}/news`, {
        params: { symbols: symbols?.join(',') }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch market news:', error);
      
      // Return demo news data
      return [
        {
          id: '1',
          title: 'Market Update: Tech Stocks Rally on Positive Earnings',
          summary: 'Technology companies continue to show strong performance in Q4 earnings reports.',
          source: 'Yahoo Finance',
          publishedAt: new Date().toISOString(),
          symbols: symbols || ['AAPL', 'MSFT', 'GOOGL']
        }
      ];
    }
  }

  // Check if Yahoo Finance API is accessible
  async checkConnection() {
    try {
      await this.getQuote('AAPL');
      return { status: 'connected', message: 'Yahoo Finance API is accessible' };
    } catch (error) {
      return { status: 'error', message: 'Yahoo Finance API is not accessible' };
    }
  }
}

export const yahooFinanceService = new YahooFinanceService();
export default yahooFinanceService;