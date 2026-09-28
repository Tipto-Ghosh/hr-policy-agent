from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class Timer:
    """A simple timer class to measure elapsed time."""
    elapsed_ms: float = 0.0
    
@contextmanager
def time_call():
    timer = Timer()
    start = time.perf_counter()
    try:
        yield timer
    finally:
        timer.elapsed_ms = (time.perf_counter() - start) * 1000