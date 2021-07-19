import json

from aiomysql import DictCursor


class Settings:
    def __init__(self, options):
        embed_util = None

        self.config = json.loads(options.get('config'))

        self.prefix = self.config['prefix']
        self.log_channel_id = self.config['log_channel_id']
        self.online_message = self.config['online_message']
        self.restarting_message = self.config['restarting_message']

        self.embed = self.config['embed']


class Config:
    def __init__(self, pool, parent):
        self.pool = pool
        self.parent = parent

    async def load_all(self):
        configs = {}
        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute("SELECT * FROM config")
                res = await cur.fetchall()
                for i in res:
                    configs[i.get('guild')] = Settings(i)
        return configs

    async def load(self, id):
        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(f"SELECT * FROM config WHERE guild={id}")
                res = await cur.fetchone()
                return json.loads(res['config'])

    async def save_default(self, guild):
        default = await self.load(0)
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO config (guild, config) "
                    "values (%s, %s) ON DUPLICATE KEY UPDATE "
                    "config=values(config)",
                    (guild.id, json.dumps(default))
                )
                await conn.commit()

    async def update_all(self):
        guilds = await self.parent.guilds.get_all()
        default = await self.load(0)
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                for id in [g.id for g in guilds]:
                    await cur.execute(
                        "INSERT IGNORE INTO config (guild, config) "
                        "values (%s, %s)",
                        (id, json.dumps(default))
                    )
                await conn.commit()

    async def update_prefix(self, id, prefix):
        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(f"SELECT * FROM config WHERE guild={id}")
                res = await cur.fetchone()
                config = json.loads(res['config'])
                config['prefix'] = prefix
                await cur.execute(f"UPDATE config SET config='{json.dumps(config)}' WHERE guild={id}")
                await conn.commit()

    async def delete(self, guild):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"DELETE FROM config WHERE guild={guild.id}")
                await conn.commit()
