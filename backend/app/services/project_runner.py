import subprocess
import asyncio
import os
import socket
import signal
import sys
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class RunningProcess:
    def __init__(self, name: str, popen: subprocess.Popen, port: int, log_lines: list[str]):
        self.name = name            # "backend" | "frontend"
        self.popen = popen          # subprocess.Popen
        self.port = port
        self.log_lines = log_lines  # list[str], ring buffer


def read_stream(stream, log_buffer: list[str]):
    try:
        for line in iter(stream.readline, ""):
            log_buffer.append(line.rstrip("\n"))
            if len(log_buffer) > 1000:
                log_buffer.pop(0)
    except Exception as e:
        log_buffer.append(f"Error reading stream: {e}")
    finally:
        try:
            stream.close()
        except Exception:
            pass


def run_command_in_thread(cmd: list[str], cwd: str, log_buffer: list[str]) -> bool:
    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=os.setsid
        )
        for line in iter(process.stdout.readline, ""):
            log_buffer.append(line.rstrip("\n"))
            if len(log_buffer) > 1000:
                log_buffer.pop(0)
        process.stdout.close()
        return process.wait() == 0
    except Exception as e:
        log_buffer.append(f"Error running command {cmd}: {e}")
        return False


class ProjectRunner:
    """Manages running generated projects on localhost. One run set per project."""
    _runs: dict[str, dict] = {}   # project_id -> {"backend": RunningProcess, "frontend": RunningProcess, "status": str, "install_logs": list[str]}

    @staticmethod
    def find_free_port(start: int = 8100) -> int:
        """Find an open TCP port starting from `start`."""
        port = start
        while port < start + 500:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", port)) != 0:
                    return port
            port += 1
        raise RuntimeError("No free port found")

    @classmethod
    def detect_stack(cls, project_dir: str) -> dict:
        """Inspect project to decide how to install + run."""
        has_backend = False
        backend_dir = None
        backend_install = []
        backend_start = []
        
        has_frontend = False
        frontend_dir = None
        frontend_install = []
        frontend_start = []

        # Check Python backend
        backend_candidate_dir = os.path.join(project_dir, "backend")
        if os.path.isdir(backend_candidate_dir) and os.path.isfile(os.path.join(backend_candidate_dir, "requirements.txt")):
            has_backend = True
            backend_dir = backend_candidate_dir
        elif os.path.isfile(os.path.join(project_dir, "requirements.txt")):
            has_backend = True
            backend_dir = project_dir

        if has_backend:
            venv_dir = os.path.join(project_dir, ".venv")
            pip_path = os.path.join(venv_dir, "bin", "pip")
            python_path = os.path.join(venv_dir, "bin", "python")
            uvicorn_path = os.path.join(venv_dir, "bin", "uvicorn")
            
            backend_install = [pip_path, "install", "-r", "requirements.txt"]
            
            # Detect main module
            if os.path.isfile(os.path.join(backend_dir, "app", "main.py")):
                main_module = "app.main:app"
            elif os.path.isfile(os.path.join(backend_dir, "main.py")):
                main_module = "main:app"
            else:
                main_module = "app.main:app" # Fallback
                
            backend_start = [uvicorn_path, main_module, "--port", "{PORT}"]

        # Check Node frontend
        frontend_candidate_dir = os.path.join(project_dir, "frontend")
        if os.path.isdir(frontend_candidate_dir) and os.path.isfile(os.path.join(frontend_candidate_dir, "package.json")):
            pkg_path = os.path.join(frontend_candidate_dir, "package.json")
            try:
                import json
                with open(pkg_path, "r") as f:
                    pkg = json.load(f)
                if "dev" in pkg.get("scripts", {}):
                    has_frontend = True
                    frontend_dir = frontend_candidate_dir
            except Exception:
                pass
        elif os.path.isfile(os.path.join(project_dir, "package.json")):
            pkg_path = os.path.join(project_dir, "package.json")
            try:
                import json
                with open(pkg_path, "r") as f:
                    pkg = json.load(f)
                if "dev" in pkg.get("scripts", {}):
                    has_frontend = True
                    frontend_dir = project_dir
            except Exception:
                pass

        if has_frontend:
            frontend_install = ["npm", "install"]
            frontend_start = ["npm", "run", "dev", "--", "--port", "{PORT}"]

        return {
            "has_backend": has_backend,
            "backend_dir": backend_dir,
            "backend_install": backend_install,
            "backend_start": backend_start,
            "has_frontend": has_frontend,
            "frontend_dir": frontend_dir,
            "frontend_install": frontend_install,
            "frontend_start": frontend_start
        }

    @classmethod
    async def install(cls, project_id: UUID, project_dir: str) -> dict:
        """Run dependency installs (backend + frontend) via asyncio.to_thread."""
        pid_str = str(project_id)
        if pid_str not in cls._runs:
            cls._runs[pid_str] = {
                "status": "stopped",
                "install_logs": [],
                "backend": None,
                "frontend": None
            }
        
        cls._runs[pid_str]["status"] = "installing"
        log_buffer = cls._runs[pid_str]["install_logs"]
        log_buffer.clear()

        stack = cls.detect_stack(project_dir)
        errors = []

        if stack["has_backend"]:
            log_buffer.append("=== Installing backend dependencies ===")
            venv_dir = os.path.join(project_dir, ".venv")
            log_buffer.append(f"Creating virtualenv at {venv_dir}...")
            venv_cmd = [sys.executable, "-m", "venv", venv_dir]
            ok = await asyncio.to_thread(run_command_in_thread, venv_cmd, project_dir, log_buffer)
            if not ok:
                errors.append("Failed to create virtual environment")
            else:
                log_buffer.append("Installing requirements via pip...")
                ok = await asyncio.to_thread(run_command_in_thread, stack["backend_install"], stack["backend_dir"], log_buffer)
                if not ok:
                    errors.append("Failed to install requirements")

        if stack["has_frontend"]:
            log_buffer.append("=== Installing frontend dependencies ===")
            log_buffer.append("Running npm install...")
            ok = await asyncio.to_thread(run_command_in_thread, stack["frontend_install"], stack["frontend_dir"], log_buffer)
            if not ok:
                errors.append("Failed to install frontend node packages")

        if errors:
            cls._runs[pid_str]["status"] = "install_failed"
            log_buffer.append(f"Installation failed with errors: {errors}")
            return {"success": False, "errors": errors}

        cls._runs[pid_str]["status"] = "installed"
        log_buffer.append("=== Dependency installation complete ===")
        return {"success": True, "errors": []}

    @classmethod
    async def start(cls, project_id: UUID, project_dir: str) -> dict:
        """Launch backend (and frontend) as subprocess.Popen with stdout/stderr piped."""
        await cls.stop(project_id)

        pid_str = str(project_id)
        if pid_str not in cls._runs:
            cls._runs[pid_str] = {
                "status": "starting",
                "install_logs": [],
                "backend": None,
                "frontend": None
            }

        stack = cls.detect_stack(project_dir)
        
        backend_url = None
        frontend_url = None
        
        try:
            from app.core.config import settings
            start_port = settings.RUNNER_PORT_START
        except Exception:
            start_port = 8100

        # Launch Backend
        if stack["has_backend"]:
            b_port = cls.find_free_port(start_port)
            start_port = b_port + 1
            cmd = [arg.replace("{PORT}", str(b_port)) for arg in stack["backend_start"]]
            
            log_buffer = []
            try:
                popen = subprocess.Popen(
                    cmd,
                    cwd=stack["backend_dir"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    preexec_fn=os.setsid
                )
                running_b = RunningProcess("backend", popen, b_port, log_buffer)
                cls._runs[pid_str]["backend"] = running_b
                asyncio.create_task(asyncio.to_thread(read_stream, popen.stdout, log_buffer))
                backend_url = f"http://localhost:{b_port}"
            except Exception as e:
                log_buffer.append(f"Failed to start backend: {e}")

        # Launch Frontend
        if stack["has_frontend"]:
            f_port = cls.find_free_port(start_port)
            cmd = [arg.replace("{PORT}", str(f_port)) for arg in stack["frontend_start"]]
            
            log_buffer = []
            try:
                popen = subprocess.Popen(
                    cmd,
                    cwd=stack["frontend_dir"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    preexec_fn=os.setsid
                )
                running_f = RunningProcess("frontend", popen, f_port, log_buffer)
                cls._runs[pid_str]["frontend"] = running_f
                asyncio.create_task(asyncio.to_thread(read_stream, popen.stdout, log_buffer))
                frontend_url = f"http://localhost:{f_port}"
            except Exception as e:
                log_buffer.append(f"Failed to start frontend: {e}")

        cls._runs[pid_str]["status"] = "running"
        return {
            "backend_url": backend_url,
            "frontend_url": frontend_url,
            "status": "running"
        }

    @classmethod
    async def stop(cls, project_id: UUID) -> dict:
        """Terminate backend + frontend processes for a project. SIGTERM then SIGKILL."""
        pid_str = str(project_id)
        if pid_str not in cls._runs:
            return {"status": "stopped"}

        run = cls._runs[pid_str]
        for name in ["backend", "frontend"]:
            proc = run.get(name)
            if proc and proc.popen:
                popen = proc.popen
                try:
                    os.killpg(os.getpgid(popen.pid), signal.SIGTERM)
                except Exception:
                    try:
                        os.kill(popen.pid, signal.SIGTERM)
                    except Exception:
                        pass

                # Wait up to 2 seconds
                for _ in range(20):
                    await asyncio.sleep(0.1)
                    if popen.poll() is not None:
                        break
                else:
                    try:
                        os.killpg(os.getpgid(popen.pid), signal.SIGKILL)
                    except Exception:
                        try:
                            os.kill(popen.pid, signal.SIGKILL)
                        except Exception:
                            pass
        
        run["status"] = "stopped"
        run["backend"] = None
        run["frontend"] = None
        return {"status": "stopped"}

    @classmethod
    def status(cls, project_id: UUID) -> dict:
        """Return run status, URLs, and alive status."""
        pid_str = str(project_id)
        if pid_str not in cls._runs:
            return {
                "status": "stopped",
                "backend_url": None,
                "frontend_url": None,
                "ports": {},
                "alive": False
            }
        run = cls._runs[pid_str]
        
        backend_alive = False
        frontend_alive = False
        
        b_proc = run.get("backend")
        if b_proc and b_proc.popen and b_proc.popen.poll() is None:
            backend_alive = True
        f_proc = run.get("frontend")
        if f_proc and f_proc.popen and f_proc.popen.poll() is None:
            frontend_alive = True
            
        ports = {}
        if b_proc:
            ports["backend"] = b_proc.port
        if f_proc:
            ports["frontend"] = f_proc.port

        backend_url = f"http://localhost:{b_proc.port}" if b_proc else None
        frontend_url = f"http://localhost:{f_proc.port}" if f_proc else None

        alive = backend_alive or frontend_alive
        status_str = run.get("status", "stopped")
        if alive and status_str != "running":
            status_str = "running"
        elif not alive and status_str in ("running", "starting"):
            status_str = "stopped"

        return {
            "status": status_str,
            "backend_url": backend_url,
            "frontend_url": frontend_url,
            "ports": ports,
            "alive": alive
        }

    @classmethod
    def get_logs(cls, project_id: UUID, source: str = "backend", tail: int = 200) -> list[str]:
        """Return last `tail` log lines for backend or frontend."""
        pid_str = str(project_id)
        if pid_str not in cls._runs:
            return []
        
        run = cls._runs[pid_str]
        if source == "install":
            logs = run.get("install_logs", [])
        else:
            proc = run.get(source)
            logs = proc.log_lines if proc else []
        
        return logs[-tail:]
