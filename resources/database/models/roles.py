from aiomysql import DictCursor
from discord import Color

class Role:
    def __init__(self, options):
        self.id = int(options.get('id'))
        self.name = options.get('name')
        self.guild = int(options.get('guild'))
        self.color = Color(int(options.get('color')))


class Roles:
    def __init__(self, pool, parent):
        self.pool = pool
        self.parent = parent

    async def update_all(self, guilds):
        role_list = []
        for g in guilds:
            for r in g.roles:
                role_list.append((r.id, r.name, r.guild.id, r.color.value))

        delete = ()
        roles_curr = await self.get_all()
        for r in roles_curr:
            if not (r.id, r.name, r.guild, r.color) in role_list:
                delete = delete + (r.id,)

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if len(delete) > 0:
                    await cur.execute(f"DELETE FROM roles WHERE id IN ({','.join(str(i) for i in delete)})")
                await cur.executemany(
                    "INSERT INTO roles (id, name, guild, color)"
                    "values (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE "
                    "name=values(name),guild=values(guild),color=values(color)", role_list
                )
                await conn.commit()

    async def get_all(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute("SELECT * FROM roles")
                res = await cur.fetchall()
                return [Role(r) for r in res]

    async def update(self, role):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO roles (id, name, guild, color)"
                    "values (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE "
                    "guild=values(guild),name=values(name),color=values(color)",
                    (role.id, role.name, role.guild.id, role.color.value)
                )
                await conn.commit()

    async def delete(self, role):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"DELETE FROM roles WHERE id={role.id}")
                await conn.commit()

    async def update_by_guild(self, guild):
        roles = []
        for r in guild.roles:
            roles.append((r.id, r.name, r.guild.id, r.color.value))

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(
                    "INSERT INTO roles (id, name, guild, color)"
                    "values (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE "
                    "name=values(name),guild=values(guild),color=values(color)", roles
                )
                await conn.commit()

    async def delete_by_guild(self, guild):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(f"DELETE FROM roles WHERE guild={guild.id}")
                await conn.commit()
