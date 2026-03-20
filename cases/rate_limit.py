"""
Rate limiting middleware and decorators for API endpoints
"""
import time
from django.http import JsonResponse
from django.core.cache import cache
from functools import wraps
import hashlib


class RateLimitMiddleware:
    """
    Rate limiting middleware for API requests
    
    Limits:
    - Anonymous users: 10 requests per minute
    - Authenticated users: 60 requests per minute
    - Premium users: 300 requests per minute
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        user_key = self._get_user_key(request)
        limit = self._get_rate_limit(request)
        
        if not self._check_rate_limit(user_key, limit):
            return JsonResponse({
                'success': False,
                'error': 'Rate limit exceeded. Please try again later.',
                'retry_after': 60
            }, status=429)
        
        response = self.get_response(request)
        
        remaining = self._get_remaining_requests(user_key, limit)
        response['X-RateLimit-Limit'] = str(limit)
        response['X-RateLimit-Remaining'] = str(remaining)
        response['X-RateLimit-Reset'] = str(60)
        
        return response
    
    def _get_user_key(self, request):
        """Generate unique key for user/IP"""
        if request.user.is_authenticated:
            return f"ratelimit:user:{request.user.id}"
        else:
            ip = self._get_client_ip(request)
            return f"ratelimit:ip:{ip}"
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def _get_rate_limit(self, request):
        """Get rate limit based on user type"""
        if request.user.is_authenticated:
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'is_premium'):
                return 300
            return 60
        return 10
    
    def _check_rate_limit(self, key, limit):
        """Check if request is within rate limit"""
        current_time = int(time.time())
        window_start = current_time - (current_time % 60)
        
        cache_key = f"{key}:{window_start}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            return False
        
        cache.set(cache_key, current_count + 1, 60)
        return True
    
    def _get_remaining_requests(self, key, limit):
        """Get remaining requests in current window"""
        current_time = int(time.time())
        window_start = current_time - (current_time % 60)
        
        cache_key = f"{key}:{window_start}"
        current_count = cache.get(cache_key, 0)
        
        return max(0, limit - current_count)


def rate_limit(limit=10, window=60):
    """
    Decorator for rate limiting specific views
    
    Args:
        limit: Maximum number of requests
        window: Time window in seconds
    
    Usage:
        @rate_limit(limit=5, window=60)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_key = _get_user_key(request)
            cache_key = f"ratelimit:{user_key}:{view_func.__name__}"
            
            current_count = cache.get(cache_key, 0)
            
            if current_count >= limit:
                return JsonResponse({
                    'success': False,
                    'error': f'Rate limit exceeded. Maximum {limit} requests per {window} seconds.',
                    'retry_after': window
                }, status=429)
            
            cache.set(cache_key, current_count + 1, window)
            
            response = view_func(request, *args, **kwargs)
            
            remaining = max(0, limit - current_count - 1)
            if hasattr(response, '__setitem__'):
                response['X-RateLimit-Limit'] = str(limit)
                response['X-RateLimit-Remaining'] = str(remaining)
                response['X-RateLimit-Reset'] = str(window)
            
            return response
        
        return _wrapped_view
    return decorator


def _get_user_key(request):
    """Generate unique key for user/IP"""
    if request.user.is_authenticated:
        return f"user:{request.user.id}"
    else:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return f"ip:{ip}"


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass