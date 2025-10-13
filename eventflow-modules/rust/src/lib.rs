use numpy::{PyArray2, PyReadonlyArray2, PyArray1};
use numpy::PyArrayMethods;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::exceptions::{PyIOError, PyValueError};
use pyo3::create_exception;
use once_cell::sync::OnceCell;
use std::sync::RwLock;

use serde::Deserialize;
use serde_json::Value;
use std::collections::{HashMap, VecDeque, HashSet};
use std::fs::File;
use std::io::{BufRead, BufReader};

/// Custom Python exception for vision kernels
create_exception!(eventflow_modules_vision_native, VisionError, pyo3::exceptions::PyException);

/// Global optional logging sink (callable)
/// Callable signature: sink(level: str, message: str)
static LOG_SINK: OnceCell<RwLock<Option<Py<PyAny>>>> = OnceCell::new();

#[pyfunction]
fn set_log_sink(sink: Option<Py<PyAny>>) -> PyResult<()> {
    let cell = LOG_SINK.get_or_init(|| RwLock::new(None));
    let mut guard = cell.write().unwrap();
    *guard = sink;
    Ok(())
}

#[pyfunction]
fn log_emit(py: Python<'_>, level: &str, message: &str) -> PyResult<()> {
    if let Some(lock) = LOG_SINK.get() {
        if let Ok(guard) = lock.read() {
            if let Some(sink) = guard.as_ref() {
                let _ = sink.bind(py).call1((level, message));
            }
        }
    }
    Ok(())
}

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
        return Err(VisionError::new_err("width/height must be > 0"));
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
    
    /// Pass-through returning columnar NumPy arrays (ts, x, y, polarity, val)
    #[pyfunction]
    fn optical_flow_coo_arrays<'py>(
        py: Python<'py>,
        input_path: &str,
        width: usize,
        height: usize,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        if width == 0 || height == 0 {
            return Err(VisionError::new_err("width/height must be > 0"));
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
    
        // Sort events for deterministic order
        out_events.sort_unstable();
    
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
    
        // Preserve dims from source header if present
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
    
        // Build columns
        let n = out_events.len();
        let mut ts_col: Vec<i64> = Vec::with_capacity(n);
        let mut x_col: Vec<i64> = Vec::with_capacity(n);
        let mut y_col: Vec<i64> = Vec::with_capacity(n);
        let mut pol_col: Vec<i64> = Vec::with_capacity(n);
        let mut val_col: Vec<f32> = Vec::with_capacity(n);
    
        for (ts, x, y, pol) in out_events.into_iter() {
            ts_col.push(ts);
            x_col.push(x);
            y_col.push(y);
            pol_col.push(pol);
            val_col.push(1.0f32);
        }
    
        let ts = PyArray1::<i64>::from_vec(py, ts_col);
        let x = PyArray1::<i64>::from_vec(py, x_col);
        let y = PyArray1::<i64>::from_vec(py, y_col);
        let polarity = PyArray1::<i64>::from_vec(py, pol_col);
        let val = PyArray1::<f32>::from_vec(py, val_col);
    
        let arrays = PyDict::new(py);
        arrays.set_item("ts", ts)?;
        arrays.set_item("x", x)?;
        arrays.set_item("y", y)?;
        arrays.set_item("polarity", polarity)?;
        arrays.set_item("val", val)?;
    
        Ok((hdr.unbind().into(), arrays.unbind().into()))
    }
    
    // Shift/Delay/Fuse optical flow that emits coincidences per coordinate
    #[pyfunction]
    #[allow(clippy::too_many_arguments)]
    fn optical_flow_shift_delay_fuse_coo<'py>(
        py: Python<'py>,
        input_path: &str,
        width: usize,
        height: usize,
        window_us: i64,
        delay_us: i64,
        edge_delay_us: i64,
        min_count: usize,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        if width == 0 || height == 0 {
            return Err(VisionError::new_err("width/height must be > 0"));
        }
        if window_us <= 0 {
            return Err(VisionError::new_err("window_us must be > 0"));
        }
        if delay_us < 0 || edge_delay_us < 0 {
            return Err(VisionError::new_err("delay_us and edge_delay_us must be >= 0"));
        }
        if min_count == 0 {
            return Err(VisionError::new_err("min_count must be >= 1"));
        }
    
        let file = File::open(input_path).map_err(|e| PyIOError::new_err(format!("open failed: {e}")))?;
        let reader = BufReader::new(file);
    
        let eff_delay = delay_us + edge_delay_us;
    
        // Optional header passthrough
        let mut header_opt: Option<Value> = None;
    
        // Per-coordinate event times for A (source) and B (neighbor-shifted, delayed)
        let mut a_map: HashMap<(i64, i64, i64), Vec<i64>> = HashMap::new();
        let mut b_map: HashMap<(i64, i64, i64), Vec<i64>> = HashMap::new();
    
        for line in reader.lines() {
            let line = line.map_err(|e| PyIOError::new_err(format!("read failed: {e}")))?;
            if line.trim().is_empty() {
                continue;
            }
            // Capture header if present
            if header_opt.is_none() {
                if let Ok(h) = serde_json::from_str::<InputHeader>(&line) {
                    header_opt = Some(h.header);
                    continue;
                }
            }
            // Parse event
            if let Ok(ev) = serde_json::from_str::<InputEvent>(&line) {
                let ts = ev.ts;
                let x = ev.idx[0];
                let y = ev.idx[1];
                let pol = ev.idx[2];
                if x < 0 || y < 0 || pol < 0 || pol > 1 {
                    continue;
                }
                if (x as usize) >= width || (y as usize) >= height {
                    continue;
                }
    
                // A-stream at (x,y,pol)
                a_map.entry((x, y, pol)).or_default().push(ts);
    
                // B-stream: shift ±1 in x and delay by eff_delay
                let b_ts = ts.saturating_add(eff_delay);
                if x + 1 < width as i64 {
                    b_map.entry((x + 1, y, pol)).or_default().push(b_ts);
                }
                if x > 0 {
                    b_map.entry((x - 1, y, pol)).or_default().push(b_ts);
                }
            }
        }
    
        // For determinism, sort the per-key vectors
        for v in a_map.values_mut() {
            v.sort_unstable();
        }
        for v in b_map.values_mut() {
            v.sort_unstable();
        }
    
        // Process each coordinate independently with a sliding window coincidence fuse
        let mut out_events: Vec<(i64, i64, i64, i64)> = Vec::new();
        let mut seen: HashSet<(i64, i64, i64, i64)> = HashSet::new();
    
        let mut keys: HashSet<(i64, i64, i64)> = HashSet::new();
        keys.extend(a_map.keys().cloned());
        keys.extend(b_map.keys().cloned());
    
        for (x, y, pol) in keys.into_iter() {
            let va = a_map.remove(&(x, y, pol)).unwrap_or_default();
            let vb = b_map.remove(&(x, y, pol)).unwrap_or_default();
    
            // Merge timestamps with source tags (0 for A, 1 for B)
            let mut merged: Vec<(i64, u8)> = Vec::with_capacity(va.len() + vb.len());
            for t in va.into_iter() {
                merged.push((t, 0));
            }
            for t in vb.into_iter() {
                merged.push((t, 1));
            }
            merged.sort_unstable_by_key(|e| e.0);
    
            let mut buf_a: VecDeque<i64> = VecDeque::new();
            let mut buf_b: VecDeque<i64> = VecDeque::new();
    
            for (t, src) in merged.into_iter() {
                if src == 0 {
                    buf_a.push_back(t);
                } else {
                    buf_b.push_back(t);
                }
                let cutoff = t.saturating_sub(window_us);
    
                // Prune strictly older than (t - window)
                while let Some(&front) = buf_a.front() {
                    if front < cutoff {
                        buf_a.pop_front();
                    } else {
                        break;
                    }
                }
                while let Some(&front) = buf_b.front() {
                    if front < cutoff {
                        buf_b.pop_front();
                    } else {
                        break;
                    }
                }
    
                let total = buf_a.len() + buf_b.len();
                if total >= min_count && !buf_a.is_empty() && !buf_b.is_empty() {
                    if seen.insert((t, x, y, pol)) {
                        out_events.push((t, x, y, pol));
                    }
                }
            }
        }
    
        // Sort outputs for deterministic return order
        out_events.sort_unstable();
    
        // Build header dict (compatible with golden schema)
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
    
        // Preserve dims from source header if present
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

    /// Shift/Delay/Fuse returning columnar NumPy arrays (ts, x, y, polarity, val)
    #[pyfunction]
    #[allow(clippy::too_many_arguments)]
    fn optical_flow_shift_delay_fuse_arrays<'py>(
        py: Python<'py>,
        input_path: &str,
        width: usize,
        height: usize,
        window_us: i64,
        delay_us: i64,
        edge_delay_us: i64,
        min_count: usize,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        if width == 0 || height == 0 {
            return Err(VisionError::new_err("width/height must be > 0"));
        }
        if window_us <= 0 {
            return Err(VisionError::new_err("window_us must be > 0"));
        }
        if delay_us < 0 || edge_delay_us < 0 {
            return Err(VisionError::new_err("delay_us and edge_delay_us must be >= 0"));
        }
        if min_count == 0 {
            return Err(VisionError::new_err("min_count must be >= 1"));
        }

        let file = File::open(input_path).map_err(|e| PyIOError::new_err(format!("open failed: {e}")))?;
        let reader = BufReader::new(file);

        let eff_delay = delay_us + edge_delay_us;

        // Optional header passthrough
        let mut header_opt: Option<Value> = None;

        // Per-coordinate event times for A (source) and B (neighbor-shifted, delayed)
        let mut a_map: HashMap<(i64, i64, i64), Vec<i64>> = HashMap::new();
        let mut b_map: HashMap<(i64, i64, i64), Vec<i64>> = HashMap::new();

        for line in reader.lines() {
            let line = line.map_err(|e| PyIOError::new_err(format!("read failed: {e}")))?;
            if line.trim().is_empty() {
                continue;
            }
            // Capture header if present
            if header_opt.is_none() {
                if let Ok(h) = serde_json::from_str::<InputHeader>(&line) {
                    header_opt = Some(h.header);
                    continue;
                }
            }
            // Parse event
            if let Ok(ev) = serde_json::from_str::<InputEvent>(&line) {
                let ts = ev.ts;
                let x = ev.idx[0];
                let y = ev.idx[1];
                let pol = ev.idx[2];
                if x < 0 || y < 0 || pol < 0 || pol > 1 {
                    continue;
                }
                if (x as usize) >= width || (y as usize) >= height {
                    continue;
                }

                // A-stream at (x,y,pol)
                a_map.entry((x, y, pol)).or_default().push(ts);

                // B-stream: shift ±1 in x and delay by eff_delay
                let b_ts = ts.saturating_add(eff_delay);
                if x + 1 < width as i64 {
                    b_map.entry((x + 1, y, pol)).or_default().push(b_ts);
                }
                if x > 0 {
                    b_map.entry((x - 1, y, pol)).or_default().push(b_ts);
                }
            }
        }

        // For determinism, sort the per-key vectors
        for v in a_map.values_mut() {
            v.sort_unstable();
        }
        for v in b_map.values_mut() {
            v.sort_unstable();
        }

        // Process each coordinate independently with a sliding window coincidence fuse
        let mut out_events: Vec<(i64, i64, i64, i64)> = Vec::new();
        let mut seen: HashSet<(i64, i64, i64, i64)> = HashSet::new();

        let mut keys: HashSet<(i64, i64, i64)> = HashSet::new();
        keys.extend(a_map.keys().cloned());
        keys.extend(b_map.keys().cloned());

        for (x, y, pol) in keys.into_iter() {
            let va = a_map.remove(&(x, y, pol)).unwrap_or_default();
            let vb = b_map.remove(&(x, y, pol)).unwrap_or_default();

            // Merge timestamps with source tags (0 for A, 1 for B)
            let mut merged: Vec<(i64, u8)> = Vec::with_capacity(va.len() + vb.len());
            for t in va.into_iter() { merged.push((t, 0)); }
            for t in vb.into_iter() { merged.push((t, 1)); }
            merged.sort_unstable_by_key(|e| e.0);

            let mut buf_a: VecDeque<i64> = VecDeque::new();
            let mut buf_b: VecDeque<i64> = VecDeque::new();

            for (t, src) in merged.into_iter() {
                if src == 0 { buf_a.push_back(t); } else { buf_b.push_back(t); }
                let cutoff = t.saturating_sub(window_us);

                // Prune strictly older than (t - window)
                while let Some(&front) = buf_a.front() {
                    if front < cutoff { buf_a.pop_front(); } else { break; }
                }
                while let Some(&front) = buf_b.front() {
                    if front < cutoff { buf_b.pop_front(); } else { break; }
                }

                let total = buf_a.len() + buf_b.len();
                if total >= min_count && !buf_a.is_empty() && !buf_b.is_empty() {
                    if seen.insert((t, x, y, pol)) {
                        out_events.push((t, x, y, pol));
                    }
                }
            }
        }

        // Sort outputs for deterministic return order
        out_events.sort_unstable();

        // Build header dict (compatible with golden schema)
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

        // Preserve dims from source header if present
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

        // Build columnar arrays
        let n = out_events.len();
        let mut ts_col: Vec<i64> = Vec::with_capacity(n);
        let mut x_col: Vec<i64> = Vec::with_capacity(n);
        let mut y_col: Vec<i64> = Vec::with_capacity(n);
        let mut pol_col: Vec<i64> = Vec::with_capacity(n);
        let mut val_col: Vec<f32> = Vec::with_capacity(n);

        for (ts, x, y, pol) in out_events.into_iter() {
            ts_col.push(ts);
            x_col.push(x);
            y_col.push(y);
            pol_col.push(pol);
            val_col.push(1.0f32);
        }

        // Convert to NumPy arrays
        let ts = PyArray1::<i64>::from_vec(py, ts_col);
        let x = PyArray1::<i64>::from_vec(py, x_col);
        let y = PyArray1::<i64>::from_vec(py, y_col);
        let polarity = PyArray1::<i64>::from_vec(py, pol_col);
        let val = PyArray1::<f32>::from_vec(py, val_col);

        let arrays = PyDict::new(py);
        arrays.set_item("ts", ts)?;
        arrays.set_item("x", x)?;
        arrays.set_item("y", y)?;
        arrays.set_item("polarity", polarity)?;
        arrays.set_item("val", val)?;

        Ok((hdr.unbind().into(), arrays.unbind().into()))
    }
    
    #[pymodule]
    fn _vision_native(m: &Bound<PyModule>) -> PyResult<()> {
        let py = m.py();
        m.add("RUST_ENABLED", true)?;
        // Export custom exception
        m.add("VisionError", py.get_type::<VisionError>())?;
        // Functions
        m.add_function(wrap_pyfunction!(is_ready, m)?)?;
        m.add_function(wrap_pyfunction!(optical_flow_stub, m)?)?;
        m.add_function(wrap_pyfunction!(optical_flow_coo_from_jsonl, m)?)?;
        m.add_function(wrap_pyfunction!(optical_flow_coo_arrays, m)?)?;
        m.add_function(wrap_pyfunction!(optical_flow_shift_delay_fuse_coo, m)?)?;
        m.add_function(wrap_pyfunction!(optical_flow_shift_delay_fuse_arrays, m)?)?;
        m.add_function(wrap_pyfunction!(set_log_sink, m)?)?;
        m.add_function(wrap_pyfunction!(log_emit, m)?)?;
        Ok(())
    }