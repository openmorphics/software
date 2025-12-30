/**
 * Jest Test Results Processor for EventFlow
 *
 * Processes test results to generate detailed reports, track performance
 * regressions, and provide insights for continuous improvement.
 */

const fs = require('fs');
const path = require('path');

class EventFlowResultsProcessor {
  constructor(globalConfig, options) {
    this.globalConfig = globalConfig;
    this.options = options;
    this.results = [];
    this.startTime = Date.now();
  }

  onTestResult(test, testResult, aggregatedResult) {
    // Process individual test results
    const processedResult = this.processTestResult(test, testResult);

    // Store for later analysis
    this.results.push(processedResult);

    // Check for performance regressions
    this.checkPerformanceRegression(processedResult);

    // Update coverage tracking
    this.updateCoverageTracking(testResult.coverage);

    return testResult;
  }

  onRunComplete(contexts, results) {
    const endTime = Date.now();
    const totalTime = endTime - this.startTime;

    // Generate comprehensive report
    const report = this.generateComprehensiveReport(results, totalTime);

    // Save report
    this.saveReport(report);

    // Print summary
    this.printSummary(report);

    // Send notifications if configured
    this.sendNotifications(report);
  }

  processTestResult(test, testResult) {
    return {
      testFile: test.path,
      testSuite: path.basename(test.path, '.test.js'),
      duration: testResult.duration,
      status: testResult.status,
      numPassingTests: testResult.numPassingTests,
      numFailingTests: testResult.numFailingTests,
      numPendingTests: testResult.numPendingTests,
      failureMessages: testResult.failureMessages,
      testResults: testResult.testResults.map(tr => ({
        title: tr.title,
        status: tr.status,
        duration: tr.duration,
        failureMessages: tr.failureMessages,
        ancestorTitles: tr.ancestorTitles
      })),
      coverage: testResult.coverage,
      memoryUsage: process.memoryUsage(),
      timestamp: new Date().toISOString()
    };
  }

  checkPerformanceRegression(testResult) {
    // Check if test duration exceeds acceptable threshold
    const maxDuration = this.getMaxTestDuration(testResult.testSuite);

    if (testResult.duration > maxDuration) {
      console.warn(`⚠️ Performance regression detected in ${testResult.testSuite}:`);
      console.warn(`   Duration: ${testResult.duration}ms (max: ${maxDuration}ms)`);

      // Log regression for tracking
      this.logRegression(testResult);
    }
  }

  getMaxTestDuration(testSuite) {
    // Domain-specific duration limits
    const limits = {
      'healthcare': 60000,    // 1 minute
      'industrial': 90000,    // 1.5 minutes
      'autonomous': 120000,   // 2 minutes
      'smart_cities': 75000,  // 1.25 minutes
      'scientific': 100000,   // ~1.7 minutes
      'agriculture': 80000,   // ~1.3 minutes
      'security': 60000       // 1 minute
    };

    // Extract domain from test suite name
    for (const [domain, limit] of Object.entries(limits)) {
      if (testSuite.toLowerCase().includes(domain)) {
        return limit;
      }
    }

    return 30000; // Default 30 seconds
  }

  logRegression(testResult) {
    const regressionLog = path.join(__dirname, '../../tests/logs/regressions.jsonl');

    const entry = {
      timestamp: new Date().toISOString(),
      testSuite: testResult.testSuite,
      duration: testResult.duration,
      expectedMax: this.getMaxTestDuration(testResult.testSuite),
      regression: testResult.duration - this.getMaxTestDuration(testResult.testSuite)
    };

    fs.appendFileSync(regressionLog, JSON.stringify(entry) + '\n');
  }

  updateCoverageTracking(coverage) {
    if (!coverage) return;

    const coverageLog = path.join(__dirname, '../../tests/logs/coverage.jsonl');

    const entry = {
      timestamp: new Date().toISOString(),
      coverage: coverage
    };

    fs.appendFileSync(coverageLog, JSON.stringify(entry) + '\n');
  }

  generateComprehensiveReport(results, totalTime) {
    const report = {
      summary: {
        totalTestSuites: results.numTotalTestSuites,
        passedTestSuites: results.numPassedTestSuites,
        failedTestSuites: results.numFailedTestSuites,
        totalTests: results.numTotalTests,
        passedTests: results.numPassedTests,
        failedTests: results.numFailedTests,
        pendingTests: results.numPendingTests,
        totalTime: totalTime,
        coverage: this.calculateCoverage(results),
        successRate: this.calculateSuccessRate(results)
      },
      performance: {
        slowestTests: this.findSlowestTests(),
        regressions: this.loadRecentRegressions(),
        averages: this.calculateAverages()
      },
      failures: {
        bySuite: this.groupFailuresBySuite(results),
        byType: this.categorizeFailures(results),
        trends: this.analyzeFailureTrends()
      },
      system: {
        nodeVersion: process.version,
        platform: process.platform,
        memoryUsage: process.memoryUsage(),
        testEnvironment: process.env.NODE_ENV || 'test'
      },
      recommendations: this.generateRecommendations(results)
    };

    return report;
  }

  calculateCoverage(results) {
    // Extract coverage from test results
    if (results.coverageMap) {
      const coverage = {};
      results.coverageMap.files().forEach(file => {
        const fileCoverage = results.coverageMap.fileCoverageFor(file);
        coverage[file] = {
          statements: fileCoverage.toSummary().statements.pct,
          branches: fileCoverage.toSummary().branches.pct,
          functions: fileCoverage.toSummary().functions.pct,
          lines: fileCoverage.toSummary().lines.pct
        };
      });
      return coverage;
    }

    return {};
  }

