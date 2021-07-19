from aiomysql import DictCursor
import pickle


class User:
    def __init__(self, options):
        self.id = int(options.get('id'))
        self.name = pickle.loads(options.get('name'))
        self.discriminator = int(options.get('discriminator'))
        self.avatar_url = options.get('avatar')


class Users:
    def __init__(self, pool, parent):
        self.pool = pool
        self.parent = parent

    async def update_all(self, users):
        user_list = []
        for user in users:
            user_list.append((user.id, pickle.dumps(user.name), user.discriminator, str(user.avatar_url)))

        delete = ()
        users_curr = await self.get_all()
        for user in users_curr:
            if not (user.id, user.name, user.discriminator, str(user.avatar_url)) in user_list:
                delete = delete + (user.id,)

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if len(delete) > 0:
                    await cur.execute(f"DELETE FROM users WHERE id IN ({','.join(str(i) for i in delete)})")
                await cur.executemany(
                    "INSERT INTO users (id, name, discriminator, avatar)"
                    "values (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE "
                    "name=values(name),discriminator=values(discriminator),avatar=values(avatar)", user_list
                )
                await conn.commit()

    async def get_all(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute("SELECT * FROM users")
                res = await cur.fetchall()
                return [User(r) for r in res]

    async def update(self, user):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (id, name, discriminator, avatar)"
                    "values (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE "
                    "name=values(name),discriminator=values(discriminator),avatar=values(avatar)",
                    (user.id, pickle.dumps(user.name), user.discriminator, str(user.avatar_url))
                )
                await conn.commit()

    async def delete(self, user):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"DELETE FROM users WHERE id={user.id}")
                await conn.commit()
