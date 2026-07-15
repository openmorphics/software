//! Alert system for runway monitoring.

use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use uuid::Uuid;
use std::collections::HashMap;

use vcfo_core::{
    errors::Result,
    models::*,
};

/// Alert thresholds configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlertThresholds {
    pub critical_runway_months: f32,  // Default: 3
    pub low_runway_months: f32,       // Default: 6
    pub burn_rate_increase: Decimal,  // Percentage increase trigger
    pub revenue_decline: Decimal,     // Percentage decline trigger
    pub cash_threshold: Decimal,      // Absolute cash minimum
}

impl Default for AlertThresholds {
    fn default() -> Self {
        Self {
            critical_runway_months: 3.0,
            low_runway_months: 6.0,
            burn_rate_increase: Decimal::from_str("0.20").unwrap(), // 20%
            revenue_decline: Decimal::from_str("0.15").unwrap(),    // 15%
            cash_threshold: Decimal::from(50000), // $50K
        }
    }
}

/// Severity levels for alerts.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum AlertSeverity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

/// Types of alerts.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AlertType {
    LowRunway,
    HighBurnRate,
    RevenueDrop,
    CashCritical,
    MilestoneAtRisk,
    Custom(String),
}

/// Details of an alert.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlertDetails {
    pub current_value: serde_json::Value,
    pub threshold_value: serde_json::Value,
    pub trend: Option<TrendData>,
    pub impact_analysis: Option<String>,
}

/// Trend data for alerts.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrendData {
    pub direction: TrendDirection,
    pub rate_of_change: Decimal,
    pub period_days: u32,
}

/// Trend direction.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TrendDirection {
    Improving,
    Stable,
    Declining,
}

/// Alert engine for monitoring runway health.
#[derive(Debug)]
pub struct AlertEngine {
    thresholds: AlertThresholds,
    notification_channels: Vec<NotificationChannel>,
}

impl AlertEngine {
    /// Create a new alert engine.
    pub fn new(thresholds: AlertThresholds) -> Self {
        Self {
            thresholds,
            notification_channels: Vec::new(),
        }
    }

