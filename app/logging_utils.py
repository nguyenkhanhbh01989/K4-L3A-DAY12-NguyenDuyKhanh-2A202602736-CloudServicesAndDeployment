from __future__ import annotations
import json
from datetime import datetime, timezone

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def log_event(event: str, level: str = "info", **fields) -> str:
    out = json.dumps({"event": event, "level": level.lower(), "timestamp": utc_now_iso(), **fields}, ensure_ascii=False)
    print(out, flush=True)
    return out
