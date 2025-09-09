# 📊 SirHiss API Connection Setup Guide

## Overview

This guide explains how to connect your trading accounts and data sources to SirHiss for automated trading. All connections use production-level security with encrypted credential storage.

## 🔒 Security First

- **Encrypted Storage**: All credentials are encrypted using AES-256 with PBKDF2 key derivation
- **No Plaintext**: Passwords and API keys are never stored in plaintext
- **Secure Transmission**: All data transmission uses HTTPS/TLS
- **Account Isolation**: Each user's credentials are completely isolated
- **Audit Logging**: All connection attempts are logged for security monitoring

## 🚀 Quick Start

1. Open SirHiss dashboard: `http://localhost:9001`
2. Log in with your account
3. Navigate to **Settings** section
4. Click **+ Add Connection**
5. Select your platform and follow the setup guide below

---

## 📈 Supported Platforms

### 1. Robinhood Trading

**What it provides:**
- Real-time portfolio data
- Stock/crypto trading execution
- Account balance and positions
- Order history and management

**Required Information:**
- Robinhood username
- Robinhood password
- MFA code (if 2FA is enabled)

**Setup Steps:**

1. **Select Platform**: Choose "Robinhood" from the dropdown
2. **Connection Name**: Enter a name like "My Robinhood Account"
3. **Credentials**:
   - Username: Your Robinhood login username
   - Password: Your Robinhood login password
   - MFA Code: If you have 2FA enabled, enter the 6-digit code from your authenticator app
4. **Test Connection**: Click "Test Connection" to verify
5. **Save**: Once test passes, click "Save Connection"

**Important Notes:**
- ⚠️ **Two-Factor Authentication**: If you have 2FA enabled on Robinhood, you'll need to provide the MFA code
- 🛡️ **Account Security**: Consider creating a dedicated Robinhood account for automated trading
- ⏱️ **Session Management**: Connections are tested periodically and will prompt for re-authentication if needed
- 📱 **Device Authorization**: Robinhood may require device authorization on first connection

**Troubleshooting:**
- **"Two-factor authentication required"**: Enter your 6-digit MFA code and try again
- **"Account requires additional verification"**: Check your email/SMS for Robinhood verification prompts
- **"Account is locked or disabled"**: Log into the Robinhood app to resolve account issues
- **"Incorrect username or password"**: Double-check your Robinhood credentials

---

### 2. Yahoo Finance (Free Market Data)

**What it provides:**
- Real-time stock quotes
- Historical price data
- Market statistics
- Company information
- No cost, no API key needed

**Required Information:**
- None (completely free service)

**Setup Steps:**

1. **Select Platform**: Choose "Yahoo Finance" from the dropdown
2. **Connection Name**: Enter a name like "Yahoo Finance Data"
3. **Test Connection**: Click "Test Connection" to verify data access
4. **Auto-Save**: Connection saves automatically after successful test

**Features:**
- ✅ **Free Forever**: No API keys, no rate limits for basic usage
- 📊 **Comprehensive Data**: Stocks, ETFs, cryptocurrencies, currencies
- 🌍 **Global Markets**: US, international exchanges
- 📈 **Historical Data**: Years of historical price data

**Use Cases:**
- Market analysis and research
- Price monitoring for trading strategies
- Portfolio performance tracking
- Market trend analysis

---

### 3. Alpha Vantage (Premium Market Data)

**What it provides:**
- High-frequency market data
- Real-time quotes
- Technical indicators
- Fundamental data
- Global market coverage

**Required Information:**
- Alpha Vantage API key

**Setup Steps:**

1. **Get API Key**:
   - Visit [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)
   - Sign up for free account
   - Copy your API key

2. **Add Connection**:
   - Select "Alpha Vantage" from platform dropdown
   - Connection Name: Enter "Alpha Vantage Data" or similar
   - API Key: Paste your Alpha Vantage API key

3. **Test Connection**: System will verify your API key works
4. **Save**: Connection saves after successful verification

**API Key Tiers:**
- 🆓 **Free Tier**: 5 API requests per minute, 500 per day
- 💎 **Premium Tiers**: Higher rates, real-time data, additional features

**Best Practices:**
- 🔐 **Keep API Key Secret**: Never share your API key
- 📊 **Monitor Usage**: Check your usage on Alpha Vantage dashboard
- 🚀 **Upgrade When Needed**: Consider premium plans for high-frequency trading

**Troubleshooting:**
- **"API key is required"**: Make sure you entered your API key correctly
- **"Alpha Vantage error: Invalid API call"**: API key may be incorrect
- **"Alpha Vantage limit: Thank you for using Alpha Vantage!"**: You've hit rate limits

---

