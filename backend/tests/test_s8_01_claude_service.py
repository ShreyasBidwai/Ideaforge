import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# TEST 1: Parse "Resets in: 4 hours 23 minutes"
def test_parse_hours_minutes():
    from app.services.claude_service import ClaudeService
    is_limited, reset_at = ClaudeService.parse_rate_limit(
        "You've reached your usage limit for this period. Resets in: 4 hours 23 minutes"
    )
    assert is_limited is True
    assert reset_at is not None
    diff = (reset_at - datetime.utcnow()).total_seconds()
    assert 4 * 3600 < diff < 5 * 3600  # roughly 4h23m in seconds

# TEST 2: Parse "Resets in: 45 minutes" (no hours)
def test_parse_minutes_only():
    from app.services.claude_service import ClaudeService
    is_limited, reset_at = ClaudeService.parse_rate_limit(
        "Rate limit exceeded. Resets in: 45 minutes"
    )
    assert is_limited is True
    assert reset_at is not None
    diff = (reset_at - datetime.utcnow()).total_seconds()
    assert 40 * 60 < diff < 50 * 60

# TEST 3: Parse "reset at 7:00 PM"
def test_parse_reset_at():
    from app.services.claude_service import ClaudeService
    is_limited, reset_at = ClaudeService.parse_rate_limit(
        "Claude usage limit reached. Your limit will reset at 7:00 PM"
    )
    assert is_limited is True
    assert reset_at is not None

# TEST 4: No rate limit returns False
def test_no_rate_limit():
    from app.services.claude_service import ClaudeService
    is_limited, reset_at = ClaudeService.parse_rate_limit(
        "Successfully created backend/app/main.py with health endpoint"
    )
    assert is_limited is False
    assert reset_at is None

# TEST 5: Generic "usage limit reached" defaults to 5 hours
def test_generic_limit_defaults():
    from app.services.claude_service import ClaudeService
    is_limited, reset_at = ClaudeService.parse_rate_limit("usage limit reached")
    assert is_limited is True
    assert reset_at is not None
    diff = (reset_at - datetime.utcnow()).total_seconds()
    assert 4.5 * 3600 < diff < 5.5 * 3600  # ~5 hours

# TEST 6: ClaudeStatus dataclass works
def test_claude_status_dataclass():
    from app.services.claude_service import ClaudeStatus
    status = ClaudeStatus(is_installed=True, cli_path="/usr/bin/claude", is_authenticated=True, version="1.0.0", error=None)
    assert status.is_installed is True
    assert status.error is None

# TEST 7: run_prompt returns correct structure
def test_run_prompt_structure():
    """run_prompt should return dict with required keys"""
    from app.services.claude_service import ClaudeService
    # Mock subprocess to avoid actual claude call
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout="Done", stderr="", returncode=0)
        result = ClaudeService.run_prompt("test prompt", "/tmp")
        assert "success" in result
        assert "output" in result
        assert "is_rate_limited" in result
        assert "duration_seconds" in result

# TEST 8: Claude status endpoint
@pytest.mark.anyio
async def test_claude_status_endpoint(client, auth_headers):
    """GET /setup/claude-status should return status object"""
    response = await client.get("/api/v1/setup/claude-status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "is_installed" in data
    assert "is_authenticated" in data
