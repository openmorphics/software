"""
EventFlow SAL API v0.1

Provides high-level functions to convert heterogeneous sensor inputs into
standardized Event Tensor JSONL streams with deterministic ordering.

Supported sources (v0.1):
- vision.dvs file sources:
    - format=jsonl (pass-through to normalized JSONL with ordering checks)
    - format=aedat3|aedat4 (placeholder requiring external decoder; see notes)
- audio.mic file sources:
    - WAV file path with streaming STFT to band events (JSONL)

Public API:
- stream_to_jsonl(uri: str, out_path: str, **kwargs) -> None
- parse_uri(uri: str) -> (scheme: str, params: dict)

Notes:
- AEDAT decoding is not implemented in-core. For full AEDAT support, integrate a decoder
  (e.g., vendor SDK) and plumb decoded events into Event Tensor records before normalization.
"""

from __future__ import annotations

import json
import math
import os
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Optional numpy acceleration for STFT
try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore


@dataclass
class SALConfig:
    rate_limit_keps: Optional[int] = None
    overflow_policy: str = "drop_tail"  # "drop_head" | "drop_tail" | "block"
    # Audio defaults
    sample_rate: int = 16000
    window_ms: int = 20
    hop_ms: int = 10
    bands: int = 32
    dtype: str = "f16"  # f32 | f16 | i16 | u8 (for audio magnitude)
    units_value: str = "dB"  # "dB" or "power"


def parse_uri(uri: str) -> Tuple[str, Dict[str, str]]:
    """
    Parse a SAL URI into a scheme and parameter map.
    Example:
      vision.dvs://file?format=jsonl&path=/data/events.jsonl
      audio.mic://file?path=/data/audio.wav&window_ms=20&hop_ms=10
    """
    parsed = urllib.parse.urlparse(uri)
    scheme = parsed.scheme  # e.g., "vision.dvs" or "audio.mic"
    q = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    # Flatten single valued
    params: Dict[str, str] = {}
    for k, v in q.items():
        params[k] = v[0] if v else ""
    # 'path' may appear in query; host part can also be used for some cases
    if "path" not in params and parsed.netloc and parsed.netloc != "file":
        params["path"] = parsed.netloc + (parsed.path or "")
    elif "path" not in params:
        params["path"] = parsed.path
    return scheme, params


def _write_jsonl_header(fh, header: Dict[str, Any]) -> None:
    fh.write(json.dumps({"header": header}, separators=(",", ":")) + "\n")


def _write_jsonl_record(fh, ts: int, idx: List[int], val: float, meta: Optional[Dict[str, Any]] = None) -> None:
    rec = {"ts": ts, "idx": idx, "val": float(val)}
    if meta:
        rec["meta"] = meta
    fh.write(json.dumps(rec, separators=(",", ":")) + "\n")


def _ensure_monotonic(sorted_ts: List[int]) -> None:
    for i in range(1, len(sorted_ts)):
        if sorted_ts[i] < sorted_ts[i - 1]:
            raise ValueError(f"non-monotonic ts at index {i}: {sorted_ts[i]} < {sorted_ts[i-1]}")


def stream_to_jsonl(uri: str, out_path: str, **kwargs) -> Dict[str, Any]:
    """
    Convert a SAL source URI into an Event Tensor JSONL stream at out_path.

    Deterministic ordering:
      - Records are sorted by ts (ascending), ties by idx lexicographically.

    Args:
      uri: SAL URI
      out_path: destination JSONL file path
      kwargs: optional overrides (e.g., rate_limit_keps, overflow_policy, sample_rate, etc.)
              telemetry_out (str): optional path to write telemetry JSON

    Returns:
      telemetry dict containing counters and sync status
    """
    scheme, params = parse_uri(uri)
    cfg = SALConfig(
        rate_limit_keps=int(kwargs.get("rate_limit_keps", params.get("rate_limit_keps", 0))) or None,
        overflow_policy=str(kwargs.get("overflow_policy", params.get("overflow_policy", "drop_tail"))),
        sample_rate=int(kwargs.get("sample_rate", params.get("sample_rate", 16000))),
        window_ms=int(kwargs.get("window_ms", params.get("window_ms", 20))),
        hop_ms=int(kwargs.get("hop_ms", params.get("hop_ms", 10))),
        bands=int(kwargs.get("bands", params.get("bands", 32))),
        dtype=str(kwargs.get("dtype", params.get("dtype", "f16"))),
        units_value=str(kwargs.get("units_value", params.get("units_value", "dB"))),
    )
    telemetry_out = kwargs.get("telemetry_out", params.get("telemetry_out"))

    if scheme == "vision.dvs":
        tele = _stream_dvs_to_jsonl(params, out_path, cfg)
    elif scheme == "audio.mic":
        tele = _stream_audio_to_jsonl(params, out_path, cfg)
    else:
        raise ValueError(f"SAL: unsupported source scheme '{scheme}'")

    # Optionally write telemetry JSON sidecar
    if telemetry_out:
        try:
            with open(str(telemetry_out), "w", encoding="utf-8") as fh:
                json.dump(tele, fh, indent=2)
        except Exception:
            # Non-fatal for v0.1
            pass
    return tele


