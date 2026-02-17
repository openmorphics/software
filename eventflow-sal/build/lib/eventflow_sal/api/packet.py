from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Literal

TimeUnit = Literal["ns","us","ms"]
MagUnit = str

@dataclass(frozen=True)
class EventPacket:
    t_ns: int; channel: int; value: float; meta: Dict[str,Any]
    def with_time_offset(self,d:int)->"EventPacket": return EventPacket(self.t_ns+d,self.channel,self.value,self.meta)

def dvs_event(t,x,y,p)->EventPacket: return EventPacket(t,0,float(p),{"unit":"pol","x":x,"y":y,"polarity":p})
def audio_band_event(t,b,m,u:MagUnit="dB")->EventPacket: return EventPacket(t,b,m,{"unit":u})
def imu_axis_event(t,a,m,u:MagUnit="m/s^2")->EventPacket: return EventPacket(t,a,m,{"unit":u})
def tactile_event(t,x,y,p,u:MagUnit="pressure")->EventPacket: return EventPacket(t,0,float(p),{"unit":u,"x":x,"y":y,"pressure":p})
def bio_signal_event(t,ch,m,u:MagUnit="dimensionless")->EventPacket: return EventPacket(t,ch,m,{"unit":u})
def environmental_event(t,sensor_type,m,u:MagUnit="ppm")->EventPacket: return EventPacket(t,0,float(m),{"unit":u,"sensor_type":sensor_type,"concentration":m})
def industrial_event(t,ch,m,u:MagUnit="dimensionless")->EventPacket: return EventPacket(t,ch,float(m),{"unit":u,"sensor_value":m})
def lidar_point_event(t,x,y,z,intensity,u:MagUnit="m")->EventPacket: return EventPacket(t,0,float(z),{"unit":u,"x":x,"y":y,"z":z,"intensity":intensity})
def radar_detection_event(t,range_m,azimuth_deg,elevation_deg,velocity_mps,u:MagUnit="m")->EventPacket: return EventPacket(t,0,float(range_m),{"unit":u,"azimuth":azimuth_deg,"elevation":elevation_deg,"velocity":velocity_mps,"range":range_m})
def soil_moisture_event(t,depth_cm,moisture_pct,u:MagUnit="%")->EventPacket: return EventPacket(t,0,float(moisture_pct),{"unit":u,"depth_cm":depth_cm,"moisture":moisture_pct})
def soil_ph_event(t,depth_cm,ph_value,u:MagUnit="pH")->EventPacket: return EventPacket(t,0,float(ph_value),{"unit":u,"depth_cm":depth_cm,"ph":ph_value})
def nutrient_event(t,nutrient_type,concentration,u:MagUnit="ppm")->EventPacket: return EventPacket(t,0,float(concentration),{"unit":u,"nutrient":nutrient_type,"concentration":concentration})
def weather_event(t,sensor_type,value,u:MagUnit="dimensionless")->EventPacket: return EventPacket(t,0,float(value),{"unit":u,"sensor_type":sensor_type,"value":value})
def crop_sensor_event(t,x,y,measurement,u:MagUnit="dimensionless")->EventPacket: return EventPacket(t,0,float(measurement),{"unit":u,"x":x,"y":y,"measurement":measurement})
