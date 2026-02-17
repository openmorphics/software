from __future__ import annotations
import functools
import sys
from typing import Any, Callable, TypeVar
from eventflow_license import LicenseValidator, LicenseError

F = TypeVar("F", bound=Callable[..., Any])

def requires_license(feature: str, tier: str = "Pro"):
    """
    Decorator for CLI commands that require a specific license feature.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                validator = LicenseValidator()
                if validator.check(feature):
                    return func(*args, **kwargs)
            except LicenseError as e:
                # Import here to avoid circular dependency
                from .main import CLI_JSON, _emit_json
                
                error_msg = f"Feature '{feature}' requires {tier} license. {e}"
                upgrade_msg = f"Visit https://eventflow.dev/pricing to upgrade."
                
                if CLI_JSON:
                    _emit_json({
                        "ok": False,
                        "error": error_msg,
                        "upgrade_url": "https://eventflow.dev/pricing",
                        "exit_code": 3
                    })
                else:
                    print(f"error: {error_msg}", file=sys.stderr)
                    print(upgrade_msg, file=sys.stderr)
                
                sys.exit(3)
            except Exception as e:
                print(f"unexpected license check failure: {e}", file=sys.stderr)
                sys.exit(3)
        return wrapper # type: ignore
    return decorator
