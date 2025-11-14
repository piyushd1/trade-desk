/**
 * PM2 Ecosystem Configuration for TradeDesk
 * 
 * This file configures PM2 to manage both backend and frontend processes
 * with automatic restarts, logging, and monitoring.
 * 
 * Usage:
 * - Start all: pm2 start ecosystem.config.js
 * - Start specific: pm2 start ecosystem.config.js --only backend
 * - Reload: pm2 reload ecosystem.config.js
 * - Monitor: pm2 monit
 */

module.exports = {
  apps: [
    {
      // FastAPI Backend
      name: 'trade-desk-backend',
      script: 'python',
      args: '-m uvicorn app.main:app --host 127.0.0.1 --port 8000',
      cwd: '/home/trade-desk/backend',
      interpreter: '/home/trade-desk/backend/venv/bin/python',
      
      // Process Management
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      
      // Restart Policy
      min_uptime: '10s',
      max_restarts: 5,
      restart_delay: 5000,
      
      // Environment Variables
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/home/trade-desk/backend',
        APP_ENV: 'production',
      },
      
      // Logging
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/home/trade-desk/logs/backend-error.log',
      out_file: '/home/trade-desk/logs/backend-out.log',
      combine_logs: true,
      
      // Graceful Shutdown
      kill_timeout: 5000,
      listen_timeout: 5000,
      shutdown_with_message: true,
    },
    
    {
      // Next.js Frontend
      name: 'trade-desk-frontend',
      script: 'npm',
      args: 'run start',
      cwd: '/home/trade-desk/frontend',
      
      // Process Management
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      
      // Restart Policy
      min_uptime: '10s',
      max_restarts: 5,
      restart_delay: 5000,
      
      // Environment Variables
      env: {
        NODE_ENV: 'production',
        PORT: 3001,
      },
      
      // Logging
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/home/trade-desk/logs/frontend-error.log',
      out_file: '/home/trade-desk/logs/frontend-out.log',
      combine_logs: true,
      
      // Node.js Specific
      node_args: '--max-old-space-size=1024',
      
      // Graceful Shutdown
      kill_timeout: 5000,
      listen_timeout: 5000,
      shutdown_with_message: true,
    },
    
    {
      // Celery Worker (if needed for background tasks)
      name: 'trade-desk-celery',
      script: 'celery',
      args: '-A app.celery_app worker --loglevel=info',
      cwd: '/home/trade-desk/backend',
      interpreter: '/home/trade-desk/backend/venv/bin/celery',
      
      // Process Management
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      
      // Environment Variables
      env: {
        PYTHONPATH: '/home/trade-desk/backend',
        APP_ENV: 'production',
      },
      
      // Logging
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/home/trade-desk/logs/celery-error.log',
      out_file: '/home/trade-desk/logs/celery-out.log',
      
      // Disable if not using Celery
      enabled: false,
    },
    
    {
      // Redis (if managing Redis through PM2)
      name: 'trade-desk-redis',
      script: 'redis-server',
      args: '/etc/redis/redis.conf',
      
      // Process Management
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      
      // Logging
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/home/trade-desk/logs/redis-error.log',
      out_file: '/home/trade-desk/logs/redis-out.log',
      
      // Disable if Redis is managed by systemd
      enabled: false,
    }
  ],
  
  // Deploy Configuration (for remote deployments)
  deploy: {
    production: {
      user: 'root',
      host: 'piyushdev.com',
      ref: 'origin/master',
      repo: 'https://github.com/piyushd1/trade-desk.git',
      path: '/home/trade-desk',
      'post-deploy': 'npm install && npm run build && pm2 reload ecosystem.config.js --env production',
      env: {
        NODE_ENV: 'production',
        APP_ENV: 'production'
      }
    }
  }
};
