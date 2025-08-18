import discord
import requests
import sys
from pytz import timezone
from datetime import datetime
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

EPIC_URL = "https://queue-times.com/en-US/parks/334/queue_times.json"
ISLANDS_URL = "https://queue-times.com/en-US/parks/64/queue_times.json"
STUDIOS_ORLANDO_URL = "https://queue-times.com/en-US/parks/65/queue_times.json"
USJ_URL = "https://queue-times.com/en-US/parks/284/queue_times.json"
USH_URL = "https://queue-times.com/en-US/parks/66/queue_times.json"
TDL_URL = "https://queue-times.com/en-US/parks/274/queue_times.json"
TDS_URL = "https://queue-times.com/en-US/parks/275/queue_times.json"
EPCOT_URL = "https://queue-times.com/en-US/parks/5/queue_times.json"
AK_URL = "https://queue-times.com/en-US/parks/8/queue_times.json"
MK_URL = "https://queue-times.com/en-US/parks/6/queue_times.json"
HOLLYWOOD_STUDIOS_URL = "https://queue-times.com/en-US/parks/7/queue_times.json"

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


COMMAND_URL_MAP = {
    "!EpicWaits": EPIC_URL,
    "!USFWaits": STUDIOS_ORLANDO_URL,
    "!IslandsWaits": ISLANDS_URL,
    "!USHWaits": USH_URL,
    "!TDLWaits": TDL_URL,
    "!TDSWaits" : TDS_URL,
    "!EpcotWaits" : EPCOT_URL,
    "!AKWaits" : AK_URL,
    "!MKWaits" : MK_URL,
    "!HollywoodWaits": HOLLYWOOD_STUDIOS_URL,
    "!USJWaits": USJ_URL
    }

COMMAND_HELP_MAP = {
    "**Epic Universe :flag_us::** " : "!EpicWaits", 
    "**Universal Studios Orlando :flag_us::** " : "!USFWaits",
    "**Universal Studios, Islands of Advanture :flag_us::** " : "!IslandsWaits",
    "**Universal Studios Hollywood :flag_us::** " : "!USHWaits",
    "**Epcot :flag_us::** " : "!EpcotWaits",
    "**Animal Kingdom :flag_us::** " : "!AKWaits",
    "**Disney's Magic Kingdom :flag_us::** " : "!MKWaits",
    "**Disney Hollywood Studios :flag_us::** " : "!HollywoodWaits",
    "**Tokyo Disneyland :flag_jp::** " : "!TDLWaits",
    "**Tokyo Disney Sea :flag_jp::** " : "!TDSWaits",
    "**Universal Studios Japan :flag_jp::** " : "!USJWaits",
}

COMMAND_LAT_LONG_MAP = {
    "!EpicWaits": "28.4407,-81.4479",
    "!USFWaits": "28.4724,-81.4690",
    "!IslandsWaits": "28.4717,-81.4702",
    "!USHWaits": "34.1371,-118.3533",
    "!TDLWaits": "35.6329,139.8804",
    "!TDSWaits" : "35.6267,139.8851",
    "!EpcotWaits" : "28.3765,-81.5494",
    "!AKWaits" : "28.3765,-81.5494",
    "!MKWaits" : "28.3765,-81.5494",
    "!HollywoodWaits": "28.3765,-81.5494",
    "!USJWaits": "34.66577,135.4323"
}

WEATHER_EMOJIS = {
    0: "☀️",   # Clear sky
    1: "🌤️",  # Mainly clear
    2: "⛅",   # Partly cloudy
    3: "☁️",   # Overcast
    45: "🌫️",  # Fog
    48: "🌁",  # Depositing rime fog
    51: "🌦️",  # Light drizzle
    53: "🌧️",  # Moderate drizzle
    55: "🌧️",  # Dense drizzle
    56: "🌨️",  # Light freezing drizzle
    57: "🌨️",  # Dense freezing drizzle
    61: "🌦️",  # Slight rain
    63: "🌧️",  # Moderate rain
    65: "🌧️",  # Heavy rain
    66: "🌨️",  # Light freezing rain
    67: "🌨️",  # Heavy freezing rain
    71: "🌨️",  # Slight snowfall
    73: "❄️",   # Moderate snowfall
    75: "❄️",   # Heavy snowfall
    77: "🌨️",  # Snow grains
    80: "🌦️",  # Slight rain showers
    81: "🌧️",  # Moderate rain showers
    82: "⛈️",  # Violent rain showers
    85: "🌨️",  # Slight snow showers
    86: "❄️",   # Heavy snow showers
    95: "⛈️",  # Thunderstorm slight/moderate
    96: "⛈️",  # Thunderstorm with slight hail
    99: "🌩️",  # Thunderstorm with heavy hail
}


with open("config", "r", encoding="utf-8") as f:
    token = f.read().strip()

#print("Loaded token:", token)

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def time_12h_no_leading_zero(dt: datetime) -> str:
    # Windows uses %#I, Unix uses %-I
    if sys.platform.startswith("win"):
        return dt.strftime("%#I:%M %p")
    else:
        return dt.strftime("%-I:%M %p")

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

