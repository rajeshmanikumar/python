import io
import os
import time
import shlex
import threading
from datetime import datetime
from typing import Callable, Dict, Optional, Tuple
import paramiko
from core.models import ServerCredential, ExecutionResult, ExecutionMode

# Global registry for async background jobs
ACTIVE_JOBS: Dict[str, ExecutionResult] = {}


class SSHConnectionError(Exception):
    pass


class SSHManager:
    def __init__(self):
        self._clients: Dict[str, paramiko.SSHClient] = {}

    def _get_client_key(self, cred: ServerCredential) -> str:
        return f"{cred.username}@{cred.host}:{cred.port}"

    def connect(self, cred: ServerCredential, timeout: int = 10) -> paramiko.SSHClient:
        """Create and authenticate a paramiko SSHClient."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": cred.host,
            "port": cred.port,
            "username": cred.username,
            "timeout": timeout,
            "banner_timeout": timeout,
            "auth_timeout": timeout,
        }

        if cred.auth_type == "key" and cred.private_key:
            key_file = io.StringIO(cred.private_key.strip())
            pkey = None
            passphrase = cred.passphrase if cred.passphrase else None

            # Attempt common key types
            for key_class in [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.DSSKey]:
                try:
                    key_file.seek(0)
                    pkey = key_class.from_private_key(key_file, password=passphrase)
                    break
                except Exception:
                    continue

            if not pkey:
                raise SSHConnectionError("Failed to parse private key. Ensure valid PEM/OpenSSH format.")
            connect_kwargs["pkey"] = pkey
        else:
            connect_kwargs["password"] = cred.password
            connect_kwargs["look_for_keys"] = False
            connect_kwargs["allow_agent"] = False

        try:
            client.connect(**connect_kwargs)
            return client
        except Exception as e:
            raise SSHConnectionError(f"SSH Connection Failed: {str(e)}")

    def test_connection(self, cred: ServerCredential) -> Tuple[bool, str, dict]:
        """Test SSH connection and fetch remote host metadata."""
        start_time = time.time()
        try:
            client = self.connect(cred, timeout=6)
            latency_ms = round((time.time() - start_time) * 1000, 1)

            # Probe remote system info
            stdin, stdout, stderr = client.exec_command(
                "uname -srm; whoami; uptime -p 2>/dev/null || uptime",
                timeout=5
            )
            output = stdout.read().decode("utf-8", errors="replace").strip().splitlines()
            client.close()

            sys_info = {
                "os_kernel": output[0] if len(output) > 0 else "Unknown",
                "logged_as": output[1] if len(output) > 1 else cred.username,
                "uptime": output[2] if len(output) > 2 else "Unknown",
                "latency_ms": latency_ms,
            }
            return True, f"Connected successfully! (Latency: {latency_ms}ms)", sys_info
        except Exception as e:
            return False, str(e), {}

    def execute_sync(
        self,
        cred: ServerCredential,
        command: str,
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> ExecutionResult:
        """
        Executes a command synchronously and streams output line-by-line via stream_callback.
        """
        job = ExecutionResult(
            command=command,
            mode=ExecutionMode.NORMAL,
            server_name=cred.name,
            server_host=cred.host,
            status="running"
        )

        start_time = time.time()
        full_stdout = []
        full_stderr = []

        try:
            client = self.connect(cred)
            transport = client.get_transport()
            if not transport:
                raise SSHConnectionError("SSH transport unavailable.")

            channel = transport.open_session()
            channel.set_combine_stderr(False)
            channel.get_pty()  # Request pseudo-terminal for natural shell output formatting
            channel.exec_command(command)

            while not channel.exit_status_ready() or channel.recv_ready() or channel.recv_stderr_ready():
                if channel.recv_ready():
                    chunk = channel.recv(4096).decode("utf-8", errors="replace")
                    if chunk:
                        full_stdout.append(chunk)
                        if stream_callback:
                            stream_callback(chunk)

                if channel.recv_stderr_ready():
                    chunk = channel.recv_stderr(4096).decode("utf-8", errors="replace")
                    if chunk:
                        full_stderr.append(chunk)
                        if stream_callback:
                            stream_callback(chunk)

                time.sleep(0.02)

            exit_code = channel.recv_exit_status()
            client.close()

            job.exit_code = exit_code
            job.stdout = "".join(full_stdout)
            job.stderr = "".join(full_stderr)
            job.duration_sec = round(time.time() - start_time, 2)
            job.status = "success" if exit_code == 0 else "failed"
            job.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        except Exception as e:
            job.status = "failed"
            job.stderr = str(e)
            job.duration_sec = round(time.time() - start_time, 2)
            job.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if stream_callback:
                stream_callback(f"\n[EXECUTION ERROR]: {str(e)}\n")

        return job

    def execute_nohup(self, cred: ServerCredential, command: str) -> ExecutionResult:
        """
        Executes a command via nohup in background on remote server and tracks PID & log file.
        """
        ts = int(time.time())
        log_file = f"/tmp/shellexec_{ts}.log"

        # Safe single-quote wrapper for command
        safe_cmd = command.replace("'", "'\"'\"'")
        nohup_script = f"nohup bash -c '{safe_cmd}' > {log_file} 2>&1 & echo $!"

        job = ExecutionResult(
            command=command,
            mode=ExecutionMode.NOHUP,
            server_name=cred.name,
            server_host=cred.host,
            status="running",
            remote_log_file=log_file
        )

        start_time = time.time()
        try:
            client = self.connect(cred)
            stdin, stdout, stderr = client.exec_command(nohup_script, timeout=10)
            pid_str = stdout.read().decode("utf-8", errors="replace").strip()
            err_str = stderr.read().decode("utf-8", errors="replace").strip()
            client.close()

            if pid_str.isdigit():
                job.remote_pid = int(pid_str)
                job.stdout = f"Command launched in background via nohup!\nRemote PID: {pid_str}\nLog file: {log_file}\n"
                job.status = "running"
            else:
                job.stdout = pid_str
                job.stderr = err_str
                job.status = "failed"

            job.duration_sec = round(time.time() - start_time, 2)
            job.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        except Exception as e:
            job.status = "failed"
            job.stderr = str(e)
            job.duration_sec = round(time.time() - start_time, 2)
            job.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ACTIVE_JOBS[job.job_id] = job
        return job

    def execute_async(self, cred: ServerCredential, command: str) -> ExecutionResult:
        """
        Executes a command asynchronously in a background Python thread.
        Registers the job in ACTIVE_JOBS.
        """
        job = ExecutionResult(
            command=command,
            mode=ExecutionMode.ASYNC,
            server_name=cred.name,
            server_host=cred.host,
            status="running"
        )
        ACTIVE_JOBS[job.job_id] = job

        def worker():
            start_time = time.time()
            try:
                client = self.connect(cred)
                stdin, stdout, stderr = client.exec_command(command, get_pty=True)
                out = stdout.read().decode("utf-8", errors="replace")
                err = stderr.read().decode("utf-8", errors="replace")
                exit_code = stdout.channel.recv_exit_status()
                client.close()

                job.exit_code = exit_code
                job.stdout = out
                job.stderr = err
                job.status = "success" if exit_code == 0 else "failed"
            except Exception as e:
                job.status = "failed"
                job.stderr = str(e)
            finally:
                job.duration_sec = round(time.time() - start_time, 2)
                job.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        return job

    def tail_remote_log(self, cred: ServerCredential, log_path: str, lines: int = 100) -> str:
        """Fetch the last N lines of a remote log file."""
        try:
            client = self.connect(cred, timeout=5)
            cmd = f"tail -n {lines} {shlex.quote(log_path)} 2>/dev/null || cat {shlex.quote(log_path)} 2>/dev/null || echo '[Log file not found or empty]'"
            stdin, stdout, stderr = client.exec_command(cmd, timeout=5)
            output = stdout.read().decode("utf-8", errors="replace")
            client.close()
            return output
        except Exception as e:
            return f"Error reading log: {str(e)}"

    def check_remote_pid(self, cred: ServerCredential, pid: int) -> Tuple[bool, str]:
        """Check if remote process PID is still running."""
        try:
            client = self.connect(cred, timeout=5)
            cmd = f"ps -p {pid} -o pid,stat,time,args --no-headers"
            stdin, stdout, stderr = client.exec_command(cmd, timeout=5)
            output = stdout.read().decode("utf-8", errors="replace").strip()
            client.close()
            if output:
                return True, f"Running: {output}"
            return False, "Process terminated or PID not found."
        except Exception as e:
            return False, f"Check error: {str(e)}"

    def kill_remote_pid(self, cred: ServerCredential, pid: int, signal: int = 15) -> Tuple[bool, str]:
        """Terminate a remote background process."""
        try:
            client = self.connect(cred, timeout=5)
            cmd = f"kill -{signal} {pid} 2>&1"
            stdin, stdout, stderr = client.exec_command(cmd, timeout=5)
            output = stdout.read().decode("utf-8", errors="replace").strip()
            client.close()
            if output:
                return False, f"Kill response: {output}"
            return True, f"Process {pid} signaled with SIG{signal} successfully."
        except Exception as e:
            return False, f"Kill error: {str(e)}"


# Singleton SSH manager
ssh_manager = SSHManager()
