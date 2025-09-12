import time
import random
import logging
from typing import Callable, Any, Optional, List, Type
from functools import wraps
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError


class RetryHandler:
    """Advanced retry mechanism with exponential backoff and smart error handling"""
    
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        
        self.logger = logging.getLogger(__name__)
        
        # Define retryable exceptions
        self.retryable_exceptions = (
            RequestException,
            ConnectionError,
            Timeout,
            HTTPError
        )
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add random jitter to avoid thundering herd
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(delay, 0.1)  # Minimum 0.1 second delay
    
    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if we should retry based on exception type and attempt count"""
        if attempt >= self.max_retries:
            return False
        
        # Always retry on network-related issues
        if isinstance(exception, self.retryable_exceptions):
            return True
        
        # Retry on specific HTTP status codes
        if isinstance(exception, HTTPError):
            status_code = exception.response.status_code if exception.response else None
            retryable_codes = {429, 500, 502, 503, 504}  # Rate limit, server errors
            return status_code in retryable_codes
        
        # Don't retry on other exceptions
        return False
    
    def retry_on_failure(self, 
                        retryable_exceptions: Optional[List[Type[Exception]]] = None,
                        max_retries: Optional[int] = None):
        """Decorator for adding retry logic to functions"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                _max_retries = max_retries or self.max_retries
                _retryable_exceptions = tuple(retryable_exceptions or self.retryable_exceptions)
                
                last_exception = None
                
                for attempt in range(_max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                        
                    except _retryable_exceptions as e:
                        last_exception = e
                        
                        if attempt == _max_retries:
                            self.logger.error(f"Function {func.__name__} failed after {_max_retries} retries: {str(e)}")
                            raise e
                        
                        delay = self._calculate_delay(attempt)
                        self.logger.warning(
                            f"Function {func.__name__} failed (attempt {attempt + 1}/{_max_retries + 1}): {str(e)}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        time.sleep(delay)
                        
                    except Exception as e:
                        # Non-retryable exception, fail immediately
                        self.logger.error(f"Function {func.__name__} failed with non-retryable exception: {str(e)}")
                        raise e
                
                # This should never be reached, but just in case
                if last_exception:
                    raise last_exception
            
            return wrapper
        return decorator


class CircuitBreaker:
    """Circuit breaker pattern for handling persistent failures"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception):
        
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        
        self.logger = logging.getLogger(__name__)
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker"""
        return (
            self.state == 'OPEN' and
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
                self.logger.info("Circuit breaker moving to HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset failure count
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.logger.info("Circuit breaker reset to CLOSED state")
            
            self.failure_count = 0
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
                self.logger.error(
                    f"Circuit breaker OPENED after {self.failure_count} failures. "
                    f"Will retry after {self.recovery_timeout} seconds"
                )
            
            raise e


class RateLimiter:
    """Rate limiting to avoid overwhelming target servers"""
    
    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        
        self.logger = logging.getLogger(__name__)
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class ErrorRecovery:
    """Comprehensive error recovery and fallback mechanisms"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_patterns = {
            'rate_limited': ['429', 'too many requests', 'rate limit'],
            'blocked': ['403', 'forbidden', 'access denied', 'blocked'],
            'not_found': ['404', 'not found'],
            'server_error': ['500', '502', '503', '504', 'server error'],
            'network_error': ['connection', 'timeout', 'network'],
            'parsing_error': ['parse', 'html', 'selector', 'beautifulsoup']
        }
    
    def classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate recovery strategy"""
        error_text = str(error).lower()
        
        for category, patterns in self.error_patterns.items():
            if any(pattern in error_text for pattern in patterns):
                return category
        
        return 'unknown'
    
    def suggest_recovery_action(self, error_category: str) -> dict:
        """Suggest recovery actions based on error type"""
        recovery_actions = {
            'rate_limited': {
                'action': 'increase_delay',
                'suggestion': 'Increase delay between requests or use Selenium',
                'retry': True,
                'delay_multiplier': 3.0
            },
            'blocked': {
                'action': 'change_headers',
                'suggestion': 'Rotate User-Agent or use proxy/Selenium',
                'retry': True,
                'delay_multiplier': 2.0
            },
            'not_found': {
                'action': 'check_url',
                'suggestion': 'Verify URL structure and catalog path',
                'retry': False
            },
            'server_error': {
                'action': 'wait_and_retry',
                'suggestion': 'Wait longer between requests',
                'retry': True,
                'delay_multiplier': 2.0
            },
            'network_error': {
                'action': 'check_connection',
                'suggestion': 'Check internet connection and target server availability',
                'retry': True,
                'delay_multiplier': 1.5
            },
            'parsing_error': {
                'action': 'update_selectors',
                'suggestion': 'Update CSS selectors or use different parsing strategy',
                'retry': False
            },
            'unknown': {
                'action': 'manual_review',
                'suggestion': 'Manual investigation required',
                'retry': False
            }
        }
        
        return recovery_actions.get(error_category, recovery_actions['unknown'])
    
    def log_detailed_error(self, error: Exception, context: dict = None):
        """Log detailed error information for debugging"""
        error_category = self.classify_error(error)
        recovery_action = self.suggest_recovery_action(error_category)
        
        self.logger.error(f"Error Category: {error_category}")
        self.logger.error(f"Error Message: {str(error)}")
        self.logger.error(f"Recovery Suggestion: {recovery_action['suggestion']}")
        
        if context:
            self.logger.error(f"Context: {context}")
        
        return {
            'category': error_category,
            'recovery_action': recovery_action,
            'error_message': str(error)
        }