from config import WeatherConfig
import openmeteo_requests
import requests_cache
from retry_requests import retry



class ParkWeatherClient:
    """
    ParkWeatherClient is responsible for fetching and processing weather data for given lon/lat commands.
    Exactly what is fetched is configurable in weather_config section of the config.
    """

    def __init__(self, weather_config: WeatherConfig):
        self.config: WeatherConfig = weather_config
        self.last_fetch_successful: bool = False
        self.last_fetched_data: dict = {}
        self.last_emoji: str = self.config.unknown_emoji
        cache_session = requests_cache.CachedSession(self.config.cache_session_name, expire_after=self.config.cache_session_expire)
        retry_session = retry(cache_session, retries=self.config.retry_count, backoff_factor=self.config.retry_backoff_factor)
        self.openmeteo_client = openmeteo_requests.Client(session=retry_session)

    async def fetch_weather(self, latitude: float, longitude: float):
        """
        Fetch weather data for the given latitude and longitude.
        Also parses the weather code from the response and updates the last_emoji.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": self.config.current_weather_query_params,
            "wind_speed_unit": self.config.wind_speed_unit,
            "temperature_unit": self.config.temperature_unit,
            "precipitation_unit": self.config.precipitation_unit,
        }

        responses = self.openmeteo_client.weather_api(self.config.url, params=params)
        if responses is None or len(responses) == 0:
            print("Error getting weather data, response is malformed")
            self.last_fetch_successful = False
            return None

        response = responses[0]
        #print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
        #print(f"Elevation: {response.Elevation()} m asl")
        #print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

        for idx, variableName in enumerate(self.config.current_weather_query_params):
            self.last_fetched_data[variableName] = response.Current().Variables(idx).Value()

        # Parse the weather code and get its corresponding emoji
        weatherCode = self.last_fetched_data.get("weather_code", None)
        if weatherCode is not None and weatherCode in self.config.weather_states:
            self.last_emoji = self.config.weather_states[weatherCode].emoji
        else:
            self.last_emoji = self.config.unknown_emoji

        self.last_fetch_successful = True

    @property
    def current_temperature(self) -> int:
        """Returns the current temperature in the specified unit."""
        return round(self.last_fetched_data.get("temperature_2m", 0), 1)
    
    @property
    def current_temperature_unit(self) -> str:
        """Returns the unit of the current temperature."""
        return self.config.temperature_unit[0].upper() if self.config.temperature_unit else self.config.unknown_emoji
