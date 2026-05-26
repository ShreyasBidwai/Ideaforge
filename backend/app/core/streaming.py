import json
from typing import Any

def format_sse_event(event_type: str, data: Any) -> str:
    """Formats an SSE event payload.
    Format: event: {type}\ndata: {json_data}\n\n
    """
    json_data = json.dumps(data)
    return f"event: {event_type}\ndata: {json_data}\n\n"