def _stream_dvs_to_jsonl(params: Dict[str, str], out_path: str, cfg: SALConfig) -> Dict[str, Any]:
    fmt = params.get("format", "jsonl").lower()
    path = params.get("path")
    if not path:
        raise ValueError("vision.dvs: missing 'path' parameter")

    if fmt == "jsonl":
        # Normalize an existing JSONL to ensure header and ordering
        produced = 0
        dropped_head = 0
        dropped_tail = 0
        anomalies_detected = 0
        with open(path, "r", encoding="utf-8") as fin, open(out_path, "w", encoding="utf-8") as fout:
            # Read header
            header_line = fin.readline()
            if not header_line:
                raise ValueError("vision.dvs jsonl: empty input")
            header_obj = json.loads(header_line)
            if "header" not in header_obj:
                raise ValueError("vision.dvs jsonl: first line must contain header")
            header = header_obj["header"]
            # Normalize header fields
            header["schema_version"] = "0.1.0"
            header["dims"] = ["x", "y", "polarity"]
            header["units"] = {"time": header.get("units", {}).get("time", "us"), "value": "dimensionless"}
            header["dtype"] = "u8"
            header["layout"] = "coo"
            meta = header.get("metadata", {})
            meta.setdefault("sensor", "dvs")
            header["metadata"] = meta
            _write_jsonl_header(fout, header)

            # Collect, sort, and write records
            records: List[Tuple[int, List[int], float]] = []
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                ts = int(rec["ts"])
                idx = [int(i) for i in rec["idx"]]
                val = float(rec.get("val", 1))
                records.append((ts, idx, val))
            # Sort deterministically: ts, then idx tuple
            records.sort(key=lambda r: (r[0], tuple(r[1])))
            _ensure_monotonic([r[0] for r in records])

            # Simple spoofing/anomaly heuristic: excessive simultaneous activations at identical ts
            # Count max same-timestamp events; if exceeds threshold ratio, flag
            if records:
                from collections import Counter
                ts_counter = Counter(ts for ts, _, _ in records)
                total = len(records)
                max_same_ts = max(ts_counter.values())
                if total > 0 and (max_same_ts / total) > 0.5:
                    anomalies_detected += 1  # crude flash/spoof indicator

            # Rate limiting (optional)
            if cfg.rate_limit_keps:
                # Cap per second per channel (idx[0]).
                cap_per_sec = cfg.rate_limit_keps * 1000  # keps -> events per second (approx)
                from collections import defaultdict, deque
                per_sec_ch_counts: Dict[int, Dict[int, int]] = defaultdict(dict)
                # For drop_head, we keep a deque and drop oldest; for drop_tail, we skip newest
                kept_by_bucket: Dict[Tuple[int, int], deque] = {}
                filtered: List[Tuple[int, List[int], float]] = []
                for ts, idx, val in records:
                    sec = ts // 1_000_000
                    ch = idx[0] if idx else 0
                    key = (sec, ch)
                    cnt = per_sec_ch_counts[sec].get(ch, 0)
                    if cnt < cap_per_sec:
                        filtered.append((ts, idx, val))
                        per_sec_ch_counts[sec][ch] = cnt + 1
                        if cfg.overflow_policy == "drop_head":
                            dq = kept_by_bucket.setdefault(key, deque())
                            dq.append((ts, idx, val))
                            # No drop now; drop happens when we overflow
                    else:
                        if cfg.overflow_policy == "drop_tail":
                            dropped_tail += 1  # skip newest
                        elif cfg.overflow_policy == "drop_head":
                            # Drop the earliest kept in this bucket and keep this one
                            dq = kept_by_bucket.setdefault(key, deque())
                            if dq:
                                dq.popleft()
                                dropped_head += 1
                                # Replace one in filtered: remove first matching bucket event
                                # Build filtered anew for this simplistic replacement:
                                removed = False
                                new_filtered: List[Tuple[int, List[int], float]] = []
                                for rts, ridx, rval in filtered:
                                    if not removed and (rts // 1_000_000 == sec) and ((ridx[0] if ridx else 0) == ch):
                                        removed = True
                                        continue
                                    new_filtered.append((rts, ridx, rval))
                                filtered = new_filtered
                                # Now append current
                                filtered.append((ts, idx, val))
                            else:
                                # Nothing to drop; act like drop_tail
                                dropped_tail += 1
                        else:
                            # block policy: since offline, we simulate by dropping tail and incrementing dropped_tail
                            dropped_tail += 1
                records = filtered

            for ts, idx, val in records:
                _write_jsonl_record(fout, ts, idx, val)
            produced = len(records)

        # Sync status stub for file-based sources
        last_ts = records[-1][0] if records else 0
        telemetry = {
            "source": "vision.dvs",
            "out": out_path,
            "counters": {
                "produced": produced,
                "dropped_head": dropped_head,
                "dropped_tail": dropped_tail,
                "blocked_time_ms": 0,
                "reordered": 0,
                "anomalies_detected": anomalies_detected,
            },
            "sync": {"drift_ppm": 0.0, "jitter_ns": 0, "last_sync_ts": last_ts},
        }
        return telemetry

    if fmt in ("aedat3", "aedat4"):
        # Placeholder: requires external decoder integration
        raise NotImplementedError(
            "vision.dvs AEDAT decoding is not implemented in-core. "
            "Integrate a decoder and map events to Event Tensor records."
        )

    raise ValueError(f"vision.dvs: unsupported format '{fmt}' (expected jsonl|aedat3|aedat4)")


def _read_wav_mono(path: str, expected_rate: int) -> Tuple[List[float], int]:
    """
    Return mono samples (float32 in [-1, 1]) and sample_rate.
    Uses Python's wave module; no external deps required. If the file is stereo,
    downmix to mono.
    """
    import wave
    import struct

    with wave.open(path, "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    # Unpack PCM
    if sample_width == 2:  # 16-bit
        fmt = "<" + "h" * (len(raw) // 2)
        ints = struct.unpack(fmt, raw)
        # Normalize to [-1, 1]
        samples = [x / 32768.0 for x in ints]
    elif sample_width == 1:  # 8-bit unsigned
        fmt = "<" + "B" * len(raw)
        ints = struct.unpack(fmt, raw)
        samples = [(x - 128) / 128.0 for x in ints]
    else:
        raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes")

    # Downmix if stereo
    if n_channels == 2:
        left = samples[0::2]
        right = samples[1::2]
        samples = [(l + r) / 2.0 for l, r in zip(left, right)]
    elif n_channels != 1:
        raise ValueError(f"Unsupported channel count: {n_channels}")

    if expected_rate and sample_rate != expected_rate:
        # Basic resample via nearest-neighbor (placeholder); for determinism in v0.1
        factor = sample_rate / expected_rate
        out_len = int(len(samples) / factor)
        resampled = [samples[int(i * factor)] for i in range(out_len)]
        sample_rate = expected_rate
        samples = resampled

    return samples, sample_rate


def _stft_frames(samples: List[float], sample_rate: int, window_ms: int, hop_ms: int) -> Iterable[List[complex]]:
    """
    Deterministic STFT implementation.
    Uses numpy FFT if available, else a pure-Python DFT (slower but deterministic).
    """
    win_size = int(sample_rate * window_ms / 1000)
    hop = int(sample_rate * hop_ms / 1000)
    if win_size <= 0 or hop <= 0:
        raise ValueError("window_ms and hop_ms must be positive")
    # Hann window
    if np is not None:
        window = 0.5 - 0.5 * np.cos(2.0 * np.pi * np.arange(win_size) / win_size)
        x = np.array(samples, dtype=float)
        for start in range(0, len(samples) - win_size + 1, hop):
            frame = x[start : start + win_size] * window
            spec = np.fft.rfft(frame)
            yield list(spec)
    else:
        window = [0.5 - 0.5 * math.cos(2.0 * math.pi * n / win_size) for n in range(win_size)]
        for start in range(0, len(samples) - win_size + 1, hop):
            frame = [samples[start + n] * window[n] for n in range(win_size)]
            # rfft: compute bins 0..win_size//2
            bins = []
            N = win_size
            for k in range(N // 2 + 1):
                re = 0.0
                im = 0.0
                for n in range(N):
                    angle = 2.0 * math.pi * k * n / N
                    re += frame[n] * math.cos(angle)
                    im -= frame[n] * math.sin(angle)
                bins.append(complex(re, im))
            yield bins


def _stream_audio_to_jsonl(params: Dict[str, str], out_path: str, cfg: SALConfig) -> Dict[str, Any]:
    path = params.get("path")
    if not path:
        raise ValueError("audio.mic: missing 'path' parameter (WAV file)")

    samples, sample_rate = _read_wav_mono(path, cfg.sample_rate)

    # Header
    header = {
        "schema_version": "0.1.0",
        "dims": ["band"],
        "units": {"time": "ms", "value": cfg.units_value},
        "dtype": cfg.dtype,
        "layout": "coo",
        "metadata": {"sample_rate": sample_rate, "window_ms": cfg.window_ms, "hop_ms": cfg.hop_ms},
    }

    # STFT and band aggregation
    frames = list(_stft_frames(samples, sample_rate, cfg.window_ms, cfg.hop_ms))
    # Power magnitude per bin
    if np is not None:
        mags = [np.abs(np.array(frame)) for frame in frames]
    else:
        mags = [[abs(x) for x in frame] for frame in frames]

    # Map bins to bands (uniform grouping)
    n_bins = len(mags[0]) if mags else 0
    bands = max(1, cfg.bands)
    bins_per_band = max(1, n_bins // bands) if n_bins else 1

    # Write JSONL
    produced = 0
    anomalies_detected = 0
    with open(out_path, "w", encoding="utf-8") as fout:
        _write_jsonl_header(fout, header)
        ts = 0  # ms
        for spectrum in mags:
            # Aggregate into bands
            values: List[float] = []
            for b in range(bands):
                start = b * bins_per_band
                end = min(len(spectrum), (b + 1) * bins_per_band)
                if start >= end:
                    agg = 0.0
                else:
                    avg = sum(float(spectrum[i]) for i in range(start, end)) / float(end - start)
                    if cfg.units_value.lower() == "db":
                        # Convert to dB with small epsilon to avoid log(0)
                        eps = 1e-12
                        agg = 20.0 * math.log10(max(avg, eps))
                    else:
                        agg = avg
                values.append(agg)

            # Simple narrowband spike detector: values exceeding median + 6 dB
            if values:
                sorted_vals = sorted(values)
                median = sorted_vals[len(sorted_vals) // 2]
                if any(v > (median + 6.0) for v in values):
                    anomalies_detected += 1

            # Emit events per band
            for band_idx, v in enumerate(values):
                _write_jsonl_record(fout, ts, [band_idx], v)
                produced += 1
            ts += cfg.hop_ms  # ms progression (windowed stream)

    telemetry = {
        "source": "audio.mic",
        "out": out_path,
        "counters": {
            "produced": produced,
            "dropped_head": 0,
            "dropped_tail": 0,
            "blocked_time_ms": 0,
            "reordered": 0,
            "anomalies_detected": anomalies_detected,
        },
        "sync": {"drift_ppm": 0.0, "jitter_ns": 0, "last_sync_ts": ts},
    }
    return telemetry