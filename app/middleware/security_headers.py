"""
Security Headers Middleware

Adds security headers to all responses to protect against common vulnerabilities.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses

    Headers added:
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filtering (legacy browsers)
    - Strict-Transport-Security: Force HTTPS (production only)
    - Content-Security-Policy: Restrict resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    """

    def __init__(self, app):
        super().__init__(app)
        logger.info("Security headers middleware initialized")

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS Protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS - Force HTTPS (only in production)
        if settings.is_production:
            # max-age=31536000 = 1 year
            # includeSubDomains = apply to all subdomains
            # preload = submit to HSTS preload list
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content Security Policy
        # Restricts where resources can be loaded from
        csp_directives = [
            "default-src 'self'",  # Default: only same origin
            "script-src 'self' 'unsafe-inline'",  # Allow inline scripts (for API docs)
            "style-src 'self' 'unsafe-inline'",   # Allow inline styles (for API docs)
            "img-src 'self' data: https:",        # Allow images from self, data URIs, and HTTPS
            "font-src 'self' data:",              # Allow fonts from self and data URIs
            "connect-src 'self'",                 # Allow AJAX/fetch only to same origin
            "frame-ancestors 'none'",             # Don't allow embedding in frames (redundant with X-Frame-Options)
            "base-uri 'self'",                    # Restrict <base> tag
            "form-action 'self'",                 # Restrict form submissions
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Referrer Policy
        # Controls how much referrer information is sent
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        # Disable potentially dangerous browser features
        permissions_directives = [
            "geolocation=()",      # Disable geolocation
            "microphone=()",       # Disable microphone
            "camera=()",           # Disable camera
            "payment=()",          # Disable payment API
            "usb=()",              # Disable USB
            "magnetometer=()",     # Disable magnetometer
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_directives)

        # Remove server header (don't reveal server info)
        if "server" in response.headers:
            del response.headers["server"]

        # Remove X-Powered-By header (don't reveal framework)
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        return response
