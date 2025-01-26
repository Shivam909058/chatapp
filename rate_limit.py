from fastapi import HTTPException
from datetime import datetime, timedelta
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window
        self.clients = defaultdict(list)
    
    def is_rate_limited(self, client_id: str) -> bool:
        now = time.time()
        client_requests = self.clients[client_id]
        
        # Remove old requests
        while client_requests and client_requests[0] < now - self.window:
            client_requests.pop(0)
        
        # Check if rate limit is exceeded
        if len(client_requests) >= self.requests:
            return True
        
        # Add new request
        client_requests.append(now)
        return False
    
    def limit(self):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                request = kwargs.get('request')
                if request:
                    client_id = request.client.host
                    if self.is_rate_limited(client_id):
                        raise HTTPException(
                            status_code=429,
                            detail="Too many requests"
                        )
                return await func(*args, **kwargs)
            return wrapper
        return decorator 