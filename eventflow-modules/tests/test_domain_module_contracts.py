from __future__ import annotations

import pytest

from eventflow_core.eir.graph import EIRGraph

from eventflow_modules.autonomous_vehicles import (
    autonomous_navigation,
    lidar_point_cloud_processing,
    sensor_fusion,
)
from eventflow_modules.bio_signals import ecg_processing, eeg_processing, emg_processing
from eventflow_modules.creative import bio_sequencer, event_graphics, music_generator
from eventflow_modules.environmental import (
    air_quality_monitoring,
    chemical_analysis,
    gas_detection,
)
from eventflow_modules.industrial import (
    predictive_maintenance,
    quality_control,
    vibration_analysis,
)
from eventflow_modules.multimodal_fusion import (
    data_association,
    decision_fusion,
    feature_extraction,
    kalman_filter,
    scene_understanding,
    temporal_alignment,
)
from eventflow_modules.robotics import event_slam, obstacle_avoidance, reflex_controller
from eventflow_modules.scientific_research import (
    correlation_analysis,
    curve_fitting,
    fft_analysis,
    high_speed_acquisition,
    oscilloscope_control,
    precision_timing,
    sensor_control,
    signal_filtering,
    spectrometer_control,
    statistical_analysis,
)
from eventflow_modules.security_surveillance import (
    intrusion_detection,
    security_automation,
    surveillance_system,
    threat_assessment,
)
from eventflow_modules.smart_agriculture import (
    automated_harvesting,
    climate_analysis,
    crop_health_assessment,
    evapotranspiration_calculation,
    growth_tracking,
    ndvi_analysis,
    nutrient_analysis,
    pest_detection,
    ph_monitoring,
    precision_spraying,
    soil_moisture_optimization,
    weather_data_processing,
)
from eventflow_modules.smart_cities import (
    crowd_analysis,
    environmental_monitoring,
    infrastructure_health,
    traffic_monitoring,
)
from eventflow_modules.tactile import pressure_detection, texture_analysis
from eventflow_modules.timeseries import anomaly_detector, change_point, spike_pattern_mining
from eventflow_modules.vision import (
    corner_tracking,
    gesture_detect,
    object_tracking,
    optical_flow,
    optical_flow_dense,
)
from eventflow_modules.wellness import hrv_index, sleep_staging, stress_index


