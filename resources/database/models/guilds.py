from aiomysql import DictCursor


class Guild:
    def __init__(self, options):
        self.id = int(options.get('id'))
        self.name = options.get('name')
        self.icon = options.get('icon')
        self.banner = options.get('banner')


class Guilds:
    def __init__(self, pool, parent):
        self.pool = pool
        self.parent = parent

    async def update_all(self, guilds):
        guild_list = []
        for guild in guilds:
            guild_list.append((guild.id, guild.name, str(guild.icon_url), str(guild.banner_url)))

        delete = ()
        guilds_curr = await self.get_all()
        for guild in guilds_curr:
            if not (guild.id, guild.name, guild.icon, guild.banner) in guild_list:
                delete = delete + (guild.id,)

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if len(delete) > 0:
                    await cur.execute(f"DELETE FROM guilds WHERE id IN ({','.join(str(i) for i in delete)})")
                await cur.executemany(
                    "INSERT INTO guilds (id, name, icon, banner)"
                    "values (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE "
                    "name=values(name),icon=values(icon),banner=values(banner)", guild_list
                )
                await conn.commit()

    async def update(self, guild):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO guilds (id, name, icon, banner)"
                    "values (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE "
                    "name=values(name),icon=values(icon),banner=values(banner)",
                    (guild.id, guild.name, str(guild.icon_url), str(guild.banner_url))
                )
                await conn.commit()

    async def delete(self, guild):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"DELETE FROM guilds WHERE id={guild.id}")
                await conn.commit()

    async def get(self, id):
        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(f"SELECT * FROM guilds WHERE id={id}")
                res = await cur.fetchone()

    async def get_all(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute("SELECT * FROM guilds")
                res = await cur.fetchall()
                return [Guild(guild) for guild in res]
