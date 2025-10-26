#!/bin/bash
# Generate secure environment variables for TrustCard production

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     TrustCard - Generate Production Environment Variables     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Generating secure random values..."
echo ""

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo "# =============================================================================
# TrustCard Production Environment Variables
# =============================================================================

# Database
POSTGRES_USER=trustcard
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=trustcard

# Redis
REDIS_PASSWORD=${REDIS_PASSWORD}

# Application
SECRET_KEY=${SECRET_KEY}
ENVIRONMENT=production
DEBUG=False
API_PORT=8000

# =============================================================================
# API KEYS - YOU MUST ADD THESE!
# =============================================================================

# Get from: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Optional: For web search fact-checking (https://serper.dev/)
SERPER_API_KEY=

# =============================================================================
# INSTAGRAM (Optional - use test account!)
# =============================================================================
INSTAGRAM_USERNAME=
INSTAGRAM_PASSWORD=
"

echo "════════════════════════════════════════════════════════════════"
echo ""
echo "✅ .env file content generated above!"
echo ""
echo "📋 Next steps on your VM:"
echo "   1. Copy the output above"
echo "   2. Run: nano .env"
echo "   3. Paste the content"
echo "   4. Add your ANTHROPIC_API_KEY (required!)"
echo "   5. Save: Ctrl+O then Enter"
echo "   6. Exit: Ctrl+X"
echo ""
echo "════════════════════════════════════════════════════════════════"

