"""Bounded, single-worker rate limiting for the public read-only API."""

from collections import OrderedDict
from threading import Lock
from time import monotonic


class PublicRateLimiter:
    def __init__(self, per_minute=60, burst=20, global_per_minute=180, global_burst=40):
        self.per_minute = per_minute
        self.burst = burst
        self.global_per_minute = global_per_minute
        self.global_burst = global_burst
        self.clients = OrderedDict()
        self.global_bucket = None
        self.lock = Lock()

    @staticmethod
    def refill(bucket, capacity, rate, now):
        tokens, previous = bucket if bucket is not None else (capacity, now)
        return min(capacity, tokens + max(0, now - previous) * rate / 60)

    def allow(self, client, now=None):
        now = monotonic() if now is None else now
        with self.lock:
            tokens = self.refill(
                self.clients.get(client), self.burst, self.per_minute, now
            )
            total = self.refill(
                self.global_bucket, self.global_burst, self.global_per_minute, now
            )
            allowed = tokens >= 1 and total >= 1
            self.clients[client] = (tokens - int(allowed), now)
            self.clients.move_to_end(client)
            self.global_bucket = (total - int(allowed), now)
            while len(self.clients) > 2048:
                self.clients.popitem(last=False)
            return allowed


public_limiter = PublicRateLimiter()
