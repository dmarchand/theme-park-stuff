import discord
import requests
import sys
from datetime import datetime

EPIC_URL = "https://queue-times.com/en-US/parks/334/queue_times.json"
ISLANDS_URL = "https://queue-times.com/en-US/parks/64/queue_times.json"
STUDIOS_ORLANDO_URL = "https://queue-times.com/en-US/parks/65/queue_times.json"
USJ_URL = "https://queue-times.com/en-US/parks/284/queue_times.json"

COMMAND_URL_MAP = {
    "!EpicWaits": EPIC_URL,
    "!USFWaits": STUDIOS_ORLANDO_URL,
    "!IslandsWaits": ISLANDS_URL,
    #"!USJWaits": USJ_URL
    }

COMMAND_HELP_MAP = {
    "**Epic Universe :flag_us::** " : "!EpicWaits", 
    "**Universal Studios Orlando :flag_us::** " : "!USFWaits",
    "**Universal Studios, Islands of Advanture :flag_us::** " : "!IslandsWaits",
    #"**Universal Studios Japan :flag_jp::** " : "!USJWaits",
}

with open("config", "r", encoding="utf-8") as f:
    token = f.read().strip()

#print("Loaded token:", token)

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

async def do_waits(message, url):
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    lines = []
    lines.append("**Wait Times**")

    for land in data.get("lands", []):
        lines.append(f"**{land.get('name')}**")
        for ride in land.get("rides", []):
            wait = f"**{ride['wait_time']} min**" if ride["is_open"] else "Closed"
            lines.append(f"{ride['name']}: {wait}")
        lines.append("")

    lines.append(f"*Data from queue-times.com • Today at {time_12h_no_leading_zero(datetime.now())}*")


    description_text = "\n".join(lines)

    embed = discord.Embed(
        title="Theme Park Wait Times",
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
            await do_waits(message, COMMAND_URL_MAP[message.content])

client.run(token)