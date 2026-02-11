//! # Virtual CFO Runway Calculator
//!
//! Core engine for calculating startup runway with scenario planning.

pub mod calculator;
pub mod scenarios;
pub mod alerts;

pub use calculator::*;
pub use scenarios::*;
pub use alerts::*;