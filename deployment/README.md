# TradeDesk Deployment Guide

This directory contains all deployment-related configurations and scripts for the TradeDesk platform.

## 📁 Directory Structure

```
deployment/
├── nginx/                  # Nginx configuration files
│   └── trade-desk.conf    # Production-optimized Nginx config
├── scripts/               # Deployment and maintenance scripts
│   ├── deploy.sh         # Full deployment script
│   ├── rollback.sh       # Rollback to previous version
│   ├── backup.sh         # Backup script
│   └── monitor.sh        # Health monitoring script
├── systemd/               # Systemd service files (alternative to PM2)
│   ├── trade-desk-backend.service
│   └── trade-desk-frontend.service
├── env/                   # Environment configuration templates
│   ├── backend.env.example
│   └── frontend.env.example
└── ecosystem.config.js    # PM2 configuration

```

## 🚀 Quick Start

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/piyushd1/trade-desk.git /home/trade-desk
   cd /home/trade-desk
   ```

2. **Configure environment**:
   ```bash
   # Backend
   cp deployment/env/backend.env.example backend/.env
   # Edit backend/.env with your values
   
   # Frontend
   cp deployment/env/frontend.env.example frontend/.env.production
   # Edit frontend/.env.production
   ```

3. **Run initial deployment**:
   ```bash
   ./deployment/scripts/deploy.sh production
   ```

### Nginx Setup

1. **Copy Nginx configuration**:
   ```bash
   sudo cp deployment/nginx/trade-desk.conf /etc/nginx/sites-available/
   sudo ln -s /etc/nginx/sites-available/trade-desk.conf /etc/nginx/sites-enabled/
   ```

2. **Test and reload Nginx**:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Process Management

#### Option 1: PM2 (Recommended)

```bash
# Start all services
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save
pm2 startup

# View logs
pm2 logs

# Monitor processes
pm2 monit
```

#### Option 2: Systemd

```bash
# Copy service files
sudo cp deployment/systemd/*.service /etc/systemd/system/

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable trade-desk-backend trade-desk-frontend
sudo systemctl start trade-desk-backend trade-desk-frontend

# Check status
sudo systemctl status trade-desk-backend
sudo systemctl status trade-desk-frontend
```

## 📜 Deployment Scripts

### deploy.sh

Full deployment script that handles:
- Code updates from Git
- Dependency installation
- Database migrations
- Frontend build
- Service restart
- Health checks

**Usage**:
```bash
./deployment/scripts/deploy.sh [environment]
# Example: ./deployment/scripts/deploy.sh production
```

### rollback.sh

Rollback to a previous deployment:

```bash
# Interactive mode (shows last 10 commits)
./deployment/scripts/rollback.sh

# Direct rollback to specific commit
./deployment/scripts/rollback.sh abc123def
```

### backup.sh

Create backups of database, config, and logs:

```bash
# Full backup
./deployment/scripts/backup.sh full

# Database only
./deployment/scripts/backup.sh database

# Configuration only
./deployment/scripts/backup.sh config
```

### monitor.sh

Health monitoring script (can be run via cron):

```bash
# Manual run
./deployment/scripts/monitor.sh

# Add to crontab for automatic monitoring
crontab -e
# Add: */5 * * * * /home/trade-desk/deployment/scripts/monitor.sh
```

## 🔐 Security Considerations

1. **SSL/TLS**: Ensure Let's Encrypt certificates are renewed automatically
2. **Firewall**: Only ports 80 and 443 should be publicly accessible
3. **Database**: Regular backups are crucial for SEBI compliance
4. **Secrets**: Never commit `.env` files or secrets to Git
5. **Updates**: Regularly update system packages and dependencies

## 📊 Monitoring

### Application Metrics
- Backend health: `https://piyushdev.com/health`
- Frontend status: Check PM2 or systemd status
- API documentation: `https://piyushdev.com/docs`

### System Monitoring
- CPU, Memory, Disk usage via `monitor.sh`
- Nginx logs: `/var/log/nginx/trade-desk-*.log`
- Application logs: `/home/trade-desk/logs/`

### Alerts
Configure alerts in `monitor.sh`:
```bash
# Edit monitor.sh
ALERT_EMAIL="your-email@example.com"
SLACK_WEBHOOK="https://hooks.slack.com/services/..."
```

## 🆘 Troubleshooting

### Service Won't Start
```bash
# Check logs
pm2 logs trade-desk-backend
# or
journalctl -u trade-desk-backend -f

# Check port availability
sudo netstat -tlnp | grep -E "8000|3001"
```

### Database Issues
```bash
# Check database integrity
cd backend
sqlite3 trade_desk.db "PRAGMA integrity_check;"

# Restore from backup
cp /home/trade-desk/backups/latest/trade_desk.db backend/
```

### High Resource Usage
```bash
# Check process usage
pm2 monit

# Restart services
pm2 restart all

# Clear caches
rm -rf frontend/.next/cache
```

## 📈 Performance Optimization

1. **Nginx Caching**: Static assets are cached for 60 days
2. **Rate Limiting**: API endpoints are rate-limited
3. **Gzip Compression**: Enabled for text-based responses
4. **Connection Pooling**: Database and Redis connections are pooled

## 🔄 CI/CD Integration

For automated deployments:

1. **GitHub Actions** (example):
   ```yaml
   - name: Deploy to server
     run: |
       ssh user@piyushdev.com "cd /home/trade-desk && ./deployment/scripts/deploy.sh production"
   ```

2. **Webhook Deployment**:
   - Set up a webhook endpoint to trigger deployments
   - Use the deployment scripts for automated updates

## 📋 Maintenance Checklist

### Daily
- [ ] Check service health via monitoring dashboard
- [ ] Review error logs for critical issues

### Weekly
- [ ] Run full backup
- [ ] Check disk usage
- [ ] Review performance metrics

### Monthly
- [ ] Update system packages
- [ ] Review and rotate logs
- [ ] Check SSL certificate expiration
- [ ] Test backup restoration

### Quarterly
- [ ] Security audit
- [ ] Dependency updates
- [ ] Performance optimization review
- [ ] Disaster recovery drill

## 🚨 Emergency Procedures

### Service Outage
1. Check service status: `pm2 status`
2. Restart services: `pm2 restart all`
3. Check logs for errors
4. If needed, rollback: `./deployment/scripts/rollback.sh`

### Database Corruption
1. Stop backend: `pm2 stop trade-desk-backend`
2. Restore from backup: `./deployment/scripts/backup.sh`
3. Run integrity check
4. Restart backend

### Security Breach
1. Enable kill switch immediately
2. Stop all services
3. Review access logs
4. Change all credentials
5. Deploy security patches

## 📞 Support

For deployment issues:
1. Check logs in `/home/trade-desk/logs/`
2. Review this documentation
3. Contact the development team

Remember: Always test deployments in staging before production!
