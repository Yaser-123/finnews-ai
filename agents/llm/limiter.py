"""
LLM Rate Limiter

Implements rate limiting with rolling window tracking to prevent API abuse.
"""

from collections import deque
import time
from typing import Deque


class LLMRateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class RateLimiter:
    """Rate limiter with rolling window tracking."""
    
    def __init__(
        self,
        max_calls_per_minute: int = 60,
        max_tokens_per_call: int = 4096,
        max_calls_per_request: int = 5
    ):
        self.max_calls_per_minute = max_calls_per_minute
        self.max_tokens_per_call = max_tokens_per_call
        self.max_calls_per_request = max_calls_per_request
        
        # Rolling window tracking
        self.call_timestamps: Deque[float] = deque()
        self.current_request_calls: int = 0
    
    def allow_call(self) -> bool:
        """
        Check if a call is allowed based on rate limits.
        
        Returns:
            bool: True if call is allowed, False otherwise
        
        Raises:
            LLMRateLimitError: If rate limit is exceeded
        """
        current_time = time.time()
        
        # Remove timestamps older than 1 minute (60 seconds)
        while self.call_timestamps and (current_time - self.call_timestamps[0]) > 60:
            self.call_timestamps.popleft()
        
        # Check calls per minute limit
        if len(self.call_timestamps) >= self.max_calls_per_minute:
            raise LLMRateLimitError(
                f"Rate limit exceeded: {self.max_calls_per_minute} calls per minute. "
                f"Please wait {60 - (current_time - self.call_timestamps[0]):.1f} seconds."
            )
        
        # Check calls per request limit
        if self.current_request_calls >= self.max_calls_per_request:
            raise LLMRateLimitError(
                f"Request limit exceeded: Maximum {self.max_calls_per_request} LLM calls per request. "
                f"Please reduce query complexity."
            )
        
        return True
    
    def register_call(self):
        """Register a successful call."""
        current_time = time.time()
        self.call_timestamps.append(current_time)
        self.current_request_calls += 1
    
    def reset_request_counter(self):
        """Reset the per-request call counter."""
        self.current_request_calls = 0
    
    def get_remaining_calls(self) -> int:
        """Get remaining calls in current window."""
        current_time = time.time()
        
        # Clean old timestamps
        while self.call_timestamps and (current_time - self.call_timestamps[0]) > 60:
            self.call_timestamps.popleft()
        
        return max(0, self.max_calls_per_minute - len(self.call_timestamps))


# Global singleton instance
rate_limiter = RateLimiter()
