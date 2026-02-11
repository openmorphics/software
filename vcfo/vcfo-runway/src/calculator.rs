//! Core runway calculation engine.

use chrono::{DateTime, Duration, Utc};
use rust_decimal::Decimal;
use uuid::Uuid;
use std::collections::HashMap;

use vcfo_core::{
    errors::{Result, VcfoError},
    metrics::{calculate_runway_months, calculate_compound_growth},
    models::*,
};

/// Configuration for the runway calculator.
#[derive(Debug, Clone)]
pub struct CalculatorConfig {
    pub default_growth_rate: Decimal,
    pub include_probabilistic: bool,
    pub monte_carlo_iterations: u32,
    pub alert_thresholds: AlertThresholds,
    pub max_projection_months: u32,
}

impl Default for CalculatorConfig {
    fn default() -> Self {
        Self {
            default_growth_rate: Decimal::ZERO,
            include_probabilistic: false,
            monte_carlo_iterations: 1000,
            alert_thresholds: AlertThresholds::default(),
            max_projection_months: 24,
        }
    }
}

/// Main runway calculator.
#[derive(Debug)]
pub struct RunwayCalculator {
    config: CalculatorConfig,
}

impl RunwayCalculator {
    /// Create a new calculator with default configuration.
    pub fn new() -> Self {
        Self::with_config(CalculatorConfig::default())
    }

    /// Create a new calculator with custom configuration.
    pub fn with_config(config: CalculatorConfig) -> Self {
        Self { config }
    }

    /// Calculate runway from input parameters.
    pub fn calculate(&self, input: RunwayInput) -> Result<RunwayCalculation> {
        let id = Uuid::new_v4();
        let created_at = Utc::now();

        let result = self.calculate_runway(&input)?;
        let scenarios = Vec::new(); // No scenarios for basic calculation

        Ok(RunwayCalculation {
            id,
            created_at,
            input,
            result,
            scenarios,
        })
    }

    /// Calculate runway with scenario simulations.
    pub fn calculate_with_scenarios(
        &self,
        input: RunwayInput,
        scenarios: Vec<Scenario>,
    ) -> Result<RunwayCalculation> {
        let mut calculation = self.calculate(input)?;
        let scenario_results = self.simulate_scenarios(&calculation.input, &scenarios)?;
        calculation.scenarios = scenario_results;
        Ok(calculation)
    }

    /// Core runway calculation logic.
    fn calculate_runway(&self, input: &RunwayInput) -> Result<RunwayResult> {
        // Calculate monthly burn rate
        let monthly_burn = self.calculate_monthly_burn(input);

        // Calculate runway months
        let runway_months = calculate_runway_months(input.current_cash, monthly_burn)
            .unwrap_or(0.0);

        // Generate monthly projections
        let monthly_projections = self.generate_projections(input, runway_months as u32)?;

        // Determine risk level
        let risk_level = self.determine_risk_level(runway_months);

        // Calculate end dates
        let now = Utc::now();
        let runway_end_date = now + Duration::days((runway_months * 30.0) as i64);
        let cash_out_date = runway_end_date; // Simplified

        // Generate critical milestones
        let critical_milestones = self.generate_milestones(input, &monthly_projections);

        Ok(RunwayResult {
            runway_months,
            runway_end_date,
            cash_out_date,
            monthly_projections,
            critical_milestones,
            risk_level,
        })
    }

    /// Calculate total monthly burn rate.
    fn calculate_monthly_burn(&self, input: &RunwayInput) -> Decimal {
        let mut total_expenses = input.monthly_burn_rate;

        // Add expenses from categories
        for category in &input.expense_categories {
            if category.is_recurring && matches!(category.frequency, Some(Frequency::Monthly)) {
                total_expenses += category.amount;
            }
        }

        // Subtract revenue
        total_expenses - input.monthly_revenue
    }

    /// Generate monthly cash flow projections.
    fn generate_projections(
        &self,
        input: &RunwayInput,
        months: u32,
    ) -> Result<Vec<MonthlyProjection>> {
        let mut projections = Vec::new();
        let mut current_cash = input.current_cash;
        let mut current_revenue = input.monthly_revenue;
        let growth_rate = input.revenue_growth_rate.unwrap_or(self.config.default_growth_rate);

        let now = Utc::now();

        for month in 0..months.min(self.config.max_projection_months) {
            let month_start = now + Duration::days(month as i64 * 30);
            let starting_cash = current_cash;

            // Apply revenue growth
            current_revenue = calculate_compound_growth(current_revenue, growth_rate, 1);

            // Calculate expenses (simplified)
            let expenses = self.calculate_monthly_burn(input);
            let net_burn = expenses - current_revenue;

            // Update cash
            current_cash -= net_burn;

            // Calculate remaining runway
            let runway_remaining = if net_burn > Decimal::ZERO {
                (current_cash / net_burn).to_f32().unwrap_or(0.0)
            } else {
                f32::INFINITY
            };

            projections.push(MonthlyProjection {
                month: month_start,
                starting_cash,
                revenue: current_revenue,
                expenses,
                net_burn,
                ending_cash: current_cash,
                runway_remaining,
            });

            // Stop if cash is depleted
            if current_cash <= Decimal::ZERO {
                break;
            }
        }

        Ok(projections)
    }

    /// Determine risk level based on runway months.
    fn determine_risk_level(&self, runway_months: f32) -> RiskLevel {
        match runway_months {
            r if r < 3.0 => RiskLevel::Critical,
            r if r < 6.0 => RiskLevel::High,
            r if r < 12.0 => RiskLevel::Medium,
            _ => RiskLevel::Low,
        }
    }

    /// Generate critical milestones.
    fn generate_milestones(
        &self,
        input: &RunwayInput,
        projections: &[MonthlyProjection],
    ) -> Vec<Milestone> {
        let mut milestones = Vec::new();

        // Add funding rounds
        if let Some(funding) = &input.planned_funding {
            if let Some(date) = funding.expected_date {
                milestones.push(Milestone {
                    date,
                    description: format!("Planned funding round: ${}", funding.amount),
                    milestone_type: MilestoneType::FundingRound,
                });
            }
        }

        // Add one-time expenses
        for expense in &input.one_time_expenses {
            milestones.push(Milestone {
                date: expense.expected_date,
                description: format!("One-time expense: {} (${})", expense.name, expense.amount),
                milestone_type: MilestoneType::ExpenseMilestone,
            });
        }

        // Add cash-out milestone
        if let Some(last_projection) = projections.last() {
            if last_projection.ending_cash <= Decimal::ZERO {
                milestones.push(Milestone {
                    date: last_projection.month,
                    description: "Projected cash depletion".to_string(),
                    milestone_type: MilestoneType::CashOut,
                });
            }
        }

        // Sort by date
        milestones.sort_by(|a, b| a.date.cmp(&b.date));

        milestones
    }

    /// Simulate multiple scenarios.
    fn simulate_scenarios(
        &self,
        base_input: &RunwayInput,
        scenarios: &[Scenario],
    ) -> Result<Vec<ScenarioResult>> {
        let mut results = Vec::new();

        for scenario in scenarios {
            let scenario_input = self.apply_scenario_adjustments(base_input, scenario)?;
            let scenario_result = self.calculate_runway(&scenario_input)?;
            let comparison = self.compare_results(base_input, &scenario_result, scenario)?;

            results.push(ScenarioResult {
                scenario: scenario.clone(),
                runway_result: scenario_result,
                comparison,
            });
        }

        Ok(results)
    }

    /// Apply scenario adjustments to input.
    fn apply_scenario_adjustments(
        &self,
        base_input: &RunwayInput,
        scenario: &Scenario,
    ) -> Result<RunwayInput> {
        let mut adjusted = base_input.clone();

        let adjustments = &scenario.adjustments;

        // Apply burn rate change
        if let Some(burn_change) = adjustments.burn_rate_change {
            adjusted.monthly_burn_rate *= Decimal::ONE + burn_change;
        }

        // Apply revenue change
        if let Some(revenue_change) = adjustments.revenue_change {
            adjusted.monthly_revenue *= Decimal::ONE + revenue_change;
        }

        // Apply growth rate change
        if let Some(growth_change) = adjustments.growth_rate_change {
            adjusted.revenue_growth_rate = Some(
                adjusted.revenue_growth_rate.unwrap_or(Decimal::ZERO) + growth_change
            );
        }

        // Add new funding
        if let Some(new_funding) = &adjustments.new_funding {
            adjusted.planned_funding = Some(new_funding.clone());
        }

        // Apply expense cuts
        for cut in &adjustments.expense_cuts {
            for category in &mut adjusted.expense_categories {
                if category.category_type == cut.category {
                    category.amount *= Decimal::ONE - cut.percentage;
                }
            }
        }

        // Add new revenue streams
        adjusted.revenue_streams.extend(adjustments.new_revenue_streams.clone());

        Ok(adjusted)
    }

