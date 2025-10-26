# 🔧 Fix Your VM Deployment

## Problem
Your containers are failing because:
1. ❌ Missing `POSTGRES_PASSWORD` and `REDIS_PASSWORD` in `.env`
2. ❌ Redis healthcheck doesn't authenticate (causes "unhealthy" status)

## Solution (Run these on your VM)

### Step 1: Stop Current Containers
```bash
cd ~/trustcard
docker-compose -f docker-compose.prod.yml down
```

### Step 2: Pull Latest Code (includes Redis healthcheck fix)
```bash
git pull origin master
```

### Step 3: Generate Secure Passwords
```bash
# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(50))"

# Generate POSTGRES_PASSWORD
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(32))"

# Generate REDIS_PASSWORD
python3 -c "import secrets; print('REDIS_PASSWORD=' + secrets.token_urlsafe(32))"
```

**Copy these values!** You'll need them in the next step.

### Step 4: Create/Edit .env File
```bash
nano .env
```

Paste this template and **replace the CHANGE_ME values** with your generated passwords:

```bash
# Database
POSTGRES_USER=trustcard
POSTGRES_PASSWORD=CHANGE_ME_PASTE_GENERATED_PASSWORD
POSTGRES_DB=trustcard

# Redis
REDIS_PASSWORD=CHANGE_ME_PASTE_GENERATED_PASSWORD

# Application
SECRET_KEY=CHANGE_ME_PASTE_GENERATED_SECRET_KEY
ENVIRONMENT=production
DEBUG=False
API_PORT=8000

# Anthropic API (required for AI features)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Optional: Instagram (use test account!)
INSTAGRAM_USERNAME=
INSTAGRAM_PASSWORD=

# Optional: Serper for web search
SERPER_API_KEY=
```

**Save and exit nano:**
- Press `Ctrl+O` then `Enter` (saves the file)
- Press `Ctrl+X` (exits nano)

### Step 5: Verify .env File
```bash
# Check that passwords are set (should NOT be empty)
cat .env | grep PASSWORD
```

### Step 6: Deploy
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Step 7: Check Status
```bash
# Wait 30 seconds for containers to start, then:
docker-compose -f docker-compose.prod.yml ps

# All containers should show "healthy" or "running"
```

### Step 8: View Logs (if issues)
```bash
# Check Redis
docker-compose -f docker-compose.prod.yml logs redis

# Check Database
docker-compose -f docker-compose.prod.yml logs db

# Check API
docker-compose -f docker-compose.prod.yml logs api

# Follow all logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 9: Test
```bash
# On VM
curl http://localhost:8000/health

# Should return: {"status":"healthy"}

# From your computer browser:
# http://YOUR_VM_IP:8000/docs
```

## Quick Nano Cheat Sheet

| Action | Keys |
|--------|------|
| Save file | `Ctrl+O` then `Enter` |
| Exit | `Ctrl+X` |
| Cut line | `Ctrl+K` |
| Paste | `Ctrl+U` |
| Search | `Ctrl+W` |

## Troubleshooting

### Still seeing "unhealthy" containers?
```bash
# Check detailed health status
docker inspect trustcard-redis-1 | grep -A 10 Health
docker inspect trustcard-db-1 | grep -A 10 Health

# Test Redis manually
docker exec trustcard-redis-1 redis-cli -a "YOUR_REDIS_PASSWORD" ping
# Should return: PONG

# Test Postgres manually
docker exec trustcard-db-1 pg_isready -U trustcard
# Should return: accepting connections
```

### Need to reset everything?
```bash
# WARNING: This deletes all data!
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d --build
```

## What Changed?

The updated `docker-compose.prod.yml` fixes the Redis healthcheck:

**Before (broken):**
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "--raw", "incr", "ping"]  # ❌ No password
```

**After (fixed):**
```yaml
environment:
  - REDIS_PASSWORD=${REDIS_PASSWORD}  # ✅ Pass password to container
healthcheck:
  test: ["CMD-SHELL", "redis-cli -a \"$$REDIS_PASSWORD\" ping | grep PONG"]  # ✅ Authenticate
```

---

**Need help?** Share the output of:
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs --tail=50
```

