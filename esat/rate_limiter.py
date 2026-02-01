"""
Rate Limiter
Provides precise rate control for email sending
"""

import time
import threading
from queue import Queue, Empty
from datetime import datetime, timedelta
import logging
from collections import deque
import math

class TokenBucket:
    """Token bucket rate limiter implementation"""
    
    def __init__(self, rate_per_second, burst_size=None):
        """
        Args:
            rate_per_second: Tokens per second
            burst_size: Maximum burst size (defaults to rate_per_second)
        """
        self.rate = rate_per_second
        self.capacity = burst_size if burst_size is not None else rate_per_second
        self.tokens = self.capacity
        self.last_update = time.time()
        self.lock = threading.Lock()
        
    def _add_tokens(self):
        """Add tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_update
        new_tokens = elapsed * self.rate
        
        with self.lock:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_update = now
    
    def consume(self, tokens=1, block=False, timeout=None):
        """
        Consume tokens from bucket
        
        Args:
            tokens: Number of tokens to consume
            block: Whether to block until tokens are available
            timeout: Maximum time to wait (seconds)
            
        Returns:
            bool: True if tokens were consumed, False otherwise
        """
        start_time = time.time()
        
        while True:
            self._add_tokens()
            
            with self.lock:
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
            
            if not block:
                return False
            
            # Calculate remaining timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
                time.sleep(min(0.01, timeout - elapsed))
            else:
                time.sleep(0.01)

class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on success/failure rates"""
    
    def __init__(self, initial_rate=1.0, min_rate=0.1, max_rate=10.0, 
                 adjustment_factor=1.5, recovery_time=60.0):
        """
        Args:
            initial_rate: Starting rate (emails per second)
            min_rate: Minimum allowed rate
            max_rate: Maximum allowed rate
            adjustment_factor: Factor to multiply/divide rate by
            recovery_time: Time to wait before increasing rate after failures
        """
        self.current_rate = initial_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.adjustment_factor = adjustment_factor
        self.recovery_time = recovery_time
        
        self.bucket = TokenBucket(initial_rate)
        self.failure_timestamps = deque()
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = time.time()
        self.lock = threading.Lock()
        
        self.logger = logging.getLogger(__name__)
    
    def _clean_old_failures(self):
        """Remove failure timestamps older than recovery_time"""
        cutoff = time.time() - self.recovery_time
        while self.failure_timestamps and self.failure_timestamps[0] < cutoff:
            self.failure_timestamps.popleft()
    
    def record_success(self):
        """Record a successful email send"""
        with self.lock:
            self.success_count += 1
            
            # Consider increasing rate if no recent failures
            self._clean_old_failures()
            if not self.failure_timestamps and self.current_rate < self.max_rate:
                time_since_adjustment = time.time() - self.last_adjustment
                if time_since_adjustment > self.recovery_time:
                    new_rate = min(self.max_rate, 
                                 self.current_rate * self.adjustment_factor)
                    if new_rate != self.current_rate:
                        self.current_rate = new_rate
                        self.bucket.rate = new_rate
                        self.last_adjustment = time.time()
                        self.logger.info(f"Rate increased to {new_rate:.2f}/second")
    
    def record_failure(self):
        """Record a failed email send"""
        with self.lock:
            self.failure_count += 1
            self.failure_timestamps.append(time.time())
            self._clean_old_failures()
            
            # Calculate failure rate in last recovery_time
            failure_rate = len(self.failure_timestamps) / self.recovery_time
            
            # Decrease rate if failure rate is high
            if failure_rate > 0.1 and self.current_rate > self.min_rate:  # 10% failure rate threshold
                new_rate = max(self.min_rate, 
                             self.current_rate / self.adjustment_factor)
                if new_rate != self.current_rate:
                    self.current_rate = new_rate
                    self.bucket.rate = new_rate
                    self.last_adjustment = time.time()
                    self.logger.warning(f"Rate decreased to {new_rate:.2f}/second due to failures")
    
    def wait(self, tokens=1, timeout=None):
        """
        Wait for tokens to become available
        
        Args:
            tokens: Number of tokens to consume
            timeout: Maximum time to wait (seconds)
            
        Returns:
            bool: True if tokens were obtained, False on timeout
        """
        return self.bucket.consume(tokens, block=True, timeout=timeout)
    
    def get_stats(self):
        """Get current rate limiter statistics"""
        with self.lock:
            return {
                'current_rate': self.current_rate,
                'success_count': self.success_count,
                'failure_count': self.failure_count,
                'recent_failures': len(self.failure_timestamps),
                'bucket_tokens': self.bucket.tokens,
                'min_rate': self.min_rate,
                'max_rate': self.max_rate
            }

