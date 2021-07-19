"""
The core file that is run when the program is started. This file is the overhead which manages all things throughout
the program's runtime.
"""

# Stdlib Modules
import asyncio
import datetime
import os

# 3rd party modules
import discord
from discord.ext import commands
from colorama import init

# Local modules
from resources.data import DataManager
from resources.utilities import EmbedUtil, Confirmation

init()


def get_prefix(bot, message):
    """
    Allows for a dynamic prefix to be used and changed on the fly.

    The 'prefix' command can update the bot's prefix actively since the bot will
    pull the prefix from this method.

    :parameters:
        bot: :class:`dpy:discord.ext.commands.Bot`
            The bot object to get the prefix for.

        message: :class:`dpy:discord.Message`
            The message that was resulting in the prefix being pulled.

    :returns:
        :class:`py:str`
            The string value stored in the 'prefix' attribute of the 'bot' parameter.
    """

    guild_id = message.guild.id
    return bot.configs[guild_id].prefix


# Allows the Discord client to see all Members, Roles, and so on, by default.
intents = discord.Intents.default()
intents.members = True
intents.presences = True

# Create the 'bot' instance, specifying the get_prefix function declared above as the prefix value.
bot = commands.Bot(
    command_prefix=get_prefix,
    description="Arizona Esports' Custom Discord Bot",
    case_insensitive=True,
    intents=intents
)

# Remove the included help command so that a custom help command can be implemented.
bot.remove_command('help')

"""
Initial Data Loading/Prep

Create a Datamanager instance, then call pertinent loading functions.

Then, create an instance of the Embed utility class for later use.
"""
bot.data_manager = DataManager(bot)
bot.data_manager.load_static()

# List of extension files to load
bot.exts = [
    'cogs.listeners',
    'cogs.rolereactions'
]

if bot.DEBUG:
    # Print to the console that the bot will run in Debug mode.
    print(f"{bot.WARN} {bot.TIMELOG()} Debug mode active.")
else:
    # Adds custom error logging if debug mode is not active.
    # NOTE: THIS WILL SIGNIFICANTLY REDUCE CLUTTER AND ERRORS ON THE CONSOLE
    # BUT NO TRACEBACK WILL BE PRINTED ON ERRORS.
    bot.exts.append('cogs.errors')

# Actually load the extension file list
for extension in bot.exts:
    bot.load_extension(extension)

print(f"{bot.OK} {bot.TIMELOG()} Connecting to Discord...")


@bot.event
async def on_ready():
    """
    Triggers once the bot has successfully established a connection to the Discord gateway.

    WARNING: This function cn be triggered multiple times, make sure anything in here can accept that.

    Sets up any bot configuration that requires a Discord connection to be mde first.
    """
    await bot.data_manager.update_all()
    await bot.data_manager.load_configs()

    # Print connection confirmation
    print(f"{bot.OK} {bot.TIMELOG()} Logged in as {bot.user} and connected to Discord! (ID: {bot.user.id})")

    # Set the "Playing" status of the bot.
    if bot.show_game_status:
        # Create an instance of a Game for the bot to be playing, set to whatever text is to be shown.
        game = discord.Game(name=bot.game_to_show.format(prefix=bot.prefix))

        # Set the status
        await bot.change_presence(activity=game)

    # Create the now online message to send to the log channel
    for i in bot.configs:
        if not bot.configs[i].log_channel_id == 0:
            embed = bot.configs[i].embed_util.get_embed(
                title=bot.configs[i].online_message.format(username=bot.user.name),
                ts=True
            )
            log_channel = bot.get_channel(bot.configs[i].log_channel_id)
            await log_channel.send(embed=embed)


