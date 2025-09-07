# 🐍 SirHiss - Automated Trading Bot Platform

A dockerized trading bot application that connects to the Robinhood API for automated stock and cryptocurrency trading. Features a modern web-based UI for managing multiple trading bot instances with customizable Python-based strategies.

![Dashboard](https://img.shields.io/badge/Status-Beta-yellow)
![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![React](https://img.shields.io/badge/React-18-blue)

## ✨ Features

- **Multi-Bot Architecture**: Create and manage multiple trading bot instances
- **Portfolio Allocation**: Allocate percentage-based portions of total portfolio to each bot
- **Real-Time Control**: Start, stop, divest, and delete bots with button clicks
- **Custom Trading Logic**: Python-based trading functions with buy/sell triggers
- **Live Parameter Modification**: Adjust bot parameters on-the-fly without stopping
- **Real-time Updates**: WebSocket-powered live status updates
- **Secure Authentication**: JWT-based user authentication with bcrypt hashing

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Robinhood account credentials

### Launch (Single Command)
```bash
git clone <repository-url>
cd SirHiss
./launch.sh
```

The launch script will:
1. Build all Docker containers
2. Start the complete application stack
3. Initialize the database with default data
4. Open the UI in your browser
5. Display access URLs and credentials

### Manual Setup
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your Robinhood credentials

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🌐 Access Points

- **Frontend UI**: http://localhost:9001
- **Backend API**: http://localhost:9002  
- **API Documentation**: http://localhost:9002/api/docs
- **Database**: localhost:9003

### Default Login
- **Username**: `admin`
- **Password**: `admin123`

## 🏗️ Architecture

### Tech Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Celery
- **Frontend**: React 18, TypeScript, Material-UI
- **Database**: PostgreSQL 15
- **Cache**: Redis
- **Deployment**: Docker + Docker Compose

### Project Structure
```
SirHiss/
├── backend/           # FastAPI Python backend
├── frontend/          # React TypeScript frontend  
├── database/          # PostgreSQL initialization
├── docker-compose.yml # Container orchestration
├── launch.sh         # Single-command launcher
└── .env              # Environment configuration
```

## 🤖 Creating Trading Bots

1. Navigate to **Bot Management** page
2. Click **Create New Bot**
3. Configure:
   - Bot name and description
   - Portfolio allocation percentage
   - Custom Python trading strategy
   - Trading parameters
4. Start/stop bots with one click
5. Monitor performance in real-time

### Example Trading Strategy
```python
class MyTradingBot(TradingBot):
    def should_buy(self, symbol, price, market_data):
        # Custom buy logic
        return price < self.parameters.get('buy_threshold', 100)
    
    def should_sell(self, symbol, position, current_price):
        # Custom sell logic
        profit_pct = (current_price - position.avg_cost) / position.avg_cost
        return profit_pct > self.parameters.get('profit_target', 0.1)
```

## 🔧 Development

### Backend Development
```bash
docker-compose exec backend bash
pytest                    # Run tests
black app/               # Format code
uvicorn app.main:app --reload
```

### Frontend Development  
```bash
docker-compose exec frontend bash
npm test                 # Run tests
npm start               # Development server
```

### Database Operations
```bash
docker-compose exec postgres psql -U sirhiss -d sirhiss_db
```

## ⚠️ Important Security Notes

- **Never commit real Robinhood credentials to version control**
- Change default admin password immediately
- Use strong `SECRET_KEY` in production
- Consider using environment-specific `.env` files
- Review bot strategies before deployment with real money

## 🚧 Development Status

This is a beta release. Core features implemented:
- ✅ User authentication
- ✅ Bot management (CRUD operations)  
- ✅ Portfolio tracking
- ✅ Real-time WebSocket updates
- ✅ Docker deployment
- 🚧 Robinhood API integration
- 🚧 Live trading execution
- 🚧 Advanced analytics

## 📝 License

MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational purposes only. Trading stocks and cryptocurrencies involves substantial risk. Past performance does not guarantee future results. The authors are not responsible for any financial losses incurred through use of this software.

---

**Happy Trading! 🐍📈**