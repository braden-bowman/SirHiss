# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

SirHiss is a dockerized trading bot application that connects to the Robinhood API for automated stock and cryptocurrency trading. The application features a browser-based UI for managing multiple trading bot instances, each with customizable parameters and Python-based trading strategies.

## Desired End State

### Core Features
- **Multi-Bot Architecture**: Create and manage multiple trading bot instances
- **Portfolio Allocation**: Allocate percentage-based portions of total portfolio to each bot
- **Real-Time Control**: Start, stop, divest, and delete bots with button clicks
- **Custom Trading Logic**: Python-based trading functions/classes with buy/sell triggers
- **Data Integration**: Primary Robinhood API data with support for additional data feeds
- **Search & Query**: Searchable and queryable market and portfolio data
- **Live Parameter Modification**: Adjust bot parameters on-the-fly without stopping

### Technical Architecture
- **Frontend**: Browser-based UI for bot management and monitoring
- **Backend**: Python-based API server handling Robinhood integration
- **Bot Engine**: Modular trading bot system with customizable strategies
- **Database**: Portfolio data, bot configurations, and trading history
- **Containerization**: Full Docker deployment for easy setup and scaling

## Development Plan

### Phase 1: Foundation
1. Set up Docker environment and project structure
2. Implement Robinhood API integration and authentication
3. Create basic database schema for portfolios and bot configurations
4. Develop core bot management system

### Phase 2: Bot Framework
1. Design base trading bot class with buy/sell trigger framework
2. Implement portfolio monitoring and market data streaming
3. Create bot lifecycle management (start/stop/divest/delete)
4. Build percentage-based portfolio allocation system

### Phase 3: UI Development
1. Create React/Vue frontend for bot management dashboard
2. Implement real-time bot status monitoring
3. Build bot parameter editing interface
4. Add data visualization for portfolio performance

### Phase 4: Advanced Features
1. Custom Python code execution for trading strategies
2. Additional data feed integration
3. Advanced search and query capabilities
4. Performance analytics and reporting

## Technology Stack

- **Backend**: Python 3.11 with FastAPI, SQLAlchemy, Celery
- **Frontend**: React 18 with TypeScript, Material-UI
- **Database**: PostgreSQL 15 with structured financial data models
- **Cache/Message Broker**: Redis for Celery task queue and caching
- **Authentication**: JWT tokens with bcrypt password hashing
- **Real-time Updates**: WebSockets for live bot status updates
- **Containerization**: Docker with docker-compose for full stack deployment
- **API Integration**: robin-stocks for Robinhood API access
- **Testing**: pytest for Python backend, Jest for React frontend

## Development Best Practices

### Code Quality
- Use iterative development with frequent testing cycles
- Implement comprehensive automated testing (unit, integration, e2e)
- Maintain thorough docstrings for all functions and classes
- Follow PEP 8 for Python and ESLint standards for JavaScript
- Keep documentation current with code changes

### Trading Bot Design
- Base trading bot class should be extensible and modular
- Implement proper risk management and portfolio protection
- Use class-based approach for trading strategies with clear interfaces
- Include market monitoring, trigger evaluation, and execution methods
- Support hot-swapping of trading parameters without bot restart

### Security Considerations
- Secure API key management for Robinhood and other services
- Implement proper authentication and authorization
- Never commit sensitive credentials to repository
- Use environment variables for configuration
- Implement proper input validation for custom Python code execution

### Data Management
- Design efficient data models for real-time trading data
- Implement proper data retention and archival policies
- Ensure data consistency across bot operations
- Build robust error handling and recovery mechanisms

## Project Status

Repository is on the `cicd` branch with initial setup in progress.

## Quick Start

### Single Command Launch
```bash
./launch.sh
```

This script will:
1. Build all Docker containers
2. Start the complete application stack
3. Initialize the database
4. Launch the UI in your browser
5. Display access URLs and credentials

### Manual Launch
```bash
# Copy environment file and configure credentials
cp .env.example .env
# Edit .env with your Robinhood credentials

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [backend|frontend|postgres|redis|celery]

# Stop services
docker-compose down
```

### Access Points
- **Frontend UI**: http://localhost:9001
- **Backend API**: http://localhost:9002
- **API Documentation**: http://localhost:9002/api/docs
- **Database**: localhost:9003 (user: sirhiss, db: sirhiss_db)

### Default Credentials
- Username: `admin`
- Password: `admin123`

## Development Commands

### Backend (FastAPI)
```bash
# Enter backend container
docker-compose exec backend bash

# Run tests
pytest

# Run linting
black app/
isort app/
flake8 app/

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 9002
```

### Frontend (React)
```bash
# Enter frontend container
docker-compose exec frontend bash

# Install dependencies
npm install

# Run tests
npm test

# Run linting
npm run lint

# Build for production
npm run build

# Start development server
npm start
```

### Database Operations
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U sirhiss -d sirhiss_db

# Backup database
docker-compose exec postgres pg_dump -U sirhiss sirhiss_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U sirhiss -d sirhiss_db < backup.sql
```

## Architecture Overview

### Directory Structure
```
SirHiss/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   │   └── endpoints/  # Route handlers
│   │   ├── core/           # Core functionality
│   │   ├── models/         # SQLAlchemy models
│   │   └── services/       # Business logic
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API and business logic
│   │   └── types/          # TypeScript type definitions
│   └── package.json        # Node dependencies
├── database/              # Database initialization
│   └── init.sql          # Initial schema and data
├── docker-compose.yml    # Container orchestration
├── launch.sh            # Single-command launcher
└── .env                # Environment configuration
```

### Key Components

#### Database Models
- **Users**: Authentication and user management
- **Portfolios**: Overall investment portfolio tracking
- **TradingBots**: Bot configurations and status
- **BotExecutions**: Trading activity history
- **Holdings**: Current positions by bot
- **MarketData**: Cached market information

#### API Endpoints
- `/api/v1/auth/*` - Authentication (login, register, user info)
- `/api/v1/bots/*` - Bot management (CRUD, start/stop, delete)
- `/api/v1/portfolio/*` - Portfolio and holdings data
- `/api/v1/market/*` - Market data and symbol search
- `/ws/{client_id}` - WebSocket for real-time updates

#### Frontend Pages
- **Dashboard**: Portfolio overview and bot status summary
- **Bot Management**: Create, configure, and control trading bots
- **Portfolio**: Detailed holdings and performance tracking
- **Login**: User authentication

### Security Implementation
- JWT token-based authentication with bcrypt password hashing
- Environment variable management for sensitive credentials
- CORS configuration for frontend-backend communication
- Input validation using Pydantic models
- PostgreSQL with parameterized queries to prevent SQL injection

### Real-time Features
- WebSocket connections for live bot status updates
- Real-time portfolio value tracking
- Live trading execution notifications
- Dynamic bot parameter updates without restart