    /// Compare scenario results with base case.
    fn compare_results(
        &self,
        base_input: &RunwayInput,
        scenario_result: &RunwayResult,
        scenario: &Scenario,
    ) -> Result<RunwayComparison> {
        let base_runway = calculate_runway_months(
            base_input.current_cash,
            self.calculate_monthly_burn(base_input),
        ).unwrap_or(0.0);

        let scenario_runway = scenario_result.runway_months;
        let runway_change_months = scenario_runway - base_runway;

        let runway_change_percentage = if base_runway > 0.0 {
            Decimal::from_f32(scenario_runway / base_runway).unwrap_or(Decimal::ZERO) - Decimal::ONE
        } else {
            Decimal::ZERO
        };

        // Calculate cash saved (simplified)
        let cash_saved = Decimal::ZERO; // Would need more complex calculation

        // Break-even date (simplified)
        let break_even_date = None;

        Ok(RunwayComparison {
            runway_change_months,
            runway_change_percentage,
            cash_saved,
            break_even_date,
        })
    }
}

impl Default for RunwayCalculator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rust_decimal_macros::dec;
    use chrono::Utc;

    #[test]
    fn test_basic_runway_calculation() {
        let calculator = RunwayCalculator::new();

        let input = RunwayInput {
            current_cash: dec!(500000),
            monthly_burn_rate: dec!(50000),
            monthly_revenue: dec!(20000),
            revenue_growth_rate: Some(dec!(0.05)),
            expense_categories: vec![],
            revenue_streams: vec![],
            one_time_expenses: vec![],
            planned_funding: None,
        };

        let result = calculator.calculate(input).unwrap();
        assert!(result.result.runway_months > 0.0);
        assert!(!result.result.monthly_projections.is_empty());
    }

    #[test]
    fn test_runway_with_negative_growth() {
        let calculator = RunwayCalculator::new();

        let input = RunwayInput {
            current_cash: dec!(100000),
            monthly_burn_rate: dec!(20000),
            monthly_revenue: dec!(5000),
            revenue_growth_rate: Some(dec!(-0.1)),
            expense_categories: vec![],
            revenue_streams: vec![],
            one_time_expenses: vec![],
            planned_funding: None,
        };

        let result = calculator.calculate(input).unwrap();
        assert!(result.result.runway_months > 0.0);
        assert!(result.result.runway_months < 10.0); // Should be less than without negative growth
    }

    #[test]
    fn test_risk_level_assessment() {
        let calculator = RunwayCalculator::new();

        // Critical risk
        let input_critical = RunwayInput {
            current_cash: dec!(50000),
            monthly_burn_rate: dec!(20000),
            monthly_revenue: dec!(0),
            revenue_growth_rate: None,
            expense_categories: vec![],
            revenue_streams: vec![],
            one_time_expenses: vec![],
            planned_funding: None,
        };

        let result = calculator.calculate(input_critical).unwrap();
        assert_eq!(result.result.risk_level, RiskLevel::Critical);

        // Low risk
        let input_low = RunwayInput {
            current_cash: dec!(1000000),
            monthly_burn_rate: dec!(20000),
            monthly_revenue: dec!(15000),
            revenue_growth_rate: None,
            expense_categories: vec![],
            revenue_streams: vec![],
            one_time_expenses: vec![],
            planned_funding: None,
        };

        let result = calculator.calculate(input_low).unwrap();
        assert_eq!(result.result.risk_level, RiskLevel::Low);
    }

    #[test]
    fn test_scenario_simulation() {
        let calculator = RunwayCalculator::new();

        let base_input = RunwayInput {
            current_cash: dec!(500000),
            monthly_burn_rate: dec!(50000),
            monthly_revenue: dec!(20000),
            revenue_growth_rate: Some(dec!(0.05)),
            expense_categories: vec![],
            revenue_streams: vec![],
            one_time_expenses: vec![],
            planned_funding: None,
        };

        let scenario = Scenario {
            id: Uuid::new_v4(),
            name: "Cost Cutting".to_string(),
            description: "Reduce burn rate by 20%".to_string(),
            adjustments: ScenarioAdjustments {
                burn_rate_change: Some(dec!(-0.20)),
                revenue_change: None,
                growth_rate_change: None,
                headcount_change: None,
                new_funding: None,
                expense_cuts: vec![],
                new_revenue_streams: vec![],
            },
        };

        let result = calculator.calculate_with_scenarios(base_input, vec![scenario]).unwrap();
        assert!(!result.scenarios.is_empty());
        assert!(result.scenarios[0].runway_result.runway_months > result.result.runway_months);
    }
}