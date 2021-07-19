from aiomysql import DictCursor


class Emoji:
    def __init__(self, options):
        self.id = int(options.get('id'))
        self.name = options.get('name')
        self.image = options.get('image')
        self.guild = options.get('guild')


class Emojis:
    def __init__(self, pool, parent):
        self.pool = pool
        self.parent = parent

    async def update_all(self, guilds):
        emoji_list = []
        delete = ()
        emojis_curr = await self.get_all()
        for guild in guilds:
            if len(guild.emojis) > 0:
                for emoji in guild.emojis:
                    emoji_list.append((emoji.id, emoji.name, str(emoji.url), guild.id))

            for emoji in emojis_curr:
                if not (emoji.id, emoji.name, emoji.image, guild.id) in emoji_list:
                    delete = delete + (emoji.id,)

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if len(delete) > 0:
                    await cur.execute(f"DELETE FROM emojis WHERE id IN ({','.join(str(i) for i in delete)})")

                await cur.executemany(
                    "INSERT INTO emojis (id, name, image, guild)"
                    "values (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE "
                    "name=values(name),image=values(image),guild=values(guild)",
                    emoji_list
                )

    async def update(self, guild, emojis):
        emoji_list = []
        for emoji in emojis:
            print(emoji.url)
            emoji_list.append((emoji.id, emoji.name, str(emoji.url), guild.id))

        delete = ()
        emojis_curr = await self.get_all()
        for emoji in emojis_curr:
            if not (emoji.id, emoji.name, emoji.image, guild.id) in emoji_list:
                delete = delete + (emoji.id,)

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if len(delete) > 0:
                    await cur.execute(f"DELETE FROM emojis WHERE id IN ({','.join(str(i) for i in delete)})")

                await cur.executemany(
                    "INSERT INTO emojis (id, name, image, guild)"
                    "values (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE "
                    "name=values(name),image=values(image),guild=values(guild)",
                    emoji_list
                )

    async def get_all(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute("SELECT * FROM emojis")
                res = await cur.fetchall()
                return [Emoji(emoji) for emoji in res]