    /// Check a single calculation for alerts.
    pub fn check_runway(&self, calc: &RunwayCalculation) -> Vec<Alert> {
        let mut alerts = Vec::new();

        // Check runway duration
        if calc.result.runway_months <= self.thresholds.critical_runway_months {
            alerts.push(Alert {
                id: Uuid::new_v4(),
                timestamp: Utc::now(),
                severity: AlertSeverity::Critical,
                alert_type: AlertType::LowRunway,
                message: format!(
                    "Critical runway: Only {:.1} months remaining",
                    calc.result.runway_months
                ),
                details: AlertDetails {
                    current_value: serde_json::json!(calc.result.runway_months),
                    threshold_value: serde_json::json!(self.thresholds.critical_runway_months),
                    trend: None,
                    impact_analysis: Some("Immediate action required to extend runway".to_string()),
                },
                recommended_actions: vec![
                    "Cut discretionary expenses".to_string(),
                    "Accelerate revenue generation".to_string(),
                    "Secure additional funding".to_string(),
                ],
            });
        } else if calc.result.runway_months <= self.thresholds.low_runway_months {
            alerts.push(Alert {
                id: Uuid::new_v4(),
                timestamp: Utc::now(),
                severity: AlertSeverity::High,
                alert_type: AlertType::LowRunway,
                message: format!(
                    "Low runway: {:.1} months remaining",
                    calc.result.runway_months
                ),
                details: AlertDetails {
                    current_value: serde_json::json!(calc.result.runway_months),
                    threshold_value: serde_json::json!(self.thresholds.low_runway_months),
                    trend: None,
                    impact_analysis: Some("Monitor closely and plan contingency measures".to_string()),
                },
                recommended_actions: vec![
                    "Review expense categories".to_string(),
                    "Explore cost optimization opportunities".to_string(),
                    "Prepare funding strategy".to_string(),
                ],
            });
        }

        // Check cash levels
        if calc.input.current_cash <= self.thresholds.cash_threshold {
            alerts.push(Alert {
                id: Uuid::new_v4(),
                timestamp: Utc::now(),
                severity: AlertSeverity::High,
                alert_type: AlertType::CashCritical,
                message: format!(
                    "Low cash balance: ${}",
                    calc.input.current_cash
                ),
                details: AlertDetails {
                    current_value: serde_json::json!(calc.input.current_cash),
                    threshold_value: serde_json::json!(self.thresholds.cash_threshold),
                    trend: None,
                    impact_analysis: Some("Cash reserves are critically low".to_string()),
                },
                recommended_actions: vec![
                    "Prioritize cash collection".to_string(),
                    "Delay non-essential expenses".to_string(),
                    "Arrange bridge financing".to_string(),
                ],
            });
        }

        // Check for at-risk milestones
        for milestone in &calc.result.critical_milestones {
            if let MilestoneType::CashOut = milestone.milestone_type {
                if milestone.date < Utc::now() + chrono::Duration::days(90) {
                    alerts.push(Alert {
                        id: Uuid::new_v4(),
                        timestamp: Utc::now(),
                        severity: AlertSeverity::Medium,
                        alert_type: AlertType::MilestoneAtRisk,
                        message: format!(
                            "Cash depletion milestone approaching: {}",
                            milestone.date.format("%Y-%m-%d")
                        ),
                        details: AlertDetails {
                            current_value: serde_json::json!(milestone.date),
                            threshold_value: serde_json::json!(Utc::now() + chrono::Duration::days(90)),
                            trend: None,
                            impact_analysis: Some("Business continuity at risk".to_string()),
                        },
                        recommended_actions: vec![
                            "Accelerate fundraising efforts".to_string(),
                            "Implement emergency cost controls".to_string(),
                            "Explore strategic partnerships".to_string(),
                        ],
                    });
                }
            }
        }

        alerts
    }

    /// Check historical calculations for trends.
    pub fn check_trends(&self, history: &[RunwayCalculation]) -> Vec<Alert> {
        let mut alerts = Vec::new();

        if history.len() < 2 {
            return alerts;
        }

        // Sort by creation date
        let mut sorted_history = history.to_vec();
        sorted_history.sort_by(|a, b| a.created_at.cmp(&b.created_at));

        // Check burn rate trends
        if let Some(burn_trend) = self.analyze_burn_trend(&sorted_history) {
            if burn_trend.rate_of_change > self.thresholds.burn_rate_increase {
                alerts.push(Alert {
                    id: Uuid::new_v4(),
                    timestamp: Utc::now(),
                    severity: AlertSeverity::High,
                    alert_type: AlertType::HighBurnRate,
                    message: format!(
                        "Burn rate increasing: +{:.1}% over {} days",
                        burn_trend.rate_of_change * Decimal::from(100),
                        burn_trend.period_days
                    ),
                    details: AlertDetails {
                        current_value: serde_json::json!(burn_trend.rate_of_change),
                        threshold_value: serde_json::json!(self.thresholds.burn_rate_increase),
                        trend: Some(burn_trend),
                        impact_analysis: Some("Increasing burn rate is reducing runway".to_string()),
                    },
                    recommended_actions: vec![
                        "Audit recent expenses".to_string(),
                        "Implement spending controls".to_string(),
                        "Review headcount efficiency".to_string(),
                    ],
                });
            }
        }

        // Check revenue trends
        if let Some(revenue_trend) = self.analyze_revenue_trend(&sorted_history) {
            if revenue_trend.rate_of_change < -self.thresholds.revenue_decline {
                alerts.push(Alert {
                    id: Uuid::new_v4(),
                    timestamp: Utc::now(),
                    severity: AlertSeverity::High,
                    alert_type: AlertType::RevenueDrop,
                    message: format!(
                        "Revenue declining: {:.1}% over {} days",
                        revenue_trend.rate_of_change * Decimal::from(100),
                        revenue_trend.period_days
                    ),
                    details: AlertDetails {
                        current_value: serde_json::json!(revenue_trend.rate_of_change),
                        threshold_value: serde_json::json!(-self.thresholds.revenue_decline),
                        trend: Some(revenue_trend),
                        impact_analysis: Some("Revenue decline is accelerating cash depletion".to_string()),
                    },
                    recommended_actions: vec![
                        "Analyze customer churn".to_string(),
                        "Review pricing strategy".to_string(),
                        "Enhance sales efforts".to_string(),
                    ],
                });
            }
        }

        alerts
    }

