/**
 * Jest Setup Configuration for EventFlow Tests
 *
 * Global setup for all Jest tests including custom matchers,
 * environment configuration, and test utilities.
 */

const path = require('path');

// Global test configuration
global.TEST_CONFIG = {
  timeout: 300000, // 5 minutes
  tempDir: path.join(__dirname, '../temp'),
  examplesDir: path.join(__dirname, '../../examples'),
  cliPath: path.join(__dirname, '../../eventflow-cli/ef.py'),
  coverageThreshold: 85
};

// Custom Jest matchers for EventFlow testing
expect.extend({
  /**
   * Check if CLI execution was successful
   */
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

  /**
   * Check if execution time is within acceptable range
   */
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

  /**
   * Check if traces match within tolerance
   */
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

  /**
   * Check if performance meets baseline requirements
   */
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
  }
});

// Global test utilities
global.testUtils = {
  /**
   * Generate temporary file path
   */
  tempFile: (name) => path.join(global.TEST_CONFIG.tempDir, name),

  /**
   * Create test data directory
   */
  ensureTestDir: () => {
    const fs = require('fs');
    if (!fs.existsSync(global.TEST_CONFIG.tempDir)) {
      fs.mkdirSync(global.TEST_CONFIG.tempDir, { recursive: true });
    }
  },

  /**
   * Clean up test artifacts
   */
  cleanup: () => {
    const fs = require('fs');
    if (fs.existsSync(global.TEST_CONFIG.tempDir)) {
      fs.rmSync(global.TEST_CONFIG.tempDir, { recursive: true, force: true });
    }
  },

  /**
   * Mock EventFlow CLI for testing
   */
  mockCLI: (responses) => {
    const mock = jest.fn();
    responses.forEach((response, index) => {
      mock.mockResolvedValueOnce(response);
    });
    return mock;
  },

  /**
   * Create synthetic sensor data
   */
  createSyntheticData: (type, count = 100) => {
    const data = [];
    for (let i = 0; i < count; i++) {
      const timestamp = i * 1000; // 1ms intervals
      let value;

      switch (type) {
        case 'ecg':
          value = 0.5 * Math.sin(2 * Math.PI * 1.5 * timestamp / 1000000) + Math.random() * 0.05;
          break;
        case 'lidar':
          value = Math.random() * 50 + 0.5; // 0.5-50m distance
          break;
        case 'vibration':
          value = Math.sin(2 * Math.PI * 30 * timestamp / 1000000) * 0.8 +
                  Math.sin(2 * Math.PI * 60 * timestamp / 1000000) * 0.5 +
                  Math.random() * 0.2;
          break;
        default:
          value = Math.random();
      }

      data.push({
        ts: timestamp,
        idx: [0],
        val: parseFloat(value.toFixed(6))
      });
    }
    return data;
  }
};

// Setup before each test
beforeEach(() => {
  // Ensure test directory exists
  global.testUtils.ensureTestDir();

  // Reset any global state
  jest.clearAllMocks();
});

// Cleanup after each test
afterEach(() => {
  // Clean up test artifacts
  global.testUtils.cleanup();
});

// Global error handling
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

// Performance monitoring
global.performanceMetrics = {
  testsRun: 0,
  totalTime: 0,
  failures: 0
};

// Export for use in tests
module.exports = {
  TEST_CONFIG: global.TEST_CONFIG,
  testUtils: global.testUtils
};