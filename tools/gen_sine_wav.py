#!/usr/bin/env python3
from __future__ import annotations
import argparse, math, os, wave, struct

def gen(path: str, sr: int = 16000, freq: float = 1000.0, dur_ms: int = 1000, amp: float = 0.4) -> str:
    n = int(sr * (dur_ms / 1000.0))
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit PCM
        wf.setframerate(sr)
        frames = []
        for i in range(n):
            x = amp * math.sin(2.0 * math.pi * freq * (i / sr))
            s = max(-1.0, min(1.0, x))
            frames.append(struct.pack("<h", int(s * 32767.0)))
        wf.writeframes(b"".join(frames))
    return path

def main():
    ap = argparse.ArgumentParser(description="Generate a deterministic sine WAV")
    ap.add_argument("--path", default="examples/wakeword/audio.wav")
    ap.add_argument("--sr", type=int, default=16000)
    ap.add_argument("--freq", type=float, default=1000.0)
    ap.add_argument("--dur-ms", type=int, default=1000)
    ap.add_argument("--amp", type=float, default=0.4)
    args = ap.parse_args()
    p = gen(args.path, args.sr, args.freq, args.dur_ms, args.amp)
    print(f"wrote: {p}")

if __name__ == "__main__":
    main()