class TimeWindowLimiter:
    """Limiter based on time windows (e.g., max per minute, hour, day)"""
    
    def __init__(self, limits):
        """
        Args:
            limits: Dict of {window_seconds: max_count}
                    Example: {60: 10, 3600: 100} = 10 per minute, 100 per hour
        """
        self.limits = sorted(limits.items(), reverse=True)  # Largest window first
        self.windows = {window: deque() for window, _ in self.limits}
        self.lock = threading.Lock()
    
    def can_send(self):
        """
        Check if sending is allowed within all windows
        
        Returns:
            bool: True if allowed, False if any limit would be exceeded
        """
        now = time.time()
        
        with self.lock:
            for window_seconds, max_count in self.limits:
                window = self.windows[window_seconds]
                cutoff = now - window_seconds
                
                # Remove old timestamps
                while window and window[0] < cutoff:
                    window.popleft()
                
                # Check if limit would be exceeded
                if len(window) >= max_count:
                    return False
            
            # Add current timestamp to all windows
            for window_seconds in self.windows:
                self.windows[window_seconds].append(now)
            
            return True
    
    def wait_until_allowed(self, timeout=None):
        """
        Wait until sending is allowed
        
        Returns:
            float: Time waited in seconds, or -1 on timeout
        """
        start_time = time.time()
        
        while True:
            if self.can_send():
                return time.time() - start_time
            
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return -1
            
            # Calculate when the next window will have space
            now = time.time()
            next_allowed = float('inf')
            
            with self.lock:
                for window_seconds, max_count in self.limits:
                    window = self.windows[window_seconds]
                    cutoff = now - window_seconds
                    
                    # Remove old timestamps
                    while window and window[0] < cutoff:
                        window.popleft()
                    
                    if len(window) >= max_count:
                        # Oldest timestamp in this window
                        oldest = window[0]
                        # Time when this window will have space
                        window_allowed = oldest + window_seconds
                        next_allowed = min(next_allowed, window_allowed)
            
            wait_time = max(0.01, min(1.0, next_allowed - now))
            time.sleep(wait_time)

class RateLimiterManager:
    """Manages multiple rate limiting strategies"""
    
    def __init__(self, config=None):
        """
        Args:
            config: Dict with rate limiting configuration
        """
        self.config = config or {
            'rate_per_second': 1.0,
            'burst_size': 5.0,
            'adaptive': True,
            'time_windows': {
                60: 10,    # 10 per minute
                3600: 100  # 100 per hour
            }
        }
        
        # Initialize limiters
        self.token_bucket = TokenBucket(
            rate_per_second=self.config['rate_per_second'],
            burst_size=self.config.get('burst_size')
        )
        
        if self.config.get('adaptive', False):
            self.adaptive_limiter = AdaptiveRateLimiter(
                initial_rate=self.config['rate_per_second'],
                min_rate=0.1,
                max_rate=50.0
            )
        else:
            self.adaptive_limiter = None
        
        if self.config.get('time_windows'):
            self.time_window_limiter = TimeWindowLimiter(
                self.config['time_windows']
            )
        else:
            self.time_window_limiter = None
        
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'total_waited': 0.0,
            'total_requests': 0,
            'rate_limited': 0
        }
    
    def acquire(self, timeout=None):
        """
        Acquire permission to send
        
        Args:
            timeout: Maximum time to wait (seconds)
            
        Returns:
            bool: True if acquired, False on timeout
        """
        self.stats['total_requests'] += 1
        start_time = time.time()
        
        # Check time window limiter first
        if self.time_window_limiter:
            wait_time = self.time_window_limiter.wait_until_allowed(timeout)
            if wait_time < 0:
                return False
        
        # Check adaptive limiter if enabled
        if self.adaptive_limiter:
            if not self.adaptive_limiter.wait(timeout=timeout):
                return False
        
        # Check token bucket
        if not self.token_bucket.consume(block=True, timeout=timeout):
            self.stats['rate_limited'] += 1
            return False
        
        waited = time.time() - start_time
        self.stats['total_waited'] += waited
        
        return True
    
    def record_success(self):
        """Record successful send for adaptive limiter"""
        if self.adaptive_limiter:
            self.adaptive_limiter.record_success()
    
    def record_failure(self):
        """Record failed send for adaptive limiter"""
        if self.adaptive_limiter:
            self.adaptive_limiter.record_failure()
    
    def set_rate(self, new_rate):
        """Dynamically adjust rate"""
        self.token_bucket.rate = new_rate
        if self.adaptive_limiter:
            self.adaptive_limiter.current_rate = new_rate
            self.adaptive_limiter.bucket.rate = new_rate
        self.logger.info(f"Rate manually adjusted to {new_rate:.2f}/second")
    
    def get_stats(self):
        """Get comprehensive statistics"""
        stats = self.stats.copy()
        
        if self.stats['total_requests'] > 0:
            stats['avg_wait_time'] = self.stats['total_waited'] / self.stats['total_requests']
            stats['rate_limit_percentage'] = (self.stats['rate_limited'] / self.stats['total_requests']) * 100
        else:
            stats['avg_wait_time'] = 0
            stats['rate_limit_percentage'] = 0
        
        stats['current_rate'] = self.token_bucket.rate
        
        if self.adaptive_limiter:
            stats.update(self.adaptive_limiter.get_stats())
        
        return stats
    
    def reset(self):
        """Reset all limiters and statistics"""
        self.token_bucket.tokens = self.token_bucket.capacity
        self.token_bucket.last_update = time.time()
        
        if self.adaptive_limiter:
            self.adaptive_limiter.failure_timestamps.clear()
            self.adaptive_limiter.success_count = 0
            self.adaptive_limiter.failure_count = 0
        
        if self.time_window_limiter:
            for window in self.time_window_limiter.windows.values():
                window.clear()
        
        self.stats = {
            'total_waited': 0.0,
            'total_requests': 0,
            'rate_limited': 0
        }
