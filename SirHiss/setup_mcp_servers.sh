#!/bin/bash

# MCP Servers Installation Script
# Comprehensive setup script for Model Context Protocol servers
# Compatible with Claude Code and Claude Desktop
# Created: 2025-01-09

set -e  # Exit on any error

echo "🚀 Starting MCP Servers Installation..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Claude CLI is available
check_claude_cli() {
    if ! command -v claude &> /dev/null; then
        print_error "Claude CLI not found. Please install Claude Code first."
        exit 1
    fi
    print_status "Claude CLI found"
}

# Check if Node.js is available
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js not found. Please install Node.js 18+ first."
        exit 1
    fi
    
    node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$node_version" -lt 18 ]; then
        print_error "Node.js version 18+ required. Current version: $(node --version)"
        exit 1
    fi
    print_status "Node.js $(node --version) found"
}

# Install Fetch MCP Server
install_fetch() {
    print_info "Installing Fetch MCP Server..."
    if claude mcp add fetch -- npx -y @modelcontextprotocol/server-fetch; then
        print_status "Fetch MCP Server installed successfully"
    else
        print_warning "Fetch MCP Server installation failed or already exists"
    fi
}

# Install Context7 MCP Server
install_context7() {
    print_info "Installing Context7 MCP Server..."
    print_warning "Context7 provides up-to-date documentation for libraries"
    print_warning "Optional: Get API key from https://context7.com/dashboard for higher rate limits"
    
    # Try without API key first
    if claude mcp add context7 -- npx -y @upstash/context7-mcp; then
        print_status "Context7 MCP Server installed successfully (without API key)"
        print_info "To add API key later: claude mcp remove context7 && claude mcp add context7 -- npx -y @upstash/context7-mcp --api-key YOUR_API_KEY"
    else
        print_warning "Context7 MCP Server installation failed or already exists"
    fi
}

# Install Filesystem MCP Server
install_filesystem() {
    print_info "Installing Filesystem MCP Server..."
    # Use current directory as default, can be customized
    local fs_path="${1:-$(pwd)}"
    
    if claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem "$fs_path"; then
        print_status "Filesystem MCP Server installed successfully (path: $fs_path)"
    else
        print_warning "Filesystem MCP Server installation failed or already exists"
    fi
}

