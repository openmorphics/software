from __future__ import annotations
import json, os

def handle(ns):
    # lazy imports to avoid load-time errors if deps not installed
    try:
        from eventflow_core.eir.serialize import load
    except Exception as e:
        raise RuntimeError("eventflow_core not available for run") from e
    from eventflow_backends import get_backend

    model_path = ns.bundle if ns.bundle.endswith(".eir") else os.path.join(ns.bundle, "model.eir")
    g = load(model_path)
    backend = get_backend(ns.backend)
    outputs = backend.run_graph(g)              # returns node→events map
    print(json.dumps({k: v[:3] for k,v in outputs.items()}, indent=2))
    return 0
