from __future__ import annotations
import os, json

def handle(ns):
    """Build and package an EventFlow model for deployment.

    Compiles an EventFlow Intermediate Representation (EIR) model into a deployable
    bundle containing all necessary artifacts for execution. This is the core
    packaging functionality for EventFlow models.

    Args:
        ns: Namespace object containing command-line arguments with attributes:
            model (str): Path to the EIR JSON model file (.eir extension required).
                        This must be a valid EventFlow Intermediate Representation
                        file containing the compiled model graph.
            out (str): Output directory path where the bundle will be created.
                      The directory will be created if it doesn't exist.
            profiles (str): Comma-separated list of deployment profiles to support.
                           Defaults to "BASE". Valid options include:
                           - BASE: Standard execution profile
                           - REALTIME: Optimized for low-latency real-time execution
                           - LEARNING: Configured for training/learning workloads
                           - LOWPOWER: Optimized for energy-efficient execution

    Returns:
        int: Exit code following EventFlow conventions:
             - 0: Success - bundle created successfully
             - 2: IO/argument error - invalid arguments or file access issues

    Raises:
        RuntimeError: When attempting to build unsupported model formats.
                     Only .eir JSON files are supported in v0.1.

    Creates bundle files:
        - model.eir: Copy of the input EIR model
        - cap.json: Capability specification with supported profiles
        - card.json: Metadata card with package information
        - trace.json: Empty trace file for runtime output capture

    Example:
        Build a model with real-time profile:

        >>> ns = argparse.Namespace(
        ...     model="my_model.eir",
        ...     out="./build_output",
        ...     profiles="BASE,REALTIME"
        ... )
        >>> handle(ns)
        Built bundle at ./build_output
        0

    Note:
        This command only supports .eir JSON models in v0.1. Python builder
        scripts are not yet supported to maintain strict packaging scope limits.
    """
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
        raise RuntimeError("builder.unsupported: only .eir JSON models are supported in v0.1; use --model path/to/model.eir")

    cap = {"profiles": ns.profiles.split(","), "min_caps": {"neurons": ">=0"}}
    with open(os.path.join(ns.out,"cap.json"),"w") as f: json.dump(cap, f, indent=2)
    with open(os.path.join(ns.out,"card.json"),"w") as f: json.dump(
        {"name":"unnamed","version":"0.0.0","task":"unknown","summary":"","license":"BSD-3-Clause"}, f, indent=2)
    with open(os.path.join(ns.out,"trace.json"),"w") as f: json.dump({}, f)
    print(f"Built bundle at {ns.out}")
    return 0
