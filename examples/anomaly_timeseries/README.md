# Time Series Anomaly Detection Example

This example shows how to convert IMU CSV to Event Tensor JSONL via SAL and run a plan.

- IMU sample CSV: examples/robotics_slam/traces/inputs/imu_sample.csv
- EIR: examples/anomaly_timeseries/eir.json

Commands
- python
  ef --json sal-stream \
     --uri "imu.6dof://file?path=examples/robotics_slam/traces/inputs/imu_sample.csv" \
     --out out/imu.norm.jsonl --telemetry-out out/imu.telemetry.json
  ef build --eir examples/anomaly_timeseries/eir.json --backend cpu-sim --plan-out out/anomaly.plan.json
  ef run --eir examples/anomaly_timeseries/eir.json \
         --backend cpu-sim \
         --input out/imu.norm.jsonl \
         --trace-out out/anomaly.golden.jsonl \
         --plan out/anomaly.plan.json
  ef --json compare-traces --golden out/anomaly.golden.jsonl \
                           --candidate out/anomaly.golden.jsonl
