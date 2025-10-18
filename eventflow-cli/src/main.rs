mod compare;

use compare::{run, CompareOptions};
use std::env;
use std::path::PathBuf;
use std::process::ExitCode;

fn print_top_help() {
    println!(
        "EventFlow CLI (Rust)
Usage:
  ef <subcommand> [options]

Subcommands:
  compare    Compare two UEC JSONL traces with time/value tolerances.

Run:
  ef compare --help
for detailed options and examples."
    );
}

fn print_compare_help() {
    println!(
        "ef compare --gold <gold.jsonl> --test <test.jsonl> --tolerance-time <seconds f64> --tolerance-val <f64>

Options:
  --gold PATH             Path to golden/reference UEC JSONL file.
  --test PATH             Path to candidate/test UEC JSONL file.
  --tolerance-time F64    Allowed absolute timestamp delta in seconds.
  --tolerance-val F64     Allowed absolute numeric payload delta.

Behavior:
  - Parses both files line-by-line; collects event-bearing lines (type == \"event\" or \"deliver\").
  - Skips lines with type == \"meta\" (non-fatal; reported as counts).
  - Compares event sequences in-order; lengths must match.
  - For each pair, checks |t_s_gold - t_s_test| ≤ tolerance-time.
  - If both have a payload with numeric fields, checks |gold - test| ≤ tolerance-val per numeric key (optional if missing).

Example:
  ef compare --gold out/golden.jsonl --test out/candidate.jsonl --tolerance-time 1e-6 --tolerance-val 1e-5"
    );
}

fn parse_compare_args(mut args: impl Iterator<Item = String>) -> Result<CompareOptions, String> {
    let mut gold: Option<PathBuf> = None;
    let mut test: Option<PathBuf> = None;
    let mut tol_time: Option<f64> = None;
    let mut tol_val: Option<f64> = None;

    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--help" | "-h" => {
                print_compare_help();
                return Err(String::from("__HELP__"));
            }
            "--gold" => {
                gold = Some(PathBuf::from(
                    args.next().ok_or_else(|| "Expected value after --gold".to_string())?,
                ));
            }
            "--test" => {
                test = Some(PathBuf::from(
                    args.next().ok_or_else(|| "Expected value after --test".to_string())?,
                ));
            }
            "--tolerance-time" => {
                let v = args
                    .next()
                    .ok_or_else(|| "Expected value after --tolerance-time".to_string())?;
                tol_time = Some(v.parse::<f64>().map_err(|_| "Invalid float for --tolerance-time".to_string())?);
            }
            "--tolerance-val" => {
                let v = args
                    .next()
                    .ok_or_else(|| "Expected value after --tolerance-val".to_string())?;
                tol_val = Some(v.parse::<f64>().map_err(|_| "Invalid float for --tolerance-val".to_string())?);
            }
            other => {
                return Err(format!("Unknown option for compare: {other}"));
            }
        }
    }

    let gold = gold.ok_or_else(|| "Missing required --gold".to_string())?;
    let test = test.ok_or_else(|| "Missing required --test".to_string())?;
    let tol_time = tol_time.ok_or_else(|| "Missing required --tolerance-time".to_string())?;
    let tol_val = tol_val.ok_or_else(|| "Missing required --tolerance-val".to_string())?;

    Ok(CompareOptions {
        gold,
        test,
        tol_time,
        tol_val,
    })
}

fn main() -> ExitCode {
    let mut args = env::args();
    let _exe = args.next(); // program name

    let Some(sub) = args.next() else {
        print_top_help();
        return ExitCode::SUCCESS;
    };

    match sub.as_str() {
        "compare" => {
            match parse_compare_args(args) {
                Ok(opts) => match run(opts) {
                    Ok(summary) => {
                        println!(
                            "OK: matched {} events (meta gold={}, test={}) within tol_time={}s tol_val={}",
                            summary.events, summary.meta_gold, summary.meta_test, summary.tol_time, summary.tol_val
                        );
                        ExitCode::SUCCESS
                    }
                    Err(msg) => {
                        eprintln!("COMPARE MISMATCH: {msg}");
                        ExitCode::from(1)
                    }
                },
                Err(e) => {
                    if e != "__HELP__" {
                        eprintln!("Error: {e}\n");
                        print_compare_help();
                    }
                    ExitCode::from(2)
                }
            }
        }
        "--help" | "-h" => {
            print_top_help();
            ExitCode::SUCCESS
        }
        other => {
            eprintln!("Unknown subcommand: {other}\n");
            print_top_help();
            ExitCode::from(2)
        }
    }
}