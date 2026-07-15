//! Domain models for financial data and calculations.

use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// A snapshot of financial data at a specific point in time.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FinancialSnapshot {
    pub timestamp: DateTime<Utc>,
    pub cash_balance: Decimal,
    pub monthly_burn_rate: Decimal,
    pub monthly_revenue: Decimal,
    pub arr: Option<Decimal>,  // Annual Recurring Revenue
    pub mrr: Option<Decimal>,  // Monthly Recurring Revenue
    pub customer_count: Option<u32>,
    pub employee_count: Option<u32>,
    pub metadata: HashMap<String, serde_json::Value>,
}

/// Categories of expenses with their details.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpenseCategory {
    pub name: String,
    pub amount: Decimal,
    pub category_type: ExpenseType,
    pub is_recurring: bool,
    pub frequency: Option<Frequency>,
}

/// Types of expenses.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExpenseType {
    Payroll,
    Marketing,
    Infrastructure,
    Legal,
    Office,
    ProductDevelopment,
    Other(String),
}

/// Frequency of recurring expenses.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Frequency {
    Monthly,
    Quarterly,
    Annual,
    OneTime,
}

/// Revenue streams with growth characteristics.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RevenueStream {
    pub name: String,
    pub amount: Decimal,
    pub stream_type: RevenueType,
    pub growth_rate: Option<Decimal>,  // Monthly growth percentage
    pub churn_rate: Option<Decimal>,   // Monthly churn percentage
}

/// Types of revenue streams.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RevenueType {
    Subscription,
    OneTime,
    Usage,
    Professional,
    Other(String),
}

/// Input parameters for runway calculations.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunwayInput {
    pub current_cash: Decimal,
    pub monthly_burn_rate: Decimal,
    pub monthly_revenue: Decimal,
    pub revenue_growth_rate: Option<Decimal>,
    pub expense_categories: Vec<ExpenseCategory>,
    pub revenue_streams: Vec<RevenueStream>,
    pub one_time_expenses: Vec<OneTimeExpense>,
    pub planned_funding: Option<FundingRound>,
}

/// One-time expenses that occur at specific dates.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OneTimeExpense {
    pub name: String,
    pub amount: Decimal,
    pub expected_date: DateTime<Utc>,
    pub probability: f32,  // 0.0 to 1.0
}

/// Planned funding rounds.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FundingRound {
    pub amount: Decimal,
    pub expected_date: Option<DateTime<Utc>>,
    pub probability: f32,
    pub dilution_percentage: Option<Decimal>,
}

/// Results of a runway calculation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunwayResult {
    pub runway_months: f32,
    pub runway_end_date: DateTime<Utc>,
    pub cash_out_date: DateTime<Utc>,
    pub monthly_projections: Vec<MonthlyProjection>,
    pub critical_milestones: Vec<Milestone>,
    pub risk_level: RiskLevel,
}

/// Monthly cash flow projections.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonthlyProjection {
    pub month: DateTime<Utc>,
    pub starting_cash: Decimal,
    pub revenue: Decimal,
    pub expenses: Decimal,
    pub net_burn: Decimal,
    pub ending_cash: Decimal,
    pub runway_remaining: f32,
}

/// Important milestones in the runway timeline.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Milestone {
    pub date: DateTime<Utc>,
    pub description: String,
    pub milestone_type: MilestoneType,
}

/// Types of milestones.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MilestoneType {
    FundingRound,
    RevenueMilestone,
    ExpenseMilestone,
    CashOut,
}

/// Risk levels for runway calculations.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RiskLevel {
    Critical,  // < 3 months
    High,      // 3-6 months
    Medium,    // 6-12 months
    Low,       // > 12 months
}

/// Complete runway calculation with metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunwayCalculation {
    pub id: Uuid,
    pub created_at: DateTime<Utc>,
    pub input: RunwayInput,
    pub result: RunwayResult,
    pub scenarios: Vec<ScenarioResult>,
}

/// Results of scenario simulations.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScenarioResult {
    pub scenario: Scenario,
    pub runway_result: RunwayResult,
    pub comparison: RunwayComparison,
}

/// Alternative scenarios to simulate.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Scenario {
    pub id: Uuid,
    pub name: String,
    pub description: String,
    pub adjustments: ScenarioAdjustments,
}

/// Adjustments to apply in a scenario.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScenarioAdjustments {
    pub burn_rate_change: Option<Decimal>,      // Percentage change
    pub revenue_change: Option<Decimal>,        // Percentage change
    pub growth_rate_change: Option<Decimal>,    // Absolute change
    pub headcount_change: Option<i32>,          // Number of employees
    pub new_funding: Option<FundingRound>,
    pub expense_cuts: Vec<ExpenseCut>,
    pub new_revenue_streams: Vec<RevenueStream>,
}

/// Expense cuts in scenarios.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpenseCut {
    pub category: ExpenseType,
    pub percentage: Decimal,
    pub effective_date: DateTime<Utc>,
}

/// Comparison between base and scenario results.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunwayComparison {
    pub runway_change_months: f32,
    pub runway_change_percentage: Decimal,
    pub cash_saved: Decimal,
    pub break_even_date: Option<DateTime<Utc>>,
}