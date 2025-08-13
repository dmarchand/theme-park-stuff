import discord
import requests
import sys
from datetime import datetime

EPIC_URL = "https://queue-times.com/en-US/parks/334/queue_times.json"

with open("config", "r", encoding="utf-8") as f:
    token = f.read().strip()

#print("Loaded token:", token)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def fetch_html(url: str, *, timeout: int = 20) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def time_12h_no_leading_zero(dt: datetime) -> str:
    # Windows uses %#I, Unix uses %-I
    if sys.platform.startswith("win"):
        return dt.strftime("%#I:%M %p")
    else:
        return dt.strftime("%-I:%M %p")

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

async def do_epic_waits(message):
    resp = requests.get(EPIC_URL)
    resp.raise_for_status()
    data = resp.json()

    lines = []
    lines.append("**Epic Universe Wait Times**")
    lines.append("Current wait times for Epic Universe. Times are updated every 5 minutes.\n")

    for land in data.get("lands", []):
        lines.append(f"**{land.get('name')}**")
        for ride in land.get("rides", []):
            wait = f"**{ride['wait_time']} min**" if ride["is_open"] else "Closed"
            lines.append(f"{ride['name']}: {wait}")
        lines.append("")

    lines.append(f"*Data from queue-times.com • Today at {time_12h_no_leading_zero(datetime.now())}*")


    description_text = "\n".join(lines)

    embed = discord.Embed(
        title="Epic Universe Wait Times",
        description=description_text,
        color=0x3498db  # pretty blue
    )

    await message.channel.send(embed=embed)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('!EpicWaits'):
        await do_epic_waits(message)    

client.run(token)