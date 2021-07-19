from aiomysql import DictCursor


class Channel:
    def __init__(self, options):
        self.id = int(options.get('id'))
        self.guild = int(options.get('guild'))
        self.name = options.get('name')
        self.type = options.get('type')


class Channels:
    def __init__(self, pool, parent):
        self.pool = pool
        self.parent = parent

    async def update_all(self, bot):
        channel_list = []
        for ch in bot.get_all_channels():
            channel_list.append((ch.id, ch.guild.id, ch.name, str(ch.type)))

        delete = ()
        channels_curr = await self.get_all()
        for ch in channels_curr:
            if not (ch.id, ch.guild, ch.name, ch.type) in channel_list:
                delete = delete + (ch.id,)

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if len(delete) > 0:
                    await cur.execute(f"DELETE FROM channels WHERE id IN ({','.join(str(i) for i in delete)})")
                await cur.executemany(
                    "INSERT INTO channels (id, guild, name, type)"
                    "values (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE "
                    "guild=values(guild),name=values(name),type=values(type)", channel_list
                )
                await conn.commit()

    async def get_all(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute("SELECT * FROM channels")
                res = await cur.fetchall()
                return [Channel(r) for r in res]

    async def update(self, channel):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO channels (id, guild, name, type)"
                    "values (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE "
                    "guild=values(guild),name=values(name),type=values(type)",
                    (channel.id, channel.guild.id, channel.name, str(channel.type))
                )
                await conn.commit()

    async def delete(self, channel):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"DELETE FROM channels WHERE id={channel.id}")
                await conn.commit()

    async def delete_by_guild(self, guild):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"DELETE FROM channels WHERE guild={guild.id}")
                await conn.commit()
