from __future__ import annotations
import argparse

def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="eventflow", description="EventFlow CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    # build
    pb = sub.add_parser("build", help="Compile and package")
    pb.add_argument("--model", required=True, help="Path to .eir or Python builder")
    pb.add_argument("--out", required=True, help="Output directory")
    pb.add_argument("--profiles", default="BASE", help="Comma list: BASE,REALTIME,LEARNING,LOWPOWER")

    # run
    pr = sub.add_parser("run", help="Execute on backend")
    pr.add_argument("--bundle", required=True, help="Path to built bundle or .eir")
    pr.add_argument("--backend", default="cpu_sim", help="Backend id")

    # profile
    pp = sub.add_parser("profile", help="Latency/energy profiling")
    pp.add_argument("--bundle", required=True)
    pp.add_argument("--backend", default="cpu_sim")

    # validate
    pv = sub.add_parser("validate", help="Conformance against golden traces")
    pv.add_argument("--bundle", required=True)
    pv.add_argument("--golden", required=True)

    return p

def main(argv=None):
    # lazy import subcommands to avoid heavy deps at import time
    from . import build, run, profile, validate
    ns = make_parser().parse_args(argv)
    if ns.cmd == "build":    return build.handle(ns)
    if ns.cmd == "run":      return run.handle(ns)
    if ns.cmd == "profile":  return profile.handle(ns)
    if ns.cmd == "validate": return validate.handle(ns)

if __name__ == "__main__":
    main()