@bot.check
async def command_permissions(ctx):
    """
    Global Permissions Manager

    This will be executed before any commands are run to make sure the user hs permission to use the command.

    Command permissions are imported from the database.rst, and can be configured via the web portal.

    :parameters:
        ctx :class:`dpy:discord.ext.commands.Context`
            The context object containing information about the command usage.
    """

    # Administrators are always allowed to use commands.
    if ctx.author.guild_permissions.administrator:
        return True
    else:
        # Finding permission schema for a command.
        # "!command" becomes "command", and "!category command" becomes "category-command"
        name = ctx.command.name
        if ctx.command.parent:
            command = ctx.command
            parent_exists = True
            while parent_exists:
                name = ctx.command.parent.name + '-' + name
                command = ctx.command.parent
                if not command.parent:
                    parent_exists = False

        # Checking command permissions
        if name in ctx.bot.permissions.keys():
            for permission in ctx.bot.permissions[name]:
                try:
                    role = ctx.guild.get_role(int(permission))
                    if role in ctx.author.roles:
                        return True
                except Exception as e:
                    print(e)
            return False
        else:
            return True


class Internal(commands.Cog, name="Internal"):
    """
    Commands related to internal bot management. The average user will never touch these.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="restart", help="Restarts the bot.")
    async def restart(self, ctx):
        """
        Restarting the Program

        Sends a confirmation menu to the user who is attempting to restart the program, then gracefully
        disconnects from Discord when given confirmation.

        Either a batch or shell script will then re-activate the bot, which will allow the bot to take
        on updates on the fly.

        :parameters:
            ctx :class:`dpy:discord.ext.commands.Context`
               The context object containing information about the command usage.
        """

        # Confirm that the user wants to restart
        confirm = await Confirmation(
            title="Restart?",
            msg="This will completely shut down the bot, and may potentially cause errors and downtime if the code "
                "has been modified and is untested."
        ).prompt(ctx)

        if confirm:
            for guild in self.bot.configs:
                settings = self.bot.configs[guild]
                if not settings.log_channel_id == 0:
                    embed = settings.embed_util.get_embed(
                        title=settings.restarting_message.format(username=self.bot.user.name),
                        ts=True
                    )
                    log = self.bot.get_channel(settings.log_channel_id)
                    await log.send(embed=embed)

            try:
                await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            except:
                pass

            for ext in self.bot.exts:
                self.bot.remove_cog(ext)

            await self.bot.close()
        else:

            embed = self.bot.configs[ctx.guild.id].embed_util.get_embed(title="Restart Cancelled")
            await ctx.send(embed=embed, delete_after=5)

    @commands.command(name="prefix", help="Changes the prefix for the bot in the guild the command is used in.")
    async def prefix(self, ctx, prefix: str):
        """
        Updates the prefix for the bot in the guild the command is used in.

        :parameters:
            ctx: :class:`dpy:discord.ext.commands.Context`
                The context object containing information about the command usage.

            prefix: :class:`py:str`
                The new prefix for the bot to use in the given guild.
        """

        settings = self.bot.configs[ctx.guild.id]
        old = settings.prefix

        self.bot.configs[ctx.guild.id].prefix = prefix

        await self.bot.db_client.config.update_prefix(ctx.guild.id, prefix)

        embed = settings.embed_util.get_embed(
            title="Prefix Updated",
            desc=f"New Prefix: `{prefix}`",
            fields=[
                {"name": "Old", "value": f"`{old}command`", "inline": True},
                {"name": "New", "value": f"`{prefix}command`", "inline": True}
            ]
        )
        await ctx.send(embed=embed)
        if not settings.log_channel_id == 0:
            log = self.bot.get_channel(settings.log_channel_id)
            await log.send(embed=embed)


# Register the internal cog with the bot
bot.add_cog(Internal(bot))

if __name__ == "__main__":
    # Run the bot, or print and error if the token is invalid
    try:
        bot.run(bot.TOKEN, bot=True, reconnect=True)
    except discord.LoginFailure:
        print(f"{bot.ERR} {bot.TIMELOG()} Invalid TOKEN variable: {bot.TOKEN}")
        input("Press enter to continue...")

