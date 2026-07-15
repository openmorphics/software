//! Error types for the Virtual CFO library.

use std::num::ParseIntError;
use thiserror::Error;

/// Main error type for Virtual CFO operations.
#[derive(Debug, Error)]
pub enum VcfoError {
    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("Calculation error: {0}")]
    CalculationError(String),

    #[error("Insufficient data: {0}")]
    InsufficientData(String),

    #[error("Configuration error: {0}")]
    ConfigError(String),

    #[error("Export error: {0}")]
    ExportError(String),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),

    #[error("Decimal parsing error: {0}")]
    DecimalError(#[from] rust_decimal::Error),

    #[error("UUID parsing error: {0}")]
    UuidError(#[from] uuid::Error),

    #[error("DateTime parsing error: {0}")]
    DateTimeError(String),
}

pub type Result<T> = std::result::Result<T, VcfoError>;