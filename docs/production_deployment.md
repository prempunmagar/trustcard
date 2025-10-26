# Production Deployment Guide

Complete guide for deploying TrustCard to production with security, performance, and monitoring best practices.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Database Setup](#database-setup)
4. [Redis Configuration](#redis-configuration)
5. [Application Deployment](#application-deployment)
6. [Security Hardening](#security-hardening)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Performance Tuning](#performance-tuning)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### ✅ Required Services
- [ ] PostgreSQL 14+ database
- [ ] Redis 6+ server
- [ ] Python 3.11+ runtime
- [ ] Celery workers
- [ ] Reverse proxy (Nginx/Caddy)
- [ ] SSL/TLS certificates

### ✅ Required Credentials
- [ ] Instagram account credentials
- [ ] Database connection string
- [ ] Secret key for sessions
- [ ] (Optional) Prometheus/Grafana for monitoring

### ✅ Resource Requirements

**Minimum** (Low traffic, ~10 analyses/hour):
- 2 CPU cores
- 4 GB RAM
- 20 GB disk space

**Recommended** (Medium traffic, ~100 analyses/hour):
- 4 CPU cores
- 8 GB RAM
- 50 GB disk space
- Celery: 4 workers

**High Traffic** (~1000 analyses/hour):
- 8+ CPU cores
- 16+ GB RAM
- 100+ GB disk space
- Celery: 8-12 workers
- Consider Redis Cluster for caching

---

## Environment Configuration

### Production `.env` File

Create `.env` in project root:

```bash
# ============================================================================
# ENVIRONMENT
# ============================================================================
ENVIRONMENT=production
DEBUG=False

# ============================================================================
# DATABASE
# ============================================================================
DATABASE_URL=postgresql://username:password@db-host:5432/trustcard
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# ============================================================================
# REDIS & CELERY
# ============================================================================
REDIS_URL=redis://redis-host:6379/0
CELERY_BROKER_URL=redis://redis-host:6379/0
CELERY_RESULT_BACKEND=redis://redis-host:6379/1

# ============================================================================
# INSTAGRAM
# ============================================================================
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password

# ============================================================================
# API
# ============================================================================
API_HOST=0.0.0.0
API_PORT=8000

# ============================================================================
# SECURITY
# ============================================================================
SECRET_KEY=<generate-strong-random-key>  # Use: openssl rand -hex 32

# CORS - Set specific origins!
CORS_ORIGINS=["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "DELETE"]
CORS_ALLOW_HEADERS=["*"]

# ============================================================================
# RATE LIMITING
# ============================================================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL=INFO
LOG_FILE=/var/log/trustcard/app.log
LOG_JSON=true  # Structured JSON logs for production

# ============================================================================
# MONITORING
# ============================================================================
ENABLE_METRICS=true
METRICS_PATH=/metrics

# ============================================================================
# VALIDATION
# ============================================================================
MAX_URL_LENGTH=2000
MAX_COMMENT_LENGTH=1000
```

### Generate Secret Key

```bash
openssl rand -hex 32
```

---

## Database Setup

### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create Database and User

```bash
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE trustcard;
CREATE USER trustcard WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE trustcard TO trustcard;
\q
```

### 3. Run Migrations

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head
```

### 4. Database Performance Tuning

Edit `/etc/postgresql/14/main/postgresql.conf`:

```conf
# Connection settings
max_connections = 100

# Memory settings (adjust based on available RAM)
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 16MB

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Query planner
random_page_cost = 1.1
effective_io_concurrency = 200
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

## Redis Configuration

### 1. Install Redis

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# Start service
sudo systemctl start redis
sudo systemctl enable redis
```

### 2. Configure Redis for Production

Edit `/etc/redis/redis.conf`:

```conf
# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru  # Evict least recently used keys

# Persistence (optional but recommended)
save 900 1        # Save after 900 sec if at least 1 key changed
save 300 10       # Save after 300 sec if at least 10 keys changed
save 60 10000     # Save after 60 sec if at least 10000 keys changed

# Security
requirepass your_redis_password_here
bind 127.0.0.1  # Only allow local connections

# Performance
tcp-backlog 511
timeout 0
tcp-keepalive 300
```

Restart Redis:
```bash
sudo systemctl restart redis
```

Update Redis URL in `.env`:
```bash
REDIS_URL=redis://:your_redis_password_here@localhost:6379/0
```

---

## Application Deployment

### Option 1: Docker (Recommended)

**1. Build Docker images:**

```bash
docker-compose -f docker-compose.prod.yml build
```

**2. Create `docker-compose.prod.yml`:**

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped
    volumes:
      - ./logs:/var/log/trustcard

  celery-worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      POSTGRES_USER: trustcard
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: trustcard
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

**3. Start services:**

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Option 2: Systemd (Ubuntu/Debian)

**1. Create systemd service for API:**

`/etc/systemd/system/trustcard-api.service`:

```ini
[Unit]
Description=TrustCard API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/trustcard
Environment="PATH=/var/www/trustcard/venv/bin"
ExecStart=/var/www/trustcard/venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-config /var/www/trustcard/logging.conf
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**2. Create systemd service for Celery workers:**

`/etc/systemd/system/trustcard-celery.service`:

```ini
[Unit]
Description=TrustCard Celery Workers
After=network.target redis.service

[Service]
Type=forking
User=www-data
WorkingDirectory=/var/www/trustcard
Environment="PATH=/var/www/trustcard/venv/bin"
ExecStart=/var/www/trustcard/venv/bin/celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --pidfile=/var/run/trustcard/celery.pid
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**3. Start services:**

```bash
sudo systemctl daemon-reload
sudo systemctl start trustcard-api
sudo systemctl start trustcard-celery
sudo systemctl enable trustcard-api
sudo systemctl enable trustcard-celery
```

---

## Security Hardening

### 1. Reverse Proxy with Nginx

Create `/etc/nginx/sites-available/trustcard`:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# Upstream
upstream trustcard_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name trustcard.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name trustcard.example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/trustcard.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/trustcard.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/trustcard_access.log;
    error_log /var/log/nginx/trustcard_error.log;

    # Rate limiting
    limit_req zone=api_limit burst=20 nodelay;

    # Proxy settings
    location / {
        proxy_pass http://trustcard_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;  # Long timeout for analysis
    }

    # Health checks (no rate limit)
    location /health {
        proxy_pass http://trustcard_api;
        access_log off;
    }

    # Metrics (restrict access)
    location /metrics {
        allow 10.0.0.0/8;  # Internal network only
        deny all;
        proxy_pass http://trustcard_api;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/trustcard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block direct access to services
# (Only Nginx should access them)
sudo ufw deny 8000/tcp
sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp

# Enable firewall
sudo ufw enable
```

### 3. File Permissions

```bash
# Application directory
sudo chown -R www-data:www-data /var/www/trustcard
sudo chmod -R 755 /var/www/trustcard

# Log directory
sudo mkdir -p /var/log/trustcard
sudo chown -R www-data:www-data /var/log/trustcard
sudo chmod 755 /var/log/trustcard

# Environment file (contains secrets!)
sudo chmod 600 /var/www/trustcard/.env
```

---

## Monitoring & Logging

### 1. Prometheus Metrics

Scrape configuration for Prometheus (`prometheus.yml`):

```yaml
scrape_configs:
  - job_name: 'trustcard'
    scrape_interval: 30s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### 2. Log Rotation

Create `/etc/logrotate.d/trustcard`:

```
/var/log/trustcard/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    create 0644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload trustcard-api
    endscript
}
```

### 3. Health Check Monitoring

Add to cron for external monitoring:

```bash
# /etc/cron.d/trustcard-health
*/5 * * * * curl -sf http://localhost:8000/health || systemctl restart trustcard-api
```

---

## Backup & Recovery

### 1. Database Backups

Create `/usr/local/bin/backup-trustcard-db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/trustcard"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/trustcard_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

pg_dump -h localhost -U trustcard trustcard | gzip > $BACKUP_FILE

# Keep only last 30 days of backups
find $BACKUP_DIR -name "trustcard_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

Add to cron:
```bash
# Daily at 2 AM
0 2 * * * /usr/local/bin/backup-trustcard-db.sh
```

### 2. Redis Persistence

Already configured in Redis section. RDB snapshots saved to `/var/lib/redis/dump.rdb`.

---

## Performance Tuning

### 1. Celery Autoscaling

```bash
# Start with 2 workers, scale up to 8 based on load
celery -A app.celery_app worker \
    --autoscale=8,2 \
    --max-tasks-per-child=100 \
    --loglevel=info
```

### 2. Database Connection Pooling

Already configured in `app/config.py`:
- `DB_POOL_SIZE=10`
- `DB_MAX_OVERFLOW=20`

### 3. Redis Memory Optimization

Monitor memory usage:
```bash
redis-cli info memory
```

Adjust `maxmemory` in `/etc/redis/redis.conf` based on usage.

---

## Troubleshooting

### Check Service Status

```bash
# API
sudo systemctl status trustcard-api

# Celery
sudo systemctl status trustcard-celery

# Database
sudo systemctl status postgresql

# Redis
sudo systemctl status redis
```

### View Logs

```bash
# API logs
sudo journalctl -u trustcard-api -f

# Celery logs
sudo journalctl -u trustcard-celery -f

# Application logs
tail -f /var/log/trustcard/app.log

# Nginx logs
tail -f /var/log/nginx/trustcard_error.log
```

### Common Issues

**1. High Memory Usage**
- Reduce Celery workers: `--concurrency=2`
- Reduce database pool: `DB_POOL_SIZE=5`
- Clear Redis cache: `redis-cli FLUSHALL`

**2. Slow Analysis**
- Check Celery queue: `celery -A app.celery_app inspect active`
- Increase workers or use autoscaling
- Check database query performance

**3. Instagram Login Failures**
- Instagram may block automated logins
- Use session persistence
- Consider using Instagram Graph API (requires approval)

**4. Database Connection Errors**
- Check `max_connections` in PostgreSQL
- Reduce `DB_POOL_SIZE` in config
- Check for connection leaks

---

## Production Checklist

### Before Go-Live

- [ ] All environment variables set correctly
- [ ] Database migrations applied
- [ ] SSL/TLS certificates installed
- [ ] Firewall configured
- [ ] Backups configured and tested
- [ ] Monitoring and alerts configured
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Team trained on operations

### After Go-Live

- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Monitor cache hit rates
- [ ] Monitor Celery queue size
- [ ] Monitor disk space
- [ ] Monitor database connections
- [ ] Check logs for errors
- [ ] Verify backups are running

---

**Questions?** Check the main [README.md](../README.md) or open an issue on GitHub.
