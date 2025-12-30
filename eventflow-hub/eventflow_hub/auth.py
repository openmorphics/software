from __future__ import annotations
import os
import hashlib
import secrets
from typing import Optional

class TokenProvider:
    def __init__(self, token: str | None = None):
        self._token = token or self._load_token()

    def get(self) -> str | None:
        return self._token

    def _load_token(self) -> str | None:
        # Try environment variable first
        token = os.environ.get("EF_HUB_TOKEN")
        if token:
            return token

        # Try token file
        token_file = os.path.expanduser("~/.ef/hub_token")
        if os.path.isfile(token_file):
            try:
                with open(token_file, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception:
                pass

        return None

class AuthManager:
    def __init__(self, token_store_path: str = "~/.ef/hub_users.json"):
        self.token_store_path = os.path.expanduser(token_store_path)
        self._ensure_store()

    def _ensure_store(self):
        os.makedirs(os.path.dirname(self.token_store_path), exist_ok=True)
        if not os.path.isfile(self.token_store_path):
            with open(self.token_store_path, "w", encoding="utf-8") as f:
                f.write("{}")

    def authenticate(self, token: str) -> Optional[str]:
        """Return username if token is valid, None otherwise"""
        try:
            import json
            with open(self.token_store_path, "r", encoding="utf-8") as f:
                users = json.load(f)
            for username, stored_token in users.items():
                if stored_token == token:
                    return username
        except Exception:
            pass
        return None

    def create_token(self, username: str) -> str:
        """Create a new token for username"""
        token = secrets.token_hex(32)
        try:
            import json
            with open(self.token_store_path, "r", encoding="utf-8") as f:
                users = json.load(f)
            users[username] = token
            with open(self.token_store_path, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=2)
        except Exception:
            pass
        return token
