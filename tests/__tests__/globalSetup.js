/**
 * Global Jest Setup for EventFlow Test Suite
 *
 * Executed once before all test suites begin.
 * Sets up global test environment and validates prerequisites.
 */

const fs = require('fs');
const path = require('path');

module.exports = async () => {
  console.log('🚀 Setting up EventFlow Test Environment...');

  // Validate prerequisites
  await validatePrerequisites();

  // Create necessary directories
  createTestDirectories();

  // Initialize test configuration
  initializeTestConfig();

  // Set up environment variables
  setupEnvironment();

  // Validate EventFlow installation
  await validateEventFlowInstallation();

  console.log('✅ EventFlow Test Environment Ready');
};

/**
 * Validate system prerequisites for testing
 */
async function validatePrerequisites() {
  console.log('🔍 Validating prerequisites...');

  // Check Node.js version
  const nodeVersion = process.version.match(/^v(\d+)\.(\d+)\.(\d+)/);
  if (!nodeVersion || parseInt(nodeVersion[1]) < 16) {
    throw new Error('Node.js 16+ required for EventFlow testing');
  }

  // Check Python availability
  try {
    const { execSync } = require('child_process');
    execSync('python3 --version', { stdio: 'pipe' });
  } catch (error) {
    throw new Error('Python 3 required for EventFlow testing');
  }

  // Check for EventFlow CLI
  const cliPath = path.join(__dirname, '../../eventflow-cli/ef.py');
  if (!fs.existsSync(cliPath)) {
    throw new Error('EventFlow CLI not found. Run installation first.');
  }

  console.log('✅ Prerequisites validated');
}

/**
 * Create test directories
 */
function createTestDirectories() {
  console.log('📁 Creating test directories...');

  const directories = [
    'tests/temp',
    'tests/coverage',
    'tests/reports',
    'tests/golden_traces',
    'tests/baselines',
    'tests/logs'
  ];

  directories.forEach(dir => {
    const fullPath = path.join(__dirname, '../..', dir);
    if (!fs.existsSync(fullPath)) {
      fs.mkdirSync(fullPath, { recursive: true });
    }
  });

  console.log('✅ Test directories created');
}

/**
 * Initialize global test configuration
 */
function initializeTestConfig() {
  console.log('⚙️ Initializing test configuration...');

  // Global test configuration
  global.EVENTFLOW_TEST_CONFIG = {
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    environment: {
      node: process.version,
      platform: process.platform,
      arch: process.arch
    },
    paths: {
      root: path.join(__dirname, '../..'),
      cli: path.join(__dirname, '../../eventflow-cli/ef.py'),
      examples: path.join(__dirname, '../../examples'),
      modules: path.join(__dirname, '../../eventflow-modules'),
      tests: path.join(__dirname, '../..'),
      temp: path.join(__dirname, '../../tests/temp')
    },
    timeouts: {
      unit: 30000,      // 30 seconds
      integration: 120000, // 2 minutes
      performance: 300000,  // 5 minutes
      e2e: 600000         // 10 minutes
    },
    coverage: {
      threshold: 85,
      exclude: [
        'node_modules/**',
        'tests/**',
        '**/*.config.js',
        '**/*.setup.js'
      ]
    }
  };

  // Performance baseline templates
  global.PERFORMANCE_BASELINES = {
    healthcare: { latency_ms: 50, accuracy: 0.95, memory_mb: 100 },
    industrial: { latency_ms: 75, accuracy: 0.92, memory_mb: 120 },
    autonomous: { latency_ms: 25, accuracy: 0.98, memory_mb: 150 },
    smart_cities: { latency_ms: 60, accuracy: 0.90, memory_mb: 110 },
    scientific: { latency_ms: 80, accuracy: 0.99, memory_mb: 130 },
    agriculture: { latency_ms: 100, accuracy: 0.88, memory_mb: 105 },
    security: { latency_ms: 40, accuracy: 0.94, memory_mb: 95 }
  };

  console.log('✅ Test configuration initialized');
}

/**
 * Set up environment variables for testing
 */
function setupEnvironment() {
  console.log('🌍 Setting up test environment...');

  // EventFlow-specific environment variables
  process.env.EVENTFLOW_TEST_MODE = '1';
  process.env.EVENTFLOW_LOG_LEVEL = 'WARN'; // Reduce log noise during tests
  process.env.PYTHONPATH = path.join(__dirname, '../..');

  // Python environment for EventFlow
  process.env.PYTHONHASHSEED = '42'; // Deterministic hashing
  process.env.EF_NATIVE = '0'; // Start with Python fallback

  // Node.js environment
  process.env.NODE_ENV = 'test';
  process.env.JEST_WORKER_ID = process.env.JEST_WORKER_ID || '1';

  console.log('✅ Test environment configured');
}

/**
 * Validate EventFlow installation and basic functionality
 */
async function validateEventFlowInstallation() {
  console.log('🔧 Validating EventFlow installation...');

  try {
    const { execSync } = require('child_process');
    const cliPath = global.EVENTFLOW_TEST_CONFIG.paths.cli;

    // Test CLI help command
    const helpOutput = execSync(`python3 ${cliPath} --help`, {
      encoding: 'utf8',
      timeout: 10000
    });

    if (!helpOutput.includes('EventFlow')) {
      throw new Error('CLI help command failed');
    }

    // Test basic validation (if example exists)
    const exampleEir = path.join(global.EVENTFLOW_TEST_CONFIG.paths.examples, 'medical_bio_signals/eir.json');
    if (fs.existsSync(exampleEir)) {
      execSync(`python3 ${cliPath} --json validate --eir ${exampleEir}`, {
        encoding: 'utf8',
        timeout: 10000
      });
    }

    console.log('✅ EventFlow installation validated');

  } catch (error) {
    console.error('❌ EventFlow validation failed:', error.message);
    throw new Error(`EventFlow installation validation failed: ${error.message}`);
  }
}

// Export configuration for use in tests
global.getTestConfig = () => global.EVENTFLOW_TEST_CONFIG;
global.getPerformanceBaselines = () => global.PERFORMANCE_BASELINES;