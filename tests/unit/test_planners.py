import json
import os
import unittest
import importlib.util
from typing import Any


def _load_module_from(path: str, name: str):
    import sys
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module {name} from {path}")
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    # Register in sys.modules before executing to satisfy dataclasses/typing introspection
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore
    return mod


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REGISTRY = _load_module_from(
    os.path.join(BASE_DIR, "eventflow-backends", "registry", "registry.py"),
    "eventflow_backend_registry_test",
)


def _minimal_eir(
    profile: str = "BASE",
    mode: str = "fixed_step",
    dt_us: int = 100,
    eps_time_us: int = 100,
) -> dict[str, Any]:
    return {
        "version": "0.1.0",
        "profile": profile,
        "seed": 0,
        "time": {
            "unit": "us",
            "mode": mode,
            **({"fixed_step_dt_us": dt_us} if mode == "fixed_step" else {}),
            "epsilon_time_us": eps_time_us,
            "epsilon_numeric": 1e-5,
        },
        "graph": {"name": "test"},
        "nodes": [
            {"id": "n0", "kind": "spiking_neuron", "op": "lif", "params": {}},
        ],
        "edges": [],
        "probes": [],
    }


class TestPlanners(unittest.TestCase):
    def test_cpu_sim_profile_incompat_raises(self):
        backend = REGISTRY.load_backend("cpu-sim")
        eir = _minimal_eir(profile="LEARNING")  # cpu-sim supports BASE/REALTIME in example DCD
        with self.assertRaisesRegex(ValueError, "backend\\.unsupported_profile"):
            backend.plan(eir)

    def test_cpu_sim_exact_event_epsilon_violation(self):
        backend = REGISTRY.load_backend("cpu-sim")
        eir = _minimal_eir(profile="BASE", mode="exact_event", eps_time_us=0)
        with self.assertRaisesRegex(ValueError, "backend\\.time_quantization_violation"):
            backend.plan(eir)

    def test_cpu_sim_emulated_ops_listed(self):
        backend = REGISTRY.load_backend("cpu-sim")
        eir = _minimal_eir(profile="BASE", mode="fixed_step", dt_us=100)
        # Replace node op with unsupported to force emulation
        eir["nodes"][0]["op"] = "unknown_op_xyz"
        plan = backend.plan(eir)
        self.assertIn("capabilities", plan)
        emu = plan["capabilities"].get("emulated_nodes", [])
        self.assertTrue(any(n.get("op") == "unknown_op_xyz" for n in emu))
        self.assertIn("negotiation", plan)
        ops = plan["negotiation"].get("ops", {})
        self.assertIn("emulated_count", ops)
        self.assertGreaterEqual(ops.get("emulated_count", 0), 1)

    def test_gpu_sim_fixed_step_dt_in_plan(self):
        backend = REGISTRY.load_backend("gpu-sim")
        eir = _minimal_eir(profile="BASE", mode="fixed_step", dt_us=100)
        plan = backend.plan(eir)
        sched = plan.get("schedule", [])
        self.assertTrue(len(sched) >= 1)
        self.assertEqual(sched[0].get("dt_us"), 100)

    def test_gpu_sim_exact_event_epsilon_violation(self):
        backend = REGISTRY.load_backend("gpu-sim")
        eir = _minimal_eir(profile="BASE", mode="exact_event", eps_time_us=0)
        with self.assertRaisesRegex(ValueError, "backend\\.time_quantization_violation"):
            backend.plan(eir)


if __name__ == "__main__":
    unittest.main()