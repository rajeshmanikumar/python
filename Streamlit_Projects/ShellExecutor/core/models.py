import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ExecutionMode(str, Enum):
    NORMAL = "normal"      # Synchronous live streaming output
    ASYNC = "async"        # Asynchronous background thread execution
    NOHUP = "nohup"        # Remote nohup background process (PID tracking)


class CriticalityLevel(str, Enum):
    USUAL = "Usual"        # Safe, read-only, harmless
    WARNING = "Warning"    # State-changing, restarts, package installs
    DANGER = "Danger"      # Destructive, deletion, system impact


@dataclass
class ServerCredential:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    host: str = ""
    port: int = 22
    username: str = ""
    auth_type: str = "password"  # "password" or "key"
    password: Optional[str] = None
    private_key: Optional[str] = None
    passphrase: Optional[str] = None
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "auth_type": self.auth_type,
            "password": self.password,
            "private_key": self.private_key,
            "passphrase": self.passphrase,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServerCredential":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            host=data.get("host", ""),
            port=int(data.get("port", 22)),
            username=data.get("username", ""),
            auth_type=data.get("auth_type", "password"),
            password=data.get("password"),
            private_key=data.get("private_key"),
            passphrase=data.get("passphrase"),
            description=data.get("description", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )


@dataclass
class AIAnalysisResult:
    criticality: CriticalityLevel = CriticalityLevel.USUAL
    summary: str = ""
    risks: str = ""
    recommendation: str = ""
    model_used: str = "ollama"
    command_analyzed: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    is_fallback: bool = False


@dataclass
class ExecutionResult:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    command: str = ""
    mode: ExecutionMode = ExecutionMode.NORMAL
    server_name: str = ""
    server_host: str = ""
    status: str = "pending"  # pending, running, success, failed, rejected
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_sec: float = 0.0
    remote_pid: Optional[int] = None
    remote_log_file: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    completed_at: Optional[str] = None
    criticality: Optional[str] = None