# Install GitHub MCP Server (if not already installed)
install_github() {
    print_info "Checking GitHub MCP Server..."
    
    if claude mcp get github &> /dev/null; then
        print_status "GitHub MCP Server already installed"
        return 0
    fi
    
    print_warning "GitHub MCP Server needs GITHUB_PERSONAL_ACCESS_TOKEN"
    print_info "Get token from: https://github.com/settings/tokens"
    
    if [ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
        print_warning "GITHUB_PERSONAL_ACCESS_TOKEN not set. Skipping GitHub server installation."
        print_info "To install later: export GITHUB_PERSONAL_ACCESS_TOKEN=your_token && claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=\$GITHUB_PERSONAL_ACCESS_TOKEN -- npx -y @modelcontextprotocol/server-github"
        return 1
    fi
    
    if claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" -- npx -y @modelcontextprotocol/server-github; then
        print_status "GitHub MCP Server installed successfully"
    else
        print_warning "GitHub MCP Server installation failed"
    fi
}

# Install Memory MCP Server (if not already installed)
install_memory() {
    print_info "Checking Memory MCP Server..."
    
    if claude mcp get memory-server &> /dev/null; then
        print_status "Memory MCP Server already installed"
        return 0
    fi
    
    if claude mcp add memory-server -- npx -y @modelcontextprotocol/server-memory; then
        print_status "Memory MCP Server installed successfully"
    else
        print_warning "Memory MCP Server installation failed"
    fi
}

# Install Database PostgreSQL MCP Server (if not already installed)
install_database_postgres() {
    print_info "Checking Database PostgreSQL MCP Server..."
    
    if claude mcp get database-postgres &> /dev/null; then
        print_status "Database PostgreSQL MCP Server already installed"
        return 0
    fi
    
    print_warning "Database server needs connection string"
    print_info "Example: postgresql://user:password@localhost:5432/dbname"
    
    if [ -z "$DATABASE_URL" ]; then
        print_warning "DATABASE_URL not set. Skipping database server installation."
        print_info "To install later: export DATABASE_URL=your_connection_string && claude mcp add database-postgres -e DATABASE_URL=\$DATABASE_URL -- npx -y postgres-mcp-server"
        return 1
    fi
    
    if claude mcp add database-postgres -e DATABASE_URL="$DATABASE_URL" -- npx -y postgres-mcp-server; then
        print_status "Database PostgreSQL MCP Server installed successfully"
    else
        print_warning "Database PostgreSQL MCP Server installation failed"
    fi
}

# Install Calculator MCP Server (if not already installed)
install_calculator() {
    print_info "Checking Calculator MCP Server..."
    
    if claude mcp get calculator &> /dev/null; then
        print_status "Calculator MCP Server already installed"
        return 0
    fi
    
    if claude mcp add calculator -- npx -y calculator-mcp-server; then
        print_status "Calculator MCP Server installed successfully"
    else
        print_warning "Calculator MCP Server installation failed"
    fi
}

# Install Playwright MCP Server (if not already installed)
install_playwright() {
    print_info "Checking Playwright MCP Server..."
    
    if claude mcp get playwright &> /dev/null; then
        print_status "Playwright MCP Server already installed"
        return 0
    fi
    
    if claude mcp add playwright npx @playwright/mcp@latest; then
        print_status "Playwright MCP Server installed successfully"
        print_info "Playwright enables browser automation and web scraping capabilities"
    else
        print_warning "Playwright MCP Server installation failed"
    fi
}

# Install Pieces MCP Server (if not already installed)
install_pieces() {
    print_info "Checking Pieces MCP Server..."
    
    if claude mcp get pieces &> /dev/null; then
        print_status "Pieces MCP Server already installed"
        return 0
    fi
    
    # Check if Pieces CLI is available
    if ! command -v pieces &> /dev/null; then
        print_warning "Pieces CLI not found. Please install Pieces for macOS first."
        print_info "Download from: https://pieces.app/"
        return 1
    fi
    
    print_info "Installing Pieces MCP Server (requires PiecesOS running)..."
    print_warning "Ensure PiecesOS is running and Long-Term Memory is enabled"
    
    if claude mcp add pieces sse://localhost:43997/mcp; then
        print_status "Pieces MCP Server installed successfully"
        print_info "Pieces provides long-term memory and workflow context to AI tools"
    else
        print_warning "Pieces MCP Server installation failed"
        print_info "Make sure PiecesOS is running and Long-Term Memory is enabled"
    fi
}

# Install additional useful MCP servers
install_additional_servers() {
    print_info "Installing additional useful MCP servers..."
    
    # Brave Search MCP Server (requires API key)
    if [ -n "$BRAVE_SEARCH_API_KEY" ]; then
        print_info "Installing Brave Search MCP Server..."
        if claude mcp add brave-search -e BRAVE_SEARCH_API_KEY="$BRAVE_SEARCH_API_KEY" -- npx -y @modelcontextprotocol/server-brave-search; then
            print_status "Brave Search MCP Server installed successfully"
        fi
    else
        print_info "Skipping Brave Search (BRAVE_SEARCH_API_KEY not set)"
    fi
    
    # Puppeteer MCP Server (for web scraping)
    print_info "Installing Puppeteer MCP Server..."
    if claude mcp add puppeteer -- npx -y @modelcontextprotocol/server-puppeteer; then
        print_status "Puppeteer MCP Server installed successfully"
    else
        print_warning "Puppeteer MCP Server installation failed"
    fi
    
    # SQLite MCP Server
    print_info "Installing SQLite MCP Server..."
    if claude mcp add sqlite -- npx -y @modelcontextprotocol/server-sqlite; then
        print_status "SQLite MCP Server installed successfully"
    else
        print_warning "SQLite MCP Server installation failed"
    fi
}

# Function to list all installed servers
list_servers() {
    echo ""
    print_info "Listing all installed MCP servers:"
    echo "=================================="
    claude mcp list
}

# Function to test server connections
test_servers() {
    echo ""
    print_info "Testing MCP server connections..."
    echo "================================="
    
    # Get list of servers and test each one
    local servers=$(claude mcp list 2>/dev/null | grep -E "^\w+" | awk '{print $1}' | tr ':' ' ' | awk '{print $1}')
    
    for server in $servers; do
        if claude mcp get "$server" &> /dev/null; then
            print_status "$server - Connected"
        else
            print_error "$server - Connection failed"
        fi
    done
}

# Main installation function
main() {
    echo "MCP Servers Installation Script"
    echo "==============================="
    echo ""
    
    # Pre-flight checks
    check_claude_cli
    check_node
    
    echo ""
    print_info "Starting MCP server installations..."
    
    # Core servers
    install_fetch
    install_context7
    install_filesystem "$1"  # Pass filesystem path as first argument
    install_github
    install_memory
    install_database_postgres
    install_calculator
    install_playwright
    install_pieces
    
    # Additional servers
    if [ "$2" = "--with-extras" ]; then
        install_additional_servers
    fi
    
    # List and test all servers
    list_servers
    test_servers
    
    echo ""
    print_status "MCP Server installation complete!"
    echo ""
    print_info "Environment variables you can set for enhanced functionality:"
    echo "  - GITHUB_PERSONAL_ACCESS_TOKEN: For GitHub integration"
    echo "  - DATABASE_URL: For PostgreSQL database access"
    echo "  - BRAVE_SEARCH_API_KEY: For Brave Search functionality"
    echo "  - CONTEXT7_API_KEY: For higher Context7 rate limits"
    echo ""
    print_info "Usage in Claude:"
    echo "  - 'use context7' - Get up-to-date documentation"
    echo "  - 'use playwright mcp' - Browser automation and web scraping"
    echo "  - 'use pieces' - Access workflow context and long-term memory"
    echo "  - '/mcp' - View available MCP tools"
    echo "  - Ask Claude to search GitHub, browse files, automate browsers, etc."
    echo ""
    print_info "To remove a server: claude mcp remove <server-name>"
    print_info "To update servers: re-run this script"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "MCP Servers Installation Script"
        echo ""
        echo "Usage: $0 [filesystem-path] [--with-extras]"
        echo ""
        echo "Arguments:"
        echo "  filesystem-path    Directory path for filesystem server (default: current directory)"
        echo "  --with-extras      Install additional MCP servers (Brave Search, Puppeteer, SQLite)"
        echo ""
        echo "Environment Variables (optional):"
        echo "  GITHUB_PERSONAL_ACCESS_TOKEN  GitHub API token"
        echo "  DATABASE_URL                  PostgreSQL connection string"
        echo "  BRAVE_SEARCH_API_KEY         Brave Search API key"
        echo "  CONTEXT7_API_KEY             Context7 API key"
        echo ""
        echo "Examples:"
        echo "  $0                                    # Install with defaults"
        echo "  $0 /path/to/project                   # Custom filesystem path"
        echo "  $0 /path/to/project --with-extras     # Install with additional servers"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac