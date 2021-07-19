"""
This file is entirely dedicated to listeners that will update specific pieces of data in the database
whenever events happen.
"""

from discord.ext import commands


class Listeners(commands.Cog, name="Listeners"):
    def __init__(self, bot):
        self.bot = bot

        print(f"{self.bot.OK} {self.bot.TIMELOG()} Loaded Listeners Cog.")

    def cog_unload(self):
        print(f"{self.bot.OK} {self.bot.TIMELOG()} Unloaded Listeners Cog.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.db_client.guilds.update(guild)
        await self.bot.db_client.config.save_default(guild)
        await self.bot.db_client.channels.update_all(self.bot)
        await self.bot.db_client.roles.update_byb_guild(guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.db_client.guilds.delete(guild)
        await self.bot.db_client.config.delete(guild)
        await self.bot.db_client.channels.delete_by_guild(guild)
        await self.bot.db_client.roles.delete_by_guild(guild)

    @commands.Cog.listener()
    async def on_guild_update(self, before, guild):
        await self.bot.db_client.guilds.update(guild)

    @commands.Cog.listener()
    async def on_member_join(self, user):
        await self.bot.db_client.users.update(user)

    @commands.Cog.listener()
    async def on_member_remove(self, user):
        await self.bot.db_client.users.delete(user)

    @commands.Cog.listener()
    async def on_member_update(self, before, user):
        await self.bot.db_client.users.update(user)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.bot.db_client.channels.update(channel)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.bot.db_client.channels.delete(channel)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, channel):
        await self.bot.db_client.channels.update(channel)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.bot.db_client.roles.update(role)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.bot.db_client.roles.delete(role)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, role):
        await self.bot.db_client.roles.update(role)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, emojis):
        await self.bot.db_client.emojis.update(guild, emojis)


def setup(bot):
    cog = Listeners(bot)
    bot.add_cog(cog)