## 🛠️ Connection Management

### Testing Connections

**Automatic Testing:**
- All connections are tested when created
- Real API calls verify credentials work
- Status indicators show current health

**Manual Testing:**
- Click "Test" on any connection card
- System performs live connection test
- Results update connection status immediately

**Connection States:**
- 🟢 **Connected**: Working properly, last test successful
- 🔴 **Error**: Connection failed, needs attention
- 🟡 **Untested**: New connection, not yet verified
- 🔵 **Testing**: Currently running connection test

### Managing Credentials

**Editing Connections:**
- Edit button available in full React application
- Currently: delete and recreate connections to update

**Deleting Connections:**
- Click "Delete" on connection card
- Confirm deletion (this cannot be undone)
- All encrypted data is permanently removed

**Security Best Practices:**
- 🔄 **Rotate Regularly**: Update passwords/keys periodically
- 👥 **Separate Accounts**: Use dedicated accounts for automated trading
- 📱 **Monitor Access**: Review connection logs regularly
- 🚨 **Immediate Action**: Delete connections if credentials are compromised

---

## 🔧 Advanced Configuration

### Environment Variables

For production deployment, set these environment variables:

```bash
# Required for production
SECRET_KEY=your-cryptographically-secure-secret-key-here
ENCRYPTION_SALT=your-unique-salt-string-here
ENVIRONMENT=production

# Database (if using external PostgreSQL)
POSTGRES_HOST=your-db-host
POSTGRES_USER=your-db-user
POSTGRES_PASSWORD=your-secure-db-password
POSTGRES_DB=sirhiss_db
```

### Connection Polling

**Automatic Health Checks:**
- System tests connections every 5 minutes
- Failed connections are retested every 15 minutes
- Status updates appear in real-time on dashboard

**Rate Limiting:**
- Built-in rate limiting prevents API abuse
- Exponential backoff on failures
- Respects platform-specific limits

### Data Usage

**Robinhood:**
- Portfolio data refreshed every 30 seconds
- Order updates in real-time
- Respects Robinhood rate limits

**Yahoo Finance:**
- Price data refreshed every 15 seconds
- Historical data cached for 5 minutes
- No rate limits for normal usage

**Alpha Vantage:**
- Requests batched to respect rate limits
- Priority given to real-time trading data
- Caching used to minimize API calls

---

## 🚨 Troubleshooting

### Common Issues

**"Connection test failed"**
1. Verify credentials are correct
2. Check if account is active/unlocked
3. Ensure 2FA codes are current (Robinhood)
4. Try again in a few minutes

**"Unable to save connection"**
1. Make sure connection test passed first
2. Check for duplicate connection names
3. Verify browser has stable internet connection

**API connections showing as "Error"**
1. Platform may be experiencing outages
2. Credentials may have expired
3. Account may be suspended/locked
4. Rate limits may have been exceeded

### Getting Help

**Check Status Pages:**
- Robinhood Status: [status.robinhood.com](https://status.robinhood.com)
- Yahoo Finance: Usually no status page (service is very reliable)
- Alpha Vantage: Check their website for announcements

**Log Analysis:**
- Connection attempts are logged with timestamps
- Error messages provide specific failure reasons
- Contact support with log details if issues persist

**Re-authentication:**
- Most connection issues resolve by re-testing
- Delete and recreate connections if problems persist
- Some platforms require periodic re-authentication

---

## 🔐 Security Considerations

### Production Deployment

**Network Security:**
- Use HTTPS/TLS for all connections
- Deploy behind firewall
- Restrict database access
- Use VPN for admin access

**Credential Management:**
- Rotate encryption keys regularly
- Use hardware security modules (HSMs) for keys
- Implement credential expiration policies
- Monitor for unauthorized access

**Compliance:**
- Log all credential access
- Implement data retention policies
- Regular security audits
- Comply with financial regulations

### Risk Management

**Account Separation:**
- Use separate accounts for automated trading
- Limit automated account balances
- Set up alerts for unusual activity
- Regular manual oversight

**API Key Security:**
- Never commit API keys to code repositories
- Use environment variables for deployment
- Rotate keys on schedule
- Monitor API key usage

---

## 📞 Support

For issues with API connections:

1. **Check This Guide**: Most issues are covered above
2. **Test Connection**: Use the built-in test feature
3. **Check Platform Status**: Verify the external service is operational
4. **Review Logs**: Check browser console for error details
5. **Contact Support**: Provide connection ID and error messages

**Remember**: SirHiss never stores your credentials in plaintext, and all connections use industry-standard encryption. Your trading account security is our top priority.

---

*Last Updated: January 2025*  
*Version: 2.0.0 - Production Release*