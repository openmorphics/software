"""
EventFlow SAL: minimal Sensor Abstraction Layer.

This package writes Event Tensor JSONL (writer-only). Each file begins with:
{ "header": { "schema_version":"0.1.0", "dims":["time","channel","value"], "units": {"time":"<s|ms|us|ns>","value":"dimensionless"}, "dtype":"f32", "layout":"coo", "metadata":{"source":"<str>","created":"<iso8601>"}} }
Followed by records:
{ "ts": <int_time_in_unit>, "idx": [<int_channel>], "val": <float_value> }
"""

from .sal import Stream
from .tensor import write_event_tensor_jsonl

__all__ = ["Stream", "write_event_tensor_jsonl"]