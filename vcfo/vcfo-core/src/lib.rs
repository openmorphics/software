//! # Virtual CFO Core Library
//!
//! Core financial calculations and domain models for startup runway analysis.

pub mod errors;
pub mod metrics;
pub mod models;

pub use errors::*;
pub use metrics::*;
pub use models::*;

#[cfg(test)]
mod tests {
    use super::*;
    use rust_decimal_macros::dec;

    #[test]
    fn test_calculate_arr() {
        let monthly_revenue = dec!(10000);
        let arr = calculate_arr(monthly_revenue);
        assert_eq!(arr, dec!(120000));
    }

    #[test]
    fn test_calculate_mrr() {
        let annual_revenue = dec!(120000);
        let mrr = calculate_mrr(annual_revenue);
        assert_eq!(mrr, dec!(10000));
    }

    #[test]
    fn test_calculate_runway_months() {
        let cash = dec!(500000);
        let burn = dec!(50000);
        let runway = calculate_runway_months(cash, burn).unwrap();
        assert!((runway - 10.0).abs() < 0.1);
    }

    #[test]
    fn test_calculate_runway_months_zero_burn() {
        let cash = dec!(500000);
        let burn = dec!(0);
        let result = calculate_runway_months(cash, burn);
        assert!(result.is_err());
    }
}