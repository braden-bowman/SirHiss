# Security Setup Guide

## 🔒 Critical Security Configuration

**⚠️ IMPORTANT**: Before running SirHiss, you MUST configure secure credentials.

## Required Environment Variables

Copy `.env.example` to `.env` and configure the following:

### Database Security
```bash
POSTGRES_USER=your_secure_username
POSTGRES_PASSWORD=generate_strong_32_char_password
POSTGRES_DB=your_database_name
```

### Application Security
```bash
# Generate a secure 32+ character secret key
SECRET_KEY=your-cryptographically-secure-secret-key-here

# Generate a unique salt for credential encryption
ENCRYPTION_SALT=your-unique-salt-string-here

# Set to production for live deployment
ENVIRONMENT=production
```

## How to Generate Secure Values

### Secret Key & Salt
```bash
# Generate secure secret key (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption salt
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### Database Password
```bash
# Generate secure database password
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

## Trading Platform Credentials

**DO NOT** put trading credentials in environment variables. Instead:

1. Start the application
2. Register a user account via the web interface
3. Use the Settings page to securely add your trading platform credentials
4. All trading credentials are encrypted before storage

## Security Best Practices

1. **Never commit `.env` files** - They're gitignored for security
2. **Use strong, unique passwords** for all services
3. **Rotate secrets regularly** in production
4. **Use HTTPS** in production environments
5. **Keep dependencies updated** with `docker-compose pull`

## Production Deployment

For production:
1. Use a managed PostgreSQL service
2. Enable SSL/TLS for all connections  
3. Set up proper firewall rules
4. Use container orchestration (Kubernetes, Docker Swarm)
5. Enable logging and monitoring
6. Regular security updates and backups

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly by emailing the maintainers rather than creating a public issue.