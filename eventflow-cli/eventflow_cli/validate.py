from __future__ import annotations
import json, os

def handle(ns):
    try:
        from eventflow_core.eir.serialize import load
        from eventflow_core.conformance.compare import trace_equivalent
    except Exception as e:
        raise RuntimeError("eventflow_core not available for validate") from e
    from eventflow_backends import get_backend

    model_path = ns.bundle if ns.bundle.endswith(".eir") else os.path.join(ns.bundle, "model.eir")
    g = load(model_path)
    backend = get_backend(ns.backend)
    cand = backend.run_graph(g)
    with open(ns.golden) as f:
        golden = json.load(f)
    ok = trace_equivalent(golden, cand, tol_t=0, tol_v=1e-6)
    print("OK" if ok else "MISMATCH")
    return 0 if ok else 2
