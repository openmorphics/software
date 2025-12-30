from __future__ import annotations
import json, os, time

def handle(ns):
    """Profile latency and energy consumption of an EventFlow model.

    Executes the model on the specified backend and measures execution time,
    providing performance metrics including latency and event output counts.
    This is the core profiling functionality for performance analysis and
    optimization of EventFlow models across different backends.

    Args:
        ns: Namespace object containing command-line arguments with attributes:
            bundle (str): Path to the built bundle (.eir file or directory).
                         If a directory, looks for model.eir inside it.
                         Must contain a valid EventFlow Intermediate Representation.
            backend (str): Backend identifier for execution. Defaults to "cpu_sim".
                          Available backends depend on system configuration and
                          installed hardware acceleration packages.

    Returns:
        int: Exit code following EventFlow conventions:
             - 0: Success - profiling completed and results displayed

    Raises:
        RuntimeError: When eventflow_core or eventflow_backends dependencies
                     are not available or bundle cannot be loaded due to
                     missing/corrupted files.

    Output:
        Prints JSON-formatted profiling report with the following fields:
        - latency_ms (float): Execution time in milliseconds
        - energy_j (None): Energy consumption in joules (currently not measured)
        - events_out (dict): Number of output events per node {"node_id": count, ...}

    Example:
        Profile bundle on CPU simulator:

        >>> ns = argparse.Namespace(
        ...     bundle="./my_bundle",
        ...     backend="cpu_sim"
        ... )
        >>> handle(ns)
        {
          "latency_ms": 45.67,
          "energy_j": null,
          "events_out": {"node_1": 1024, "node_2": 512}
        }
        0

    Note:
        Uses lazy imports to avoid loading heavy dependencies during CLI parsing.
        Energy measurement is currently not implemented (returns None).
        Backend availability depends on installed eventflow-backends package.
    """
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
