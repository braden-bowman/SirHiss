# MCP Server Configuration for SirHiss Trading Platform

This document outlines the Model Context Protocol (MCP) servers configured for the SirHiss trading platform project.

## Successfully Configured MCP Servers

### 1. Memory Server
- **Package**: `@modelcontextprotocol/server-memory`
- **Status**: ✓ Connected
- **Purpose**: Knowledge graph-based persistent memory for the AI assistant
- **Use Case**: Remembers project context, trading strategies, and user preferences across sessions

### 2. Database PostgreSQL Server
- **Package**: `postgres-mcp-server`
- **Status**: ✓ Connected
- **Purpose**: Direct interaction with PostgreSQL databases
- **Use Case**: Query trading data, bot configurations, and portfolio information directly

### 3. GitHub Server
- **Package**: `@modelcontextprotocol/server-github`
- **Status**: ✓ Connected
- **Purpose**: Interact with GitHub repositories, issues, and pull requests
- **Use Case**: Manage code changes, track issues, and collaborate on development

### 4. Calculator Server
- **Package**: `calculator-mcp-server`
- **Status**: ✓ Connected
- **Purpose**: Precise numerical calculations
- **Use Case**: Financial calculations, portfolio allocation computations, and trading math

## Configuration Commands Used

```bash
# Add memory server for persistent AI context
claude mcp add memory-server -- npx -y @modelcontextprotocol/server-memory

# Add PostgreSQL database server
claude mcp add database-postgres -- npx -y postgres-mcp-server

# Add GitHub integration
claude mcp add github -- npx -y @modelcontextprotocol/server-github

# Add calculator for financial calculations
claude mcp add calculator -- npx -y calculator-mcp-server
```

## Failed Configurations (Removed)

The following servers failed to connect and were removed:
- **Fetch Server**: Web content fetching (connection issues)
- **Context7**: Documentation server (connection issues)
- **Browser Automation**: Local browser control (connection issues)
- **Git Server**: Repository management (connection issues)
- **Filesystem**: File operations (connection issues)
- **Time Server**: Time and timezone operations (connection issues)

## Trading-Specific MCP Servers (Require API Keys)

### Alpaca Trading
```bash
# Requires API credentials
claude mcp add alpaca-trading -e ALPACA_API_KEY=your_key -e ALPACA_SECRET_KEY=your_secret -e ALPACA_BASE_URL=https://paper-api.alpaca.markets -- npx -y alpaca-mcp-server
```

### AlphaVantage Market Data
```bash
# Requires API key
claude mcp add alphavantage -e ALPHA_VANTAGE_API_KEY=your_key -- npx -y alphavantage-mcp-server
```

## Verifying Configuration

To check the status of all MCP servers:
```bash
claude mcp list
```

To get detailed information about a specific server:
```bash
claude mcp get <server-name>
```

## Benefits for SirHiss Trading Platform

1. **Memory Server**: Maintains context about trading strategies and user preferences
2. **Database Server**: Direct SQL queries to the PostgreSQL database for real-time data
3. **GitHub Server**: Streamlined development workflow and issue tracking
4. **Calculator Server**: Accurate financial calculations for portfolio management

## Notes

- All servers are configured in local scope (private to this project)
- Servers with external dependencies (API keys, network services) may require additional configuration
- Failed servers indicate either missing dependencies or network connectivity issues
- Consider re-attempting failed server configurations after ensuring prerequisites are met