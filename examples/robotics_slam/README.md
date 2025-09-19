# Robotics SLAM Example

- EIR: examples/robotics_slam/eir.json
- Input: IMU JSONL generated via SAL from CSV

Commands
- python
  ef --json sal-stream --uri "imu.6dof://file?path=examples/robotics_slam/traces/inputs/imu_sample.csv" \
     --out out/imu.norm.jsonl --telemetry-out out/imu.telemetry.json
  ef run --eir examples/robotics_slam/eir.json --backend cpu-sim \
         --input out/imu.norm.jsonl --trace-out out/robotics_slam.golden.jsonl
