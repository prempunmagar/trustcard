#!/bin/bash
# =============================================================================
# TrustCard VM Deployment Script
# =============================================================================
# Run this script on your Azure VM to deploy TrustCard in production mode
#
# Usage:
#   bash deploy_vm.sh
#
# Or for fresh deployment (removes all data):
#   bash deploy_vm.sh --fresh
#
# =============================================================================

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              TrustCard - Production Deployment                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Warning: Running as root. Consider using a regular user with docker permissions."
fi

# Parse arguments
FRESH_DEPLOY=false
if [ "$1" == "--fresh" ]; then
    FRESH_DEPLOY=true
    echo "🔥 Fresh deployment mode - will remove all existing data!"
    echo ""
fi

# Check if we're in the trustcard directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Error: docker-compose.prod.yml not found!"
    echo "   Please run this script from the trustcard directory."
    exit 1
fi

echo "📍 Current directory: $(pwd)"
echo ""

# Step 1: Stop existing containers
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Stopping existing containers..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$FRESH_DEPLOY" = true ]; then
    docker-compose -f docker-compose.prod.yml down -v
    echo "✅ Containers and volumes removed"
else
    docker-compose -f docker-compose.prod.yml down
    echo "✅ Containers stopped (data preserved)"
fi
echo ""

# Step 2: Pull latest code
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Pulling latest code from git..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git pull origin master
echo "✅ Code updated"
echo ""

# Step 3: Setup environment file
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Setting up environment file..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f ".env.production" ]; then
    cp .env.production .env
    echo "✅ Copied .env.production to .env"
else
    echo "❌ Error: .env.production not found!"
    echo "   Please create .env.production with your configuration."
    exit 1
fi
echo ""

# Step 4: Verify environment variables
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Verifying environment variables..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check required variables
REQUIRED_VARS=("POSTGRES_PASSWORD" "REDIS_PASSWORD" "SECRET_KEY" "ANTHROPIC_API_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=.\+" .env; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Error: Missing or empty required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "   Please edit .env and set these variables."
    exit 1
fi

echo "✅ All required environment variables are set"
echo ""

# Show what we're deploying with (hide sensitive values)
echo "Configuration:"
echo "  - POSTGRES_USER: $(grep POSTGRES_USER .env | cut -d'=' -f2)"
echo "  - POSTGRES_PASSWORD: [SET]"
echo "  - REDIS_PASSWORD: [SET]"
echo "  - SECRET_KEY: [SET]"
echo "  - ANTHROPIC_API_KEY: [SET]"
echo "  - INSTAGRAM_USERNAME: $(grep INSTAGRAM_USERNAME .env | cut -d'=' -f2)"
echo ""

# Step 5: Clean up old images (optional)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Cleaning up old Docker images..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker system prune -f || true
echo "✅ Cleanup complete"
echo ""

# Step 6: Build and start containers
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Building and starting containers..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker-compose -f docker-compose.prod.yml up -d --build
echo "✅ Containers started"
echo ""

# Step 7: Wait for services to be healthy
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: Waiting for services to be healthy..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏳ This may take up to 60 seconds..."
echo ""

# Wait up to 60 seconds for health checks
SECONDS=0
MAX_WAIT=60
while [ $SECONDS -lt $MAX_WAIT ]; do
    HEALTHY=$(docker-compose -f docker-compose.prod.yml ps | grep -c "healthy" || true)
    TOTAL=$(docker-compose -f docker-compose.prod.yml ps -q | wc -l)

    echo "   [$SECONDS/$MAX_WAIT seconds] Services: $HEALTHY healthy"

    if [ "$HEALTHY" -ge 3 ]; then
        echo ""
        echo "✅ Services are healthy!"
        break
    fi

    sleep 5
done
echo ""

# Step 8: Show status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 8: Deployment Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker-compose -f docker-compose.prod.yml ps
echo ""

# Step 9: Test the API
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 9: Testing API..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sleep 5  # Give API a moment to start

if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is responding!"
    echo ""
    echo "Health check response:"
    curl -s http://localhost:8000/health | python3 -m json.tool || curl -s http://localhost:8000/health
else
    echo "⚠️  API is not responding yet. Check logs:"
    echo "   docker-compose -f docker-compose.prod.yml logs api"
fi
echo ""

# Final summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Access your application:"
echo "   • API Docs:    http://$(curl -s ifconfig.me):8000/docs"
echo "   • Health:      http://$(curl -s ifconfig.me):8000/health"
echo "   • Local Docs:  http://localhost:8000/docs"
echo ""
echo "📊 Useful commands:"
echo "   • View logs:        docker-compose -f docker-compose.prod.yml logs -f"
echo "   • View API logs:    docker-compose -f docker-compose.prod.yml logs -f api"
echo "   • View status:      docker-compose -f docker-compose.prod.yml ps"
echo "   • Restart:          docker-compose -f docker-compose.prod.yml restart"
echo "   • Stop:             docker-compose -f docker-compose.prod.yml down"
echo ""
echo "🔍 Troubleshooting:"
echo "   • Check logs:       docker-compose -f docker-compose.prod.yml logs"
echo "   • Test Redis:       docker exec trustcard-redis-1 redis-cli -a \"\$REDIS_PASSWORD\" ping"
echo "   • Test Postgres:    docker exec trustcard-db-1 pg_isready -U trustcard"
echo ""
