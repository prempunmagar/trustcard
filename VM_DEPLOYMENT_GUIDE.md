# 🚀 TrustCard VM Deployment Guide

Complete guide to deploy TrustCard on your Azure VM in production mode.

## 📋 Prerequisites

- Azure VM with Ubuntu/Debian
- Docker and Docker Compose installed
- Git installed
- SSH access to the VM

## 🎯 Quick Start (Automated)

### Option 1: Fresh Deployment (Recommended for first time)

```bash
# SSH into your VM
ssh -i vmtrustcard_key.pem azureuser@YOUR_VM_IP

# Clone or update the repository
cd ~
git clone https://github.com/YOUR_USERNAME/trustcard.git
# OR if already cloned:
cd trustcard
git pull origin master

# Run the automated deployment script
bash deploy_vm.sh --fresh
```

The `--fresh` flag will:
- Remove all existing containers and data
- Pull latest code
- Rebuild everything from scratch
- Start all services

### Option 2: Update Existing Deployment

```bash
# SSH into your VM
ssh -i vmtrustcard_key.pem azureuser@YOUR_VM_IP

# Navigate to the trustcard directory
cd ~/trustcard

# Run the deployment script (preserves data)
bash deploy_vm.sh
```

This will:
- Stop containers (keeps data volumes)
- Pull latest code
- Rebuild and restart containers
- Preserve database and Redis data

## 📝 What the Script Does

The `deploy_vm.sh` script automates the entire deployment:

1. ✅ Stops existing containers
2. ✅ Pulls latest code from git
3. ✅ Sets up environment variables from `.env.production`
4. ✅ Verifies all required variables are set
5. ✅ Cleans up old Docker images
6. ✅ Builds and starts all containers
7. ✅ Waits for services to be healthy
8. ✅ Tests the API
9. ✅ Shows deployment status

## 🔍 Manual Deployment (Step by Step)

If you prefer to deploy manually or troubleshoot:

### Step 1: Prepare the VM

```bash
# SSH into your VM
ssh -i vmtrustcard_key.pem azureuser@YOUR_VM_IP

# Navigate to project
cd ~/trustcard

# Pull latest code
git pull origin master
```

### Step 2: Setup Environment

```bash
# Copy production environment file
cp .env.production .env

# Verify the file has all required values
cat .env | grep -E "POSTGRES_PASSWORD|REDIS_PASSWORD|SECRET_KEY|ANTHROPIC_API_KEY"
```

### Step 3: Deploy

```bash
# Stop old containers (add -v to remove data)
docker-compose -f docker-compose.prod.yml down

# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Wait 30 seconds for services to start
sleep 30

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Step 4: Verify

```bash
# Check health
curl http://localhost:8000/health

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 🎯 Expected Output

After successful deployment, `docker-compose ps` should show:

```
NAME                        STATUS              PORTS
trustcard-api-1            Up (healthy)        0.0.0.0:8000->8000/tcp
trustcard-celery_worker-1  Up (healthy)
trustcard-db-1             Up (healthy)        5432/tcp
trustcard-redis-1          Up (healthy)        6379/tcp
```

## 🧪 Testing the Deployment

### Test Health Endpoint

```bash
# On the VM
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### Test API Documentation

```bash
# Get your VM's public IP
curl ifconfig.me

# Then visit in your browser:
# http://YOUR_VM_IP:8000/docs
```

### Test an Analysis (Example)

```bash
curl -X POST "http://localhost:8000/api/posts/analyze" \
  -H "Content-Type: application/json" \
  -d '{"post_url": "https://www.instagram.com/p/SOME_POST_ID/"}'
```

## 📊 Monitoring & Management

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f celery_worker
docker-compose -f docker-compose.prod.yml logs -f redis
docker-compose -f docker-compose.prod.yml logs -f db
```

### Check Container Status

```bash
docker-compose -f docker-compose.prod.yml ps
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart api
```

### Stop Services

```bash
# Stop (keeps data)
docker-compose -f docker-compose.prod.yml down

# Stop and remove data
docker-compose -f docker-compose.prod.yml down -v
```

## 🔧 Troubleshooting

### Containers Show "Unhealthy"

```bash
# Check detailed health status
docker inspect trustcard-redis-1 | grep -A 10 Health
docker inspect trustcard-db-1 | grep -A 10 Health

# Test services manually
docker exec trustcard-redis-1 redis-cli -a "$(grep REDIS_PASSWORD .env | cut -d'=' -f2)" ping
# Should return: PONG

docker exec trustcard-db-1 pg_isready -U trustcard
# Should return: accepting connections
```

### API Not Responding

```bash
# Check API logs
docker-compose -f docker-compose.prod.yml logs api

# Check if port is listening
netstat -tlnp | grep 8000

# Try restarting the API
docker-compose -f docker-compose.prod.yml restart api
```

### Database Connection Issues

```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Verify database is accepting connections
docker exec trustcard-db-1 psql -U trustcard -d trustcard -c "SELECT version();"
```

### Redis Connection Issues

```bash
# Check Redis logs
docker-compose -f docker-compose.prod.yml logs redis

# Test Redis connection
docker exec trustcard-redis-1 redis-cli -a "$(grep REDIS_PASSWORD .env | cut -d'=' -f2)" ping
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes

# Then redeploy
bash deploy_vm.sh
```

## 🔄 Update Workflow

When you push new code:

```bash
# On your local machine
git add .
git commit -m "Your changes"
git push origin master

# On the VM
cd ~/trustcard
bash deploy_vm.sh
```

The script will automatically:
- Pull the latest code
- Rebuild containers
- Restart services

## 🔐 Security Notes

### Firewall Configuration

Make sure port 8000 is open in your Azure Network Security Group:

```bash
# Check if port is accessible from outside
curl http://YOUR_VM_IP:8000/health
```

### Environment Variables

The `.env.production` file is committed to the repo but contains **test credentials only**. For real production:

1. Never commit `.env` with real secrets
2. Generate strong passwords:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. Add `.env` to `.gitignore`

### SSL/TLS (Future Enhancement)

For production, consider:
- Setting up nginx as reverse proxy
- Adding SSL certificate (Let's Encrypt)
- Running API behind HTTPS

## 📱 Accessing the Application

After deployment:

| Endpoint | URL | Description |
|----------|-----|-------------|
| API Docs | `http://YOUR_VM_IP:8000/docs` | Interactive API documentation |
| ReDoc | `http://YOUR_VM_IP:8000/redoc` | Alternative API documentation |
| Health Check | `http://YOUR_VM_IP:8000/health` | Service health status |
| Root | `http://YOUR_VM_IP:8000/` | Welcome message |

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs --tail=100
   ```

2. **Check service status:**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

3. **Verify environment variables:**
   ```bash
   cat .env | grep -E "PASSWORD|KEY"
   ```

4. **Try a fresh deployment:**
   ```bash
   bash deploy_vm.sh --fresh
   ```

## ✅ Success Checklist

- [ ] All 4 containers showing "Up (healthy)" status
- [ ] Health endpoint returns `{"status":"healthy"}`
- [ ] API docs accessible at `http://YOUR_VM_IP:8000/docs`
- [ ] No errors in logs
- [ ] Can submit test analysis request

---

**Happy Deploying! 🚀**
