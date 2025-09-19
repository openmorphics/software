from __future__ import annotations
"""
EventFlow SAL high-level API

Provides stream_to_jsonl(uri, out, **options) used by the ef CLI.

Features:
- Supports URIs:
    - vision.dvs:///path/to/file.aedat4
    - audio.mic:///path/to/file.wav
    - imu.6dof:///path/to/file.csv
  Compatibility shim:
    - vision.dvs://file?format=jsonl&path=/path/to/events.jsonl (pass-through normalization)
- Deterministic JSONL emission with a header then event records
- Basic telemetry: counts, time span, dt stats, eps, simple drift estimate, jitter
"""

import json
import os
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

from eventflow_sal.open import open as open_source
from eventflow_sal.api.uri import parse_sensor_uri, SensorURI
from eventflow_sal.api.packet import EventPacket


def _ensure_dir(path: str) -> None:
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)


def _percentile(sorted_vals: List[int], q: float) -> int:
    if not sorted_vals:
        return 0
    if q <= 0:
        return int(sorted_vals[0])
    if q >= 1:
        return int(sorted_vals[-1])
    idx = int(round((len(sorted_vals) - 1) * q))
    return int(sorted_vals[idx])


def _write_header(fh, dims: List[str], units_value: str, metadata: Dict[str, Any]) -> None:
    header = {
        "schema_version": "0.1.0",
        "dims": dims,
        "units": {"time": "us", "value": units_value},
        "dtype": "f32",
        "layout": "coo",
        "metadata": metadata,
    }
    fh.write(json.dumps({"header": header}) + "\n")


def _write_event(fh, ts_ns: int, idx: List[int], val: float) -> None:
    # Header declares time in microseconds; keep event records in native ns and let downstream convert?
    # For SAL JSONL we emit native 'ts' in microseconds to match common datasets.
    ts_us = int(round(ts_ns / 1000.0))
    fh.write(json.dumps({"ts": ts_us, "idx": idx, "val": float(val)}) + "\n")


def _dims_for_scheme(scheme: str) -> Tuple[List[str], str]:
    if scheme == "vision.dvs://":
        return (["x", "y", "polarity"], "dimensionless")
    if scheme == "audio.mic://":
        return (["band"], "dB")
    if scheme == "imu.6dof://":
        return (["axis"], "mixed")  # accel: m/s^2, gyro: rad/s
    # Fallback
    return (["ch"], "dimensionless")


def _idx_for_packet(scheme: str, pkt: EventPacket) -> List[int]:
    if scheme == "vision.dvs://":
        x = int(pkt.meta.get("x", 0))
        y = int(pkt.meta.get("y", 0))
        pol = int(pkt.meta.get("polarity", 0))
        return [x, y, pol]
    # audio and imu are channel/axis indexed by packet.channel
    return [int(pkt.channel)]


