//! Scenario simulation engine.

use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use uuid::Uuid;
use std::collections::HashMap;

use vcfo_core::{
    errors::{Result, VcfoError},
    models::*,
};

/// Configuration for Monte Carlo simulations.
#[derive(Debug, Clone)]
pub struct MonteCarloConfig {
    pub iterations: u32,
    pub confidence_levels: Vec<f32>,  // e.g., [0.50, 0.75, 0.90, 0.95]
    pub variable_ranges: HashMap<String, VariableRange>,
}

impl Default for MonteCarloConfig {
    fn default() -> Self {
        Self {
            iterations: 1000,
            confidence_levels: vec![0.50, 0.75, 0.90, 0.95],
            variable_ranges: HashMap::new(),
        }
    }
}

/// Range for a variable in Monte Carlo simulation.
#[derive(Debug, Clone)]
pub struct VariableRange {
    pub min: Decimal,
    pub max: Decimal,
    pub distribution: Distribution,
}

/// Distribution types for Monte Carlo variables.
#[derive(Debug, Clone)]
pub enum Distribution {
    Uniform,
    Normal { mean: f64, std_dev: f64 },
    Beta { alpha: f64, beta: f64 },
    Triangular { mode: f64 },
}

/// Results from Monte Carlo simulation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonteCarloResult {
    pub iterations_run: u32,
    pub percentiles: HashMap<u32, RunwayResult>,  // P50, P75, P90, P95
    pub probability_distribution: Vec<(f32, f32)>, // (runway_months, probability)
    pub confidence_intervals: Vec<ConfidenceInterval>,
}

/// Confidence interval for a metric.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfidenceInterval {
    pub level: f32,
    pub lower_bound: f32,
    pub upper_bound: f32,
    pub metric: String,
}

/// Results from sensitivity analysis.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensitivityResult {
    pub variable_impacts: HashMap<String, VariableImpact>,
    pub tornado_chart_data: Vec<TornadoBar>,
}

/// Impact of a variable on the result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VariableImpact {
    pub variable_name: String,
    pub base_value: f32,
    pub impact_on_runway: f32,
    pub sensitivity_coefficient: f32,
}

/// Data for tornado chart visualization.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TornadoBar {
    pub variable: String,
    pub low_impact: f32,
    pub high_impact: f32,
    pub base_case: f32,
}

/// Results from optimization analysis.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationResult {
    pub target_runway: f32,
    pub current_runway: f32,
    pub recommended_changes: Vec<RecommendedChange>,
    pub feasibility_score: f32,
}

/// Recommended change to improve runway.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OptimizationAction {
    CutExpenses { category: ExpenseType, percentage: Decimal },
    IncreaseRevenue { amount: Decimal, time_frame_months: u32 },
    RaiseFunding { amount: Decimal, dilution: Option<Decimal> },
    ReduceBurnRate { percentage: Decimal },
}

/// Difficulty level for implementing a change.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Difficulty {
    Easy,
    Medium,
    Hard,
    VeryHard,
}

/// Scenario simulation engine.
#[derive(Debug)]
pub struct ScenarioEngine {
    base_calculation: RunwayCalculation,
    monte_carlo_config: MonteCarloConfig,
}

impl ScenarioEngine {
    /// Create a new scenario engine.
    pub fn new(base_calculation: RunwayCalculation) -> Self {
        Self {
            base_calculation,
            monte_carlo_config: MonteCarloConfig::default(),
        }
    }

    /// Simulate a single scenario.
    pub fn simulate_single(&self, scenario: Scenario) -> Result<ScenarioResult> {
        // This would use the calculator to simulate the scenario
        // For now, return a placeholder
        Err(VcfoError::CalculationError("Not implemented".to_string()))
    }

    /// Simulate multiple scenarios.
    pub fn simulate_multiple(&self, scenarios: Vec<Scenario>) -> Result<Vec<ScenarioResult>> {
        let mut results = Vec::new();
        for scenario in scenarios {
            results.push(self.simulate_single(scenario)?);
        }
        Ok(results)
    }

    /// Run Monte Carlo simulation.
    pub fn monte_carlo_simulation(&self) -> Result<MonteCarloResult> {
        // Placeholder implementation
        Err(VcfoError::CalculationError("Monte Carlo simulation not implemented".to_string()))
    }

    /// Run sensitivity analysis.
    pub fn sensitivity_analysis(&self, variables: Vec<String>) -> Result<SensitivityResult> {
        // Placeholder implementation
        Err(VcfoError::CalculationError("Sensitivity analysis not implemented".to_string()))
    }

    /// Optimize for target runway.
    pub fn optimize_for_runway(&self, target_months: f32) -> Result<OptimizationResult> {
        // Placeholder implementation
        Err(VcfoError::CalculationError("Optimization not implemented".to_string()))
    }
}

/// Helper function to generate common scenarios.
pub struct ScenarioBuilder;

impl ScenarioBuilder {
    /// Create a "worst case" scenario.
    pub fn worst_case() -> Scenario {
        Scenario {
            id: Uuid::new_v4(),
            name: "Worst Case".to_string(),
            description: "Revenue drops 30%, expenses increase 20%".to_string(),
            adjustments: ScenarioAdjustments {
                burn_rate_change: Some(Decimal::from_str("0.20").unwrap()),
                revenue_change: Some(Decimal::from_str("-0.30").unwrap()),
                growth_rate_change: Some(Decimal::from_str("-0.02").unwrap()),
                headcount_change: Some(2),
                new_funding: None,
                expense_cuts: vec![],
                new_revenue_streams: vec![],
            },
        }
    }

    /// Create a "best case" scenario.
    pub fn best_case() -> Scenario {
        Scenario {
            id: Uuid::new_v4(),
            name: "Best Case".to_string(),
            description: "Revenue grows 50%, expenses cut 15%".to_string(),
            adjustments: ScenarioAdjustments {
                burn_rate_change: Some(Decimal::from_str("-0.15").unwrap()),
                revenue_change: Some(Decimal::from_str("0.50").unwrap()),
                growth_rate_change: Some(Decimal::from_str("0.03").unwrap()),
                headcount_change: Some(-1),
                new_funding: None,
                expense_cuts: vec![
                    ExpenseCut {
                        category: ExpenseType::Marketing,
                        percentage: Decimal::from_str("0.20").unwrap(),
                        effective_date: Utc::now(),
                    }
                ],
                new_revenue_streams: vec![],
            },
        }
    }

    /// Create a funding delay scenario.
    pub fn funding_delay(delay_months: u32) -> Scenario {
        let delayed_date = Utc::now() + chrono::Duration::days(delay_months as i64 * 30);

        Scenario {
            id: Uuid::new_v4(),
            name: format!("Funding Delay ({} months)", delay_months),
            description: format!("Funding round delayed by {} months", delay_months),
            adjustments: ScenarioAdjustments {
                burn_rate_change: None,
                revenue_change: None,
                growth_rate_change: None,
                headcount_change: None,
                new_funding: Some(FundingRound {
                    amount: Decimal::from(1000000), // Assume $1M round
                    expected_date: Some(delayed_date),
                    probability: 0.8,
                    dilution_percentage: Some(Decimal::from_str("0.15").unwrap()),
                }),
                expense_cuts: vec![],
                new_revenue_streams: vec![],
            },
        }
    }

    /// Create a hiring freeze scenario.
    pub fn hiring_freeze() -> Scenario {
        Scenario {
            id: Uuid::new_v4(),
            name: "Hiring Freeze".to_string(),
            description: "Freeze hiring, cut discretionary expenses".to_string(),
            adjustments: ScenarioAdjustments {
                burn_rate_change: Some(Decimal::from_str("-0.10").unwrap()),
                revenue_change: None,
                growth_rate_change: None,
                headcount_change: Some(0), // No new hires
                new_funding: None,
                expense_cuts: vec![
                    ExpenseCut {
                        category: ExpenseType::Marketing,
                        percentage: Decimal::from_str("0.30").unwrap(),
                        effective_date: Utc::now(),
                    },
                    ExpenseCut {
                        category: ExpenseType::Office,
                        percentage: Decimal::from_str("0.25").unwrap(),
                        effective_date: Utc::now(),
                    },
                ],
                new_revenue_streams: vec![],
            },
        }
    }
}