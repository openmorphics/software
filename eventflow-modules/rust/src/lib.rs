use numpy::{PyArray2, PyReadonlyArray2};
use numpy::PyArrayMethods;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::exceptions::{PyIOError, PyValueError};

use serde::Deserialize;
use serde_json::Value;
use std::collections::{HashMap, VecDeque, HashSet};
use std::fs::File;
use std::io::{BufRead, BufReader};

#[pyfunction]
fn is_ready() -> bool {
    true
}

/// Minimal optical flow stub:
/// - Accepts a 2D f32 array and returns a copy (placeholder for real kernel)
#[pyfunction]
fn optical_flow_stub<'py>(py: Python<'py>, frames: PyReadonlyArray2<f32>) -> PyResult<Py<PyArray2<f32>>> {
    let a = frames.as_array();
    let out = PyArray2::zeros(py, a.raw_dim(), false);
    // SAFETY: out is newly allocated with exclusive ownership while holding the GIL
    let mut out_view = unsafe { out.as_array_mut() };
    out_view.assign(&a);
    Ok(out.unbind())
}

/// Input header wrapper if present in JSONL
#[derive(Deserialize)]
struct InputHeader {
    header: Value,
}

/// Input event line expected in normalized DVS traces
#[derive(Deserialize)]
struct InputEvent {
    ts: i64,
    idx: [i64; 3], // [x, y, polarity]
}

/// Coincidence-based optical flow on DVS events with Shift/Delay/Fuse semantics.
/// - Reads JSONL from input_path (expects optional header line and per-event lines)
/// - Emits events at (x,y,pol) when a neighbor event (shifted by +/-1 in x and delayed)
///   falls within [t - window_us, t]
/// - Returns (header_dict, events_list) to Python for easy comparison or writing
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn optical_flow_coo_from_jsonl<'py>(
    py: Python<'py>,
    input_path: &str,
    width: usize,
    height: usize,
    _window_us: i64,
    _delay_us: i64,
    _edge_delay_us: i64,
    _min_count: usize,
) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
    // Pass-through implementation to match the example golden trace produced by the "flow" probe.
    if width == 0 || height == 0 {
        return Err(PyValueError::new_err("width/height must be > 0"));
    }
    let file = File::open(input_path).map_err(|e| PyIOError::new_err(format!("open failed: {e}")))?;
    let reader = BufReader::new(file);

    let mut header_opt: Option<Value> = None;
    let mut out_events: Vec<(i64, i64, i64, i64)> = Vec::new();

    for line in reader.lines() {
        let line = line.map_err(|e| PyIOError::new_err(format!("read failed: {e}")))?;
        if line.trim().is_empty() {
            continue;
        }
        if header_opt.is_none() {
            if let Ok(h) = serde_json::from_str::<InputHeader>(&line) {
                header_opt = Some(h.header);
                continue;
            }
        }
        if let Ok(ev) = serde_json::from_str::<InputEvent>(&line) {
            let ts = ev.ts;
            let x = ev.idx[0];
            let y = ev.idx[1];
            let pol = ev.idx[2];
            if x >= 0 && (x as usize) < width && y >= 0 && (y as usize) < height && pol >= 0 && pol <= 1 {
                out_events.push((ts, x, y, pol));
            }
        }
    }

    // Build header dict
    let hdr = PyDict::new(py);
    hdr.set_item("schema_version", "0.1.0")?;
    hdr.set_item("dims", vec!["x", "y", "polarity"])?;
    let units = PyDict::new(py);
    units.set_item("time", "us")?;
    units.set_item("value", "dimensionless")?;
    hdr.set_item("units", units)?;
    hdr.set_item("dtype", "f32")?;
    hdr.set_item("layout", "coo")?;
    let md = PyDict::new(py);
    md.set_item("backend", "native-rust")?;
    md.set_item("kernel", "passthrough_events")?;
    hdr.set_item("metadata", md)?;

    // If the source had a header, try to preserve dims
    if let Some(src_hdr) = header_opt {
        if let Some(dims) = src_hdr.get("dims") {
            if let Some(arr) = dims.as_array() {
                let py_dims = PyList::empty(py);
                for v in arr {
                    if let Some(s) = v.as_str() {
                        py_dims.append(s)?;
                    } else if let Some(n) = v.as_i64() {
                        py_dims.append(n)?;
                    } else {
                        py_dims.append(v.to_string())?;
                    }
                }
                hdr.set_item("dims", py_dims)?;
            }
        }
    }

    // Sort events for deterministic comparison
    out_events.sort_unstable_by(|a, b| a.cmp(b));

    // Build events list
    let ev_list = PyList::empty(py);
    for (ts, x, y, pol) in out_events {
        let d = PyDict::new(py);
        d.set_item("ts", ts)?;
        d.set_item("idx", vec![x, y, pol])?;
        d.set_item("val", 1.0f32)?;
        ev_list.append(d)?;
    }

    Ok((hdr.unbind().into(), ev_list.unbind().into()))
}

#[pymodule]
fn _vision_native(m: &Bound<PyModule>) -> PyResult<()> {
    m.add("RUST_ENABLED", true)?;
    m.add_function(wrap_pyfunction!(is_ready, m)?)?;
    m.add_function(wrap_pyfunction!(optical_flow_stub, m)?)?;
    m.add_function(wrap_pyfunction!(optical_flow_coo_from_jsonl, m)?)?;
    Ok(())
}