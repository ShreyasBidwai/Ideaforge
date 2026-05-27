import subprocess
import shutil
import time
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

class ClaudeOutputParser:
    """Parse and clean Claude Code CLI output"""
    
    @staticmethod
    def clean_output(raw: str) -> str:
        if not raw:
            return ""
        # ANSI escape pattern
        ansi_pattern = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\(B')
        cleaned = ansi_pattern.sub('', raw)
        
        # Null bytes
        cleaned = cleaned.replace('\x00', '')
        
        # Normalize line endings
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
        
        # Strip progress bar characters
        progress_chars = "█░▒▓▕▏▄▀■▰▱"
        for char in progress_chars:
            cleaned = cleaned.replace(char, '')
            
        # Strip leading/trailing whitespace per line
        lines = [line.strip() for line in cleaned.split('\n')]
        cleaned = '\n'.join(lines)
        
        return cleaned.strip()
    
    @staticmethod
    def extract_files_created(output: str) -> list[str]:
        if not output:
            return []
        patterns = [
            re.compile(r'Created\s+([^\s\n\r]+)', re.IGNORECASE),
            re.compile(r'Wrote\s+to\s+([^\s\n\r]+)', re.IGNORECASE),
            re.compile(r'Modified\s+([^\s\n\r]+)', re.IGNORECASE),
            re.compile(r'Edit:\s+([^\s\n\r]+)', re.IGNORECASE)
        ]
        files = []
        for line in output.split('\n'):
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    path = match.group(1).rstrip('.')
                    if path not in files:
                        files.append(path)
        return files
    
    @staticmethod
    def extract_errors(output: str) -> list[str]:
        if not output:
            return []
        patterns = [
            re.compile(r'Error:\s+.*', re.IGNORECASE),
            re.compile(r'Traceback\s+\(most\s+recent\s+call\s+last\):', re.IGNORECASE),
            re.compile(r'ModuleNotFoundError:\s+.*', re.IGNORECASE),
            re.compile(r'SyntaxError:\s+.*', re.IGNORECASE),
            re.compile(r'npm\s+ERR!.*', re.IGNORECASE),
            re.compile(r'Permission\s+denied', re.IGNORECASE)
        ]
        errors = []
        for line in output.split('\n'):
            for pattern in patterns:
                if pattern.search(line):
                    errors.append(line.strip())
                    break
        return errors
    
    @staticmethod
    def detect_success(output: str) -> bool:
        if not output:
            return False
        output_lower = output.lower()
        
        # Check for failure indicators
        fail_indicators = [
            "error:",
            "failed",
            "traceback",
            "permission denied",
            "modulenotfounderror",
            "syntaxerror"
        ]
        if any(indicator in output_lower for indicator in fail_indicators):
            return False
            
        # Check for success indicators
        success_indicators = [
            "created",
            "wrote",
            "modified",
            "edit:"
        ]
        if any(indicator in output_lower for indicator in success_indicators):
            return True
            
        return True
    
    @staticmethod
    def parse_test_results(output: str) -> dict:
        passed = 0
        failed = 0
        errors = 0
        total = 0
        all_passed = False
        raw_summary = ""
        
        if not output:
            return {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "total": total,
                "all_passed": all_passed,
                "raw_summary": raw_summary
            }
            
        # Check for collection errors
        if "ERROR collecting" in output or "collection error" in output.lower():
            errors += 1
            
        # Check for pytest summary line
        pytest_summary_match = re.search(r'={5,}.*={5,}', output)
        if pytest_summary_match:
            raw_summary = pytest_summary_match.group(0)
            if "no tests ran" in raw_summary:
                pass
            else:
                passed_match = re.search(r'(\d+)\s+passed', raw_summary)
                if passed_match:
                    passed = int(passed_match.group(1))
                failed_match = re.search(r'(\d+)\s+failed', raw_summary)
                if failed_match:
                    failed = int(failed_match.group(1))
                errors_match = re.search(r'(\d+)\s+error', raw_summary)
                if errors_match:
                    errors = int(errors_match.group(1))
        else:
            # Check for vitest patterns
            for line in output.split('\n'):
                if line.strip().startswith("Tests") or line.strip().startswith("Test Files"):
                    p_match = re.search(r'(\d+)\s+passed', line)
                    if p_match and "Tests" in line:
                        passed = int(p_match.group(1))
                    f_match = re.search(r'(\d+)\s+failed', line)
                    if f_match and "Tests" in line:
                        failed = int(f_match.group(1))
                    if not raw_summary or "Tests" in line:
                        raw_summary = line.strip()
                        
        total = passed + failed + errors
        all_passed = passed > 0 and failed == 0 and errors == 0
        
        return {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total": total,
            "all_passed": all_passed,
            "raw_summary": raw_summary
        }

@dataclass
class ClaudeStatus:
    is_installed: bool
    cli_path: str | None
    is_authenticated: bool
    version: str | None
    error: str | None

class ClaudeService:
    """Wrapper around the Claude Code CLI"""
    
    @staticmethod
    def check_installation() -> ClaudeStatus:
        """
        Check if claude CLI is available:
        1. shutil.which("claude") — find binary
        2. subprocess.run(["claude", "--version"]) — get version
        3. subprocess.run(["claude", "-p", "say hello", "--output-format", "text"]) — test auth
        4. Return ClaudeStatus with results
        
        If claude not found: is_installed=False, error="Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
        If not authenticated: is_installed=True, is_authenticated=False, error="Claude Code not authenticated. Run: claude login"
        If working: all True, version populated
        """
        path = shutil.which("claude")
        if not path:
            try:
                res = subprocess.run(["claude", "--version"], capture_output=True, text=True)
                if res.returncode == 0:
                    path = "claude"
            except Exception:
                pass
                
        if not path:
            return ClaudeStatus(
                is_installed=False,
                cli_path=None,
                is_authenticated=False,
                version=None,
                error="Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )
            
        version = None
        try:
            res = subprocess.run(["claude", "--version"], capture_output=True, text=True)
            if res.returncode == 0:
                version = res.stdout.strip()
        except Exception:
            pass

        try:
            res_auth = subprocess.run(
                ["claude", "-p", "say hello", "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=15
            )
            output = (res_auth.stdout or "") + (res_auth.stderr or "")
            
            is_auth = True
            error_msg = None
            
            if any(p in output.lower() for p in ["login", "auth", "not logged in", "not authenticated", "oauth"]):
                is_auth = False
                error_msg = "Claude Code not authenticated. Run: claude login"
            elif res_auth.returncode == 127:
                is_auth = False
                error_msg = "Claude Code not authenticated. Run: claude login"
            elif res_auth.returncode != 0:
                is_limited, _ = ClaudeService.parse_rate_limit(output)
                if not is_limited:
                    is_auth = False
                    error_msg = "Claude Code not authenticated. Run: claude login"

            return ClaudeStatus(
                is_installed=True,
                cli_path=path,
                is_authenticated=is_auth,
                version=version,
                error=error_msg
            )
        except Exception:
            return ClaudeStatus(
                is_installed=True,
                cli_path=path,
                is_authenticated=False,
                version=version,
                error="Claude Code not authenticated. Run: claude login"
            )
    
    @staticmethod
    def run_prompt(prompt: str, cwd: str, timeout: int = 300) -> dict:
        """
        Execute a prompt via claude -p.
        
        Command: claude -p "{prompt}" --allowedTools "Read,Write,Edit,Bash" --output-format text
        
        Returns: {
            "success": bool,
            "output": str,
            "error": str | None,
            "is_rate_limited": bool,
            "rate_limit_reset": datetime | None,  # parsed from output
            "exit_code": int,
            "duration_seconds": float
        }
        
        Handles:
        - Normal success: success=True, output=stdout
        - Rate limit: parse reset time from stderr/stdout, is_rate_limited=True
        - Timeout (>300s): success=False, error="Prompt execution timed out"
        - Process error: success=False, error=stderr
        """
        start_time = time.time()
        cmd = [
            "claude",
            "-p",
            prompt,
            "--allowedTools",
            "Read,Write,Edit,Bash",
            "--dangerously-skip-permissions",
            "--output-format",
            "text"
        ]
        try:
            res = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration = time.time() - start_time
            stdout = res.stdout or ""
            stderr = res.stderr or ""
            output = stdout + "\n" + stderr
            
            cleaned_output = ClaudeOutputParser.clean_output(output)
            
            is_limited, reset_at = ClaudeService.parse_rate_limit(output)
            
            success = res.returncode == 0 and ClaudeOutputParser.detect_success(cleaned_output)
            error = None
            if not success and not is_limited:
                error = stderr or cleaned_output or f"Process exited with code {res.returncode}"
                
            return {
                "success": success and not is_limited,
                "output": cleaned_output,
                "error": error,
                "is_rate_limited": is_limited,
                "rate_limit_reset": reset_at,
                "exit_code": res.returncode,
                "duration_seconds": duration
            }
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                "success": False,
                "output": "",
                "error": "Prompt execution timed out",
                "is_rate_limited": False,
                "rate_limit_reset": None,
                "exit_code": -1,
                "duration_seconds": duration
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "is_rate_limited": False,
                "rate_limit_reset": None,
                "exit_code": -1,
                "duration_seconds": duration
            }
    
    @staticmethod
    def parse_rate_limit(output: str) -> tuple[bool, datetime | None]:
        """
        Parse rate limit from Claude output.
        
        Patterns to match:
        1. "Resets in: X hours Y minutes" → compute datetime
        2. "Resets in: Y minutes" → compute datetime (no hours)
        3. "Your limit will reset at H:MM PM" → parse time (assume today, or tomorrow if past)
        4. "usage limit reached" → rate limited but no time given, default 5 hours
        5. "rate limit" → same as above
        
        Returns: (is_rate_limited: bool, reset_at: datetime | None)
        """
        if not output:
            return False, None
            
        output_lower = output.lower()
        is_limited = False
        
        if any(p in output_lower for p in ["usage limit reached", "rate limit", "resets in:", "limit will reset"]):
            is_limited = True
            
        if not is_limited:
            return False, None
            
        hours_mins_match = re.search(r'resets in:\s*(\d+)\s*hours?\s*(\d+)\s*minutes?', output, re.IGNORECASE)
        if hours_mins_match:
            hours = int(hours_mins_match.group(1))
            mins = int(hours_mins_match.group(2))
            reset_at = datetime.utcnow() + timedelta(hours=hours, minutes=mins)
            return True, reset_at
            
        mins_match = re.search(r'resets in:\s*(\d+)\s*minutes?', output, re.IGNORECASE)
        if mins_match:
            mins = int(mins_match.group(1))
            reset_at = datetime.utcnow() + timedelta(minutes=mins)
            return True, reset_at
            
        time_match = re.search(r'(?:reset at|resets at|reset will be at|limit will reset at)\s*(\d+:\d+\s*(?:AM|PM|am|pm)?)', output, re.IGNORECASE)
        if not time_match:
            time_match = re.search(r'reset\s+at\s*(\d+:\d+\s*(?:AM|PM|am|pm)?)', output, re.IGNORECASE)
            
        if time_match:
            try:
                time_str = time_match.group(1).strip()
                parsed_time = None
                
                for fmt in ("%I:%M %p", "%I:%M %P", "%I:%M%p", "%I:%M%P", "%H:%M"):
                    try:
                        parsed_time = datetime.strptime(time_str, fmt).time()
                        break
                    except ValueError:
                        pass
                        
                if not parsed_time:
                    clean_time = re.sub(r'\s+', '', time_str)
                    for fmt in ("%I:%M%p", "%I:%M%P", "%H:%M"):
                        try:
                            parsed_time = datetime.strptime(clean_time, fmt).time()
                            break
                        except ValueError:
                            pass
                            
                if parsed_time:
                    now = datetime.utcnow()
                    reset_at = datetime.combine(now.date(), parsed_time)
                    if reset_at <= now:
                        reset_at += timedelta(days=1)
                    return True, reset_at
            except Exception:
                pass
                
        reset_at = datetime.utcnow() + timedelta(hours=5)
        return True, reset_at
