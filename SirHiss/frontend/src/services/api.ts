import axios from 'axios';

// Create API instance
export const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:9002/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types for API responses
export interface TradingBot {
  id: number;
  name: string;
  description?: string;
  allocated_percentage: number;
  allocated_amount: number;
  current_value: number;
  status: 'running' | 'stopped' | 'paused' | 'error';
  parameters: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Portfolio {
  id: number;
  total_value: number;
  available_cash: number;
  robinhood_account_id?: string;
}

export interface Holding {
  id: number;
  symbol: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pl: number;
  asset_type: string;
}

// Bot API functions
export const botApi = {
  getBots: () => api.get<TradingBot[]>('/bots'),
  getBot: (id: number) => api.get<TradingBot>(`/bots/${id}`),
  createBot: (data: Partial<TradingBot>) => api.post<TradingBot>('/bots', data),
  updateBot: (id: number, data: Partial<TradingBot>) => api.put<TradingBot>(`/bots/${id}`, data),
  startBot: (id: number) => api.post(`/bots/${id}/start`),
  stopBot: (id: number) => api.post(`/bots/${id}/stop`),
  deleteBot: (id: number) => api.delete(`/bots/${id}`),
};

// Portfolio API functions
export const portfolioApi = {
  getPortfolio: () => api.get<Portfolio>('/portfolio'),
  getHoldings: () => api.get<Holding[]>('/portfolio/holdings'),
};

// Market data API functions
export const marketApi = {
  getQuote: (symbol: string) => api.get(`/market/quote/${symbol}`),
  searchSymbols: (query: string) => api.get(`/market/search?query=${query}`),
};