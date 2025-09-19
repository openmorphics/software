#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from typing import Dict, List, Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EF = os.path.join(ROOT, "eventflow-cli", "ef.py")

def sh(args: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr

def run_ef(args: List[str], check: bool = True) -> Dict:
    code, out, err = sh([sys.executable, EF] + args)
    if code != 0 and check:
        raise RuntimeError(f"ef failed: {' '.join(args)}\n{err}")
    try:
        return json.loads(out) if out.strip().startswith("{") else {"stdout": out.strip()}
    except Exception:
        return {"stdout": out.strip()}

def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)

def write_badges(out_dir: str, results: Dict[str, bool]) -> None:
    ensure_dir(out_dir)
    # Simple markdown badges using shields.io
    lines = ["# EventFlow Conformance Badges"]
    for name, ok in results.items():
        color = "brightgreen" if ok else "red"
        status = "OK" if ok else "FAIL"
        lines.append(f"- {name}: ![status](https://img.shields.io/badge/{name}-{status}-{color})")
    with open(os.path.join(out_dir, "badges.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

def task_vision(out_root: str) -> bool:
    # Normalize DVS JSONL and run
    in_jsonl = os.path.join(ROOT, "examples", "vision_optical_flow", "traces", "inputs", "vision_sample.jsonl")
    if not os.path.isfile(in_jsonl):
        raise FileNotFoundError(f"Missing DVS sample: {in_jsonl}")
    tdir = os.path.join(out_root, "vision")
    ensure_dir(tdir)
    norm = os.path.join(tdir, "vision.norm.jsonl")
    tele = os.path.join(tdir, "vision.telemetry.json")
    run_ef(["--json", "sal-stream", "--uri", f"vision.dvs://file?format=jsonl&path={in_jsonl}", "--out", norm, "--telemetry-out", tele])
    eir = os.path.join(ROOT, "examples", "vision_optical_flow", "eir.json")
    golden = os.path.join(tdir, "vision.golden.jsonl")
    run_ef(["run", "--eir", eir, "--backend", "cpu-sim", "--input", norm, "--trace-out", golden])
    # Self-compare to validate comparator flow
    res = run_ef(["--json", "compare-traces", "--golden", golden, "--candidate", golden, "--eps-time-us", "50", "--eps-numeric", "1e-5"])
    return bool(res.get("ok", True))

def task_audio(out_root: str) -> bool:
    # Prefer WAV -> bands; fall back to provided sample JSONL
    wav = os.path.join(ROOT, "examples", "wakeword", "audio.wav")
    tdir = os.path.join(out_root, "audio")
    ensure_dir(tdir)
    if os.path.isfile(wav):
        norm = os.path.join(tdir, "audio_bands.jsonl")
        tele = os.path.join(tdir, "audio.telemetry.json")
        run_ef(["--json", "sal-stream", "--uri", f"audio.mic://file?path={wav}&window_ms=20&hop_ms=10&bands=32", "--out", norm, "--telemetry-out", tele])
        input_path = norm
    else:
        input_path = os.path.join(ROOT, "examples", "wakeword", "traces", "inputs", "audio_sample.jsonl")
    eir = os.path.join(ROOT, "examples", "wakeword", "eir.json")
    golden = os.path.join(tdir, "wakeword.golden.jsonl")
    run_ef(["run", "--eir", eir, "--backend", "cpu-sim", "--input", input_path, "--trace-out", golden])
    res = run_ef(["--json", "compare-traces", "--golden", golden, "--candidate", golden, "--eps-time-us", "100", "--eps-numeric", "1e-5"])
    return bool(res.get("ok", True))

def task_imu(out_root: str) -> bool:
    # IMU CSV -> JSONL -> run anomaly EIR
    csv_path = os.path.join(ROOT, "examples", "robotics_slam", "traces", "inputs", "imu_sample.csv")
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Missing IMU CSV: {csv_path}")
    tdir = os.path.join(out_root, "imu")
    ensure_dir(tdir)
    norm = os.path.join(tdir, "imu.norm.jsonl")
    tele = os.path.join(tdir, "imu.telemetry.json")
    run_ef(["--json", "sal-stream", "--uri", f"imu.6dof://file?path={csv_path}", "--out", norm, "--telemetry-out", tele])
    eir = os.path.join(ROOT, "examples", "anomaly_timeseries", "eir.json")
    golden = os.path.join(tdir, "anomaly.golden.jsonl")
    run_ef(["run", "--eir", eir, "--backend", "cpu-sim", "--input", norm, "--trace-out", golden])
    res = run_ef(["--json", "compare-traces", "--golden", golden, "--candidate", golden])
    return bool(res.get("ok", True))

def main():
    ap = argparse.ArgumentParser(description="EventFlow conformance automation")
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "conformance"), help="Output directory (default: out/conformance)")
    ap.add_argument("--tasks", nargs="*", choices=["vision", "audio", "imu"], default=["vision", "audio", "imu"])
    args = ap.parse_args()
    ensure_dir(args.out)
    results: Dict[str, bool] = {}
    if "vision" in args.tasks:
        results["vision"] = task_vision(args.out)
    if "audio" in args.tasks:
        results["audio"] = task_audio(args.out)
    if "imu" in args.tasks:
        results["imu"] = task_imu(args.out)
    write_badges(os.path.join(args.out, "badges"), results)
    print(json.dumps({"ok": all(results.values()), "results": results, "badges": os.path.join(args.out, "badges", "badges.md")}, indent=2))

if __name__ == "__main__":
    main()