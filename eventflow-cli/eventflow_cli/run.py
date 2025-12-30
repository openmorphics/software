from __future__ import annotations
import json, os

def handle(ns):
    """Execute an EventFlow model on a specified backend.

    Loads a built EventFlow bundle and executes it on the chosen backend,
    displaying the first few output events from each node. This is the core
    execution functionality for testing and validating model behavior.

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
             - 0: Success - model executed and results displayed
             - 2: IO/argument error - bundle not found or invalid backend

    Raises:
        RuntimeError: When eventflow_core dependencies are not available or
                     bundle cannot be loaded due to missing/corrupted files.

    Output:
        Prints JSON-formatted output events from each node, limited to first 3
        events per node for readability. Output format:
        {"node_id": [event1, event2, event3], ...}

    Example:
        Execute bundle on CPU simulator:

        >>> ns = argparse.Namespace(
        ...     bundle="./my_bundle",
        ...     backend="cpu_sim"
        ... )
        >>> handle(ns)
        {"node_1": [{"type": "spike", "t_s": 0.001, "neuron": 5}, ...], ...}
        0

    Note:
        Uses lazy imports to avoid loading heavy dependencies during CLI parsing.
        Backend availability depends on installed eventflow-backends package.
    """
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
