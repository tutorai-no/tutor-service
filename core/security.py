"""
Advanced security utilities and middleware for the Aksio backend.

This module provides comprehensive security features including
input validation, XSS protection, SQL injection prevention,
and security headers.
"""

import hashlib
import hmac
import json
import logging
import re
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status

import bleach

logger = logging.getLogger(__name__)
User = get_user_model()


class SecurityHeaders:
    """Security headers configuration."""

    HEADERS = {
        # Prevent clickjacking
        "X-Frame-Options": "DENY",
        # Prevent MIME type sniffing
        "X-Content-Type-Options": "nosniff",
        # Enable XSS protection
        "X-XSS-Protection": "1; mode=block",
        # Strict transport security (HTTPS only)
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        # Content Security Policy
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        ),
        # Referrer policy
        "Referrer-Policy": "strict-origin-when-cross-origin",
        # Permissions policy
        "Permissions-Policy": (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        ),
    }


class SecurityMiddleware(MiddlewareMixin):
    """
    Comprehensive security middleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

        # Security configuration
        self.max_request_size = getattr(
            settings, "MAX_REQUEST_SIZE", 10 * 1024 * 1024
        )  # 10MB
        self.blocked_user_agents = getattr(settings, "BLOCKED_USER_AGENTS", [])
        self.rate_limit_cache_prefix = "security_rate_limit"

    def process_request(self, request):
        """Process incoming request for security threats."""

        # Check request size
        if hasattr(request, "META") and "CONTENT_LENGTH" in request.META:
            try:
                content_length = int(request.META["CONTENT_LENGTH"])
                if content_length > self.max_request_size:
                    logger.warning(
                        f"Request too large: {content_length} bytes from {self._get_client_ip(request)}"
                    )
                    return JsonResponse(
                        {"error": "Request too large"},
                        status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    )
            except (ValueError, TypeError):
                pass

        # Check for suspicious user agents
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if self._is_suspicious_user_agent(user_agent):
            logger.warning(
                f"Suspicious user agent: {user_agent} from {self._get_client_ip(request)}"
            )
            return JsonResponse(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Check for SQL injection patterns
        if self._detect_sql_injection(request):
            logger.warning(f"SQL injection attempt from {self._get_client_ip(request)}")
            return JsonResponse(
                {"error": "Malicious request detected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for XSS patterns
        if self._detect_xss_attempt(request):
            logger.warning(f"XSS attempt from {self._get_client_ip(request)}")
            return JsonResponse(
                {"error": "Malicious request detected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return None

    def process_response(self, request, response):
        """Add security headers to response."""

        # Add security headers
        for header, value in SecurityHeaders.HEADERS.items():
            response[header] = value

        # Add CSRF token header for AJAX requests
        if hasattr(request, "META") and "HTTP_X_REQUESTED_WITH" in request.META:
            if hasattr(request, "META") and "CSRF_COOKIE" in request.META:
                response["X-CSRFToken"] = request.META["CSRF_COOKIE"]

        return response

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get real client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return ip

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious."""
        if not user_agent:
            return True

        suspicious_patterns = [
            r"(sqlmap|nikto|nmap|masscan|nessus)",
            r"(bot|crawler|spider|scraper)",
            r"(curl|wget|python-requests)",
            r"<script",
            r"javascript:",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True

        return False

    def _detect_sql_injection(self, request: HttpRequest) -> bool:
        """Detect potential SQL injection attempts."""
        sql_injection_patterns = [
            r"(\bunion\s+select\b)",
            r"(\bselect\s+.*\bfrom\b)",
            r"(\binsert\s+into\b)",
            r"(\bdelete\s+from\b)",
            r"(\bdrop\s+table\b)",
            r"(\bor\s+1\s*=\s*1)",
            r"(\band\s+1\s*=\s*1)",
            r"(\bor\s+'.*'\s*=\s*'.*')",
            r"(--|\#|\bmysql_)",
            r"(\bexec\s*\()",
            r"(\bchar\s*\(\d+\))",
        ]

        # Check URL parameters
        for param_value in request.GET.values():
            for pattern in sql_injection_patterns:
                if re.search(pattern, param_value, re.IGNORECASE):
                    return True

        # Check POST data
        if hasattr(request, "body") and request.body:
            try:
                body_str = request.body.decode("utf-8")
                for pattern in sql_injection_patterns:
                    if re.search(pattern, body_str, re.IGNORECASE):
                        return True
            except UnicodeDecodeError:
                pass

        return False

    def _detect_xss_attempt(self, request: HttpRequest) -> bool:
        """Detect potential XSS attempts."""
        xss_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<applet[^>]*>",
            r"vbscript:",
            r"expression\s*\(",
        ]

        # Check URL parameters
        for param_value in request.GET.values():
            for pattern in xss_patterns:
                if re.search(pattern, param_value, re.IGNORECASE):
                    return True

        # Check POST data
        if hasattr(request, "body") and request.body:
            try:
                body_str = request.body.decode("utf-8")
                for pattern in xss_patterns:
                    if re.search(pattern, body_str, re.IGNORECASE):
                        return True
            except UnicodeDecodeError:
                pass

        return False


