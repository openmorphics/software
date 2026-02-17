from __future__ import annotations
import os
import json
from typing import Any, Dict, Optional

class LicenseCache:
    """Manages local storage of the license file."""
    def __init__(self, path: Optional[str] = None):
        self.path = path or os.path.expanduser("~/.eventflow/license.json")

    def install(self, license_data: Dict[str, Any]) -> None:
        """Save a new license file to the local cache."""
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        # Set restricted permissions (0600)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(license_data, f, indent=2, sort_keys=True)
        os.chmod(self.path, 0o600)

    def load(self) -> Optional[Dict[str, Any]]:
        """Load the license from local storage."""
        if not os.path.exists(self.path):
            return None
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def clear(self) -> None:
        """Remove the local license file."""
        if os.path.exists(self.path):
            os.remove(self.path)
