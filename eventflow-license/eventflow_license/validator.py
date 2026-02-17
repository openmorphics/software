from __future__ import annotations
import json
import os
import base64
from datetime import datetime
from typing import Any, Dict, Optional
import nacl.signing
import nacl.encoding
from .errors import LicenseExpiredError, LicenseInvalidError, FeatureNotLicensedError

# Default public key for production (Ed25519)
# In a real implementation, this would be a constant
EVENTFLOW_PUBLIC_KEY = "S0m3PuB1icK3yF0rEv3ntF1owS1gninG12345678"

class LicenseValidator:
    def __init__(self, public_key: str = EVENTFLOW_PUBLIC_KEY, license_path: Optional[str] = None):
        self.public_key = public_key
        self.license_path = license_path or os.path.expanduser("~/.eventflow/license.json")
        self._license_data: Optional[Dict[str, Any]] = None

    def _load_license(self) -> Dict[str, Any]:
        if self._license_data is not None:
            return self._license_data

        if not os.path.exists(self.license_path):
            raise LicenseInvalidError("License file not found. Install a license using 'eventflow license install'.")

        try:
            with open(self.license_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise LicenseInvalidError(f"Failed to read license file: {e}")

        # Basic structure check
        required = ["features", "expires", "org", "signature"]
        for field in required:
            if field not in data:
                raise LicenseInvalidError(f"Malformed license: missing '{field}' field.")

        # Verify signature
        try:
            # Reconstruct the message that was signed (everything except signature)
            msg_data = {k: v for k, v in data.items() if k != "signature"}
            message = json.dumps(msg_data, sort_keys=True).encode("utf-8")
            
            # verify_key = nacl.signing.VerifyKey(self.public_key, encoder=nacl.encoding.Base64Encoder)
            # verify_key.verify(message, base64.b64decode(data["signature"]))
            
            # FOR MVP STUB: assume signature is "VALID" for now if it exists
            # In real code, uncomment the nacl lines above
            if not data["signature"]:
                raise LicenseInvalidError("Missing signature")
        except Exception as e:
            raise LicenseInvalidError(f"License signature verification failed: {e}")

        # Check expiry
        try:
            expiry = datetime.fromisoformat(data["expires"])
            if datetime.now() > expiry:
                raise LicenseExpiredError(f"License expired on {data['expires']}")
        except ValueError:
            raise LicenseInvalidError("Invalid expiry date format")

        self._license_data = data
        return data

    def check(self, feature: str) -> bool:
        """Check if a specific feature is enabled in the current license."""
        try:
            data = self._load_license()
            features = data.get("features", {})
            if features.get(feature) is True:
                return True
            raise FeatureNotLicensedError(f"Feature '{feature}' is not included in your license.")
        except (LicenseExpiredError, LicenseInvalidError, FeatureNotLicensedError):
            raise
        except Exception as e:
            raise LicenseInvalidError(f"Unexpected error during license check: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Return status of the current license."""
        try:
            data = self._load_license()
            return {
                "ok": True,
                "org": data.get("org"),
                "expires": data.get("expires"),
                "features": data.get("features", {})
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
