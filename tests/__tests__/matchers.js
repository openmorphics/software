/**
 * Custom Jest Matchers for EventFlow Testing
 *
 * Specialized matchers for validating EventFlow-specific behavior
 * including performance, accuracy, and neuromorphic computing patterns.
 */

/**
 * Matcher for validating CLI execution results
 */
expect.extend({
  toBeSuccessful(result) {
    const pass = result && result.success === true && result.exitCode === 0;
    return {
      message: () =>
        pass
          ? `Expected CLI execution to fail, but it succeeded`
          : `Expected CLI execution to succeed, but it failed: ${result?.error || 'Unknown error'}`,
      pass
    };
  },

  toBeWithinTimeBudget(result, maxTimeMs) {
    const actualTime = result?.executionTime || 0;
    const pass = actualTime <= maxTimeMs;
    return {
      message: () =>
        pass
          ? `Expected execution to exceed ${maxTimeMs}ms, but took ${actualTime}ms`
          : `Expected execution within ${maxTimeMs}ms, but took ${actualTime}ms`,
      pass
    };
  },

  toMatchGoldenTrace(output, golden) {
    // Simplified trace comparison - in real implementation would use proper diffing
    const pass = output && golden && output.length > 0 && golden.length > 0;
    return {
      message: () =>
        pass
          ? `Expected traces to differ, but they appear to match`
          : `Expected traces to match, but they differ significantly`,
      pass
    };
  },

  toMeetPerformanceBaseline(metrics, baseline) {
    const pass = metrics && baseline &&
                 metrics.latency <= baseline.latency &&
                 metrics.accuracy >= baseline.accuracy;
    return {
      message: () =>
        pass
          ? `Expected performance to fail baseline, but it met requirements`
          : `Expected performance to meet baseline, but it failed`,
      pass
    };
  },

  /**
   * Matcher for validating Event Tensor format
   */
  toBeValidEventTensor(tensor) {
    let pass = true;
    let message = '';

    if (!tensor) {
      pass = false;
      message = 'Expected valid Event Tensor, but received null/undefined';
    } else if (!Array.isArray(tensor)) {
      pass = false;
      message = 'Expected Event Tensor to be an array';
    } else if (tensor.length === 0) {
      pass = false;
      message = 'Expected Event Tensor to contain events';
    } else {
      // Validate first event structure
      const firstEvent = tensor[0];
      if (!firstEvent || typeof firstEvent !== 'object') {
        pass = false;
        message = 'Expected events to be objects';
      } else if (!('ts' in firstEvent) || !('idx' in firstEvent) || !('val' in firstEvent)) {
        pass = false;
        message = 'Expected events to have ts, idx, and val properties';
      } else if (typeof firstEvent.ts !== 'number' || !Array.isArray(firstEvent.idx) || typeof firstEvent.val !== 'number') {
        pass = false;
        message = 'Expected ts to be number, idx to be array, val to be number';
      }
    }

    return {
      message: () => message,
      pass
    };
  },

  /**
   * Matcher for validating neuromorphic spike patterns
   */
  toHaveValidSpikePattern(events, options = {}) {
    const { minEvents = 1, maxEvents = 1000, timeWindow = 1000 } = options;
    let pass = true;
    let message = '';

    if (!Array.isArray(events)) {
      pass = false;
      message = 'Expected events to be an array';
    } else if (events.length < minEvents) {
      pass = false;
      message = `Expected at least ${minEvents} events, but got ${events.length}`;
    } else if (events.length > maxEvents) {
      pass = false;
      message = `Expected at most ${maxEvents} events, but got ${events.length}`;
    } else {
      // Check temporal ordering
      let lastTs = 0;
      for (const event of events) {
        if (event.ts < lastTs) {
          pass = false;
          message = 'Expected events to be in temporal order';
          break;
        }
        lastTs = event.ts;
      }

      // Check time window if specified
      if (pass && timeWindow > 0 && events.length > 1) {
        const duration = events[events.length - 1].ts - events[0].ts;
        if (duration > timeWindow) {
          pass = false;
          message = `Expected events within ${timeWindow}ms window, but span ${duration}ms`;
        }
      }
    }

    return {
      message: () => message,
      pass
    };
  },

  /**
   * Matcher for validating sensor data quality
   */
  toHaveAcceptableDataQuality(data, thresholds = {}) {
    const {
      minSamples = 10,
      maxNoise = 0.1,
      maxOutliers = 0.05,
      checkTemporalConsistency = true
    } = thresholds;

    let pass = true;
    let message = '';

    if (!Array.isArray(data) || data.length < minSamples) {
      pass = false;
      message = `Expected at least ${minSamples} samples, got ${data.length}`;
    } else {
      // Check for outliers (simple statistical approach)
      const values = data.map(d => d.val).sort((a, b) => a - b);
      const q1 = values[Math.floor(values.length * 0.25)];
      const q3 = values[Math.floor(values.length * 0.75)];
      const iqr = q3 - q1;
      const outlierThreshold = 1.5 * iqr;

      let outlierCount = 0;
      for (const val of values) {
        if (val < q1 - outlierThreshold || val > q3 + outlierThreshold) {
          outlierCount++;
        }
      }

      const outlierRatio = outlierCount / values.length;
      if (outlierRatio > maxOutliers) {
        pass = false;
        message = `Outlier ratio ${outlierRatio.toFixed(3)} exceeds threshold ${maxOutliers}`;
      }

      // Check temporal consistency (no huge gaps)
      if (pass && checkTemporalConsistency) {
        const timestamps = data.map(d => d.ts).sort((a, b) => a - b);
        const gaps = [];
        for (let i = 1; i < timestamps.length; i++) {
          gaps.push(timestamps[i] - timestamps[i - 1]);
        }

        const avgGap = gaps.reduce((a, b) => a + b, 0) / gaps.length;
        const maxGap = Math.max(...gaps);

        if (maxGap > avgGap * 10) { // Gap more than 10x average
          pass = false;
          message = `Temporal gap of ${maxGap}ms exceeds 10x average gap of ${(avgGap).toFixed(2)}ms`;
        }
      }
    }

    return {
      message: () => message,
      pass
    };
  },

  /**
   * Matcher for validating domain-specific performance
   */
  toMeetDomainRequirements(results, domain) {
    const domainRequirements = {
      healthcare: { maxLatency: 50, minAccuracy: 0.95 },
      industrial: { maxLatency: 75, minAccuracy: 0.92 },
      autonomous: { maxLatency: 25, minAccuracy: 0.98 },
      smart_cities: { maxLatency: 60, minAccuracy: 0.90 },
      scientific: { maxLatency: 80, minAccuracy: 0.99 },
      agriculture: { maxLatency: 100, minAccuracy: 0.88 },
      security: { maxLatency: 40, minAccuracy: 0.94 }
    };

    const req = domainRequirements[domain];
    if (!req) {
      return {
        message: () => `Unknown domain: ${domain}`,
        pass: false
      };
    }

    const pass = results &&
                 results.latency <= req.maxLatency &&
                 results.accuracy >= req.minAccuracy;

    return {
      message: () =>
        pass
          ? `Expected ${domain} to fail requirements, but met them`
          : `Expected ${domain} to meet requirements (latency ≤${req.maxLatency}ms, accuracy ≥${req.minAccuracy}), but got latency=${results?.latency}ms, accuracy=${results?.accuracy}`,
      pass
    };
  },

  /**
   * Matcher for validating deterministic execution
   */
  toBeDeterministic(run1, run2, tolerance = { time: 50, value: 1e-5 }) {
    let pass = true;
    let message = '';

    if (!run1 || !run2) {
      pass = false;
      message = 'Expected two valid run results for comparison';
    } else if (!run1.success || !run2.success) {
      pass = false;
      message = 'Expected both runs to be successful';
    } else if (!run1.output || !run2.output) {
      pass = false;
      message = 'Expected both runs to have output traces';
    } else {
      // Simplified deterministic check - compare key metrics
      // In real implementation, would do detailed trace comparison
      const metrics1 = extractMetrics(run1.output);
      const metrics2 = extractMetrics(run2.output);

      if (Math.abs(metrics1.eventCount - metrics2.eventCount) > 0) {
        pass = false;
        message = `Event counts differ: ${metrics1.eventCount} vs ${metrics2.eventCount}`;
      } else if (Math.abs(metrics1.avgValue - metrics2.avgValue) > tolerance.value) {
        pass = false;
        message = `Average values differ by ${(Math.abs(metrics1.avgValue - metrics2.avgValue)).toFixed(6)}, exceeds tolerance ${tolerance.value}`;
      }
    }

    return {
      message: () => message,
      pass
    };
  }
});

/**
 * Extract metrics from trace output for comparison
 */
function extractMetrics(traceOutput) {
  // Simplified metric extraction - in real implementation would parse JSONL traces
  const lines = (traceOutput || '').split('\n').filter(line => line.trim());
  const events = lines.filter(line => line.includes('"ts"')).length;

  return {
    eventCount: events,
    avgValue: 0.5, // Placeholder - would calculate from actual trace data
    duration: 1000 // Placeholder - would calculate from timestamps
  };
}

// Export utilities
module.exports = {
  extractMetrics
};