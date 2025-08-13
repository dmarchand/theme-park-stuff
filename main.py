import discord
import requests
import sys
from pytz import timezone
from datetime import datetime

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

tz = timezone('EST')

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

async def do_waits(message, url, command):
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    print (data)
    lines = []
    if(len(data.get("lands")) == 0):
        print("No lands...")
        for ride in data.get("rides", []):
            wait = f"**{ride['wait_time']} min**" if ride["is_open"] else "Closed"
            lines.append(f"{ride['name']}: {wait}")
        lines.append("")
    else: 
        for land in data.get("lands", []):
            lines.append(f"**{land.get('name')}**")
            for ride in land.get("rides", []):
                wait = f"**{ride['wait_time']} min**" if ride["is_open"] else "Closed"
                lines.append(f"{ride['name']}: {wait}")
            lines.append("")

    lines.append(f"*Data from queue-times.com • Today at {time_12h_no_leading_zero(datetime.now(tz))}*")

    park_title = ""
    for entry in COMMAND_HELP_MAP:
        if(COMMAND_HELP_MAP[entry] == command):
            park_title = entry.replace('*','')[:-2]
    description_text = "\n".join(lines)

    embed = discord.Embed(
        title=f"""Wait Times for {park_title}""",
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