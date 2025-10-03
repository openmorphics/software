use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::{prelude::*, Py};
use pyo3::create_exception;
use once_cell::sync::OnceCell;
use std::sync::RwLock;
use std::collections::VecDeque;

// Custom Python exceptions
create_exception!(eventflow_core_native, BucketError, pyo3::exceptions::PyException);
create_exception!(eventflow_core_native, FuseError, pyo3::exceptions::PyException);

// Global optional logging sink (callable)
static LOG_SINK: OnceCell<RwLock<Option<Py<PyAny>>>> = OnceCell::new();

#[pyfunction]
fn is_ready() -> bool {
    true
}

#[pyfunction]
fn sum_f32(a: f32, b: f32) -> f32 {
    a + b
}

#[pyfunction]
fn sum_ndarray_f32(_py: Python<'_>, arr: PyReadonlyArray1<f32>) -> PyResult<f32> {
    let a = arr.as_array();
    let sum = a.sum();
    Ok(sum)
}

/// Bucketize and sum values over fixed windows:
/// - Inputs: times (ns, i64), values (f32), and dt_ns (i64)
/// - For each event (t, v), assign bucket key k = floor(t / dt_ns) * dt_ns
/// - Aggregate contiguous runs (groupby semantics) and emit at (k + dt_ns)
/// Returns: (times_out_ns: i64[], sums_out: f32[])
#[pyfunction]
fn bucket_sum_i64_f32<'py>(
    py: Python<'py>,
    t_ns: PyReadonlyArray1<i64>,
    vals: PyReadonlyArray1<f32>,
    dt_ns: i64,
) -> PyResult<(Py<PyArray1<i64>>, Py<PyArray1<f32>>)> {
    if dt_ns <= 0 {
        return Err(BucketError::new_err("dt_ns must be > 0"));
    }
    let t_a = t_ns.as_array();
    let v_a = vals.as_array();
    if t_a.len() != v_a.len() {
        return Err(BucketError::new_err("t_ns and vals must have the same length"));
    }

    // Implement contiguous-run aggregation to mirror itertools.groupby behavior
    let mut out_t: Vec<i64> = Vec::new();
    let mut out_v: Vec<f32> = Vec::new();

    if t_a.len() == 0 {
        let t_arr = PyArray1::from_vec(py, out_t).unbind();
        let v_arr = PyArray1::from_vec(py, out_v).unbind();
        return Ok((t_arr, v_arr));
    }

    let mut prev_key: i64 = (t_a[0] / dt_ns) * dt_ns;
    let mut acc_f64: f64 = v_a[0] as f64;

    for (&t, &v) in t_a.iter().zip(v_a.iter()).skip(1) {
        let key = (t / dt_ns) * dt_ns;
        if key == prev_key {
            acc_f64 += v as f64;
        } else {
            // Flush previous bucket at boundary (k + dt)
            out_t.push(prev_key + dt_ns);
            out_v.push(acc_f64 as f32);
            // Start new bucket
            prev_key = key;
            acc_f64 = v as f64;
        }
    }

    // Flush final bucket
    out_t.push(prev_key + dt_ns);
    out_v.push(acc_f64 as f32);

    let t_arr = PyArray1::from_vec(py, out_t).unbind();
    let v_arr = PyArray1::from_vec(py, out_v).unbind();
    Ok((t_arr, v_arr))
}

/// Coincidence fuse detector:
/// Given event times for streams A and B, a window in ns, and min_count,
/// emit a coincidence at time t when both buffers have at least one event
/// within [t - window, t], and the total count across A and B in the window
/// is at least min_count. Returns times and values (all ones).
#[pyfunction]
fn fuse_coincidence_i64<'py>(
    py: Python<'py>,
    t_a: PyReadonlyArray1<i64>,
    t_b: PyReadonlyArray1<i64>,
    window_ns: i64,
    min_count: usize,
) -> PyResult<(Py<PyArray1<i64>>, Py<PyArray1<f32>>)> {
    if window_ns <= 0 {
        return Err(FuseError::new_err("window_ns must be > 0"));
    }
    let a = t_a.as_array();
    let b = t_b.as_array();

    // Merge timestamps with source tags (0 for A, 1 for B) and sort.
    let mut merged: Vec<(i64, u8)> = Vec::with_capacity(a.len() + b.len());
    for &t in a.iter() { merged.push((t, 0)); }
    for &t in b.iter() { merged.push((t, 1)); }
    merged.sort_by_key(|x| x.0);

    let mut buf_a: VecDeque<i64> = VecDeque::new();
    let mut buf_b: VecDeque<i64> = VecDeque::new();
    let mut out_t: Vec<i64> = Vec::new();
    let mut out_v: Vec<f32> = Vec::new();

    for (t, src) in merged.into_iter() {
        if src == 0 { buf_a.push_back(t); } else { buf_b.push_back(t); }
        let cutoff = t - window_ns;

        while let Some(&front) = buf_a.front() {
            if front < cutoff { buf_a.pop_front(); } else { break; }
        }
        while let Some(&front) = buf_b.front() {
            if front < cutoff { buf_b.pop_front(); } else { break; }
        }

        let total = buf_a.len() + buf_b.len();
        if total >= min_count && !buf_a.is_empty() && !buf_b.is_empty() {
            out_t.push(t);
            out_v.push(1.0f32);
        }
    }

    let t_arr = PyArray1::from_vec(py, out_t).unbind();
    let v_arr = PyArray1::from_vec(py, out_v).unbind();
    Ok((t_arr, v_arr))
}

// Logging bridge API
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

#[pymodule]
fn _native(m: &Bound<PyModule>) -> PyResult<()> {
    let py = m.py();
    m.add("RUST_ENABLED", true)?;
    // Export custom exception types
    m.add("BucketError", py.get_type::<BucketError>())?;
    m.add("FuseError", py.get_type::<FuseError>())?;
    // Functions
    m.add_function(wrap_pyfunction!(is_ready, m)?)?;
    m.add_function(wrap_pyfunction!(sum_f32, m)?)?;
    m.add_function(wrap_pyfunction!(sum_ndarray_f32, m)?)?;
    m.add_function(wrap_pyfunction!(bucket_sum_i64_f32, m)?)?;
    m.add_function(wrap_pyfunction!(fuse_coincidence_i64, m)?)?;
    m.add_function(wrap_pyfunction!(set_log_sink, m)?)?;
    m.add_function(wrap_pyfunction!(log_emit, m)?)?;
    Ok(())
}