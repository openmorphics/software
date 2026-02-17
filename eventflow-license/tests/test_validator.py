import os
import json
import pytest
import tempfile
from datetime import datetime, timedelta
from eventflow_license import LicenseValidator, LicenseCache, LicenseInvalidError, LicenseExpiredError, FeatureNotLicensedError

@pytest.fixture
def temp_license_path():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_cache_install_load(temp_license_path):
    cache = LicenseCache(path=temp_license_path)
    data = {"features": {"pro": True}, "expires": "2099-01-01", "org": "Test", "signature": "SIG"}
    cache.install(data)
    
    loaded = cache.load()
    assert loaded == data
    assert (os.stat(temp_license_path).st_mode & 0o777) == 0o600

def test_validator_valid(temp_license_path):
    cache = LicenseCache(path=temp_license_path)
    expiry = (datetime.now() + timedelta(days=30)).isoformat()
    data = {
        "features": {"conformance": True},
        "expires": expiry,
        "org": "EventFlow",
        "signature": "DUMMY_SIG"
    }
    cache.install(data)
    
    validator = LicenseValidator(license_path=temp_license_path)
    assert validator.check("conformance") is True

def test_validator_expired(temp_license_path):
    cache = LicenseCache(path=temp_license_path)
    expiry = (datetime.now() - timedelta(days=1)).isoformat()
    data = {
        "features": {"conformance": True},
        "expires": expiry,
        "org": "EventFlow",
        "signature": "DUMMY_SIG"
    }
    cache.install(data)
    
    validator = LicenseValidator(license_path=temp_license_path)
    with pytest.raises(LicenseExpiredError):
        validator.check("conformance")

def test_validator_missing_feature(temp_license_path):
    cache = LicenseCache(path=temp_license_path)
    expiry = (datetime.now() + timedelta(days=30)).isoformat()
    data = {
        "features": {"conformance": False},
        "expires": expiry,
        "org": "EventFlow",
        "signature": "DUMMY_SIG"
    }
    cache.install(data)
    
    validator = LicenseValidator(license_path=temp_license_path)
    with pytest.raises(FeatureNotLicensedError):
        validator.check("conformance")

def test_validator_missing_license():
    validator = LicenseValidator(license_path="/non/existent/path.json")
    with pytest.raises(LicenseInvalidError):
        validator.check("any")
