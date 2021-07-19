"""
The database connection client responsible for actual database communications.
"""

# Stdlib imports
import asyncio

# 3rd party imports
from sshtunnel import SSHTunnelForwarder
import aiomysql

# Local imports
from .models.guilds import Guilds
from .models.config import Config
from .models.users import Users
from .models.channels import Channels
from .models.roles import Roles
from .models.emojis import Emojis
from .models.rolereactions import RoleReactions


class DatabaseClient:
    def __init__(self, remote_host, remote_port, ssh_user, ssh_pass, ssh_key_file, user, password, db):
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.ssh_user = ssh_user
        self.ssh_pass = ssh_pass
        self.ssh_key_file = ssh_key_file
        self.user = user
        self.password = password
        self.db = db

        self.server = None
        self.pool = None

        self.loop = asyncio.get_event_loop()

        self.start_server()
        self.loop.run_until_complete(self.create_pool())

        self.guilds = Guilds(self.pool, self)
        self.config = Config(self.pool, self)
        self.users = Users(self.pool, self)
        self.channels = Channels(self.pool, self)
        self.roles = Roles(self.pool, self)
        self.emojis = Emojis(self.pool, self)
        self.rolereactions = RoleReactions(self.pool, self)

    def start_server(self):
        self.server = SSHTunnelForwarder(
            (self.remote_host, self.remote_port),
            ssh_username=self.ssh_user,
            ssh_password=self.ssh_pass,
            ssh_private_key=self.ssh_key_file,
            remote_bind_address=('127.0.0.1', 3306)
        )
        self.server.start()

    async def create_pool(self):
        self.pool = await aiomysql.create_pool(
            host='127.0.0.1',
            port=self.server.local_bind_port,
            user=self.user,
            password=self.password,
            db=self.db,
            loop=self.loop
        )

    async def stop(self):
        self.pool.terminate()
        await self.pool.wait_closed()
        self.server.stop()


