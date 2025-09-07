-- SirHiss Database Initialization

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio table for tracking overall portfolio
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    total_value DECIMAL(15, 2) DEFAULT 0.00,
    available_cash DECIMAL(15, 2) DEFAULT 0.00,
    robinhood_account_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trading bots table
CREATE TABLE IF NOT EXISTS trading_bots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    allocated_percentage DECIMAL(5, 2) NOT NULL CHECK (allocated_percentage >= 0 AND allocated_percentage <= 100),
    allocated_amount DECIMAL(15, 2) DEFAULT 0.00,
    current_value DECIMAL(15, 2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'stopped' CHECK (status IN ('running', 'stopped', 'paused', 'error')),
    strategy_code TEXT,
    parameters JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bot execution history
CREATE TABLE IF NOT EXISTS bot_executions (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES trading_bots(id) ON DELETE CASCADE,
    execution_type VARCHAR(20) NOT NULL CHECK (execution_type IN ('buy', 'sell', 'analysis')),
    symbol VARCHAR(10),
    quantity DECIMAL(15, 8),
    price DECIMAL(15, 2),
    total_value DECIMAL(15, 2),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
    error_message TEXT,
    execution_data JSONB DEFAULT '{}',
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Holdings table for tracking current positions
CREATE TABLE IF NOT EXISTS holdings (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
    bot_id INTEGER REFERENCES trading_bots(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    quantity DECIMAL(15, 8) NOT NULL DEFAULT 0,
    average_cost DECIMAL(15, 2) NOT NULL DEFAULT 0,
    current_price DECIMAL(15, 2) DEFAULT 0,
    market_value DECIMAL(15, 2) DEFAULT 0,
    unrealized_pl DECIMAL(15, 2) DEFAULT 0,
    asset_type VARCHAR(20) DEFAULT 'stock' CHECK (asset_type IN ('stock', 'crypto', 'option')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, bot_id, symbol)
);

-- Market data cache
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(15, 2) NOT NULL,
    volume BIGINT DEFAULT 0,
    market_cap DECIMAL(20, 2),
    pe_ratio DECIMAL(10, 2),
    data_source VARCHAR(50) DEFAULT 'robinhood',
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, data_source, timestamp)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_trading_bots_user_id ON trading_bots(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_bots_status ON trading_bots(status);
CREATE INDEX IF NOT EXISTS idx_bot_executions_bot_id ON bot_executions(bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_executions_executed_at ON bot_executions(executed_at);
CREATE INDEX IF NOT EXISTS idx_holdings_portfolio_id ON holdings(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_holdings_bot_id ON holdings(bot_id);
CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON holdings(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);

-- Create a default admin user (password: admin123 - CHANGE IN PRODUCTION)
INSERT INTO users (username, email, hashed_password) 
VALUES ('admin', 'admin@sirhiss.local', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW') 
ON CONFLICT (username) DO NOTHING;