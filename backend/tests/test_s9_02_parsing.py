import pytest

# TEST 1: Strip ANSI codes
def test_strip_ansi():
    from backend.app.services.claude_service import ClaudeOutputParser
    raw = "\x1b[32mSuccess\x1b[0m: Created file \x1b[1mapp.py\x1b[0m"
    cleaned = ClaudeOutputParser.clean_output(raw)
    assert "\x1b" not in cleaned
    assert "Success" in cleaned
    assert "app.py" in cleaned

# TEST 2: Extract created files
def test_extract_files():
    from backend.app.services.claude_service import ClaudeOutputParser
    output = """
    Created backend/app/main.py
    Wrote to backend/app/core/config.py
    Modified backend/app/models/user.py
    """
    files = ClaudeOutputParser.extract_files_created(output)
    assert "backend/app/main.py" in files
    assert "backend/app/core/config.py" in files
    assert "backend/app/models/user.py" in files

# TEST 3: Parse pytest "5 passed"
def test_parse_pytest_passed():
    from backend.app.services.claude_service import ClaudeOutputParser
    output = "========================= 5 passed in 2.31s ========================="
    result = ClaudeOutputParser.parse_test_results(output)
    assert result["passed"] == 5
    assert result["failed"] == 0
    assert result["all_passed"] is True

# TEST 4: Parse pytest "3 passed, 2 failed"
def test_parse_pytest_mixed():
    from backend.app.services.claude_service import ClaudeOutputParser
    output = "========================= 3 passed, 2 failed in 4.52s ========================="
    result = ClaudeOutputParser.parse_test_results(output)
    assert result["passed"] == 3
    assert result["failed"] == 2
    assert result["all_passed"] is False

# TEST 5: Parse vitest output
def test_parse_vitest():
    from backend.app.services.claude_service import ClaudeOutputParser
    output = """
    ✓ src/__tests__/app.test.tsx (3 tests) 45ms
    ✓ src/__tests__/auth.test.tsx (5 tests) 120ms
    
    Test Files  2 passed (2)
    Tests  8 passed (8)
    """
    result = ClaudeOutputParser.parse_test_results(output)
    assert result["passed"] == 8
    assert result["all_passed"] is True

# TEST 6: Parse no tests found
def test_parse_no_tests():
    from backend.app.services.claude_service import ClaudeOutputParser
    output = "========================= no tests ran in 0.01s ========================="
    result = ClaudeOutputParser.parse_test_results(output)
    assert result["total"] == 0

# TEST 7: Parse collection error
def test_parse_collection_error():
    from backend.app.services.claude_service import ClaudeOutputParser
    output = """
    ERROR collecting tests/test_auth.py
    ModuleNotFoundError: No module named 'backend'
    """
    result = ClaudeOutputParser.parse_test_results(output)
    assert result["errors"] > 0

# TEST 8: Detect success
def test_detect_success():
    from backend.app.services.claude_service import ClaudeOutputParser
    assert ClaudeOutputParser.detect_success("Created backend/app/main.py\nWrote to config.py") is True
    assert ClaudeOutputParser.detect_success("Error: Permission denied\nFailed to create file") is False

# TEST 9: Detect failure with traceback
def test_detect_failure_traceback():
    from backend.app.services.claude_service import ClaudeOutputParser
    output = """
    Traceback (most recent call last):
      File "main.py", line 1
    ModuleNotFoundError: No module named 'fastapi'
    """
    assert ClaudeOutputParser.detect_success(output) is False

# TEST 10: Extract errors
def test_extract_errors():
    from backend.app.services.claude_service import ClaudeOutputParser
    output = """
    Creating files...
    Error: Cannot write to /root/protected
    npm ERR! code EACCES
    Done.
    """
    errors = ClaudeOutputParser.extract_errors(output)
    assert len(errors) >= 2

# TEST 11: Handle empty output
def test_handle_empty():
    from backend.app.services.claude_service import ClaudeOutputParser
    assert ClaudeOutputParser.clean_output("") == ""
    assert ClaudeOutputParser.extract_files_created("") == []
    assert ClaudeOutputParser.parse_test_results("")["total"] == 0

# TEST 12: Clean output preserves meaningful content
def test_clean_preserves_content():
    from backend.app.services.claude_service import ClaudeOutputParser
    output = "Line 1\nLine 2\nLine 3"
    cleaned = ClaudeOutputParser.clean_output(output)
    assert "Line 1" in cleaned
    assert "Line 2" in cleaned
    assert "Line 3" in cleaned
