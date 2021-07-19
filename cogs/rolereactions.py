"""
This file handles managing all role reaction messages.
"""

import asyncio
import pickle

from discord.ext import commands, tasks


class RoleReactions(commands.Cog, name="Role Reactions"):
    def __init__(self, bot):
        self.bot = bot
        self.role_reaction_updater.start()
        print(f"{self.bot.OK} {self.bot.TIMELOG()} Loaded Role Reactions Cog.")

    def cog_unload(self):
        self.role_reaction_updater.cancel()
        print(f"{self.bot.OK} {self.bot.TIMELOG()} Unloaded Role Reactions Cog.")

    @tasks.loop(seconds=30.0)
    async def role_reaction_updater(self):
        self.bot.role_reactions = await self.bot.db_client.rolereactions.get_all()

        for rr in self.bot.role_reactions:
            if rr.start_time and not rr.message_id:
                channel = self.bot.get_channel(rr.channel_id)

                embed = self.bot.configs[channel.guild.id].embed_util.get_embed(
                    title=rr.title
                )

                emojis = []
                entries = []
                for r in rr.reactions:
                    if bool(r.iscustom):
                        emoji = self.bot.get_emoji(int(r.emoji))
                    else:
                        emoji = r.emoji

                    role = channel.guild.get_role(int(r.role))
                    if emoji and role:
                        emojis.append(emoji)
                        entries.append(f"{str(emoji)} - {role.mention}")

                if rr.description not in [None, '']:
                    embed.description = rr.description + "\n\n" + "\n".join(entries)

                msg = await channel.send(embed=embed)

                for e in emojis:
                    await msg.add_reaction(e)

                await self.bot.db_client.rolereactions.started(rr.id, msg.id)
            elif not rr.start_time and rr.message_id:
                ch = self.bot.get_channel(rr.channel_id)
                msg = await ch.fetch_message(rr.message_id)
                if msg:
                    await msg.delete()

                await self.bot.db_client.rolereactions.stopped(rr.id)

    @role_reaction_updater.before_loop
    async def before_updater_start(self):
        await self.bot.wait_until_ready()
        while not hasattr(self.bot, 'configs'):
            await asyncio.sleep(3)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if hasattr(self.bot, 'role_reactions'):
            for i in self.bot.role_reactions:
                if payload.message_id == i.message_id:
                    if payload.emoji.is_custom_emoji():
                        for r in i.reactions:
                            if r.iscustom and int(r.emoji) == payload.emoji.id:
                                role = self.bot.get_guild(payload.guild_id).get_role(int(r.role))
                                if role:
                                    await payload.member.add_roles(role)
                    else:
                        for r in i.reactions:
                            if not r.iscustom and r.emoji == payload.emoji.name:
                                role = self.bot.get_guild(payload.guild_id).get_role(int(r.role))
                                if role:
                                    await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if hasattr(self.bot, 'role_reactions'):
            for i in self.bot.role_reactions:
                if payload.message_id == i.message_id:
                    if payload.emoji.is_custom_emoji():
                        for r in i.reactions:
                            if r.iscustom and int(r.emoji) == payload.emoji.id:
                                guild = self.bot.get_guild(payload.guild_id)
                                role = guild.get_role(int(r.role))
                                if role:
                                    member = guild.get_member(payload.user_id)
                                    await member.remove_roles(role)
                    else:
                        for r in i.reactions:
                            if not r.iscustom and r.emoji == payload.emoji.name:
                                guild = self.bot.get_guild(payload.guild_id)
                                role = guild.get_role(int(r.role))
                                if role:
                                    member = guild.get_member(payload.user_id)
                                    await member.remove_roles(role)


def setup(bot):
    cog = RoleReactions(bot)
    bot.add_cog(cog)
