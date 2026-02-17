import json
import os
import subprocess
import pytest
import tempfile
from datetime import datetime, timedelta

def run_cli(*args):
    """Helper to run the repo-local CLI."""
    # Ensure we use the local packages
    env = os.environ.copy()
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ppath = [
        os.path.join(root, "eventflow-core"),
        os.path.join(root, "eventflow-sal"),
        os.path.join(root, "eventflow-backends"),
        os.path.join(root, "eventflow-cli"),
        os.path.join(root, "eventflow-license"),
        os.path.join(root, "eventflow-conformance"),
    ]
    env["PYTHONPATH"] = os.pathsep.join(ppath)
    
    cmd = ["python3", os.path.join(root, "eventflow-cli", "ef.py")] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)

def test_version():
    res = run_cli("version")
    assert res.returncode == 0
    assert "0.2.0" in res.stdout

def test_conformance_gated_no_license():
    # Ensure no license file exists in the test env
    # For this test, we rely on the default path not having a license
    # or we can point it to a non-existent file if our validator supported ENV overrides for path
    # Since it uses os.path.expanduser("~/.eventflow/license.json"), we might need to mock home
    
    with tempfile.TemporaryDirectory() as tmp_home:
        env = os.environ.copy()
        env["HOME"] = tmp_home
        
        # Create a dummy EIR
        eir_path = os.path.join(tmp_home, "test.eir.json")
        with open(eir_path, "w") as f:
            json.dump({"profile": "BASE", "nodes": []}, f)
            
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cmd = ["python3", os.path.join(root, "eventflow-cli", "ef.py"), "verify-conformance", "--eir", eir_path]
        
        ppath = [
            os.path.join(root, "eventflow-core"),
            os.path.join(root, "eventflow-sal"),
            os.path.join(root, "eventflow-backends"),
            os.path.join(root, "eventflow-cli"),
            os.path.join(root, "eventflow-license"),
            os.path.join(root, "eventflow-conformance"),
        ]
        env["PYTHONPATH"] = os.pathsep.join(ppath)
        
        res = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        assert res.returncode == 3
        assert "requires Pro license" in res.stderr

def test_conformance_with_valid_license():
    with tempfile.TemporaryDirectory() as tmp_home:
        env = os.environ.copy()
        env["HOME"] = tmp_home
        
        # Install dummy license
        license_dir = os.path.join(tmp_home, ".eventflow")
        os.makedirs(license_dir)
        license_path = os.path.join(license_dir, "license.json")
        
        expiry = (datetime.now() + timedelta(days=365)).isoformat()
        license_data = {
            "features": {"conformance": True, "pro_backends": True},
            "expires": expiry,
            "org": "TestOrg",
            "signature": "VALID_STUB"
        }
        with open(license_path, "w") as f:
            json.dump(license_data, f)
            
        # Create a dummy EIR
        eir_path = os.path.join(tmp_home, "test.eir.json")
        with open(eir_path, "w") as f:
            json.dump({"profile": "BASE", "nodes": []}, f)
            
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cmd = ["python3", os.path.join(root, "eventflow-cli", "ef.py"), "verify-conformance", "--eir", eir_path]
        
        ppath = [
            os.path.join(root, "eventflow-core"),
            os.path.join(root, "eventflow-sal"),
            os.path.join(root, "eventflow-backends"),
            os.path.join(root, "eventflow-cli"),
            os.path.join(root, "eventflow-license"),
            os.path.join(root, "eventflow-conformance"),
        ]
        env["PYTHONPATH"] = os.pathsep.join(ppath)
        
        res = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        assert res.returncode == 0
        assert "PASSED" in res.stdout
