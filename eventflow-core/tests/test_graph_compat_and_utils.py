from __future__ import annotations

from eventflow_core.conformance.compare import trace_equivalent
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import DelayLine, EventFuse, LIFNeuron
from eventflow_core.eir.serialize import load as load_graph
from eventflow_core.eir.serialize import save as save_graph
from eventflow_core.eir.validate import validate as validate_graph
from eventflow_core.runtime.trace import load as load_trace
from eventflow_core.runtime.trace import record as record_trace


def test_graph_legacy_compat_methods_and_two_arg_connect(tmp_path):
    g = EIRGraph(name="compat")
    assert g.name == "compat"

    src = g.add_source("src", "sensor://a")
    inp = g.add_input("inp", "sensor://b")
    legacy = g.add_node("legacy_threshold", {"op": "threshold", "threshold": 5.0})
    custom = g.add_op("custom_stage", {"foo": "bar"})
    out = g.add_output("sink", custom)

    # Legacy edge helper should map to connect(src, dst)
    g.add_edge(src, legacy)
    g.add_edge(inp, legacy)
    g.connect(legacy, custom)
    g.enable_native_acceleration()

    assert out == "sink"
    assert "source:src" in g.metadata
    assert "source:inp" in g.metadata
    assert g.metadata["native_acceleration"] == "enabled"
    assert legacy in g.nodes and custom in g.nodes and out in g.nodes
    assert len(g.topo()) == len(g.nodes)


def test_add_op_known_kinds_builds_nodes():
    g = EIRGraph()
    for kind in (
        "lif",
        "exp_syn",
        "delay",
        "fuse",
        "stft",
        "mel",
        "xy_to_ch",
        "shift_xy",
        "bucket",
        "bucket_sum",
        "event_filter",
    ):
        g.add_op(kind)

    assert len(g.nodes) == 11
    assert g.nodes["lif"].op.kind == "lif"
    assert g.nodes["delay"].op.params["delay"] == "0 ms"
    assert g.nodes["bucket_sum"].op.kind == "bucket_sum"
    assert g.nodes["event_filter"].op.kind == "event_filter"


def test_graph_serialize_roundtrip_and_validate(tmp_path):
    g = EIRGraph(metadata={"version": "test"})
    g.add_node("src", DelayLine("src", delay="0 ms").as_op())
    g.add_node("delay", DelayLine("delay", delay="1 ms").as_op())
    g.add_node("f", EventFuse("f", window="2 ms", min_count=1).as_op())
    g.connect("src", "out", "delay", "in")
    g.connect("src", "out", "f", "a")
    g.connect("delay", "out", "f", "b")

    path = tmp_path / "graph.json"
    save_graph(g, str(path))
    loaded = load_graph(str(path))

    assert set(loaded.nodes) == {"src", "delay", "f"}
    assert len(loaded.edges) == 3
    validate_graph(loaded)  # should not raise


def test_runtime_trace_record_load_and_compare(tmp_path):
    trace = {
        "node_a": [(0, 0, 1.0, {"unit": "x"}), (10, 0, 2.0, {"unit": "x"})],
        "node_b": [(5, 1, 3.0, {"unit": "y"})],
    }
    path = tmp_path / "trace.json"
    record_trace(str(path), trace)
    loaded = load_trace(str(path))

    assert trace_equivalent(trace, loaded)
    assert not trace_equivalent(trace, {"node_a": trace["node_a"]})
    off_value = {"node_a": [(0, 0, 1.0, {}), (10, 0, 9.0, {})], "node_b": [(5, 1, 3.0, {})]}
    assert not trace_equivalent(trace, off_value, tol_v=0.1)