def _normalize_existing_jsonl(in_path: str, out_path: str) -> Dict[str, Any]:
    """
    Pass-through normalization for an existing JSONL Event Tensor file.
    This preserves ordering and updates/ensures a header is present.
    """
    tele: Dict[str, Any] = {}
    _ensure_dir(out_path)
    host_t0 = time.monotonic_ns()
    with open(in_path, "r", encoding="utf-8") as fin, open(out_path, "w", encoding="utf-8") as fout:
        first = fin.readline()
        count = 0
        ts_min = None
        ts_max = None
        dt_prev = None
        dt_list: List[int] = []
        if first:
            try:
                obj = json.loads(first)
                if "header" in obj:
                    # Write header as-is
                    fout.write(first if first.endswith("\n") else first + "\n")
                else:
                    # Synthesize a minimal header if first line wasn't header
                    _write_header(fout, ["ch"], "dimensionless", {"source": "jsonl"})
                    # Process the first line as an event
                    ts_us = int(obj["ts"])
                    idx = list(obj.get("idx", []))
                    val = float(obj.get("val", 0.0))
                    _write_event(fout, ts_us * 1000, idx, val)
                    count += 1
                    ts_min = ts_us
                    ts_max = ts_us
                    dt_prev = ts_us
            except Exception:
                # Not JSON header, synthesize one and treat line as event
                _write_header(fout, ["ch"], "dimensionless", {"source": "jsonl"})
                try:
                    obj = json.loads(first)
                    ts_us = int(obj["ts"])
                    idx = list(obj.get("idx", []))
                    val = float(obj.get("val", 0.0))
                    _write_event(fout, ts_us * 1000, idx, val)
                    count += 1
                    ts_min = ts_us
                    ts_max = ts_us
                    dt_prev = ts_us
                except Exception:
                    pass
        for line in fin:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ts_us = int(rec["ts"])
            idx = list(rec.get("idx", []))
            val = float(rec.get("val", 0.0))
            _write_event(fout, ts_us * 1000, idx, val)
            count += 1
            if ts_min is None or ts_us < ts_min:
                ts_min = ts_us
            if ts_max is None or ts_us > ts_max:
                ts_max = ts_us
            if dt_prev is not None:
                dt_list.append(ts_us - dt_prev)
            dt_prev = ts_us
        # Telemetry
        dt_list_sorted = sorted(dt_list)
        duration_us = 0 if (ts_min is None or ts_max is None) else (ts_max - ts_min)
        eps = (count / (duration_us / 1_000_000.0)) if duration_us > 0 else 0.0
        # Clock summary (host vs sensor span); best-effort for file passthrough
        host_duration_ns = max(1, time.monotonic_ns() - host_t0)
        sensor_duration_ns = int(duration_us * 1000)
        drift_ppm_est = ((sensor_duration_ns - host_duration_ns) / float(host_duration_ns)) * 1e6 if host_duration_ns > 0 else 0.0
        # Jitter summary derived from dt distribution
        median_dt_us = dt_list_sorted[len(dt_list_sorted)//2] if dt_list_sorted else 0
        jitter_us = sorted(abs(dt - median_dt_us) for dt in dt_list_sorted)
        jitter_p50_us = jitter_us[len(jitter_us)//2] if jitter_us else 0
        jitter_p95_us = jitter_us[int(len(jitter_us)*0.95)] if jitter_us else 0
        jitter_p99_us = jitter_us[int(len(jitter_us)*0.99)] if jitter_us else 0
        tele = {
            "path_in": in_path,
            "path_out": out_path,
            "count": count,
            "ts_min_us": ts_min,
            "ts_max_us": ts_max,
            "duration_us": duration_us,
            "events_per_second": eps,
            "dt": {
                "count": len(dt_list_sorted),
                "p50_us": _percentile(dt_list_sorted, 0.50),
                "p95_us": _percentile(dt_list_sorted, 0.95),
                "p99_us": _percentile(dt_list_sorted, 0.99),
                "median_us": median_dt_us,
            },
            "clock": {
                "host_duration_ns": host_duration_ns,
                "sensor_duration_ns": sensor_duration_ns,
                "drift_ppm_est": drift_ppm_est,
                "jitter_p50_us": jitter_p50_us,
                "jitter_p95_us": jitter_p95_us,
                "jitter_p99_us": jitter_p99_us,
            },
            "normalized": True,
        }
    return tele


def stream_to_jsonl(
    uri: str,
    out: str,
    *,
    sample_rate: Optional[int] = None,   # reserved
    window_ms: Optional[int] = None,     # reserved
    hop_ms: Optional[int] = None,        # used for audio WAV (hop size)
    bands: Optional[int] = None,         # used for audio (band count)
    rate_limit_keps: Optional[int] = None,   # reserved
    overflow_policy: Optional[str] = None,   # reserved
    telemetry_out: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Normalize a SAL source to Event Tensor JSONL.
    Returns a telemetry dictionary; writes telemetry JSON when telemetry_out is provided.
    """
    # Compatibility shim for jsonl pass-through: vision.dvs://file?format=jsonl&path=...
    u = parse_sensor_uri(uri)
    params = dict(u.params) if hasattr(u, "params") else {}
    if u.scheme == "vision.dvs://" and params.get("format") == "jsonl" and "path" in params:
        tele = _normalize_existing_jsonl(params["path"], out)
        if telemetry_out:
            _ensure_dir(telemetry_out)
            with open(telemetry_out, "w", encoding="utf-8") as tf:
                json.dump(tele, tf, indent=2)
        return tele

    # Map public kwargs to driver constructor names
    overrides: Dict[str, Any] = {}
    if bands is not None:
        overrides["b"] = int(bands)
    if hop_ms is not None:
        overrides["hop"] = int(hop_ms) * 1_000_000  # ns

    # Open source via registry
    src = open_source(uri, **overrides)

    # Determine dims/units for header
    dims, units_value = _dims_for_scheme(u.scheme)

    # Telemetry accumulators
    host_t0 = time.monotonic_ns()
    host_t_last = host_t0
    count = 0
    ts_min_ns: Optional[int] = None
    ts_max_ns: Optional[int] = None
    dt_list_ns: List[int] = []
    prev_ts_ns: Optional[int] = None

    _ensure_dir(out)
    with open(out, "w", encoding="utf-8") as fh:
        _write_header(fh, dims, units_value, metadata=src.metadata())
        for pkt in src.subscribe():
            ts_ns = int(pkt.t_ns)
            idx = _idx_for_packet(u.scheme, pkt)
            val = float(pkt.value)
            _write_event(fh, ts_ns, idx, val)
            # Telemetry
            count += 1
            if ts_min_ns is None or ts_ns < ts_min_ns:
                ts_min_ns = ts_ns
            if ts_max_ns is None or ts_ns > ts_max_ns:
                ts_max_ns = ts_ns
            # Inter-arrival time (ns) in sensor time domain
            if prev_ts_ns is not None:
                dt_list_ns.append(ts_ns - prev_ts_ns)
            prev_ts_ns = ts_ns

    duration_ns = 0 if (ts_min_ns is None or ts_max_ns is None) else (ts_max_ns - ts_min_ns)
    duration_us = int(round(duration_ns / 1000.0))
    host_duration_ns = max(1, time.monotonic_ns() - host_t0)
    # Estimate drift as (sensor_span - host_span)/host_span in ppm (best-effort)
    drift_ppm_est = ((duration_ns - host_duration_ns) / float(host_duration_ns)) * 1e6 if host_duration_ns > 0 else 0.0
    dts_us_sorted = sorted(int(round(x / 1000.0)) for x in dt_list_ns if x > 0)
    eps = (count / (duration_us / 1_000_000.0)) if duration_us > 0 else 0.0
    median_dt_us = dts_us_sorted[len(dts_us_sorted)//2] if dts_us_sorted else 0
    jitter_us = sorted(abs(dt - median_dt_us) for dt in dts_us_sorted)
    jitter_p50_us = jitter_us[len(jitter_us)//2] if jitter_us else 0
    jitter_p95_us = jitter_us[int(len(jitter_us)*0.95)] if jitter_us else 0
    jitter_p99_us = jitter_us[int(len(jitter_us)*0.99)] if jitter_us else 0

    telemetry = {
        "uri": uri,
        "out": out,
        "count": count,
        "ts_min_us": None if ts_min_ns is None else int(round(ts_min_ns / 1000.0)),
        "ts_max_us": None if ts_max_ns is None else int(round(ts_max_ns / 1000.0)),
        "duration_us": duration_us,
        "events_per_second": eps,
        "dt": {
            "count": len(dts_us_sorted),
            "p50_us": _percentile(dts_us_sorted, 0.50),
            "p95_us": _percentile(dts_us_sorted, 0.95),
            "p99_us": _percentile(dts_us_sorted, 0.99),
            "median_us": median_dt_us,
        },
        "clock": {
            "host_duration_ns": host_duration_ns,
            "sensor_duration_ns": duration_ns,
            "drift_ppm_est": drift_ppm_est,
            "jitter_p50_us": jitter_p50_us,
            "jitter_p95_us": jitter_p95_us,
            "jitter_p99_us": jitter_p99_us,
        },
        "normalized": True,
    }

    if telemetry_out:
        _ensure_dir(telemetry_out)
        with open(telemetry_out, "w", encoding="utf-8") as tf:
            json.dump(telemetry, tf, indent=2)

    return telemetry


__all__ = ["stream_to_jsonl"]