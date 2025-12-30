/**
 * EventFlow Test Utilities
 *
 * Shared utilities and helpers for comprehensive testing across all domains.
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');

/**
 * Execute EventFlow CLI command with timeout and error handling
 */
function executeCLI(args, options = {}) {
  const {
    timeout = 30000,
    cwd = path.join(__dirname, '../..'),
    env = { ...process.env, PYTHONPATH: cwd },
    expectError = false
  } = options;

  const cliPath = path.join(cwd, 'eventflow-cli', 'ef.py');
  const cmd = `python3 ${cliPath} ${args.join(' ')}`;

  try {
    const result = execSync(cmd, {
      encoding: 'utf8',
      timeout,
      maxBuffer: 1024 * 1024 * 10, // 10MB buffer
      cwd,
      env
    });

    return {
      success: true,
      output: result.trim(),
      exitCode: 0,
      command: cmd
    };
  } catch (error) {
    const result = {
      success: false,
      output: error.stdout ? error.stdout.trim() : '',
      error: error.stderr ? error.stderr.trim() : error.message,
      exitCode: error.status || 1,
      command: cmd
    };

    if (!expectError) {
      console.error(`CLI command failed: ${cmd}`);
      console.error(`Exit code: ${result.exitCode}`);
      console.error(`Error: ${result.error}`);
    }

    return result;
  }
}

/**
 * Generate synthetic test data for various sensor types
 */
function generateSyntheticData(type, options = {}) {
  const {
    count = 1000,
    sampleRate = 1000,
    duration = 1000,
    noiseLevel = 0.05,
    pattern = 'sine'
  } = options;

  const events = [];
  const startTime = Date.now() * 1000; // microseconds

  for (let i = 0; i < count; i++) {
    const timestamp = startTime + (i * duration * 1000 / count);
    let value;

    // Generate data based on type
    switch (type) {
      case 'ecg':
        // Simulate ECG waveform with PQRST complex
        const phase = (i / count) * 4 * Math.PI;
        value = Math.sin(phase) * 0.8 +
                Math.sin(phase * 3) * 0.3 +
                Math.sin(phase * 5) * 0.1;
        break;

      case 'lidar':
        // Distance measurements with some variation
        const baseDistance = 10 + Math.sin(i * 0.01) * 2;
        value = baseDistance + (Math.random() - 0.5) * noiseLevel;
        break;

      case 'vibration':
        // Multi-frequency vibration pattern
        value = Math.sin(2 * Math.PI * 30 * i / count) * 0.6 +
                Math.sin(2 * Math.PI * 60 * i / count) * 0.4 +
                Math.sin(2 * Math.PI * 120 * i / count) * 0.2;
        break;

      case 'temperature':
        // Temperature with diurnal variation
        const hourOfDay = (i / count) * 24;
        const baseTemp = 20;
        const diurnalVariation = Math.sin((hourOfDay - 6) * Math.PI / 12) * 5;
        value = baseTemp + diurnalVariation + (Math.random() - 0.5) * 0.5;
        break;

      case 'acceleration':
        // 3-axis acceleration (simplified)
        value = Math.random() * 2 - 1; // -1 to 1 range
        break;

      default:
        // Generic noisy signal
        if (pattern === 'sine') {
          value = Math.sin(2 * Math.PI * i / count) + (Math.random() - 0.5) * noiseLevel;
        } else if (pattern === 'random') {
          value = Math.random() * 2 - 1;
        } else {
          value = Math.sin(2 * Math.PI * i / count);
        }
    }

    events.push({
      ts: Math.floor(timestamp),
      idx: type === 'lidar' ? [0, 1, 2] : [0], // 3D for LiDAR
      val: parseFloat(value.toFixed(6))
    });
  }

  return events;
}

/**
 * Write Event Tensor data to JSONL file
 */
function writeEventTensorFile(filePath, events, metadata = {}) {
  const header = {
    header: {
      version: "0.1.0",
      dims: events.length > 0 && events[0].idx.length > 1 ? [events.length, events[0].idx.length] : [events.length],
      units: metadata.units || "arbitrary",
      layout: metadata.layout || "temporal",
      ...metadata
    }
  };

  const lines = [
    JSON.stringify(header),
    ...events.map(event => JSON.stringify(event))
  ];

  fs.writeFileSync(filePath, lines.join('\n') + '\n');
}

/**
 * Read and parse Event Tensor file
 */
function readEventTensorFile(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.trim().split('\n');

  let header = null;
  const events = [];

  for (const line of lines) {
    if (!line.trim()) continue;

    const data = JSON.parse(line);

    if (data.header) {
      header = data.header;
    } else {
      events.push(data);
    }
  }

  return { header, events };
}

/**
 * Compare two Event Tensor files for similarity
 */
