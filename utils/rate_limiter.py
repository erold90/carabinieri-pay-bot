# utils/rate_limiter.py
"""Rate limiter per evitare flood"""
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class RateLimiter:
    def __init__(self, max_requests=30, window_seconds=60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)
        self.locks = defaultdict(asyncio.Lock)
    
    async def check_rate_limit(self, user_id: int) -> bool:
        """Controlla se l'utente ha superato il rate limit"""
        async with self.locks[user_id]:
            now = datetime.now()
            
            # Pulisci richieste vecchie
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if now - req_time < self.window
            ]
            
            # Controlla limite
            if len(self.requests[user_id]) >= self.max_requests:
                return False
            
            # Aggiungi richiesta
            self.requests[user_id].append(now)
            return True

rate_limiter = RateLimiter()
