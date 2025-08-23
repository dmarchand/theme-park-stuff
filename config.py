from pydantic import BaseModel
from typing import Dict, List

class WeatherState(BaseModel):
    emoji: str
    description: str

class WeatherConfig(BaseModel):
    url: str
    cache_session_name: str
    cache_session_expire: int
    retry_count: int
    retry_backoff_factor: float
    current_weather_query_params: List[str]
    wind_speed_unit: str
    temperature_unit: str
    precipitation_unit: str
    unknown_emoji: str
    weather_states: Dict[int, WeatherState]

class CountryConfig(BaseModel):
    name: str
    flag: str

class ParkConfig(BaseModel):
    name: str
    url: str
    lat: float
    lon: float
    country: CountryConfig

class ParkClientConfig(BaseModel):
    include_single_rider_lines: bool
    default_land_key: str
    single_rider_prefix: str
    stale_data_threshold_seconds: int

class DiscordClientConfig(BaseModel):
    token_filename: str
    embed_color: str

    def get_embed_color(self) -> int:
        return int(self.embed_color, 16)

class AppConfig(BaseModel):
    use_discord: bool
    countries: Dict[str, CountryConfig]
    parks: Dict[str, ParkConfig]
    commands: Dict[str, ParkConfig]
    weather_config: WeatherConfig
    park_client_config: ParkClientConfig
    discord_client_config: DiscordClientConfig
    include_weather: bool
    error_color: str
    wait_response_title_suffix: str
    wait_response_error_description: str
    help_response_title: str
    help_command: str
    stale_data_message: str
    all_closed_message: str
    current_weather_header: str
    weather_data_unavailable_message: str
