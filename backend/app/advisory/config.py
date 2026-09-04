from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CropRuleConfig(BaseModel):
    crop_name: str
    display_name: str
    aliases: List[str] = Field(default_factory=list)
    
    # Irrigation parameters
    irrigation_rain_prob_delay_pct: int = 50
    irrigation_rain_mm_delay: float = 3.0
    irrigation_heavy_rain_drainage_mm: float = 25.0
    irrigation_temp_max_c: float = 38.0
    irrigation_dry_hours_needed: int = 12
    
    # Spraying / Chemical Application parameters
    spray_rain_prob_postpone_pct: int = 40
    spray_rain_mm_postpone: float = 1.5
    spray_dry_window_hours_needed: int = 24
    spray_wind_speed_max_kmh: float = 18.0
    spray_wind_drift_caution_kmh: float = 15.0
    spray_humidity_max_pct: int = 85
    spray_temp_max_c: float = 35.0
    
    # Agronomic disease risk
    prolonged_humidity_risk_pct: int = 80
    
    # Agronomic descriptions
    water_sensitivity_note: str
    spray_sensitivity_note: str


# Pre-configured crop profiles with validated agronomic rules
CROP_PROFILES: Dict[str, CropRuleConfig] = {
    "paddy": CropRuleConfig(
        crop_name="paddy",
        display_name="Paddy (Rice)",
        aliases=["rice", "dhan", "వరి", "धान", "நெல்"],
        irrigation_rain_prob_delay_pct=50,
        irrigation_rain_mm_delay=4.0,
        irrigation_heavy_rain_drainage_mm=30.0,
        spray_rain_prob_postpone_pct=40,
        spray_rain_mm_postpone=1.5,
        spray_dry_window_hours_needed=24,
        spray_wind_speed_max_kmh=20.0,
        spray_wind_drift_caution_kmh=15.0,
        prolonged_humidity_risk_pct=85,
        water_sensitivity_note="Paddy requires standing water in certain growth stages, but excess rain during drainage windows or maturity causes lodging and nutrient leaching.",
        spray_sensitivity_note="Foliar sprays for blast or brown planthopper require at least 12-24 hours without rainfall for systemic absorption."
    ),
    "cotton": CropRuleConfig(
        crop_name="cotton",
        display_name="Cotton",
        aliases=["kapas", "పత్తి", "कपास", "பருத்தி"],
        irrigation_rain_prob_delay_pct=45,
        irrigation_rain_mm_delay=2.5,
        irrigation_heavy_rain_drainage_mm=20.0,
        spray_rain_prob_postpone_pct=35,
        spray_rain_mm_postpone=1.0,
        spray_dry_window_hours_needed=24,
        spray_wind_speed_max_kmh=15.0,
        spray_wind_drift_caution_kmh=12.0,
        prolonged_humidity_risk_pct=80,
        water_sensitivity_note="Cotton is extremely sensitive to waterlogging. Excessive moisture promotes root rot and premature boll shedding.",
        spray_sensitivity_note="Cotton foliar spraying (for whitefly, bollworm) requires calm wind (<15 km/h) to prevent spray drift and rain-free canopy."
    ),
    "wheat": CropRuleConfig(
        crop_name="wheat",
        display_name="Wheat",
        aliases=["gehun", "గోధుమ", "गेहूं", "கோதுமை"],
        irrigation_rain_prob_delay_pct=40,
        irrigation_rain_mm_delay=2.0,
        irrigation_heavy_rain_drainage_mm=25.0,
        spray_rain_prob_postpone_pct=40,
        spray_rain_mm_postpone=1.5,
        spray_dry_window_hours_needed=24,
        spray_wind_speed_max_kmh=16.0,
        spray_wind_drift_caution_kmh=12.0,
        prolonged_humidity_risk_pct=80,
        water_sensitivity_note="Critical irrigation stages include Crown Root Initiation (CRI) and flowering; avoid over-irrigating before rainfall.",
        spray_sensitivity_note="Rust and aphid treatments require dry leaves and moderate wind to adhere effectively."
    ),
    "sugarcane": CropRuleConfig(
        crop_name="sugarcane",
        display_name="Sugarcane",
        aliases=["ganna", "చెరకు", "गन्ना", "கரும்பு"],
        irrigation_rain_prob_delay_pct=55,
        irrigation_rain_mm_delay=5.0,
        irrigation_heavy_rain_drainage_mm=35.0,
        spray_rain_prob_postpone_pct=45,
        spray_rain_mm_postpone=2.0,
        spray_dry_window_hours_needed=24,
        spray_wind_speed_max_kmh=22.0,
        spray_wind_drift_caution_kmh=18.0,
        prolonged_humidity_risk_pct=85,
        water_sensitivity_note="High water consumption crop; can absorb moderate precipitation, but prolonged stagnation causes red rot in poorly drained soils.",
        spray_sensitivity_note="Tall canopy spraying requires good weather windows and adequate droplet retention."
    ),
    "chilli": CropRuleConfig(
        crop_name="chilli",
        display_name="Chilli / Spices",
        aliases=["chilli", "spices", "mirchi", "మిరప", "मिर्च", "மிளகாய்"],
        irrigation_rain_prob_delay_pct=40,
        irrigation_rain_mm_delay=2.0,
        irrigation_heavy_rain_drainage_mm=15.0,
        spray_rain_prob_postpone_pct=30,
        spray_rain_mm_postpone=0.8,
        spray_dry_window_hours_needed=36,
        spray_wind_speed_max_kmh=15.0,
        spray_wind_drift_caution_kmh=10.0,
        prolonged_humidity_risk_pct=75,
        water_sensitivity_note="Chilli is susceptible to damping off and fruit rot (anthracnose); soil must not remain waterlogged.",
        spray_sensitivity_note="Fungicide and foliar sprays are highly sensitive to wash-off; rainfall within 24-36h drastically reduces efficacy."
    )
}


def get_crop_profile(crop_query: Optional[str]) -> CropRuleConfig:
    """
    Resolve crop profile by name or alias. Defaults to Paddy if unspecified.
    """
    if not crop_query:
        return CROP_PROFILES["paddy"]
    
    q = crop_query.strip().lower()
    for key, profile in CROP_PROFILES.items():
        if key in q or q in key:
            return profile
        for alias in profile.aliases:
            if alias.lower() in q:
                return profile
    
    # Generic crop fallback based on paddy/field-crop standards
    return CROP_PROFILES["paddy"]


def register_crop_profile(profile: CropRuleConfig):
    """
    Runtime extension to register additional crops.
    """
    CROP_PROFILES[profile.crop_name.lower()] = profile
