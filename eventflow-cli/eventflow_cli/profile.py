from __future__ import annotations
import json, os, time

def handle(ns):
    try:
        from eventflow_core.eir.serialize import load
    except Exception as e:
        raise RuntimeError("eventflow_core not available for profile") from e
    from eventflow_backends import get_backend

    model_path = ns.bundle if ns.bundle.endswith(".eir") else os.path.join(ns.bundle, "model.eir")
    g = load(model_path)
    backend = get_backend(ns.backend)
    t0 = time.time()
    outputs = backend.run_graph(g)
    dt = (time.time()-t0)*1000
    report = {"latency_ms": dt, "energy_j": None, "events_out": {k:len(v) for k,v in outputs.items()}}
    print(json.dumps(report, indent=2))
    return 0
