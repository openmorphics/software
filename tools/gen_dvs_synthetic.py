#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os

def write_header(fh, w: int, h: int):
    hdr = {
        "schema_version": "0.1.0",
        "dims": ["x","y","polarity"],
        "units": {"time":"us","value":"dimensionless"},
        "dtype": "u8",
        "layout":"coo",
        "metadata":{"sensor":"dvs","width":w,"height":h}
    }
    fh.write(json.dumps({"header": hdr}) + "\n")

def write_events(fh, events):
    for ts, x, y, p in events:
        fh.write(json.dumps({"ts": ts, "idx": [int(x), int(y), int(p)], "val": 1}) + "\n")

def main():
    ap = argparse.ArgumentParser(description="Generate a tiny synthetic DVS JSONL")
    ap.add_argument("--path", default="examples/vision_corner_tracking/traces/inputs/corner_sample.jsonl")
    ap.add_argument("--width", type=int, default=8)
    ap.add_argument("--height", type=int, default=8)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.path) or ".", exist_ok=True)
    with open(args.path, "w", encoding="utf-8") as f:
        write_header(f, args.width, args.height)
        # simple east-moving dot across y=2
        events = [
            (0, 1, 2, 1),
            (1000, 2, 2, 1),
            (2000, 3, 2, 1),
            (3000, 4, 2, 1),
            (4000, 5, 2, 1),
        ]
        write_events(f, events)
    print(f"wrote: {args.path}")

if __name__ == "__main__":
    main()
