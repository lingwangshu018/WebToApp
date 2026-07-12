import json
import logging
import sys
import time
from typing import Any, Optional


_CONFIGURED = False


def setup_logging(level: str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    root.setLevel(getattr(logging, str(level or "INFO").upper(), logging.INFO))
    _CONFIGURED = True


def log_event(event: str, **fields: Any) -> None:
    payload = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event}
    for key, value in fields.items():
        if value is not None:
            payload[key] = value
    try:
        print(json.dumps(payload, ensure_ascii=False), flush=True)
    except Exception:
        print(f"{event} {fields}", flush=True)


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
