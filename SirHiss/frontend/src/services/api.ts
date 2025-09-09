import axios from 'axios';

// Create API instance
export const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:9002/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to automatically include API key or auth token
api.interceptors.request.use(
  (config) => {
    // Try API key first (from environment variable)
    const apiKey = process.env.REACT_APP_SIRHISS_API_KEY;
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey;
    } else {
      // Fall back to JWT token (for backward compatibility)
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

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

// Algorithm types and interfaces
export interface AlgorithmConfig {
  id: number;
  bot_id: number;
  algorithm_type: string;
  algorithm_name: string;
  position_size: number;
  max_position_size: number;
  stop_loss: number;
  take_profit: number;
  risk_per_trade: number;
  enabled: boolean;
  parameters: Record<string, any>;
  total_trades: number;
  winning_trades: number;
  win_rate: number;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  created_at: string;
  updated_at: string;
}

export interface AlgorithmTemplate {
  id: number;
  name: string;
  algorithm_type: string;
  description: string;
  category: string;
  default_position_size: number;
  default_parameters: Record<string, any>;
  difficulty_level: string;
  min_capital: number;
  recommended_timeframe: string;
}

export interface AlgorithmCreateData {
  algorithm_type: string;
  algorithm_name: string;
  position_size: number;
  max_position_size?: number;
  stop_loss?: number;
  take_profit?: number;
  risk_per_trade?: number;
  enabled?: boolean;
  parameters?: Record<string, any>;
}

// Algorithm API functions
export const algorithmApi = {
  // Templates
  getTemplates: (category?: string, difficulty?: string) => {
    let url = '/algorithms/templates';
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (difficulty) params.append('difficulty', difficulty);
    if (params.toString()) url += `?${params.toString()}`;
    return api.get<AlgorithmTemplate[]>(url);
  },
  
  getAlgorithmTypes: () => api.get('/algorithms/types'),
  
  // Bot algorithms
  getBotAlgorithms: (botId: number) => 
    api.get<AlgorithmConfig[]>(`/algorithms/bots/${botId}/algorithms`),
  
  createBotAlgorithm: (botId: number, data: AlgorithmCreateData) =>
    api.post<AlgorithmConfig>(`/algorithms/bots/${botId}/algorithms`, data),
  
  createAlgorithmFromTemplate: (botId: number, templateId: number, algorithmName: string, positionSize?: number) =>
    api.post<AlgorithmConfig>(`/algorithms/bots/${botId}/algorithms/from-template/${templateId}`, {
      algorithm_name: algorithmName,
      position_size: positionSize
    }),
  
  // Algorithm management
  updateAlgorithm: (algorithmId: number, data: Partial<AlgorithmCreateData>) =>
    api.put<AlgorithmConfig>(`/algorithms/algorithms/${algorithmId}`, data),
  
  deleteAlgorithm: (algorithmId: number) =>
    api.delete(`/algorithms/algorithms/${algorithmId}`),
  
  toggleAlgorithm: (algorithmId: number) =>
    api.post(`/algorithms/algorithms/${algorithmId}/toggle`),
  
  // Algorithm parameters
  getAlgorithmParameters: (algorithmId: number) =>
    api.get(`/algorithms/algorithms/${algorithmId}/parameters`),
  
  updateAlgorithmParameters: (algorithmId: number, parameters: Record<string, any>) =>
    api.put(`/algorithms/algorithms/${algorithmId}/parameters`, parameters),
  
  // Performance
  getAlgorithmPerformance: (algorithmId: number, limit?: number) => {
    let url = `/algorithms/algorithms/${algorithmId}/performance`;
    if (limit) url += `?limit=${limit}`;
    return api.get(url);
  },
};