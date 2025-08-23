import asyncio
import discord
import sys
import yaml

from pytz import timezone
from datetime import datetime
from config import AppConfig
from discord_client import DiscordClient
from park_data_client import ParkDataClient
from weather_client import ParkWeatherClient


class App:

    def __init__(self, config_path: str = "config.yaml"):
        self.configPath: str = config_path
        self.config: AppConfig = None
        self.discordClient: DiscordClient = None
        self.weatherClient: ParkWeatherClient = None
        self.parkDataClient: ParkDataClient = None

    def startup(self):
        """
        Starts up the application by initializing clients and loading configuration.
        """

        # Load configuration (park data, commands, URLs, etc.)
        # Should always be done prior to anything else, as lots of stuff depends on config
        self.config = self._load_yaml_config()
        
        self.weatherClient = ParkWeatherClient(self.config.weather_config)
        self.parkDataClient = ParkDataClient(self.config.park_client_config)

        # Discord startup
        if self.config.use_discord:
            self.discordClient = DiscordClient(self.config.discord_client_config)
            if not self.discordClient.configure():
                print("Failed to configure Discord client but use_discord is enabled, bailing out...")
                return
            
            # Binding discord events
            self.discordClient.client.event(self.on_ready)
            self.discordClient.client.event(self.on_message)
            self.discordClient.run()
        

    ## Discord Event Handlers -- it'd be nice to not have these in the main app, but for now it's the easiest way to communicate between the client and app

    async def on_ready(self):
        """
        Called when the Discord bot is ready.
        """
        print(f'We have logged in as {self.discordClient.client.user}')

    async def on_message(self, message: discord.Message):
        """
        Called when a Discord message is received, ignores messages from the bot itself.
        Determines the appropriate action based on the message content.
        """
        if message.author == self.discordClient.client.user:
            return

        if message.content.startswith(self.config.help_command):
            await self.do_help()
        else:
            if message.content in self.config.commands:
                await self.do_waits(message.content)

    ## Command Handlers

    async def do_response(self, title: str, description: str, color: int = None):
        """
        Sends a response message, either through Discord or the console.
        """
        if self.config.use_discord and self.discordClient:
            await self.discordClient.send_discord_embed(title, description, color)
        else:
            print(f"{title}\n{description}")

    async def do_help(self):
        """
        Sends a help message listing all available park wait commands.
        """
        lines = []
        lines.append(f"**Park Wait Commands Supported**\n")
        for command_name, park in self.config.commands.items():
            # "**Epcot :flag_us::** !EpcotWaits"
            lines.append(f"""**{park.name} {park.country.flag}:** {command_name}""")

        description_text = "\n".join(lines)
        await self.do_response(
            title=self.config.help_response_title,
            description=description_text
        )

    async def do_waits(self, command: str):
        """
        Handles a wait check command for a specific park.
        """
        park = self.config.commands[command]
        await self.parkDataClient.fetch_park_data(park)
        self.parkDataClient.process_park_data()

        # Something went wrong while getting or processing the data, all we can do is let the client know an error occurred.
        if not self.parkDataClient.hasData:
            await self.do_response(
                title=self.config.help_response_title,
                description=self.config.wait_response_error_description,
                color=self.config.error_color
            )
        
        messageLines = self.parkDataClient.messageLines
        dt = datetime.now(tz=timezone(self.parkDataClient.parkTz))
        timeStr = self._time_12h_no_leading_zero(dt)
        messageLines.append(f"*Data from queue-times.com • Local time: {timeStr} *")

        if self.parkDataClient.is_data_stale():
            messageLines.insert(1, f"{self.config.stale_data_message}\n")
        elif self.parkDataClient.allClosed:
            messageLines.insert(1, f"{self.config.all_closed_message}\n")

        # Optionally append weather data
        if self.config.include_weather:
            await self.weatherClient.fetch_weather(park.lat, park.lon)
            if self.weatherClient.last_fetch_successful:
                self.weatherClient.last_fetched_data
                messageLines.insert(0, f"{self.config.current_weather_header}\n   {self.weatherClient.current_temperature}{self.weatherClient.current_temperature_unit} {self.weatherClient.last_emoji}\n")
            else:
                messageLines.insert(0, f"{self.config.current_weather_header}\n   {self.config.weather_data_unavailable_message}\n")

        descriptionText = "\n".join(messageLines)
        await self.do_response(
            title=f"Data for {park.name}",
            description=descriptionText
        )

    ## Private helpers

    def _time_12h_no_leading_zero(self, dt: datetime) -> str:
        # Windows uses %#I, Unix uses %-I
        if sys.platform.startswith("win"):
            return dt.strftime("%#I:%M %p")
        else:
            return dt.strftime("%-I:%M %p")

    def _load_yaml_config(self) -> AppConfig:
        """
        Loads the YAML configuration file and returns an AppConfig object.
        Config is done via pydantic, which handles config validation on load and loading .yml into the AppConfig and other models.
        """
        try:
            with open(self.configPath, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
                if not config_data:
                    raise ValueError("Config data is empty or could not be loaded")
                # Convert weather_emojis keys to int, this is how we want to look them up, but YAML doesn't support numeric key types
                if "weather_config" in config_data and "weather_states" in config_data["weather_config"]:
                    config_data["weather_config"]["weather_states"] = {int(k): v for k, v in config_data["weather_config"]["weather_states"].items()}
            return AppConfig(**config_data)
        except FileNotFoundError:
            print("Config file not found.")
            raise
        except yaml.YAMLError as e:
            print("Error parsing YAML:", e)
            raise

async def demo(config_file: str):
    """
    Demonstrates the application's functionality with a specific configuration file.
    """
    app = App(config_path=config_file)
    app.startup()
    await app.do_waits("!EpcotWaits")

if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    asyncio.run(demo(config_path))