    /// Send notifications for alerts.
    pub fn send_notifications(&self, alerts: &[Alert]) -> Result<()> {
        for channel in &self.notification_channels {
            channel.send_alerts(alerts)?;
        }
        Ok(())
    }

    /// Add a notification channel.
    pub fn add_notification_channel(&mut self, channel: NotificationChannel) {
        self.notification_channels.push(channel);
    }

    /// Analyze burn rate trend.
    fn analyze_burn_trend(&self, history: &[RunwayCalculation]) -> Option<TrendData> {
        if history.len() < 2 {
            return None;
        }

        let first = &history[0];
        let last = &history[history.len() - 1];

        let period_days = (last.created_at - first.created_at).num_days() as u32;
        if period_days == 0 {
            return None;
        }

        let burn_change = (last.input.monthly_burn_rate - first.input.monthly_burn_rate)
            / first.input.monthly_burn_rate;

        let rate_of_change = burn_change / Decimal::from(period_days);

        let direction = if rate_of_change > Decimal::from_str("0.001").unwrap() {
            TrendDirection::Declining // Higher burn rate is worse
        } else if rate_of_change < Decimal::from_str("-0.001").unwrap() {
            TrendDirection::Improving
        } else {
            TrendDirection::Stable
        };

        Some(TrendData {
            direction,
            rate_of_change,
            period_days,
        })
    }

    /// Analyze revenue trend.
    fn analyze_revenue_trend(&self, history: &[RunwayCalculation]) -> Option<TrendData> {
        if history.len() < 2 {
            return None;
        }

        let first = &history[0];
        let last = &history[history.len() - 1];

        let period_days = (last.created_at - first.created_at).num_days() as u32;
        if period_days == 0 {
            return None;
        }

        let revenue_change = (last.input.monthly_revenue - first.input.monthly_revenue)
            / first.input.monthly_revenue;

        let rate_of_change = revenue_change / Decimal::from(period_days);

        let direction = if rate_of_change > Decimal::from_str("0.001").unwrap() {
            TrendDirection::Improving
        } else if rate_of_change < Decimal::from_str("-0.001").unwrap() {
            TrendDirection::Declining
        } else {
            TrendDirection::Stable
        };

        Some(TrendData {
            direction,
            rate_of_change,
            period_days,
        })
    }
}

/// Notification channel for alerts.
#[derive(Debug)]
pub enum NotificationChannel {
    Email { address: String },
    Slack { webhook_url: String },
    Webhook { url: String },
}

impl NotificationChannel {
    /// Send alerts through this channel.
    pub fn send_alerts(&self, alerts: &[Alert]) -> Result<()> {
        // Placeholder implementation
        match self {
            NotificationChannel::Email { address } => {
                println!("Sending {} alerts to email: {}", alerts.len(), address);
            }
            NotificationChannel::Slack { webhook_url } => {
                println!("Sending {} alerts to Slack webhook", alerts.len());
            }
            NotificationChannel::Webhook { url } => {
                println!("Sending {} alerts to webhook: {}", alerts.len(), url);
            }
        }
        Ok(())
    }
}

impl Default for AlertEngine {
    fn default() -> Self {
        Self::new(AlertThresholds::default())
    }
}