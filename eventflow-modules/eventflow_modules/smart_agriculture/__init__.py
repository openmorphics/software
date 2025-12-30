"""Smart agriculture domain module exports for precision farming applications. See usage examples in [README](eventflow-modules/README.md:1)."""
from __future__ import annotations
from .crop_monitoring import crop_health_assessment, ndvi_analysis, growth_tracking
from .soil_analysis import soil_moisture_optimization, ph_monitoring, nutrient_analysis
from .agricultural_automation import precision_spraying, automated_harvesting, pest_detection
from .environmental_monitoring import weather_data_processing, climate_analysis, evapotranspiration_calculation
__all__ = [
    "crop_health_assessment",
    "ndvi_analysis",
    "growth_tracking",
    "soil_moisture_optimization",
    "ph_monitoring",
    "nutrient_analysis",
    "precision_spraying",
    "automated_harvesting",
    "pest_detection",
    "weather_data_processing",
    "climate_analysis",
    "evapotranspiration_calculation",
]