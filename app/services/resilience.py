"""
Resilience & Fault Tolerance Service for ResearchPilot (Phase 12).

This module provides two foundational patterns for resilient agent systems:
1. Retry with Exponential Backoff: Automatically retries temporary network
   hiccups with escalating delays (0.2s, 0.4s, 0.8s...).
2. Circuit Breaker: Automatically detects when an external service (like live search)
   is repeatedly failing, trips to 'OPEN', and fast-fails to fallbacks
   without stalling downstream multi-agent nodes!
"""

import time
from typing import Callable, Any, Tuple, Type


# -----------------------------------------------------------------------------
# 1. Retry with Exponential Backoff
# -----------------------------------------------------------------------------
def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 2,
    initial_delay: float = 0.2,
    backoff_factor: float = 2.0,
    allowed_exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Any:
    """
    Executes a zero-argument function, retrying up to max_retries on transient errors.

    Args:
        func: A callable to execute (e.g. lambda: requests.get(...))
        max_retries: Maximum number of retry attempts (default is 2)
        initial_delay: Starting delay in seconds before first retry (default is 0.2s)
        backoff_factor: Multiplier applied to delay after each failure (default is 2.0)
        allowed_exceptions: Tuple of exception types to catch and retry

    Returns:
        The successful return value of func()
    """
    current_delay = initial_delay
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except allowed_exceptions as err:
            last_error = err
            if attempt < max_retries:
                print(f"[Resilience] Attempt {attempt + 1} failed ({err}). Retrying in {current_delay:.2f}s...")
                time.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                print(f"[Resilience] All {max_retries + 1} attempts exhausted. Final error: {err}")

    raise last_error


# -----------------------------------------------------------------------------
# 2. Circuit Breaker Pattern
# -----------------------------------------------------------------------------
class CircuitBreaker:
    """
    A simple, transparent Circuit Breaker.

    States:
    - CLOSED: Healthy and normal. All calls pass through.
    - OPEN: Service has failed repeatedly. Rejects calls immediately for cooldown period.
    - HALF-OPEN: Cooldown expired. Allows a single test probe call to see if service recovered.
    """

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 15.0):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    def can_execute(self) -> bool:
        """
        Determines whether an external call should be attempted or fast-failed.
        """
        now = time.time()

        if self.state == "OPEN":
            if now - self.last_failure_time >= self.cooldown_seconds:
                # Cooldown period elapsed! Transition to HALF-OPEN to test recovery
                self.state = "HALF-OPEN"
                print("[Circuit Breaker] Cooldown expired. Transitioning from OPEN to HALF-OPEN (probing).")
                return True
            return False  # Still cooling down, fast-fail!

        return True  # CLOSED or HALF-OPEN

    def record_success(self) -> None:
        """
        Registers a successful operation. Resets failure metrics and closes circuit.
        """
        self.success_count += 1
        if self.state != "CLOSED":
            print(f"[Circuit Breaker] Probe succeeded. Resetting state from {self.state} to CLOSED.")
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        """
        Registers a failure. If consecutive failures exceed threshold, trips circuit to OPEN.
        """
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "HALF-OPEN":
            # Probe failed, immediately trip back to OPEN
            self.state = "OPEN"
            print("[Circuit Breaker] HALF-OPEN probe failed. Returning to OPEN state.")
        elif self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            print(f"[Circuit Breaker] Threshold reached ({self.failure_count} consecutive failures). Tripping circuit to OPEN for {self.cooldown_seconds}s!")

    def reset(self) -> None:
        """
        Manually resets the circuit breaker back to CLOSED state.
        """
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = 0.0
        print("[Circuit Breaker] Manually reset to CLOSED state.")

    def get_status(self) -> dict:
        """
        Returns a dictionary summary of the current circuit breaker health metrics.
        """
        now = time.time()
        time_until_retry = 0.0
        if self.state == "OPEN":
            time_until_retry = max(0.0, self.cooldown_seconds - (now - self.last_failure_time))

        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "cooldown_seconds": self.cooldown_seconds,
            "seconds_until_probe": round(time_until_retry, 2)
        }


# Global circuit breaker instance protecting web search integrations
search_circuit_breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=15.0)
