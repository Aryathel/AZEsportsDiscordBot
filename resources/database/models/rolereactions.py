import pickle

from aiomysql import DictCursor


class Reaction:
    def __init__(self, options):
        self.id = options.get('id')
        self.role_reaction = options.get('role_reaction')
        self.iscustom = options.get('iscustom')
        self.emoji = pickle.loads(options.get('emoji'))
        print(self.emoji)
        self.role = options.get('role')


class RoleReaction:
    def __init__(self, options, reactions):
        self.id = options.get('id')
        self.title = options.get('title')
        self.description = options.get('description')
        self.message_id = options.get('message_id')
        self.channel_id = options.get('channel_id')
        self.start_time = options.get('start_time')
        self.reactions = reactions


class RoleReactions:
    def __init__(self, pool, parent):
        self.pool = pool
        self.parent = parent

    async def get_all(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute("SELECT * FROM role_reactions")
                res = await cur.fetchall()
                rrs = []
                for rr in res:
                    await cur.execute(f"SELECT * FROM reaction WHERE role_reaction=\"{rr['id']}\"")
                    reactions = await cur.fetchall()
                    reactions = [Reaction(r) for r in reactions]
                    rrs.append(RoleReaction(rr, reactions))

                return rrs

    async def started(self, rr, msg):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE role_reactions SET "
                    f"message_id={msg} WHERE id=\"{rr}\";"
                )

    async def stopped(self, rr):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE role_reactions SET "
                    f"message_id=null WHERE id=\"{rr}\";",
                )