class InputSanitizer:
    """
    Advanced input sanitization utilities.
    """

    # Allowed HTML tags for rich text content
    ALLOWED_TAGS = [
        "p",
        "br",
        "strong",
        "em",
        "u",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "blockquote",
        "code",
        "pre",
    ]

    # Allowed HTML attributes
    ALLOWED_ATTRIBUTES = {
        "*": ["class"],
        "a": ["href", "title"],
        "img": ["src", "alt", "width", "height"],
    }

    @classmethod
    def sanitize_html(
        cls,
        content: str,
        allowed_tags: list[str] = None,
        allowed_attributes: dict[str, list[str]] = None,
    ) -> str:
        """
        Sanitize HTML content to prevent XSS attacks.

        Args:
            content: Raw HTML content
            allowed_tags: List of allowed HTML tags
            allowed_attributes: Dict of allowed attributes per tag

        Returns:
            Sanitized HTML content
        """
        if not content:
            return ""

        tags = allowed_tags or cls.ALLOWED_TAGS
        attributes = allowed_attributes or cls.ALLOWED_ATTRIBUTES

        return bleach.clean(content, tags=tags, attributes=attributes, strip=True)

    @classmethod
    def sanitize_text(cls, content: str, max_length: int = None) -> str:
        """
        Sanitize plain text content.

        Args:
            content: Raw text content
            max_length: Maximum allowed length

        Returns:
            Sanitized text content
        """
        if not content:
            return ""

        # Remove all HTML tags
        sanitized = bleach.clean(content, tags=[], strip=True)

        # Normalize whitespace
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        # Truncate if necessary
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip()

        return sanitized

    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format."""
        if not email:
            return False

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(email_pattern, email))

    @classmethod
    def validate_username(cls, username: str) -> bool:
        """Validate username format."""
        if not username:
            return False

        # Allow alphanumeric characters, underscores, and hyphens
        username_pattern = r"^[a-zA-Z0-9_-]{3,30}$"
        return bool(re.match(username_pattern, username))

    @classmethod
    def validate_password_strength(cls, password: str) -> tuple[bool, list[str]]:
        """
        Validate password strength.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        if not password:
            return False, ["Password is required"]

        issues = []

        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", password):
            issues.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            issues.append("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            issues.append("Password must contain at least one number")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")

        return len(issues) == 0, issues


