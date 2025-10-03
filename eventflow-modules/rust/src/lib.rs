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
    window_us: i64,
    delay_us: i64,
    edge_delay_us: i64,
    min_count: usize,
) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
    if window_us <= 0 {
        return Err(PyValueError::new_err("window_us must be > 0"));
    }
    if delay_us < 0 || edge_delay_us < 0 {
        return Err(PyValueError::new_err("delay_us and edge_delay_us must be >= 0"));
    }
    if min_count == 0 {
        return Err(PyValueError::new_err("min_count must be >= 1"));
    }
    let file = File::open(input_path).map_err(|e| PyIOError::new_err(format!("open failed: {e}")))?;
    let reader = BufReader::new(file);

    let eff_delay = delay_us + edge_delay_us;

    // For each (x,y,pol), maintain deques:
    // - a_map: raw A-stream timestamps at the exact (x,y,pol)
    // - east_map / west_map: neighbor-delayed B-stream timestamps arriving at (x,y,pol)
    let mut a_map: HashMap<(i64, i64, i64), VecDeque<i64>> = HashMap::new();
    let mut east_map: HashMap<(i64, i64, i64), VecDeque<i64>> = HashMap::new();
    let mut west_map: HashMap<(i64, i64, i64), VecDeque<i64>> = HashMap::new();
    let mut out_events: Vec<(i64, i64, i64, i64)> = Vec::new();
    let mut seen: HashSet<(i64, i64, i64, i64)> = HashSet::new();
    let mut header_opt: Option<Value> = None;

    // Helper to prune timestamps older than cutoff
    fn prune(deq: &mut VecDeque<i64>, cutoff: i64) {
        while let Some(&front) = deq.front() {
            if front < cutoff {
                deq.pop_front();
            } else {
                break;
            }
        }
    }

    for line in reader.lines() {
        let line = line.map_err(|e| PyIOError::new_err(format!("read failed: {e}")))?;
        if line.trim().is_empty() {
            continue;
        }
        // Attempt header
        if header_opt.is_none() {
            if let Ok(h) = serde_json::from_str::<InputHeader>(&line) {
                header_opt = Some(h.header);
                continue;
            }
        }
        // Attempt event
        let ev: InputEvent = match serde_json::from_str::<InputEvent>(&line) {
            Ok(v) => v,
            Err(_) => {
                // Skip unknown line shapes
                continue
            }
        };
        let ts = ev.ts;
        let x = ev.idx[0];
        let y = ev.idx[1];
        let pol = ev.idx[2];

        if y < 0 || y >= height as i64 || pol < 0 || pol > 1 {
            continue;
        }

        let key_a = (x, y, pol);
        let a_deq = a_map.entry(key_a).or_insert_with(VecDeque::new);
        a_deq.push_back(ts);

        let cutoff = ts.saturating_sub(window_us);

        // Check east-sourced B-events at current location
        if let Some(deq_e) = east_map.get_mut(&key_a) {
            prune(a_deq, cutoff);
            prune(deq_e, cutoff);
            if !a_deq.is_empty() && !deq_e.is_empty() && (a_deq.len() + deq_e.len()) >= min_count {
                if seen.insert((ts, x, y, pol)) {
                    out_events.push((ts, x, y, pol));
                }
            }
        }

        // Check west-sourced B-events at current location
        if let Some(deq_w) = west_map.get_mut(&key_a) {
            prune(a_deq, cutoff);
            prune(deq_w, cutoff);
            if !a_deq.is_empty() && !deq_w.is_empty() && (a_deq.len() + deq_w.len()) >= min_count {
                if seen.insert((ts, x, y, pol)) {
                    out_events.push((ts, x, y, pol));
                }
            }
        }

        // Generate future B-events
        let b_ts = ts.saturating_add(eff_delay);
        let cutoff_b = b_ts.saturating_sub(window_us);

        // Eastward fan-out: event at `x` creates B-event at `x+1`
        if x + 1 < width as i64 {
            let key_e = (x + 1, y, pol);
            let b_deq_e = east_map.entry(key_e).or_insert_with(VecDeque::new);
            b_deq_e.push_back(b_ts);
            if let Some(a_deq_e) = a_map.get_mut(&key_e) {
                prune(a_deq_e, cutoff_b);
                prune(b_deq_e, cutoff_b);
                if !a_deq_e.is_empty() && !b_deq_e.is_empty() && (a_deq_e.len() + b_deq_e.len()) >= min_count {
                    if seen.insert((b_ts, x + 1, y, pol)) {
                        out_events.push((b_ts, x + 1, y, pol));
                    }
                }
            }
        }

        // Westward fan-out: event at `x` creates B-event at `x-1`
        if x > 0 {
            let key_w = (x - 1, y, pol);
            let b_deq_w = west_map.entry(key_w).or_insert_with(VecDeque::new);
            b_deq_w.push_back(b_ts);
            if let Some(a_deq_w) = a_map.get_mut(&key_w) {
                prune(a_deq_w, cutoff_b);
                prune(b_deq_w, cutoff_b);
                if !a_deq_w.is_empty() && !b_deq_w.is_empty() && (a_deq_w.len() + b_deq_w.len()) >= min_count {
                    if seen.insert((b_ts, x - 1, y, pol)) {
                        out_events.push((b_ts, x - 1, y, pol));
                    }
                }
            }
        }
    }

    // Build header dict (inner header payload), matching golden schema shape
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
    md.set_item("kernel", "optical_flow_shift_delay_fuse")?;
    hdr.set_item("metadata", md)?;

    // If the source had a header, we can try to override dims if provided (best-effort)
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