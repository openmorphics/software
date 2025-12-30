/**
 * Jest Configuration for EventFlow Test Harness
 *
 * Comprehensive testing configuration for automated testing across
 * all 10 domain modules with performance benchmarks and CI/CD integration.
 */

module.exports = {
  // Test environment and setup
  testEnvironment: 'node',
  setupFilesAfterEnv: ['<rootDir>/tests/setupJest.js'],
  testMatch: [
    '<rootDir>/tests/__tests__/**/*.test.js',
    '<rootDir>/tests/__tests__/**/*.spec.js'
  ],

  // Test execution
  testTimeout: 300000, // 5 minutes max per test
  maxWorkers: process.env.CI ? 2 : '50%', // Limit workers in CI
  bail: process.env.CI ? 1 : 0, // Stop on first failure in CI

  // Coverage configuration
  collectCoverageFrom: [
    'tests/__tests__/**/*.js',
    '!tests/__tests__/**/*.test.js',
    '!tests/__tests__/**/*.spec.js',
    '!**/node_modules/**'
  ],
  coverageDirectory: 'tests/coverage',
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json-summary'
  ],
  coverageThreshold: {
    global: {
      branches: 85,
      functions: 90,
      lines: 85,
      statements: 85
    }
  },

  // Test reporting
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: 'tests/reports',
      outputName: 'junit.xml',
      suiteName: 'EventFlow Integration Tests'
    }]
  ],

  // Custom test environment
  testEnvironmentOptions: {
    url: 'http://localhost'
  },

  // Global setup and teardown
  globalSetup: '<rootDir>/tests/globalSetup.js',
  globalTeardown: '<rootDir>/tests/globalTeardown.js',

  // Module mocking
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@test/(.*)$': '<rootDir>/tests/$1'
  },

  // Transform configuration
  transform: {
    '^.+\\.js$': 'babel-jest'
  },

  // Module directories
  moduleDirectories: [
    'node_modules',
    '<rootDir>'
  ],

  // Test results processor
  testResultsProcessor: '<rootDir>/tests/resultsProcessor.js',

  // Custom matchers and utilities
  setupFiles: [
    '<rootDir>/tests/matchers.js'
  ]
};