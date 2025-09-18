"""
Sensor Abstraction Layer (SAL) stubs
"""
__all__ = ["open", "close", "read"]

def open(uri: str, **kwargs):
    raise NotImplementedError("SAL.open stub")

def read(source, n=None, duration=None):
    raise NotImplementedError("SAL.read stub")

def close(source):
    raise NotImplementedError("SAL.close stub")
