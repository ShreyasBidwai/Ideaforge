import subprocess
import shutil
import time
import re
import os
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

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
    def _find_claude_binary() -> str | None:
        """Find the claude binary path across common locations"""
        claude_path = shutil.which("claude")
        if claude_path:
            return claude_path
            
        for path in ["~/.npm-global/bin/claude", "/usr/local/bin/claude", "/usr/bin/claude", "~/.local/bin/claude"]:
            expanded = os.path.expanduser(path)
            if os.path.isfile(expanded):
                return expanded
        return None

    @staticmethod
    def check_installation() -> ClaudeStatus:
        """Check if claude CLI is available and authenticated"""
        path = ClaudeService._find_claude_binary()
        if not path:
            return ClaudeStatus(
                is_installed=False,
                cli_path=None,
                is_authenticated=False,
                version=None,
                error="Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )
            
        version = None
        env = os.environ.copy()
        npm_global = os.path.expanduser("~/.npm-global/bin")
        local_bin = os.path.expanduser("~/.local/bin")
        if npm_global not in env.get("PATH", ""):
            env["PATH"] = npm_global + ":" + env.get("PATH", "")
        if local_bin not in env.get("PATH", ""):
            env["PATH"] = local_bin + ":" + env.get("PATH", "")

        try:
            res = subprocess.run([path, "--version"], capture_output=True, text=True, env=env)
            if res.returncode == 0:
                version = res.stdout.strip()
        except Exception:
            pass

        try:
            res_auth = subprocess.run(
                [path, "-p", "--dangerously-skip-permissions", "--output-format", "text"],
                input="say hello",
                capture_output=True,
                text=True,
                timeout=15,
                env=env
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
        except Exception as e:
            return ClaudeStatus(
                is_installed=True,
                cli_path=path,
                is_authenticated=False,
                version=version,
                error=f"Claude Code not authenticated: {str(e)}"
            )
    
    @staticmethod
    def run_prompt(prompt: str, cwd: str, timeout: int = 600, tools: str = "Read,Write,Edit,Bash", check_success: bool = True) -> dict:
        """Execute a prompt via claude -p with full debug logging and tool fallback"""
        
        # Step 1: Find claude binary
        claude_path = ClaudeService._find_claude_binary()
        logger.info(f"[CLAUDE DEBUG] claude binary path: {claude_path}")
        logger.info(f"[CLAUDE DEBUG] PATH env: {os.environ.get('PATH', 'NOT SET')}")
        
        if not claude_path:
            logger.error("[CLAUDE DEBUG] Claude Code CLI not found anywhere!")
            ret = {
                "success": False,
                "output": "",
                "error": "Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code",
                "is_rate_limited": False,
                "rate_limit_reset": None,
                "exit_code": -1,
                "duration_seconds": 0
            }
            ClaudeService._log_activity(prompt, cwd, timeout, ret)
            return ret
        
        # Step 2: Build command
        cmd = [
            claude_path, 
            "-p", 
            "--dangerously-skip-permissions",
            "--output-format", 
            "text"
        ]
        if tools is not None:
            cmd.extend(["--tools", tools])
        logger.info(f"[CLAUDE DEBUG] Command: {' '.join(cmd[:3])}... (prompt length: {len(prompt)} chars passed via stdin)")
        logger.info(f"[CLAUDE DEBUG] Working directory: {cwd}")
        logger.info(f"[CLAUDE DEBUG] Timeout: {timeout}s")
        logger.info(f"[CLAUDE DEBUG] CWD exists: {os.path.isdir(cwd)}")
        
        # Step 3: Build environment
        env = os.environ.copy()
        npm_global = os.path.expanduser("~/.npm-global/bin")
        local_bin = os.path.expanduser("~/.local/bin")
        if npm_global not in env.get("PATH", ""):
            env["PATH"] = npm_global + ":" + env.get("PATH", "")
        if local_bin not in env.get("PATH", ""):
            env["PATH"] = local_bin + ":" + env.get("PATH", "")
        
        logger.info(f"[CLAUDE DEBUG] Node path: {shutil.which('node')}")
        logger.info(f"[CLAUDE DEBUG] NPM path: {shutil.which('npm')}")
        
        # Step 4: Execute
        start_time = time.time()
        logger.info(f"[CLAUDE DEBUG] Starting subprocess at {time.strftime('%H:%M:%S')}...")
        
        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout,
                env=env
            )
            
            # Step 5: Handle retry without tools if that failed
            if result.returncode != 0 and any(flag in (result.stderr or "") or flag in (result.stdout or "") for flag in ["allowedTools", "tools"]):
                logger.info("[CLAUDE DEBUG] Retrying without tools flags")
                cmd = [
                    claude_path, 
                    "-p", 
                    "--dangerously-skip-permissions", 
                    "--output-format", 
                    "text"
                ]
                result = subprocess.run(
                    cmd,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    timeout=timeout,
                    env=env
                )
            
            duration = time.time() - start_time
            logger.info(f"[CLAUDE DEBUG] Subprocess completed in {duration:.1f}s")
            logger.info(f"[CLAUDE DEBUG] Exit code: {result.returncode}")
            logger.info(f"[CLAUDE DEBUG] Stdout length: {len(result.stdout or '')} chars")
            logger.info(f"[CLAUDE DEBUG] Stderr length: {len(result.stderr or '')} chars")
            
            stdout_str = result.stdout or ""
            stderr_str = result.stderr or ""
            
            if stdout_str:
                logger.info(f"[CLAUDE DEBUG] Stdout preview: {stdout_str[:500]}")
            if stderr_str:
                logger.warning(f"[CLAUDE DEBUG] Stderr preview: {stderr_str[:500]}")
            
            combined_output = stdout_str + "\n" + stderr_str
            cleaned_output = ClaudeOutputParser.clean_output(combined_output)
            
            # Check for rate limit
            is_limited, reset_at = ClaudeService.parse_rate_limit(combined_output)
            
            if is_limited:
                logger.warning(f"[CLAUDE DEBUG] Rate limited! Reset at: {reset_at}")
            
            success = result.returncode == 0
            if check_success:
                success = success and ClaudeOutputParser.detect_success(cleaned_output)
            error = None
            if not success and not is_limited:
                error = stderr_str or cleaned_output or f"Process exited with code {result.returncode}"
            
            ret = {
                "success": success and not is_limited,
                "output": cleaned_output,
                "error": error,
                "is_rate_limited": is_limited,
                "rate_limit_reset": reset_at,
                "exit_code": result.returncode,
                "duration_seconds": duration
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"[CLAUDE DEBUG] Subprocess TIMED OUT after {duration:.1f}s")
            ret = {
                "success": False,
                "output": "",
                "error": f"Claude Code timed out after {timeout} seconds",
                "is_rate_limited": False,
                "rate_limit_reset": None,
                "exit_code": -1,
                "duration_seconds": duration
            }
        except FileNotFoundError as e:
            logger.error(f"[CLAUDE DEBUG] FileNotFoundError: {e}")
            ret = {
                "success": False,
                "output": "",
                "error": f"Claude Code binary not found: {e}",
                "is_rate_limited": False,
                "rate_limit_reset": None,
                "exit_code": -1,
                "duration_seconds": 0
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[CLAUDE DEBUG] Unexpected error: {type(e).__name__}: {e}")
            ret = {
                "success": False,
                "output": "",
                "error": f"Unexpected error: {type(e).__name__}: {e}",
                "is_rate_limited": False,
                "rate_limit_reset": None,
                "exit_code": -1,
                "duration_seconds": duration
            }
            
        ClaudeService._log_activity(prompt, cwd, timeout, ret)
        return ret
        
    @staticmethod
    def _log_activity(prompt: str, cwd: str, timeout: int, result_dict: dict):
        """Log the prompt and results to backend/logs/claude_activity.log"""
        try:
            log_dir = "/home/dev84/Work/aiAutomation/backend/logs"
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "claude_activity.log")
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"TIMESTAMP: {datetime.utcnow().isoformat()}Z\n")
                f.write(f"CWD: {cwd}\n")
                f.write(f"TIMEOUT: {timeout}s\n")
                f.write(f"DURATION: {result_dict.get('duration_seconds', 0):.1f}s\n")
                f.write(f"EXIT CODE: {result_dict.get('exit_code', -1)}\n")
                f.write(f"SUCCESS: {result_dict.get('success', False)}\n")
                f.write(f"RATE LIMITED: {result_dict.get('is_rate_limited', False)}\n")
                if result_dict.get('rate_limit_reset'):
                    f.write(f"RATE LIMIT RESET: {result_dict['rate_limit_reset'].isoformat()}Z\n")
                f.write(f"\nPROMPT:\n{prompt}\n")
                f.write(f"\n{'-'*40} OUTPUT {'-'*40}\n")
                f.write(result_dict.get('output', ''))
                if result_dict.get('error'):
                    f.write(f"\nERROR:\n{result_dict['error']}\n")
                f.write(f"\n{'='*80}\n")
        except Exception as e:
            logger.error(f"[CLAUDE DEBUG] Failed to write activity log: {e}")
            
    @staticmethod
    def parse_rate_limit(output: str) -> tuple[bool, datetime | None]:
        """
        Parse rate limit from Claude output.
        
        Patterns to match:
        1. "Resets in: X hours Y minutes" -> compute datetime
        2. "Resets in: Y minutes" -> compute datetime (no hours)
        3. "Your limit will reset at H:MM PM" -> parse time
        4. "resets H:MM PM" -> parse time
        5. "usage limit reached" -> rate limited but no time given, default 5 hours
        6. "session limit" -> same as above
        
        Returns: (is_rate_limited: bool, reset_at: datetime | None)
        """
        # If it is a valid JSON document (or contains one), it's not a rate limit message
        try:
            cleaned = output.strip()
            # Remove potential markdown block wrap if any
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```[a-zA-Z]*\n|```$", "", cleaned, flags=re.MULTILINE).strip()
            if (cleaned.startswith('{') and cleaned.endswith('}')) or (cleaned.startswith('[') and cleaned.endswith(']')):
                import json
                json.loads(cleaned)
                return False, None
            # Check if it contains a valid JSON object or array anywhere
            match_obj = re.search(r'\{[\s\S]*\}', cleaned)
            if match_obj:
                import json
                json.loads(match_obj.group())
                return False, None
            match_arr = re.search(r'\[[\s\S]*\]', cleaned)
            if match_arr:
                import json
                json.loads(match_arr.group())
                return False, None
        except Exception:
            pass

        output_lower = output.lower()
        is_limited = False
        
        # Avoid matching generic terms like 'rate limit' which are common in task descriptions
        limit_keywords = [
            "usage limit reached",
            "rate limit resets in",
            "rate limit exceeded",
            "resets in:",
            "limit will reset",
            "session limit",
            "hit your limit"
        ]
        if any(p in output_lower for p in limit_keywords):
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
            
        time_match = re.search(r'(?:reset at|resets at|reset will be at|limit will reset at|resets)\s*(\d+:\d+\s*(?:AM|PM|am|pm)?)', output, re.IGNORECASE)
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
                    now_local = datetime.now()
                    reset_at_local = datetime.combine(now_local.date(), parsed_time)
                    if reset_at_local <= now_local:
                        reset_at_local += timedelta(days=1)
                    
                    # Convert local to UTC
                    now_utc = datetime.utcnow()
                    offset = now_local - now_utc
                    reset_at = reset_at_local - offset
                    return True, reset_at
            except Exception:
                pass
                
        reset_at = datetime.utcnow() + timedelta(hours=5)
        return True, reset_at
