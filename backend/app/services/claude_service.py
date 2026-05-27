import subprocess
import shutil
import time
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

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
            
            is_limited, reset_at = ClaudeService.parse_rate_limit(output)
            
            success = res.returncode == 0
            error = None
            if not success:
                error = stderr or stdout or f"Process exited with code {res.returncode}"
                
            return {
                "success": success and not is_limited,
                "output": stdout,
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