function compareEventTensors(file1, file2, tolerance = { time: 50, value: 1e-5 }) {
  const data1 = readEventTensorFile(file1);
  const data2 = readEventTensorFile(file2);

  // Basic checks
  if (data1.events.length !== data2.events.length) {
    return { match: false, reason: `Event count mismatch: ${data1.events.length} vs ${data2.events.length}` };
  }

  if (data1.events.length === 0) {
    return { match: true, reason: 'Both files are empty' };
  }

  // Compare events
  for (let i = 0; i < data1.events.length; i++) {
    const e1 = data1.events[i];
    const e2 = data2.events[i];

    // Time comparison
    if (Math.abs(e1.ts - e2.ts) > tolerance.time) {
      return {
        match: false,
        reason: `Time mismatch at event ${i}: ${e1.ts} vs ${e2.ts} (diff: ${Math.abs(e1.ts - e2.ts)})`
      };
    }

    // Value comparison
    if (Math.abs(e1.val - e2.val) > tolerance.value) {
      return {
        match: false,
        reason: `Value mismatch at event ${i}: ${e1.val} vs ${e2.val} (diff: ${Math.abs(e1.val - e2.val)})`
      };
    }

    // Index comparison (if present)
    if (e1.idx && e2.idx) {
      if (JSON.stringify(e1.idx) !== JSON.stringify(e2.idx)) {
        return {
          match: false,
          reason: `Index mismatch at event ${i}: ${JSON.stringify(e1.idx)} vs ${JSON.stringify(e2.idx)}`
        };
      }
    }
  }

  return { match: true, reason: 'All events match within tolerance' };
}

/**
 * Create temporary test directory
 */
function createTempDir(prefix = 'eventflow-test-') {
  const os = require('os');
  const crypto = require('crypto');

  const tempDir = path.join(os.tmpdir(), prefix + crypto.randomBytes(8).toString('hex'));
  fs.mkdirSync(tempDir, { recursive: true });

  return tempDir;
}

/**
 * Clean up temporary directory
 */
function cleanupTempDir(dirPath) {
  if (fs.existsSync(dirPath)) {
    fs.rmSync(dirPath, { recursive: true, force: true });
  }
}

/**
 * Wait for a condition with timeout
 */
async function waitFor(condition, timeout = 5000, interval = 100) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    if (await condition()) {
      return true;
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }

  return false;
}

/**
 * Performance measurement utilities
 */
const performanceUtils = {
  /**
   * Measure execution time of async function
   */
  async measureTime(asyncFn) {
    const start = process.hrtime.bigint();
    const result = await asyncFn();
    const end = process.hrtime.bigint();
    const executionTime = Number(end - start) / 1e6; // Convert to milliseconds

    return { result, executionTime };
  },

  /**
   * Measure memory usage during function execution
   */
  async measureMemory(asyncFn) {
    const startMemory = process.memoryUsage();
    const { result, executionTime } = await this.measureTime(asyncFn);
    const endMemory = process.memoryUsage();

    const memoryDelta = {
      rss: endMemory.rss - startMemory.rss,
      heapUsed: endMemory.heapUsed - startMemory.heapUsed,
      heapTotal: endMemory.heapTotal - startMemory.heapTotal,
      external: endMemory.external - startMemory.external
    };

    return { result, executionTime, memoryDelta };
  }
};

/**
 * Domain-specific test helpers
 */
const domainHelpers = {
  /**
   * Healthcare domain validation
   */
  validateHealthcareResult(result, expectedMetrics = {}) {
    const { minHR = 50, maxHR = 150, accuracy = 0.95 } = expectedMetrics;

    if (!result || !result.metrics) {
      return { valid: false, reason: 'Missing metrics in result' };
    }

    const { heartRate, accuracy: resultAccuracy } = result.metrics;

    if (heartRate < minHR || heartRate > maxHR) {
      return { valid: false, reason: `Heart rate ${heartRate} outside range [${minHR}, ${maxHR}]` };
    }

    if (resultAccuracy < accuracy) {
      return { valid: false, reason: `Accuracy ${resultAccuracy} below threshold ${accuracy}` };
    }

    return { valid: true, reason: 'Healthcare metrics within acceptable ranges' };
  },

  /**
   * Industrial domain validation
   */
  validateIndustrialResult(result, expectedVibration = {}) {
    const { maxAmplitude = 1.0, frequencyRange = [10, 1000] } = expectedVibration;

    if (!result || !result.analysis) {
      return { valid: false, reason: 'Missing analysis in result' };
    }

    const { peakAmplitude, dominantFrequency } = result.analysis;

    if (peakAmplitude > maxAmplitude) {
      return { valid: false, reason: `Peak amplitude ${peakAmplitude} exceeds threshold ${maxAmplitude}` };
    }

    if (dominantFrequency < frequencyRange[0] || dominantFrequency > frequencyRange[1]) {
      return { valid: false, reason: `Dominant frequency ${dominantFrequency} outside range [${frequencyRange[0]}, ${frequencyRange[1]}]` };
    }

    return { valid: true, reason: 'Industrial metrics within acceptable ranges' };
  },

  /**
   * Autonomous domain validation
   */
  validateAutonomousResult(result, expectedPerformance = {}) {
    const { maxLatency = 25, minAccuracy = 0.98 } = expectedPerformance;

    if (!result || !result.performance) {
      return { valid: false, reason: 'Missing performance metrics in result' };
    }

    const { latency, accuracy } = result.performance;

    if (latency > maxLatency) {
      return { valid: false, reason: `Latency ${latency}ms exceeds threshold ${maxLatency}ms` };
    }

    if (accuracy < minAccuracy) {
      return { valid: false, reason: `Accuracy ${accuracy} below threshold ${minAccuracy}` };
    }

    return { valid: true, reason: 'Autonomous performance within acceptable ranges' };
  }
};

module.exports = {
  executeCLI,
  generateSyntheticData,
  writeEventTensorFile,
  readEventTensorFile,
  compareEventTensors,
  createTempDir,
  cleanupTempDir,
  waitFor,
  performanceUtils,
  domainHelpers
};