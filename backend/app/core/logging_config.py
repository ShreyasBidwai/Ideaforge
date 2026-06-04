"""Central logging configuration for IdeaForge.

Sets up a single, complete, timestamped log file at ``backend/logs/complete.log``
that captures *everything* that flows through Python's logging system:

* application logs from every module (``logging.getLogger(__name__)``)
* uvicorn server + HTTP access logs
* the build orchestrator's per-project build activity
* Claude run summaries
* ``warnings.warn(...)`` output (via ``captureWarnings``)

The file handler rotates (25 MB x 5 backups) so it never grows unbounded, and
there is a single writer (this process) so rotation is race-free. Call
:func:`setup_logging` once, as early as possible, before other modules import.
"""

import logging
import logging.handlers
import os
import sys

# this file lives at backend/app/core/logging_config.py -> resolve backend/logs
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(os.path.dirname(_CORE_DIR))  # core -> app -> backend
LOG_DIR = os.path.join(_BACKEND_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "complete.log")

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Marker so repeated calls (e.g. uvicorn --reload re-imports) never double-add
# handlers to the same logger.
_HANDLER_FLAG = "_ideaforge_complete_log"


def _make_file_handler() -> logging.Handler:
    os.makedirs(LOG_DIR, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=25 * 1024 * 1024,  # 25 MB per file
        backupCount=5,              # keep complete.log.1 .. complete.log.5
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    setattr(handler, _HANDLER_FLAG, True)
    return handler


def _already_attached(target: logging.Logger) -> bool:
    return any(getattr(h, _HANDLER_FLAG, False) for h in target.handlers)


def setup_logging(level: int = logging.INFO) -> str:
    """Configure the unified complete.log file + console output.

    Idempotent: safe to call multiple times. Returns the absolute log path.
    """
    file_handler = _make_file_handler()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    setattr(console_handler, _HANDLER_FLAG, True)

    root = logging.getLogger()
    root.setLevel(level)
    if not _already_attached(root):
        root.addHandler(file_handler)
        root.addHandler(console_handler)

    # uvicorn installs its own (console) handlers, so attach the file handler
    # directly to capture its lines into complete.log:
    #   * "uvicorn"        -> server lifecycle; also catches "uvicorn.error",
    #                         which has no own handler and propagates up to it.
    #   * "uvicorn.access" -> HTTP request log.
    # We set propagate=False on each so a line is written to the file exactly
    # once. Without this, a record bubbles uvicorn.access -> uvicorn -> root,
    # hitting the file handler up to three times.
    for name in ("uvicorn", "uvicorn.access"):
        ulog = logging.getLogger(name)
        if not _already_attached(ulog):
            ulog.addHandler(file_handler)
            ulog.propagate = False

    # Route warnings.warn(...) through logging so deprecation/runtime warnings
    # land in complete.log instead of only stderr.
    logging.captureWarnings(True)

    return LOG_FILE
