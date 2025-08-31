"""
Middleware module for the AIS system.

This module provides middleware components for:
- Request processing and routing
- Authentication and authorization
- Rate limiting and throttling
- Logging and monitoring
- Error handling and recovery
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import secrets
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanitize_log_input(value: Any) -> str:
    """Sanitize input for logging to prevent log injection."""
    if value is None:
        return "None"
    log_str = str(value)
    log_str = re.sub(r'[\r\n]', ' ', log_str)
    if len(log_str) > 200:
        log_str = log_str[:200] + "..."
    return log_str


class MiddlewareType(Enum):
    """Middleware type enumeration."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMITING = "rate_limiting"
    LOGGING = "logging"
    MONITORING = "monitoring"
    ERROR_HANDLING = "error_handling"
    CACHING = "caching"
    VALIDATION = "validation"


class RequestPriority(Enum):
    """Request priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class RequestContext:
    """Request context information."""
    request_id: str
    timestamp: datetime
    priority: RequestPriority
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MiddlewareResult:
    """Result from middleware processing."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseMiddleware:
    """Base class for all middleware components."""
    
    def __init__(self, name: str, middleware_type: MiddlewareType):
        self.name = name
        self.middleware_type = middleware_type
        self.enabled = True
        self.logger = logger
    
    async def process_request(self, request: Dict[str, Any], 
                           context: RequestContext) -> MiddlewareResult:
        """Process a request through this middleware."""
        if not self.enabled:
            return MiddlewareResult(success=True, message="Middleware disabled")
        
        try:
            return await self._process(request, context)
        except Exception as e:
            self.logger.error(f"Middleware {self.name} failed: {e}")
            return MiddlewareResult(
                success=False,
                message=f"Middleware processing failed",
                error=str(e)
            )
    
    async def _process(self, request: Dict[str, Any], 
                      context: RequestContext) -> MiddlewareResult:
        """Override this method to implement specific middleware logic."""
        raise NotImplementedError("Subclasses must implement _process")
    
    def enable(self):
        """Enable the middleware."""
        self.enabled = True
        self.logger.info(f"Middleware {sanitize_log_input(self.name)} enabled")
    
    def disable(self):
        """Disable the middleware."""
        self.enabled = False
        self.logger.info(f"Middleware {sanitize_log_input(self.name)} disabled")


class AuthenticationMiddleware(BaseMiddleware):
    """Middleware for request authentication."""
    
    def __init__(self):
        super().__init__("authentication", MiddlewareType.AUTHENTICATION)
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.token_secret = secrets.token_urlsafe(32)
    
    async def _process(self, request: Dict[str, Any], 
                      context: RequestContext) -> MiddlewareResult:
        """Authenticate the request."""
        # Check for API key
        api_key = request.get("api_key") or request.get("headers", {}).get("X-API-Key")
        if api_key and api_key in self.api_keys:
            key_info = self.api_keys[api_key]
            if not key_info.get("expired", False):
                context.user_id = key_info.get("user_id")
                context.metadata["auth_method"] = "api_key"
                return MiddlewareResult(
                    success=True,
                    message="API key authentication successful",
                    data={"user_id": context.user_id}
                )
        
        # Check for session token
        session_token = request.get("session_token") or request.get("headers", {}).get("X-Session-Token")
        if session_token and session_token in self.sessions:
            session_info = self.sessions[session_token]
            if not session_info.get("expired", False):
                context.user_id = session_info.get("user_id")
                context.session_id = session_token
                context.metadata["auth_method"] = "session"
                return MiddlewareResult(
                    success=True,
                    message="Session authentication successful",
                    data={"user_id": context.user_id, "session_id": session_token}
                )
        
        # Check for JWT token
        jwt_token = request.get("jwt_token") or request.get("headers", {}).get("Authorization")
        if jwt_token and jwt_token.startswith("Bearer "):
            token = jwt_token[7:]  # Remove "Bearer " prefix
            try:
                # Simple JWT validation (in production, use proper JWT library)
                if self._validate_jwt(token):
                    payload = self._decode_jwt(token)
                    context.user_id = payload.get("user_id")
                    context.metadata["auth_method"] = "jwt"
                    return MiddlewareResult(
                        success=True,
                        message="JWT authentication successful",
                        data={"user_id": context.user_id}
                    )
            except Exception as e:
                self.logger.warning(f"JWT validation failed: {e}")
        
        # No valid authentication found
        return MiddlewareResult(
            success=False,
            message="Authentication required",
            error="No valid authentication credentials found"
        )
    
    def _validate_jwt(self, token: str) -> bool:
        """Validate JWT token (simplified implementation)."""
        # In production, use proper JWT validation
        return len(token) > 10 and "." in token
    
    def _decode_jwt(self, token: str) -> Dict[str, Any]:
        """Decode JWT token (simplified implementation)."""
        # In production, use proper JWT decoding
        parts = token.split(".")
        if len(parts) == 3:
            try:
                import base64
                payload = base64.b64decode(parts[1] + "==").decode()
                return json.loads(payload)
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
                self.logger.warning(f"JWT decode error: {sanitize_log_input(e)}")
                pass
        return {"user_id": "unknown"}
    
    def add_api_key(self, api_key: str, user_id: str, expires_at: Optional[datetime] = None):
        """Add an API key."""
        self.api_keys[api_key] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "expires_at": expires_at,
            "expired": False
        }
    
    def add_session(self, user_id: str, expires_in: timedelta = timedelta(hours=24)) -> str:
        """Create a new session and return the session token."""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + expires_in
        
        self.sessions[session_token] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "expires_at": expires_at,
            "expired": False
        }
        
        return session_token
    
    def revoke_session(self, session_token: str):
        """Revoke a session."""
        if session_token in self.sessions:
            self.sessions[session_token]["expired"] = True


