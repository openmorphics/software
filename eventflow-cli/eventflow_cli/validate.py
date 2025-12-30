from __future__ import annotations
import json, os

def handle(ns):
    """Validate an EventFlow model against golden reference traces.

    Executes the model on the specified backend and compares the output traces
    against a golden reference file to verify conformance and correctness.
    This is the core validation functionality for ensuring model behavior matches
    expected results across different backends and configurations.

    Args:
        ns: Namespace object containing command-line arguments with attributes:
            bundle (str): Path to the built bundle (.eir file or directory).
                         If a directory, looks for model.eir inside it.
                         Must contain a valid EventFlow Intermediate Representation.
            golden (str): Path to the golden reference trace file (JSON format).
                         Contains expected output traces for comparison.
            backend (str): Backend identifier for execution. Defaults to "cpu_sim".
                          Available backends depend on system configuration and
                          installed hardware acceleration packages.

    Returns:
        int: Exit code following EventFlow conventions:
             - 0: Success - traces match golden reference
             - 2: Validation failure - traces do not match within tolerances

    Raises:
        RuntimeError: When eventflow_core or eventflow_backends dependencies
                     are not available or bundle cannot be loaded due to
                     missing/corrupted files.

    Output:
        Prints "OK" if traces match within tolerances, "MISMATCH" otherwise.

    Note:
        Uses lazy imports to avoid loading heavy dependencies during CLI parsing.
        Trace comparison uses default tolerances: tol_t=0, tol_v=1e-6.
        Backend availability depends on installed eventflow-backends package.
    """
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
