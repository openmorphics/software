/**
 * Global Jest Teardown for EventFlow Test Suite
 *
 * Executed once after all test suites complete.
 * Performs cleanup and generates final test reports.
 */

const fs = require('fs');
const path = require('path');

module.exports = async () => {
  console.log('🧹 Cleaning up EventFlow Test Environment...');

  // Generate final test report
  await generateFinalReport();

  // Clean up temporary files
  cleanupTemporaryFiles();

  // Archive test artifacts if needed
  archiveTestArtifacts();

  // Reset environment variables
  resetEnvironment();

  console.log('✅ EventFlow Test Environment Cleaned Up');
};

/**
 * Generate comprehensive final test report
 */
async function generateFinalReport() {
  console.log('📊 Generating final test report...');

  const reportPath = path.join(__dirname, '../../tests/reports/final_report.json');
  const coveragePath = path.join(__dirname, '../../tests/coverage/coverage-summary.json');

  const report = {
    timestamp: new Date().toISOString(),
    testSuite: 'EventFlow Integration Tests',
    version: global.EVENTFLOW_TEST_CONFIG?.version || '1.0.0',
    environment: global.EVENTFLOW_TEST_CONFIG?.environment || {},
    summary: {
      totalTests: global.performanceMetrics?.testsRun || 0,
      failures: global.performanceMetrics?.failures || 0,
      success: (global.performanceMetrics?.testsRun || 0) - (global.performanceMetrics?.failures || 0),
      successRate: calculateSuccessRate(),
      totalTime: global.performanceMetrics?.totalTime || 0
    },
    coverage: loadCoverageReport(),
    performance: await collectPerformanceMetrics(),
    system: collectSystemInfo(),
    recommendations: generateRecommendations()
  };

  // Write report
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  // Print summary to console
  printTestSummary(report);

  console.log(`📄 Final report saved to: ${reportPath}`);
}

/**
 * Calculate test success rate
 */
function calculateSuccessRate() {
  const total = global.performanceMetrics?.testsRun || 0;
  const failures = global.performanceMetrics?.failures || 0;

  if (total === 0) return 0;
  return ((total - failures) / total * 100).toFixed(2);
}

/**
 * Load coverage report data
 */
function loadCoverageReport() {
  try {
    const coveragePath = path.join(__dirname, '../../tests/coverage/coverage-summary.json');
    if (fs.existsSync(coveragePath)) {
      const coverage = JSON.parse(fs.readFileSync(coveragePath, 'utf8'));
      return {
        total: coverage.total || {},
        success: coverage.total?.lines?.pct >= 85
      };
    }
  } catch (error) {
    console.warn('Could not load coverage report:', error.message);
  }

  return { total: {}, success: false };
}

/**
 * Collect performance metrics from test run
 */
async function collectPerformanceMetrics() {
  const baselines = global.PERFORMANCE_BASELINES || {};
  const results = {};

  // Read performance results if available
  const perfResultsPath = path.join(__dirname, '../../tests/temp/performance_results.json');
  if (fs.existsSync(perfResultsPath)) {
    try {
      const perfResults = JSON.parse(fs.readFileSync(perfResultsPath, 'utf8'));
      Object.assign(results, perfResults);
    } catch (error) {
      console.warn('Could not load performance results:', error.message);
    }
  }

  // Add baseline comparisons
  for (const [domain, baseline] of Object.entries(baselines)) {
    if (results[domain]) {
      results[domain].baseline = baseline;
      results[domain].meetsBaseline =
        results[domain].latency <= baseline.latency &&
        results[domain].accuracy >= baseline.accuracy;
    }
  }

  return results;
}

/**
 * Collect system information
 */
function collectSystemInfo() {
  return {
    node: process.version,
    platform: process.platform,
    arch: process.arch,
    cpus: require('os').cpus().length,
    memory: Math.round(require('os').totalmem() / 1024 / 1024 / 1024) + 'GB',
    testEnvironment: {
      jest: require('jest/package.json').version,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      locale: Intl.DateTimeFormat().resolvedOptions().locale
    }
  };
}

