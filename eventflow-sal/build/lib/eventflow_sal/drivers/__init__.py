from __future__ import annotations

# Keep driver imports lazy so optional dependencies (e.g., scipy) are only
# required when the corresponding driver module is used.
_EXPORTS = {
    "DVSSource": (".dvs", "DVSSource"),
    "AEDAT4FileSource": (".dvs", "AEDAT4FileSource"),
    "MicSource": (".audio", "MicSource"),
    "WAVFileSource": (".audio", "WAVFileSource"),
    "IMUSource": (".imu", "IMUSource"),
    "CSVFileSource": (".imu", "CSVFileSource"),
    "EnvironmentalSource": (".environmental", "EnvironmentalSource"),
    "EnvironmentalFileSource": (".environmental", "EnvironmentalFileSource"),
    "FusionSource": (".fusion", "FusionSource"),
    "FusionFileSource": (".fusion", "FusionFileSource"),
    "LiDARSource": (".automotive", "LiDARSource"),
    "LiDARFileSource": (".automotive", "LiDARFileSource"),
    "RadarSource": (".automotive", "RadarSource"),
    "RadarFileSource": (".automotive", "RadarFileSource"),
    "TrafficCameraSource": (".city", "TrafficCameraSource"),
    "NoiseSensorSource": (".city", "NoiseSensorSource"),
    "PollutionSensorSource": (".city", "PollutionSensorSource"),
    "CrowdSensorSource": (".city", "CrowdSensorSource"),
    "InfrastructureSensorSource": (".city", "InfrastructureSensorSource"),
    "CitySensorFileSource": (".city", "CitySensorFileSource"),
}

__all__ = list(_EXPORTS.keys())


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)
    mod_name, symbol = _EXPORTS[name]
    mod = __import__(f"{__name__}{mod_name}", fromlist=[symbol])
    return getattr(mod, symbol)
