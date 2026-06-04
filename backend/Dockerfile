# IdeaForge backend — FastAPI API that ALSO shells out to the Claude Code CLI
# to build/run generated projects. So this image needs: Python + Node + the
# Claude CLI, and it must run as a NON-root user (Claude refuses
# --dangerously-skip-permissions when running as root).
FROM python:3.10-slim-bookworm

# --- System dependencies --------------------------------------------------
#  * Node 20 + npm  -> required by the Claude CLI and by generated JS projects
#  * git/build tools -> Claude builds + compiling any child-project deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      curl ca-certificates gnupg git build-essential \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install -g @anthropic-ai/claude-code \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# --- Python dependencies (installed system-wide) --------------------------
# Installed as root into /usr/local so a bind-mounted /app cannot hide them.
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# --- Non-root user matching the host UID/GID (1001) -----------------------
# Lets Claude run with --dangerously-skip-permissions and keeps bind-mounted
# host files (source code + ~/.claude credentials) readable/writable.
RUN groupadd -g 1001 app \
 && useradd -u 1001 -g 1001 -m -s /bin/bash app

COPY --chown=1001:1001 . .

ENV HOME=/home/app \
    PYTHONUNBUFFERED=1
USER app

EXPOSE 8000

# Apply DB migrations, then start the API. (compose adds --reload for dev.)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
