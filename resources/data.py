"""
The file which manages all data streams. From connection to the database.rst to modifying console output,
this file handles it all.
"""

# Stdlib imports
import datetime
import os

# 3rd part imports
from colorama import Fore

# Local imports
from resources.database import DatabaseClient
from resources.utilities import EmbedUtil


class DataManager:
    """
    The data management class at the core of everything the bot does.
    """
    def __init__(self, bot):
        self.bot = bot

        # Establishing database connection
        remote_host = os.getenv('az_esports_db_host')
        remote_port = int(os.getenv('az_esports_db_port'))
        ssh_user = os.getenv('az_esports_ssh_user')
        ssh_pass = os.getenv('az_esports_ssh_pass')
        ssh_key_file = os.getenv('az_esports_ssh_file')
        user = os.getenv('az_esports_db_user')
        password = os.getenv('az_esports_db_pass')
        name = os.getenv('az_esports_db_name')
        self.bot.db_client = DatabaseClient(
            remote_host=remote_host,
            remote_port=remote_port,
            ssh_user=ssh_user,
            ssh_pass=ssh_pass,
            ssh_key_file=ssh_key_file,
            user=user,
            password=password,
            db=name
        )

    def load_static(self):
        """
        Load the static hard-coded configurations for the bot.
        """
        self.bot.TOKEN = os.getenv('AZEsportsBotToken')
        self.bot.DEBUG = True
        self.bot.embed_ts = lambda: datetime.datetime.now(datetime.timezone.utc)

        # Logging Variables
        self.bot.OK = f"{Fore.GREEN}[OK]{Fore.RESET}  "
        self.bot.WARN = f"{Fore.YELLOW}[WARN]{Fore.RESET}"
        self.bot.ERR = f"{Fore.RED}[ERR]{Fore.RESET} "
        self.bot.TIMELOG = lambda: datetime.datetime.now().strftime('[%m/%d/%Y | %I:%M:%S %p]')

    async def update_all(self):
        """
        Updates all visible data to the bot, like guilds, channels, etc, in the database.

        This should only be called as the bot is coming online, in case any guilds or channels were updated while
        the bot was offline.
        """
        await self.bot.db_client.guilds.update_all(self.bot.guilds)
        await self.bot.db_client.config.update_all()
        await self.bot.db_client.users.update_all(self.bot.users)
        await self.bot.db_client.channels.update_all(self.bot)
        await self.bot.db_client.roles.update_all(self.bot.guilds)
        await self.bot.db_client.emojis.update_all(self.bot.guilds)

    async def load_configs(self):
        """
        Load the dynamic configurations for the bot.
        """
        # Loading configs from database
        configs = await self.bot.db_client.config.load_all()

        self.bot.configs = {}
        for key in configs:
            if not key == 0:
                configs[key].embed_util = EmbedUtil(self.bot, configs[key])
                self.bot.configs[key] = configs[key]

        self.bot.show_game_status = False

    async def load_data(self):
        """
        Loads the data from the database into the bot's memory.
        """
        pass
