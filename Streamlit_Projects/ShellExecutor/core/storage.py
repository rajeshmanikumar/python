import os
import json
from pathlib import Path
from typing import List, Optional
from cryptography.fernet import Fernet
from core.models import ServerCredential

DATA_DIR = Path(__file__).parent.parent / "data"
KEY_FILE = DATA_DIR / ".secret.key"
SERVERS_FILE = DATA_DIR / "servers.json"


class CredentialStorage:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._cipher = self._init_cipher()

    def _init_cipher(self) -> Fernet:
        """Initialize or load the encryption key."""
        if not KEY_FILE.exists():
            key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as f:
                f.write(key)
        else:
            with open(KEY_FILE, "rb") as f:
                key = f.read().strip()
        return Fernet(key)

    def _encrypt(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        return self._cipher.encrypt(text.encode("utf-8")).decode("utf-8")

    def _decrypt(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        try:
            return self._cipher.decrypt(text.encode("utf-8")).decode("utf-8")
        except Exception:
            return None

    def list_servers(self) -> List[ServerCredential]:
        """Load and decrypt all stored servers."""
        if not SERVERS_FILE.exists():
            return []
        try:
            with open(SERVERS_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
            servers = []
            for rec in records:
                # Decrypt sensitive fields
                rec["password"] = self._decrypt(rec.get("password"))
                rec["private_key"] = self._decrypt(rec.get("private_key"))
                rec["passphrase"] = self._decrypt(rec.get("passphrase"))
                servers.append(ServerCredential.from_dict(rec))
            return servers
        except Exception as e:
            print(f"Error loading servers: {e}")
            return []

    def get_server(self, server_id: str) -> Optional[ServerCredential]:
        """Fetch a single server by ID."""
        for server in self.list_servers():
            if server.id == server_id:
                return server
        return None

    def save_server(self, server: ServerCredential) -> None:
        """Save a new server or update an existing one."""
        servers = self.list_servers()
        existing_idx = next((i for i, s in enumerate(servers) if s.id == server.id), None)
        
        if existing_idx is not None:
            servers[existing_idx] = server
        else:
            servers.append(server)
            
        self._persist(servers)

    def delete_server(self, server_id: str) -> bool:
        """Delete a server by ID."""
        servers = self.list_servers()
        new_servers = [s for s in servers if s.id != server_id]
        if len(new_servers) < len(servers):
            self._persist(new_servers)
            return True
        return False

    def _persist(self, servers: List[ServerCredential]) -> None:
        """Encrypt and write servers to disk."""
        records = []
        for s in servers:
            d = s.to_dict()
            d["password"] = self._encrypt(s.password)
            d["private_key"] = self._encrypt(s.private_key)
            d["passphrase"] = self._encrypt(s.passphrase)
            records.append(d)
        with open(SERVERS_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)


# Global singleton instance
storage = CredentialStorage()
