import discord

from config import DiscordClientConfig


class DiscordClient:
    """
    DiscordClient is responsible for managing the Discord bot client and sending messages.
    """
    def __init__(self, discord_config: DiscordClientConfig):
        self.config = discord_config
        self.token: str = ""
        self.client: discord.Client = None
        self.embedColor: int = self.config.get_embed_color()

    def configure(self) -> bool:
        """
        Configures the Discord client by loading the token and setting up intents.
        """
        if not self.load_token():
            print("Failed to load the discord token, bailing out...")
            return False
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        return True

    def load_token(self) -> bool:
        """
        Loads the Discord bot token from a file.
        """
        with open(self.config.token_filename, "r", encoding="utf-8") as f:
            token = f.read().strip()
        if not token:
            raise ValueError("Discord token failed to load")
            return False
        #if self.debugEnabled:
        #    print("Loaded token:", token)
        self.token = token
        return True
    
    def run(self):
        """
        Starts the Discord client.
        """
        if not self.client or not self.token:
            print("Discord client is not properly configured, bailing out...")
            return
        print("Starting Discord client...")
        self.client.run(self.token)
    
    async def send_discord_embed(self, title: str, description: str, message: discord.Message, color: int = None):
        """
        Sends a rich embed message to a Discord channel.
        """
        if color is None:
            color = self.embedColor
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        await message.channel.send(embed=embed)