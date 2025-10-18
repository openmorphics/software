use serde_json::Value;
use std::collections::HashSet;
use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::path::{Path, PathBuf};

pub struct CompareOptions {
    pub gold: PathBuf,
    pub test: PathBuf,
    pub tol_time: f64,
    pub tol_val: f64,
}

pub struct Summary {
    pub events: usize,
    pub meta_gold: usize,
    pub meta_test: usize,
    pub tol_time: f64,
    pub tol_val: f64,
}

pub fn run(opts: CompareOptions) -> Result<Summary, String> {
    let (gold_events, gold_meta) =
        parse_file(&opts.gold).map_err(|e| format!("Failed to read gold file: {e}"))?;
    let (test_events, test_meta) =
        parse_file(&opts.test).map_err(|e| format!("Failed to read test file: {e}"))?;

    if gold_events.len() != test_events.len() {
        return Err(format!(
            "Event length mismatch: gold={} test={}",
            gold_events.len(),
            test_events.len()
        ));
    }

    for (i, (g, t)) in gold_events.iter().zip(test_events.iter()).enumerate() {
        let kind_g = g.get("type").and_then(|v| v.as_str()).unwrap_or("?");
        let kind_t = t.get("type").and_then(|v| v.as_str()).unwrap_or("?");

        if kind_g != kind_t {
            return Err(format!(
                "Mismatch at idx={i}: kind gold='{kind_g}' test='{kind_t}'"
            ));
        }

        let tg = get_f64(g, "t_s").map_err(|_| format!("Missing/invalid t_s in gold at idx={i}"))?;
        let tt = get_f64(t, "t_s").map_err(|_| format!("Missing/invalid t_s in test at idx={i}"))?;
        let dt = (tg - tt).abs();
        if dt > opts.tol_time {
            return Err(format!(
                "Time mismatch at idx={i}: kind={kind_g} t_s_gold={tg} t_s_test={tt} Δt={dt} > tol_time={}",
                opts.tol_time
            ));
        }

        // Optional numeric payload comparison (non-fatal if absent).
        if let (Some(pg), Some(pt)) = (
            g.get("payload").and_then(|v| v.as_object()),
            t.get("payload").and_then(|v| v.as_object()),
        ) {
            // Intersect keys that are numeric on both sides
            let keys_g: HashSet<_> = pg
                .iter()
                .filter(|(_, v)| v.is_number())
                .map(|(k, _)| k.as_str())
                .collect();
            let keys_t: HashSet<_> = pt
                .iter()
                .filter(|(_, v)| v.is_number())
                .map(|(k, _)| k.as_str())
                .collect();
            for &k in keys_g.intersection(&keys_t) {
                let ng = pg.get(k).and_then(|v| v.as_f64()).unwrap_or(f64::NAN);
                let nt = pt.get(k).and_then(|v| v.as_f64()).unwrap_or(f64::NAN);
                if ng.is_finite() && nt.is_finite() {
                    let dv = (ng - nt).abs();
                    if dv > opts.tol_val {
                        return Err(format!(
                            "Payload numeric mismatch at idx={i}: kind={kind_g} key='{k}' gold={ng} test={nt} Δ={dv} > tol_val={}",
                            opts.tol_val
                        ));
                    }
                }
            }
        }
    }

    Ok(Summary {
        events: gold_events.len(),
        meta_gold: gold_meta.len(),
        meta_test: test_meta.len(),
        tol_time: opts.tol_time,
        tol_val: opts.tol_val,
    })
}

fn parse_file(path: &Path) -> io::Result<(Vec<Value>, Vec<Value>)> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut events = Vec::new();
    let mut metas = Vec::new();

    for line in reader.lines() {
        let line = match line {
            Ok(s) => s,
            Err(_) => continue, // ignore unreadable line
        };
        let s = line.trim();
        if s.is_empty() {
            continue;
        }
        let val: Value = match serde_json::from_str(s) {
            Ok(v) => v,
            Err(_) => continue, // treat unparseable as ignorable
        };
        match val.get("type").and_then(|v| v.as_str()) {
            Some("meta") => metas.push(val),
            Some("event") | Some("deliver") => events.push(val),
            _ => { /* ignore other types */ }
        }
    }
    Ok((events, metas))
}

fn get_f64(v: &Value, key: &str) -> Result<f64, ()> {
    if let Some(x) = v.get(key) {
        if let Some(f) = x.as_f64() {
            return Ok(f);
        }
        if let Some(s) = x.as_str() {
            if let Ok(f) = s.parse::<f64>() {
                return Ok(f);
            }
        }
    }
    Err(())
}