async def do_help(message):
    lines = []
    lines.append("**Park Wait Commands Supported**\n")
    for entry in COMMAND_HELP_MAP:
        lines.append(f"""{entry} {COMMAND_HELP_MAP[entry]}""")

    description_text = "\n".join(lines)

    embed = discord.Embed(
        title="Theme Park Enjoyment Bot Help",
        description=description_text,
        color=0x3498db  # pretty blue
    )

    await message.channel.send(embed=embed)    

async def do_waits(message, url, command):
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    parkInfoUrl = url.replace("/queue_times", '')
    parkResp = requests.get(parkInfoUrl)
    parkData = parkResp.json()
    parkTz = parkData['timezone']

    latestUpdate = 22221755542666
    allClosed = True

    lines = []
    if(len(data.get("lands")) == 0):
        print("No lands...")
        for ride in data.get("rides", []):
            if ("Single Rider" in ride['name']):
                continue
            wait = f"**{ride['wait_time']} min**" if ride["is_open"] else "Closed"
            lines.append(f"{ride['name']}: {wait}")

            if (ride["is_open"]):
                allClosed = False

            if "last_updated" in ride:
                dt = datetime.fromisoformat(ride["last_updated"].replace("Z", "+00:00"))
                epoch = int(dt.timestamp())
                if epoch < latestUpdate:
                    latestUpdate = epoch
        lines.append("")
    else: 
        for land in data.get("lands", []):
            lines.append(f"**{land.get('name')}**")
            for ride in land.get("rides", []):
                if ("Single Rider" in ride['name']):
                    continue
                wait = f"**{ride['wait_time']} min**" if ride["is_open"] else "Closed"
                lines.append(f"{ride['name']}: {wait}")

                if (ride["is_open"]):
                    allClosed = False

                if "last_updated" in ride:
                    dt = datetime.fromisoformat(ride["last_updated"].replace("Z", "+00:00"))
                    epoch = int(dt.timestamp())
                    if epoch < latestUpdate:
                        latestUpdate = epoch
            lines.append("")



    park_title = ""
    for entry in COMMAND_HELP_MAP:
        if(COMMAND_HELP_MAP[entry] == command):
            park_title = entry.replace('*','')[:-2]

    params = {
        "latitude": COMMAND_LAT_LONG_MAP.get(command).split(",")[0],
        "longitude": COMMAND_LAT_LONG_MAP.get(command).split(",")[1],
        "current": ["temperature_2m", "relative_humidity_2m", "precipitation", "rain", "showers", "weather_code", "wind_speed_10m"],
        "wind_speed_unit": "ms",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
    }

    responses = openmeteo.weather_api(WEATHER_URL, params=params)

    response = responses[0]
    print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_relative_humidity_2m = current.Variables(1).Value()
    current_precipitation = current.Variables(2).Value()
    current_rain = current.Variables(3).Value()
    current_showers = current.Variables(4).Value()
    current_weather_code = current.Variables(5).Value()
    current_wind_speed_10m = current.Variables(6).Value()

    #print(f"\nCurrent time: {current.Time()}")
    #print(f"Current temperature_2m: {current_temperature_2m}")
    #print(f"Current relative_humidity_2m: {current_relative_humidity_2m}")
    #print(f"Current precipitation: {current_precipitation}")
    #print(f"Current rain: {current_rain}")
    #print(f"Current showers: {current_showers}")
    #print(f"Current weather_code: {current_weather_code}")
    #print(f"Current wind_speed_10m: {current_wind_speed_10m}")

    emoji = WEATHER_EMOJIS.get(current_weather_code, "❓")

    ctz = timezone(parkTz)
    dt = datetime.now(tz=ctz)
    timeStr = dt.strftime("%I:%M %p")

    utcTz = timezone('UTC')
    utcdt = datetime.now(utcTz)

    nowEpoch = int(utcdt.timestamp())
    is_stale = (latestUpdate == 0) or (nowEpoch - latestUpdate >= 3600)
    print(f"Latest Update Epoch {latestUpdate}, current epoch in UTC: {nowEpoch}")

    lines.append(f"*Data from queue-times.com • Local time: {timeStr} *")

    lines.insert(0, f"**Current weather**\n   {round(current_temperature_2m, 1)}F {emoji}\n")

    if is_stale:
        lines.insert(1, ":no_entry_sign: Rides last updated over an hour ago, this park might be **CLOSED** :no_entry_sign: \n")
    elif allClosed:
        lines.insert(1, ":no_entry_sign: All rides are closed, this park might be **CLOSED** :no_entry_sign: \n")

    description_text = "\n".join(lines)



    embed = discord.Embed(
        title=f"""Data for {park_title}""",
        description=description_text,
        color=0x3498db  # pretty blue
    )

    await message.channel.send(embed=embed)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('!WaitsHelp'):
        await do_help(message)
    else:
        if(message.content in COMMAND_URL_MAP):
            await do_waits(message, COMMAND_URL_MAP[message.content], message.content)

client.run(token)