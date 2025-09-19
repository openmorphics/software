from __future__ import annotations
import os, json

def handle(ns):
    # lazy import to avoid hard dependency during parsing/tests
    try:
        from eventflow_core.eir.serialize import load  # noqa: F401
    except Exception:
        load = None

    os.makedirs(ns.out, exist_ok=True)

    # If .eir, copy; else unsupported for now
    if ns.model.endswith(".eir"):
        with open(ns.model, "r") as f_in, open(os.path.join(ns.out, "model.eir"), "w") as f_out:
            f_out.write(f_in.read())
    else:
        raise NotImplementedError("Python builder import not implemented")

    cap = {"profiles": ns.profiles.split(","), "min_caps": {"neurons": ">=0"}}
    with open(os.path.join(ns.out,"cap.json"),"w") as f: json.dump(cap, f, indent=2)
    with open(os.path.join(ns.out,"card.json"),"w") as f: json.dump(
        {"name":"unnamed","version":"0.0.0","task":"unknown","summary":"","license":"BSD-3-Clause"}, f, indent=2)
    with open(os.path.join(ns.out,"trace.json"),"w") as f: json.dump({}, f)
    print(f"Built bundle at {ns.out}")
    return 0