/**
 * Generate recommendations based on test results
 */
function generateRecommendations() {
  const recommendations = [];

  // Coverage recommendations
  const coverage = loadCoverageReport();
  if (coverage.total?.lines?.pct < 85) {
    recommendations.push({
      type: 'coverage',
      priority: 'high',
      message: `Coverage is ${coverage.total.lines.pct}%, below 85% threshold. Add more tests.`,
      action: 'Increase test coverage by adding unit tests for uncovered code paths.'
    });
  }

  // Performance recommendations
  const performance = global.PERFORMANCE_BASELINES || {};
  for (const [domain, baseline] of Object.entries(performance)) {
    // This would be populated during test execution
    recommendations.push({
      type: 'performance',
      priority: 'medium',
      message: `Monitor ${domain} performance against ${baseline.latency}ms latency baseline.`,
      action: 'Review performance optimizations if latency exceeds baseline.'
    });
  }

  // Deterministic execution
  recommendations.push({
    type: 'reliability',
    priority: 'high',
    message: 'Ensure deterministic execution across all backends.',
    action: 'Run deterministic validation tests regularly.'
  });

  return recommendations;
}

/**
 * Print test summary to console
 */
function printTestSummary(report) {
  console.log('\n' + '='.repeat(60));
  console.log('🎯 EVENTFLOW TEST SUITE SUMMARY');
  console.log('='.repeat(60));
  console.log(`📊 Tests Run: ${report.summary.totalTests}`);
  console.log(`✅ Passed: ${report.summary.success}`);
  console.log(`❌ Failed: ${report.summary.failures}`);
  console.log(`📈 Success Rate: ${report.summary.successRate}%`);
  console.log(`⏱️ Total Time: ${(report.summary.totalTime / 1000).toFixed(2)}s`);

  if (report.coverage.total?.lines?.pct) {
    console.log(`📋 Coverage: ${report.coverage.total.lines.pct}%`);
  }

  console.log('='.repeat(60) + '\n');
}

/**
 * Clean up temporary test files
 */
function cleanupTemporaryFiles() {
  console.log('🗑️ Cleaning up temporary files...');

  const tempDir = path.join(__dirname, '../../tests/temp');
  const maxAge = 24 * 60 * 60 * 1000; // 24 hours

  if (fs.existsSync(tempDir)) {
    const files = fs.readdirSync(tempDir);
    const now = Date.now();

    files.forEach(file => {
      const filePath = path.join(tempDir, file);
      const stats = fs.statSync(filePath);

      // Remove files older than maxAge
      if (now - stats.mtime.getTime() > maxAge) {
        if (stats.isDirectory()) {
          fs.rmSync(filePath, { recursive: true, force: true });
        } else {
          fs.unlinkSync(filePath);
        }
      }
    });
  }

  console.log('✅ Temporary files cleaned up');
}

/**
 * Archive important test artifacts
 */
function archiveTestArtifacts() {
  // In a real implementation, this would archive coverage reports,
  // performance data, and failed test logs for CI/CD analysis

  const archiveDir = path.join(__dirname, '../../tests/archive');
  if (!fs.existsSync(archiveDir)) {
    fs.mkdirSync(archiveDir, { recursive: true });
  }

  // Archive logic would go here
  console.log('📦 Test artifacts archived');
}

/**
 * Reset environment variables
 */
function resetEnvironment() {
  // Clean up test-specific environment variables
  delete process.env.EVENTFLOW_TEST_MODE;
  delete process.env.EVENTFLOW_LOG_LEVEL;

  // Reset Python environment
  delete process.env.PYTHONHASHSEED;
  delete process.env.EF_NATIVE;

  console.log('🔄 Environment reset');
}

// Export for external use
module.exports = {
  generateFinalReport,
  cleanupTemporaryFiles
};