//! Financial metrics calculations.

use rust_decimal::Decimal;
use crate::errors::{Result, VcfoError};
use crate::models::{FinancialSnapshot, RevenueStream, ExpenseCategory};

/// Calculate Annual Recurring Revenue (ARR) from monthly revenue.
pub fn calculate_arr(monthly_revenue: Decimal) -> Decimal {
    monthly_revenue * Decimal::from(12)
}

/// Calculate Monthly Recurring Revenue (MRR) from annual revenue.
pub fn calculate_mrr(annual_revenue: Decimal) -> Decimal {
    annual_revenue / Decimal::from(12)
}

/// Calculate burn rate from expenses and revenue.
pub fn calculate_burn_rate(
    monthly_expenses: Decimal,
    monthly_revenue: Decimal,
) -> Decimal {
    monthly_expenses - monthly_revenue
}

/// Calculate net burn rate (gross burn minus revenue).
pub fn calculate_net_burn_rate(
    gross_burn: Decimal,
    monthly_revenue: Decimal,
) -> Decimal {
    gross_burn - monthly_revenue
}

/// Calculate runway in months given cash and burn rate.
pub fn calculate_runway_months(
    current_cash: Decimal,
    monthly_burn_rate: Decimal,
) -> Result<f32> {
    if monthly_burn_rate <= Decimal::ZERO {
        return Err(VcfoError::CalculationError(
            "Burn rate must be positive to calculate runway".to_string()
        ));
    }

    let runway = (current_cash / monthly_burn_rate).to_f32().unwrap_or(0.0);
    Ok(runway)
}

/// Calculate compound monthly growth.
pub fn calculate_compound_growth(
    initial_amount: Decimal,
    growth_rate: Decimal,
    months: u32,
) -> Decimal {
    if growth_rate == Decimal::ZERO {
        return initial_amount;
    }

    let growth_factor = Decimal::ONE + growth_rate;
    let mut result = initial_amount;

    for _ in 0..months {
        result *= growth_factor;
    }

    result
}

/// Calculate customer acquisition cost (CAC).
pub fn calculate_cac(
    marketing_expenses: Decimal,
    new_customers: u32,
) -> Result<Decimal> {
    if new_customers == 0 {
        return Err(VcfoError::CalculationError(
            "Cannot calculate CAC with zero new customers".to_string()
        ));
    }

    Ok(marketing_expenses / Decimal::from(new_customers))
}

/// Calculate customer lifetime value (LTV).
pub fn calculate_ltv(
    average_revenue_per_customer: Decimal,
    customer_lifetime_months: u32,
    churn_rate: Decimal,
) -> Decimal {
    if churn_rate >= Decimal::ONE {
        return Decimal::ZERO;
    }

    let retention_rate = Decimal::ONE - churn_rate;
    let lifetime_value = average_revenue_per_customer * Decimal::from(customer_lifetime_months);

    // Simple LTV calculation (can be enhanced with discounting)
    lifetime_value / (Decimal::ONE - retention_rate)
}

/// Calculate LTV/CAC ratio.
pub fn calculate_ltv_cac_ratio(
    ltv: Decimal,
    cac: Decimal,
) -> Result<Decimal> {
    if cac == Decimal::ZERO {
        return Err(VcfoError::CalculationError(
            "CAC cannot be zero for LTV/CAC ratio".to_string()
        ));
    }

    Ok(ltv / cac)
}

/// Calculate monthly churn rate from customer counts.
pub fn calculate_churn_rate(
    starting_customers: u32,
    ending_customers: u32,
) -> Result<Decimal> {
    if starting_customers == 0 {
        return Err(VcfoError::CalculationError(
            "Starting customer count cannot be zero".to_string()
        ));
    }

    let churned = starting_customers.saturating_sub(ending_customers);
    Ok(Decimal::from(churned) / Decimal::from(starting_customers))
}

/// Calculate revenue growth rate.
pub fn calculate_growth_rate(
    previous_revenue: Decimal,
    current_revenue: Decimal,
) -> Result<Decimal> {
    if previous_revenue == Decimal::ZERO {
        return Err(VcfoError::CalculationError(
            "Previous revenue cannot be zero for growth calculation".to_string()
        ));
    }

    Ok((current_revenue - previous_revenue) / previous_revenue)
}

/// Calculate break-even point in months.
pub fn calculate_break_even_months(
    fixed_costs: Decimal,
    variable_cost_per_unit: Decimal,
    price_per_unit: Decimal,
    initial_units: u32,
) -> Result<f32> {
    if price_per_unit <= variable_cost_per_unit {
        return Err(VcfoError::CalculationError(
            "Price per unit must be greater than variable cost per unit".to_string()
        ));
    }

    let contribution_margin = price_per_unit - variable_cost_per_unit;
    let break_even_units = (fixed_costs / contribution_margin).to_f32().unwrap_or(0.0);

    // Simple estimation - in reality this would need more complex modeling
    let months = break_even_units / initial_units as f32;
    Ok(months)
}

/// Calculate weighted average cost of capital (WACC) - simplified version.
pub fn calculate_wacc(
    equity_value: Decimal,
    debt_value: Decimal,
    cost_of_equity: Decimal,
    cost_of_debt: Decimal,
    tax_rate: Decimal,
) -> Decimal {
    let total_value = equity_value + debt_value;
    if total_value == Decimal::ZERO {
        return Decimal::ZERO;
    }

    let equity_weight = equity_value / total_value;
    let debt_weight = debt_value / total_value;

    let after_tax_cost_of_debt = cost_of_debt * (Decimal::ONE - tax_rate);

    equity_weight * cost_of_equity + debt_weight * after_tax_cost_of_debt
}