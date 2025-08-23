import pytest
from unittest.mock import patch, MagicMock
from config import AppConfig, WeatherConfig, DiscordClientConfig, ParkClientConfig, CountryConfig, ParkConfig, WeatherState
from park_data_client import ParkDataClient
from weather_client import ParkWeatherClient
from discord_client import DiscordClient
import time
import asyncio


def make_dummy_park_config():
    return ParkConfig(
        name="Test Park",
        url="http://example.com/queue_times.json",
        lat=0.0,
        lon=0.0,
        country=CountryConfig(name="Testland", flag=":flag_test:")
    )

def make_dummy_park_client_config():
    return ParkClientConfig(
        include_single_rider_lines=False,
        default_land_key="DEFAULT_LAND",
        single_rider_prefix="Single Rider",
        stale_data_threshold_seconds=3600
    )

def make_dummy_weather_config():
    return WeatherConfig(
        url="http://example.com/weather",
        cache_session_name=".cache",
        cache_session_expire=3600,
        retry_count=1,
        retry_backoff_factor=0.1,
        current_weather_query_params=["temperature_2m", "weather_code"],
        wind_speed_unit="ms",
        temperature_unit="fahrenheit",
        precipitation_unit="inch",
        unknown_emoji="❓",
        weather_states={0: WeatherState(emoji="☀️", description="Clear sky")}
    )

def make_dummy_discord_config():
    return DiscordClientConfig(
        token_filename="dummy",
        embed_color="0x3498db"
    )

def test_park_data_client_process_park_data_valid():
    client = ParkDataClient(make_dummy_park_client_config())
    client.parkData = {"timezone": "UTC"}
    client.queueTimesData = {
        "lands": [
            {"name": "Land1", "rides": [
                {"name": "Ride1", "is_open": True, "wait_time": 10, "last_updated": "2024-01-01T12:00:00Z"}
            ]}
        ]
    }
    client.process_park_data()
    assert client.parkTz == "UTC"
    assert any("Ride1" in line for line in client.messageLines)
    assert not client.allClosed

def test_park_data_client_process_park_data_missing_timezone():
    client = ParkDataClient(make_dummy_park_client_config())
    client.parkData = {}
    client.queueTimesData = {}
    client.process_park_data()
    assert client.parkTz == ""

def test_park_data_client_is_data_stale():
    client = ParkDataClient(make_dummy_park_client_config())
    client.parkTz = "UTC"
    client.latestUpdate = int(time.time()) - 4000
    assert client.is_data_stale()
    client.latestUpdate = int(time.time())
    assert not client.is_data_stale()

def test_park_data_client_hasData():
    client = ParkDataClient(make_dummy_park_client_config())
    client.messageLines = []
    assert not client.hasData
    client.messageLines = ["something"]
    assert client.hasData

def test_weather_client_current_temperature_and_unit():
    config = make_dummy_weather_config()
    client = ParkWeatherClient(config)
    client.last_fetched_data = {"temperature_2m": 72.6}
    assert client.current_temperature == 72.6
    assert client.current_temperature_unit == "F"

def test_weather_client_fetch_weather_sets_emoji_and_success(monkeypatch):
    config = make_dummy_weather_config()
    client = ParkWeatherClient(config)
    fake_response = MagicMock()
    fake_response.Current().Variables.side_effect = lambda idx: MagicMock(Value=lambda: [72.0, 0][idx])
    monkeypatch.setattr(client.openmeteo_client, "weather_api", lambda url, params: [fake_response])
    client.config.current_weather_query_params = ["temperature_2m", "weather_code"]
    client.config.weather_states = {0: WeatherState(emoji="☀️", description="Clear sky")}
    asyncio.run(client.fetch_weather(0, 0))
    assert client.last_fetch_successful
    assert client.last_emoji == "☀️"

def test_discord_client_get_embed_color():
    config = make_dummy_discord_config()
    assert config.get_embed_color() == int("0x3498db", 16)

def test_app_config_parsing():
    # Minimal config for parsing
    app_config = AppConfig(
        use_discord=False,
        countries={"US": CountryConfig(name="United States", flag=":flag_us:")},
        parks={"Test": make_dummy_park_config()},
        commands={"!TestWaits": make_dummy_park_config()},
        weather_config=make_dummy_weather_config(),
        park_client_config=make_dummy_park_client_config(),
        discord_client_config=make_dummy_discord_config(),
        include_weather=True,
        error_color="0xff0000",
        wait_response_title_suffix="Wait Times",
        wait_response_error_description="No wait time data available.",
        help_response_title="Help",
        help_command="!Help",
        stale_data_message="Stale data",
        all_closed_message="All closed",
        current_weather_header="Weather",
        weather_data_unavailable_message="No weather"
    )
    assert app_config.use_discord is False
    assert app_config.weather_config.url.startswith("http")