CASES = [
    pytest.param(autonomous_navigation, {"sensor_input": "sensor://fused"}, id="autonomous-navigation"),
    pytest.param(lidar_point_cloud_processing, {"source": "sensor://lidar"}, id="autonomous-lidar"),
    pytest.param(sensor_fusion, {"sources": {"lidar": "a", "radar": "b"}}, id="autonomous-fusion"),
    pytest.param(ecg_processing, {"source": "ecg://lead"}, id="bio-ecg"),
    pytest.param(eeg_processing, {"source": "eeg://cap"}, id="bio-eeg"),
    pytest.param(emg_processing, {"source": "emg://arm"}, id="bio-emg"),
    pytest.param(bio_sequencer, {"bio_stream": "bio://events"}, id="creative-sequencer"),
    pytest.param(event_graphics, {"streams": "gfx://events"}, id="creative-graphics"),
    pytest.param(music_generator, {"streams": "music://events"}, id="creative-musicgen"),
    pytest.param(gas_detection, {"source": "gas://sensor"}, id="environmental-gas"),
    pytest.param(chemical_analysis, {"source": "chem://sensor"}, id="environmental-chemical"),
    pytest.param(air_quality_monitoring, {"sources": ["aq://a", "aq://b"]}, id="environmental-air-quality"),
    pytest.param(vibration_analysis, {"source": "vibe://sensor"}, id="industrial-vibration"),
    pytest.param(predictive_maintenance, {"source": "machine://sensor"}, id="industrial-predictive-maint"),
    pytest.param(quality_control, {"source": "qc://line"}, id="industrial-quality"),
    pytest.param(kalman_filter, {"sources": ["cam://0", "imu://0"]}, id="fusion-kalman"),
    pytest.param(data_association, {"sources": ["cam://0", "radar://0"]}, id="fusion-association"),
    pytest.param(temporal_alignment, {"sources": ["cam://0", "imu://0"]}, id="fusion-temporal"),
    pytest.param(scene_understanding, {"sources": ["fusion://scene"]}, id="fusion-scene"),
    pytest.param(feature_extraction, {"sources": ["fusion://features"]}, id="fusion-feature-extraction"),
    pytest.param(decision_fusion, {"sources": ["decision://a", "decision://b"]}, id="fusion-decision"),
    pytest.param(reflex_controller, {"sensor_stream": "robot://touch"}, id="robotics-reflex"),
    pytest.param(event_slam, {"dvs_source": "robot://dvs", "imu_source": "robot://imu"}, id="robotics-slam"),
    pytest.param(obstacle_avoidance, {"depth_or_flow": "robot://range"}, id="robotics-obstacle"),
    pytest.param(fft_analysis, {"source": "sig://a"}, id="scientific-fft"),
    pytest.param(signal_filtering, {"source": "sig://a"}, id="scientific-signal-filter"),
    pytest.param(correlation_analysis, {"source": "sig://a"}, id="scientific-correlation"),
    pytest.param(curve_fitting, {"source": "exp://a"}, id="scientific-curve-fit"),
    pytest.param(statistical_analysis, {"source": "exp://a"}, id="scientific-statistics"),
    pytest.param(high_speed_acquisition, {"source": "daq://a"}, id="scientific-hs-acq"),
    pytest.param(precision_timing, {"source": "clock://a"}, id="scientific-precision-timing"),
    pytest.param(spectrometer_control, {"source": "spec://a"}, id="scientific-spectrometer"),
    pytest.param(oscilloscope_control, {"source": "scope://a"}, id="scientific-oscilloscope"),
    pytest.param(sensor_control, {"source": "sensor://a"}, id="scientific-sensor-control"),
    pytest.param(intrusion_detection, {"source": "sec://cam"}, id="security-intrusion"),
    pytest.param(security_automation, {"source": "sec://threat"}, id="security-automation"),
    pytest.param(surveillance_system, {"source": "sec://network"}, id="security-surveillance"),
    pytest.param(threat_assessment, {"source": "sec://intrusion"}, id="security-threat"),
    pytest.param(crop_health_assessment, {"source": "agri://crop"}, id="agri-crop-health"),
    pytest.param(ndvi_analysis, {"source": "agri://multi"}, id="agri-ndvi"),
    pytest.param(growth_tracking, {"source": "agri://growth"}, id="agri-growth"),
    pytest.param(soil_moisture_optimization, {"source": "agri://soil"}, id="agri-soil-moisture"),
    pytest.param(ph_monitoring, {"source": "agri://ph"}, id="agri-ph"),
    pytest.param(nutrient_analysis, {"source": "agri://nutrients"}, id="agri-nutrients"),
    pytest.param(precision_spraying, {"source": "agri://spray"}, id="agri-precision-spraying"),
    pytest.param(automated_harvesting, {"source": "agri://harvest"}, id="agri-automated-harvest"),
    pytest.param(pest_detection, {"source": "agri://pests"}, id="agri-pest-detection"),
    pytest.param(weather_data_processing, {"source": "agri://weather"}, id="agri-weather"),
    pytest.param(climate_analysis, {"source": "agri://climate"}, id="agri-climate"),
    pytest.param(evapotranspiration_calculation, {"source": "agri://et"}, id="agri-evapotranspiration"),
    pytest.param(traffic_monitoring, {"source": "city://traffic"}, id="city-traffic"),
    pytest.param(crowd_analysis, {"source": "city://crowd"}, id="city-crowd"),
    pytest.param(environmental_monitoring, {"source": "city://environment"}, id="city-environment"),
    pytest.param(infrastructure_health, {"source": "city://infrastructure"}, id="city-infrastructure"),
    pytest.param(pressure_detection, {"source": "touch://pressure"}, id="tactile-pressure"),
    pytest.param(texture_analysis, {"source": "touch://texture"}, id="tactile-texture"),
    pytest.param(anomaly_detector, {"stream": "ts://events"}, id="timeseries-anomaly"),
    pytest.param(change_point, {"stream": "ts://events"}, id="timeseries-change-point"),
    pytest.param(spike_pattern_mining, {"stream": "ts://events"}, id="timeseries-spike-mining"),
    pytest.param(optical_flow, {"source": "vision://events"}, id="vision-optical-flow"),
    pytest.param(optical_flow_dense, {"source": "vision://events"}, id="vision-optical-flow-dense"),
    pytest.param(corner_tracking, {"source": "vision://events"}, id="vision-corner-tracking"),
    pytest.param(gesture_detect, {"flow_graph_or_source": "vision://events"}, id="vision-gesture"),
    pytest.param(object_tracking, {"source": "vision://events"}, id="vision-object-tracking"),
    pytest.param(hrv_index, {"heart_stream": "well://heart"}, id="wellness-hrv"),
    pytest.param(sleep_staging, {"bio_streams": "well://sleep"}, id="wellness-sleep"),
    pytest.param(stress_index, {"bio_streams": "well://stress"}, id="wellness-stress"),
]


@pytest.mark.parametrize("builder, kwargs", CASES)
def test_domain_module_builders_return_graph(builder, kwargs):
    graph = builder(**kwargs)
    assert isinstance(graph, EIRGraph)
    assert graph.nodes, f"{builder.__name__} produced an empty graph"

    # Structural contract: every edge endpoint refers to a known node.
    for edge in graph.edges:
        assert edge.src[0] in graph.nodes
        assert edge.dst[0] in graph.nodes


@pytest.mark.parametrize("builder,arg_name", [
    (hrv_index, "heart_stream"),
    (sleep_staging, "bio_streams"),
    (stress_index, "bio_streams"),
])
def test_wellness_window_validation(builder, arg_name):
    kwargs = {arg_name: "well://stream", "window": " "}
    with pytest.raises(ValueError, match="window must be a non-empty string"):
        builder(**kwargs)
