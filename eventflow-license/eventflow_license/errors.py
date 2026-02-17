class LicenseError(Exception):
    """Base class for license errors."""
    pass

class LicenseInvalidError(LicenseError):
    """Raised when the license file is malformed or the signature is invalid."""
    pass

class LicenseExpiredError(LicenseError):
    """Raised when the license has reached its expiration date."""
    pass

class FeatureNotLicensedError(LicenseError):
    """Raised when the user attempts to use a feature not included in their license."""
    pass