  calculateSuccessRate(results) {
    const total = results.numTotalTests;
    const passed = results.numPassedTests;

    return total > 0 ? ((passed / total) * 100).toFixed(2) : 0;
  }

  findSlowestTests() {
    return this.results
      .filter(r => r.status === 'passed')
      .sort((a, b) => b.duration - a.duration)
      .slice(0, 10)
      .map(r => ({
        suite: r.testSuite,
        duration: r.duration
      }));
  }

  loadRecentRegressions() {
    const regressionLog = path.join(__dirname, '../../tests/logs/regressions.jsonl');

    if (!fs.existsSync(regressionLog)) return [];

    try {
      const content = fs.readFileSync(regressionLog, 'utf8');
      const lines = content.trim().split('\n');
      return lines.slice(-10).map(line => JSON.parse(line)); // Last 10 regressions
    } catch (error) {
      return [];
    }
  }

  calculateAverages() {
    if (this.results.length === 0) return {};

    const totalDuration = this.results.reduce((sum, r) => sum + r.duration, 0);
    const totalTests = this.results.reduce((sum, r) => sum + r.numPassingTests + r.numFailingTests, 0);

    return {
      avgTestDuration: totalTests > 0 ? totalDuration / totalTests : 0,
      avgSuiteDuration: this.results.length > 0 ? totalDuration / this.results.length : 0,
      totalTestSuites: this.results.length,
      totalTests: totalTests
    };
  }

  groupFailuresBySuite(results) {
    const failures = {};

    results.testResults.forEach(suite => {
      if (suite.numFailingTests > 0) {
        failures[suite.testFile] = {
          count: suite.numFailingTests,
          tests: suite.testResults
            .filter(test => test.status === 'failed')
            .map(test => ({
              title: test.title,
              error: test.failureMessages?.[0] || 'Unknown error'
            }))
        };
      }
    });

    return failures;
  }

  categorizeFailures(results) {
    const categories = {
      timeout: [],
      assertion: [],
      exception: [],
      other: []
    };

    results.testResults.forEach(suite => {
      suite.testResults.forEach(test => {
        if (test.status === 'failed' && test.failureMessages) {
          const message = test.failureMessages[0];

          if (message.includes('timeout')) {
            categories.timeout.push({ suite: suite.testFile, test: test.title, message });
          } else if (message.includes('AssertionError') || message.includes('Expect')) {
            categories.assertion.push({ suite: suite.testFile, test: test.title, message });
          } else if (message.includes('Exception') || message.includes('Error:')) {
            categories.exception.push({ suite: suite.testFile, test: test.title, message });
          } else {
            categories.other.push({ suite: suite.testFile, test: test.title, message });
          }
        }
      });
    });

    return categories;
  }

  analyzeFailureTrends() {
    // Analyze failure patterns over time
    // This would compare with historical data in a real implementation
    return {
      increasing: [], // Tests failing more over time
      decreasing: [], // Tests failing less over time
      consistent: []  // Consistent failure patterns
    };
  }

  generateRecommendations(results) {
    const recommendations = [];

    // Coverage recommendations
    if (results.successRate < 95) {
      recommendations.push({
        type: 'coverage',
        priority: 'high',
        message: `Test success rate is ${results.successRate}%. Consider improving test reliability.`,
        action: 'Review and fix failing tests, add error handling.'
      });
    }

    // Performance recommendations
    const slowTests = this.findSlowestTests();
    if (slowTests.length > 0 && slowTests[0].duration > 10000) { // > 10 seconds
      recommendations.push({
        type: 'performance',
        priority: 'medium',
        message: `Slowest test takes ${slowTests[0].duration}ms. Consider optimization.`,
        action: 'Profile slow tests and optimize execution time.'
      });
    }

    // Reliability recommendations
    const regressions = this.loadRecentRegressions();
    if (regressions.length > 0) {
      recommendations.push({
        type: 'reliability',
        priority: 'high',
        message: `${regressions.length} performance regressions detected.`,
        action: 'Review recent changes and optimize performance.'
      });
    }

    return recommendations;
  }

  saveReport(report) {
    const reportDir = path.join(__dirname, '../../tests/reports');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const reportPath = path.join(reportDir, `test_report_${timestamp}.json`);

    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    // Also save as latest
    const latestPath = path.join(reportDir, 'latest_report.json');
    fs.writeFileSync(latestPath, JSON.stringify(report, null, 2));

    console.log(`📊 Test report saved to: ${reportPath}`);
  }

  printSummary(report) {
    console.log('\n' + '='.repeat(60));
    console.log('🧪 EVENTFLOW TEST SUMMARY');
    console.log('='.repeat(60));
    console.log(`📊 Test Suites: ${report.summary.passedTestSuites}/${report.summary.totalTestSuites} passed`);
    console.log(`✅ Tests: ${report.summary.passedTests}/${report.summary.totalTests} passed`);
    console.log(`⏱️ Total Time: ${(report.summary.totalTime / 1000).toFixed(2)}s`);
    console.log(`📈 Success Rate: ${report.summary.successRate}%`);

    if (report.recommendations.length > 0) {
      console.log('\n💡 Recommendations:');
      report.recommendations.forEach(rec => {
        console.log(`  ${rec.priority.toUpperCase()}: ${rec.message}`);
      });
    }

    console.log('='.repeat(60) + '\n');
  }

  sendNotifications(report) {
    // In a real implementation, this could send notifications to
    // Slack, email, or CI/CD systems based on test results

    if (report.summary.successRate < 90) {
      console.warn('⚠️ Test success rate below 90%. Consider investigation.');
    }

    if (report.recommendations.some(r => r.priority === 'high')) {
      console.warn('🚨 High-priority recommendations detected. Review required.');
    }
  }
}

module.exports = EventFlowResultsProcessor;