class SecurityAuditLogger:
    """
    Security event logging and audit trail.
    """

    def __init__(self):
        self.logger = logging.getLogger("security_audit")

    def log_login_attempt(
        self,
        user_identifier: str,
        success: bool,
        ip_address: str,
        user_agent: str = None,
    ):
        """Log login attempt."""
        event_data = {
            "event_type": "login_attempt",
            "user_identifier": user_identifier,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": timezone.now().isoformat(),
        }

        if success:
            self.logger.info(f"Successful login: {json.dumps(event_data)}")
        else:
            self.logger.warning(f"Failed login: {json.dumps(event_data)}")

    def log_permission_denied(
        self, user_id: str, resource: str, action: str, ip_address: str
    ):
        """Log permission denied event."""
        event_data = {
            "event_type": "permission_denied",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "ip_address": ip_address,
            "timestamp": timezone.now().isoformat(),
        }

        self.logger.warning(f"Permission denied: {json.dumps(event_data)}")

    def log_security_violation(
        self, violation_type: str, details: dict[str, Any], ip_address: str
    ):
        """Log security violation."""
        event_data = {
            "event_type": "security_violation",
            "violation_type": violation_type,
            "details": details,
            "ip_address": ip_address,
            "timestamp": timezone.now().isoformat(),
        }

        self.logger.error(f"Security violation: {json.dumps(event_data)}")

    def log_data_access(
        self, user_id: str, resource_type: str, resource_id: str, action: str
    ):
        """Log data access for audit trail."""
        event_data = {
            "event_type": "data_access",
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "timestamp": timezone.now().isoformat(),
        }

        self.logger.info(f"Data access: {json.dumps(event_data)}")


class TokenManager:
    """
    Secure token generation and validation.
    """

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        import secrets

        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_hmac_token(data: str, secret_key: str = None) -> str:
        """Generate HMAC token for data integrity."""
        if not secret_key:
            secret_key = settings.SECRET_KEY

        return hmac.new(
            secret_key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify_hmac_token(data: str, token: str, secret_key: str = None) -> bool:
        """Verify HMAC token."""
        if not secret_key:
            secret_key = settings.SECRET_KEY

        expected_token = TokenManager.generate_hmac_token(data, secret_key)
        return hmac.compare_digest(expected_token, token)

    @staticmethod
    def generate_api_key(user_id: str) -> str:
        """Generate API key for user."""
        timestamp = str(int(timezone.now().timestamp()))
        data = f"{user_id}:{timestamp}"

        return f"ak_{TokenManager.generate_hmac_token(data)[:24]}"


class IPWhitelist:
    """
    IP address whitelisting for admin functions.
    """

    def __init__(self):
        self.whitelist = getattr(settings, "ADMIN_IP_WHITELIST", [])
        self.cache_timeout = 300  # 5 minutes

    def is_ip_whitelisted(self, ip_address: str) -> bool:
        """Check if IP address is whitelisted."""
        if not self.whitelist:
            return True  # No whitelist configured

        # Check cache first
        cache_key = f"ip_whitelist_{ip_address}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Check whitelist
        is_whitelisted = self._check_ip_in_whitelist(ip_address)

        # Cache result
        cache.set(cache_key, is_whitelisted, self.cache_timeout)

        return is_whitelisted

    def _check_ip_in_whitelist(self, ip_address: str) -> bool:
        """Check if IP is in whitelist (supports CIDR notation)."""
        import ipaddress

        try:
            ip = ipaddress.ip_address(ip_address)

            for whitelist_entry in self.whitelist:
                try:
                    if "/" in whitelist_entry:
                        # CIDR notation
                        network = ipaddress.ip_network(whitelist_entry, strict=False)
                        if ip in network:
                            return True
                    else:
                        # Single IP
                        if ip == ipaddress.ip_address(whitelist_entry):
                            return True
                except (ipaddress.AddressValueError, ValueError):
                    continue

            return False

        except (ipaddress.AddressValueError, ValueError):
            return False


class SecurityConfig:
    """
    Centralized security configuration.
    """

    # Password policy
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL_CHARS = True

    # Session security
    SESSION_TIMEOUT_MINUTES = 30
    SESSION_REQUIRE_HTTPS = True

    # API security
    API_RATE_LIMIT_PER_MINUTE = 60
    API_RATE_LIMIT_PER_HOUR = 1000

    # File upload security
    ALLOWED_FILE_EXTENSIONS = [".pdf", ".docx", ".doc", ".txt", ".md"]
    MAX_FILE_SIZE_MB = 10

    # Content security
    MAX_TEXT_LENGTH = 10000
    MAX_HTML_LENGTH = 50000


# Global instances
security_audit_logger = SecurityAuditLogger()
input_sanitizer = InputSanitizer()
token_manager = TokenManager()
ip_whitelist = IPWhitelist()
