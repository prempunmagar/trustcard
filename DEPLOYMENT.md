# TrustCard Deployment Guide

## Overview
TrustCard is a containerized application that analyzes Instagram posts for authenticity using AI. This guide covers deployment on various platforms.

## Prerequisites

- Docker & Docker Compose installed
- Instagram test account (DO NOT use personal account)
- Anthropic Claude API key (https://console.anthropic.com/)
- (Optional) Serper.dev API key for web search verification

## Quick Start (Local Development)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd TrustCard
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

## Production Deployment

### Option 1: VPS/Cloud Server (AWS, DigitalOcean, etc.)

#### Requirements
- Ubuntu 22.04+ or similar Linux distribution
- 4GB RAM minimum (8GB recommended)
- 20GB storage
- Docker & Docker Compose installed

#### Steps

1. **Connect to your server**
   ```bash
   ssh user@your-server-ip
   ```

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

3. **Install Docker Compose**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

4. **Clone and setup**
   ```bash
   git clone <your-repo-url>
   cd TrustCard
   cp .env.example .env
   nano .env  # Edit with your production values
   ```

5. **Production Environment Variables**
   ```env
   # REQUIRED - Generate strong random passwords
   POSTGRES_PASSWORD=<generate-strong-password>
   REDIS_PASSWORD=<generate-strong-password>
   SECRET_KEY=<generate-random-key>
   
   # API Keys
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
   SERPER_API_KEY=<optional>
   
   # Instagram
   INSTAGRAM_USERNAME=your_test_account
   INSTAGRAM_PASSWORD=your_test_password
   
   # Port (default 8000)
   API_PORT=8000
   ```

6. **Start production services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

7. **Set up reverse proxy (Nginx)**
   ```bash
   sudo apt install nginx
   sudo nano /etc/nginx/sites-available/trustcard
   ```

   Add this configuration:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Enable and restart:
   ```bash
   sudo ln -s /etc/nginx/sites-available/trustcard /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

8. **Set up SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

9. **Enable automatic updates and monitoring**
   ```bash
   # Auto-restart on failure
   docker-compose -f docker-compose.prod.yml up -d --restart unless-stopped
   
   # View logs
   docker-compose -f docker-compose.prod.yml logs -f
   ```

### Option 2: Railway.app

1. **Create account** at https://railway.app
2. **Create new project** > "Deploy from GitHub"
3. **Add services**:
   - PostgreSQL (from template)
   - Redis (from template)
   - Your app (from GitHub repo)
4. **Set environment variables** in Railway dashboard
5. **Deploy** - Railway will automatically build and deploy

### Option 3: Render.com

1. **Create account** at https://render.com
2. **New Web Service** > Connect GitHub repo
3. **Configure**:
   - Build Command: `docker build -t trustcard .`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Add PostgreSQL** and **Redis** from Render dashboard
5. **Set environment variables**
6. **Deploy**

### Option 4: Heroku

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login and create app
heroku login
heroku create trustcard-app

# Add addons
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini

# Set environment variables
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
heroku config:set INSTAGRAM_USERNAME=test_account
heroku config:set INSTAGRAM_PASSWORD=password
heroku config:set SECRET_KEY=<random-key>

# Deploy
git push heroku main
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key for AI detection |
| `INSTAGRAM_USERNAME` | Yes | Instagram test account username |
| `INSTAGRAM_PASSWORD` | Yes | Instagram test account password |
| `SECRET_KEY` | Yes | Random secret for sessions |
| `DATABASE_URL` | Yes (auto) | PostgreSQL connection string |
| `REDIS_URL` | Yes (auto) | Redis connection string |
| `SERPER_API_KEY` | No | Google Search API for claim verification |
| `DEBUG` | No | Set to `False` in production |
| `API_PORT` | No | Port to run API on (default: 8000) |

## Post-Deployment

### Health Checks
```bash
# Check API health
curl http://your-domain.com/health

# Check all services
docker-compose -f docker-compose.prod.yml ps
```

### Monitoring
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f celery_worker
```

### Backup Database
```bash
# Backup
docker exec trustcard-db pg_dump -U trustcard trustcard > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i trustcard-db psql -U trustcard trustcard < backup_20250126.sql
```

### Scaling
```bash
# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=5

# Scale API workers (edit docker-compose.prod.yml)
# Change: --workers 4 to --workers 8
```

## Security Best Practices

1. **Use strong passwords** for all services
2. **Enable firewall** (UFW on Ubuntu)
   ```bash
   sudo ufw allow 22
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```
3. **Regular updates**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
4. **Rate limiting** - Configure nginx rate limits
5. **API keys** - Rotate Instagram credentials regularly
6. **HTTPS only** - Always use SSL certificates

## Troubleshooting

### Container won't start
```bash
docker-compose -f docker-compose.prod.yml logs <service-name>
```

### Database connection issues
```bash
# Check database is running
docker exec trustcard-db pg_isready -U trustcard

# Access database
docker exec -it trustcard-db psql -U trustcard
```

### Celery worker not processing
```bash
# Check worker status
docker exec trustcard-celery-worker celery -A app.celery_app inspect active

# Restart worker
docker-compose -f docker-compose.prod.yml restart celery_worker
```

### Instagram session expired
- Rotate Instagram credentials in .env
- Restart services
- Consider using multiple Instagram accounts

## Cost Estimates

### Monthly Costs (USD)
- **VPS (DigitalOcean/Linode)**: $12-24/month (4GB RAM)
- **Railway.app**: $5-20/month (usage-based)
- **Render.com**: $7-25/month (starter plan)
- **Heroku**: $12-25/month (hobby tier)
- **Anthropic Claude API**: Pay-per-use (~$0.01-0.10 per analysis)
- **Serper API** (optional): Free tier available

## Support

For issues or questions:
- GitHub Issues: <your-repo-url>/issues
- Documentation: Check README.md and CLAUDE.md

## License

[Your License Here]