class AuthorizationMiddleware(BaseMiddleware):
    """Middleware for request authorization."""
    
    def __init__(self):
        super().__init__("authorization", MiddlewareType.AUTHORIZATION)
        self.user_permissions: Dict[str, List[str]] = {}
        self.role_permissions: Dict[str, List[str]] = {}
        self.user_roles: Dict[str, List[str]] = {}
    
    async def _process(self, request: Dict[str, Any], 
                      context: RequestContext) -> MiddlewareResult:
        """Authorize the request."""
        if not context.user_id:
            return MiddlewareResult(
                success=False,
                message="Authorization failed",
                error="User not authenticated"
            )
        
        # Get user permissions
        user_perms = self.user_permissions.get(context.user_id, [])
        user_roles = self.user_roles.get(context.user_id, [])
        
        # Get role permissions
        role_perms = []
        for role in user_roles:
            role_perms.extend(self.role_permissions.get(role, []))
        
        # Combine permissions
        all_permissions = list(set(user_perms + role_perms))
        
        # Check if user has required permissions
        required_permission = request.get("required_permission")
        if required_permission and required_permission not in all_permissions:
            return MiddlewareResult(
                success=False,
                message="Insufficient permissions",
                error=f"Permission '{required_permission}' required"
            )
        
        # Add permissions to context
        context.metadata["permissions"] = all_permissions
        context.metadata["roles"] = user_roles
        
        return MiddlewareResult(
            success=True,
            message="Authorization successful",
            data={"permissions": all_permissions, "roles": user_roles}
        )
    
    def add_user_permission(self, user_id: str, permission: str):
        """Add a permission to a user."""
        if user_id not in self.user_permissions:
            self.user_permissions[user_id] = []
        if permission not in self.user_permissions[user_id]:
            self.user_permissions[user_id].append(permission)
    
    def add_role_permission(self, role: str, permission: str):
        """Add a permission to a role."""
        if role not in self.role_permissions:
            self.role_permissions[role] = []
        if permission not in self.role_permissions[role]:
            self.role_permissions[role].append(permission)
    
    def assign_user_role(self, user_id: str, role: str):
        """Assign a role to a user."""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
        if role not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role)


class RateLimitingMiddleware(BaseMiddleware):
    """Middleware for rate limiting requests."""
    
    def __init__(self, requests_per_minute: int = 60):
        super().__init__("rate_limiting", MiddlewareType.RATE_LIMITING)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, List[datetime]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.block_duration = timedelta(minutes=5)
    
    async def _process(self, request: Dict[str, Any], 
                      context: RequestContext) -> MiddlewareResult:
        """Apply rate limiting to the request."""
        source_ip = context.source_ip or "unknown"
        
        # Check if IP is blocked
        if source_ip in self.blocked_ips:
            block_until = self.blocked_ips[source_ip]
            if datetime.now() < block_until:
                return MiddlewareResult(
                    success=False,
                    message="Rate limit exceeded",
                    error=f"IP {source_ip} is blocked until {block_until}"
                )
            else:
                # Remove expired block
                del self.blocked_ips[source_ip]
        
        # Check rate limit
        now = datetime.now()
        if source_ip not in self.request_counts:
            self.request_counts[source_ip] = []
        
        # Remove old requests (older than 1 minute)
        cutoff = now - timedelta(minutes=1)
        self.request_counts[source_ip] = [
            req_time for req_time in self.request_counts[source_ip]
            if req_time > cutoff
        ]
        
        # Check if limit exceeded
        if len(self.request_counts[source_ip]) >= self.requests_per_minute:
            # Block the IP
            self.blocked_ips[source_ip] = now + self.block_duration
            return MiddlewareResult(
                success=False,
                message="Rate limit exceeded",
                error=f"Too many requests from {source_ip}"
            )
        
        # Add current request
        self.request_counts[source_ip].append(now)
        
        # Add rate limit info to context
        remaining_requests = self.requests_per_minute - len(self.request_counts[source_ip])
        context.metadata["rate_limit"] = {
            "remaining": remaining_requests,
            "reset_time": now + timedelta(minutes=1)
        }
        
        return MiddlewareResult(
            success=True,
            message="Rate limit check passed",
            data={"remaining_requests": remaining_requests}
        )


