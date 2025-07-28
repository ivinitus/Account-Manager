import time
from typing import Dict, Any

cache: Dict[str, Any] = {
    "last_used": None,
    "last_used_timestamp": 0,
}

CACHE_TIMEOUT = 30  

def normalize_output(acc: dict) -> dict:
    """Return a user-friendly JSON-serialisable representation."""
    return {
        "Customer ID": acc["customer_id"],
        "Email": acc["email"],
        "Password": acc["password"],
        "Marketplace": acc["marketplace"],
        "Type": acc["type"],
        "Date": acc["date"],
    }


def is_cache_valid() -> bool:
    """Return True if the `last_used` cache entry is still fresh."""
    return cache["last_used"] is not None and (
        time.time() - cache["last_used_timestamp"] < CACHE_TIMEOUT
    )