class LoggingMiddleware(BaseMiddleware):
    """Middleware for request logging."""
    
    def __init__(self):
        super().__init__("logging", MiddlewareType.LOGGING)
        self.request_log: List[Dict[str, Any]] = []
        self.max_log_size = 1000
    
    async def _process(self, request: Dict[str, Any], 
                      context: RequestContext) -> MiddlewareResult:
        """Log the request."""
        log_entry = {
            "request_id": context.request_id,
            "timestamp": context.timestamp.isoformat(),
            "user_id": context.user_id,
            "source_ip": context.source_ip,
            "user_agent": context.user_agent,
            "priority": context.priority.value,
            "request_data": request
        }
        
        # Add to log
        self.request_log.append(log_entry)
        
        # Trim log if too large
        if len(self.request_log) > self.max_log_size:
            self.request_log = self.request_log[-self.max_log_size:]
        
        # Log to logger
        self.logger.info(f"Request {sanitize_log_input(context.request_id)} from {sanitize_log_input(context.source_ip)} "
                        f"(user: {sanitize_log_input(context.user_id)}, priority: {context.priority.value})")
        
        return MiddlewareResult(
            success=True,
            message="Request logged successfully"
        )
    
    def get_recent_requests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent request logs."""
        return self.request_log[-limit:]


class MonitoringMiddleware(BaseMiddleware):
    """Middleware for request monitoring and metrics."""
    
    def __init__(self):
        super().__init__("monitoring", MiddlewareType.MONITORING)
        self.request_times: List[float] = []
        self.error_counts: Dict[str, int] = {}
        self.success_counts: Dict[str, int] = {}
    
    async def _process(self, request: Dict[str, Any], 
                      context: RequestContext) -> MiddlewareResult:
        """Monitor the request."""
        start_time = time.time()
        
        # Add timing info to context
        context.metadata["monitoring"] = {
            "start_time": start_time,
            "request_type": request.get("type", "unknown")
        }
        
        return MiddlewareResult(
            success=True,
            message="Monitoring started"
        )
    
    def record_request_completion(self, context: RequestContext, 
                                success: bool, error: Optional[str] = None):
        """Record the completion of a request."""
        if "monitoring" in context.metadata:
            start_time = context.metadata["monitoring"]["start_time"]
            duration = time.time() - start_time
            
            # Record timing
            self.request_times.append(duration)
            if len(self.request_times) > 1000:
                self.request_times = self.request_times[-1000:]
            
            # Record counts
            request_type = context.metadata["monitoring"].get("request_type", "unknown")
            if success:
                self.success_counts[request_type] = self.success_counts.get(request_type, 0) + 1
            else:
                self.error_counts[request_type] = self.error_counts.get(request_type, 0) + 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        if not self.request_times:
            return {"error": "No data available"}
        
        return {
            "total_requests": len(self.request_times),
            "average_response_time": sum(self.request_times) / len(self.request_times),
            "min_response_time": min(self.request_times),
            "max_response_time": max(self.request_times),
            "success_counts": dict(self.success_counts),
            "error_counts": dict(self.error_counts)
        }


class ErrorHandlingMiddleware(BaseMiddleware):
    """Middleware for error handling and recovery."""
    
    def __init__(self):
        super().__init__("error_handling", MiddlewareType.ERROR_HANDLING)
        self.error_handlers: Dict[str, Callable] = {}
        self.retry_configs: Dict[str, Dict[str, Any]] = {}
    
    async def _process(self, request: Dict[str, Any], 
                      context: RequestContext) -> MiddlewareResult:
        """Set up error handling for the request."""
        # Add error handling info to context
        context.metadata["error_handling"] = {
            "retry_count": 0,
            "max_retries": self.retry_configs.get(request.get("type", "default"), {}).get("max_retries", 3),
            "retry_delay": self.retry_configs.get(request.get("type", "default"), {}).get("retry_delay", 1.0)
        }
        
        return MiddlewareResult(
            success=True,
            message="Error handling configured"
        )
    
    def add_error_handler(self, error_type: str, handler: Callable):
        """Add an error handler for a specific error type."""
        self.error_handlers[error_type] = handler
    
    def set_retry_config(self, request_type: str, max_retries: int, retry_delay: float):
        """Set retry configuration for a request type."""
        self.retry_configs[request_type] = {
            "max_retries": max_retries,
            "retry_delay": retry_delay
        }
    
    async def handle_error(self, error: Exception, context: RequestContext) -> MiddlewareResult:
        """Handle an error that occurred during request processing."""
        error_type = type(error).__name__
        
        # Check if we have a specific handler
        if error_type in self.error_handlers:
            try:
                result = await self.error_handlers[error_type](error, context)
                return result
            except Exception as e:
                self.logger.error(f"Error handler for {error_type} failed: {e}")
        
        # Default error handling
        self.logger.error(f"Unhandled error in request {context.request_id}: {error}")
        
        return MiddlewareResult(
            success=False,
            message="Internal server error",
            error=str(error)
        )


class MiddlewarePipeline:
    """Pipeline for executing multiple middleware components."""
    
    def __init__(self):
        self.middleware: List[BaseMiddleware] = []
        self.logger = logger
    
    def add_middleware(self, middleware: BaseMiddleware):
        """Add middleware to the pipeline."""
        self.middleware.append(middleware)
        self.logger.info(f"Added middleware: {sanitize_log_input(middleware.name)}")
    
    def remove_middleware(self, name: str):
        """Remove middleware from the pipeline."""
        self.middleware = [m for m in self.middleware if m.name != name]
        self.logger.info(f"Removed middleware: {sanitize_log_input(name)}")
    
    async def process_request(self, request: Dict[str, Any], 
                           context: RequestContext) -> MiddlewareResult:
        """Process a request through all middleware in the pipeline."""
        self.logger.info(f"Processing request {sanitize_log_input(context.request_id)} through {len(self.middleware)} middleware")
        
        for middleware in self.middleware:
            if not middleware.enabled:
                continue
            
            result = await middleware.process_request(request, context)
            if not result.success:
                self.logger.warning(f"Middleware {sanitize_log_input(middleware.name)} failed: {sanitize_log_input(result.message)}")
                return result
            
            self.logger.debug(f"Middleware {middleware.name} completed successfully")
        
        return MiddlewareResult(
            success=True,
            message="All middleware completed successfully"
        )
    
    def get_middleware_status(self) -> Dict[str, Any]:
        """Get status of all middleware in the pipeline."""
        return {
            "total_middleware": len(self.middleware),
            "enabled_middleware": len([m for m in self.middleware if m.enabled]),
            "middleware_details": [
                {
                    "name": m.name,
                    "type": m.middleware_type.value,
                    "enabled": m.enabled
                }
                for m in self.middleware
            ]
        }


# Convenience functions for creating middleware
def create_middleware_pipeline() -> MiddlewarePipeline:
    """Create a default middleware pipeline with common middleware."""
    pipeline = MiddlewarePipeline()
    
    # Add default middleware
    pipeline.add_middleware(AuthenticationMiddleware())
    pipeline.add_middleware(AuthorizationMiddleware())
    pipeline.add_middleware(RateLimitingMiddleware())
    pipeline.add_middleware(LoggingMiddleware())
    pipeline.add_middleware(MonitoringMiddleware())
    pipeline.add_middleware(ErrorHandlingMiddleware())
    
    return pipeline


def create_request_context(request_id: str, priority: RequestPriority = RequestPriority.NORMAL,
                         **kwargs) -> RequestContext:
    """Create a request context."""
    return RequestContext(
        request_id=request_id,
        timestamp=datetime.now(),
        priority=priority,
        **kwargs
    )


if __name__ == "__main__":
    async def main():
        """Test the middleware system."""
        print("Testing middleware system...")
        
        # Create pipeline
        pipeline = create_middleware_pipeline()
        
        # Create test request and context
        request = {
            "type": "test",
            "data": {"message": "Hello, World!"},
            "api_key": test_api_key
        }
        
        context = create_request_context(
            request_id="test_001",
            priority=RequestPriority.HIGH,
            source_ip="127.0.0.1",
            user_agent="TestClient/1.0"
        )
        
        # Add test API key
        auth_middleware = next(m for m in pipeline.middleware if isinstance(m, AuthenticationMiddleware))
        # Example API key - in production, load from environment variables
        test_api_key = os.getenv("TEST_API_KEY", "test_key_123")
        auth_middleware.add_api_key(test_api_key, "test_user")
        
        # Process request
        result = await pipeline.process_request(request, context)
        print(f"Pipeline result: {result}")
        
        # Get pipeline status
        status = pipeline.get_middleware_status()
        print(f"Pipeline status: {status}")
    
    asyncio.run(main())
