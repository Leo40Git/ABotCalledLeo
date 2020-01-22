import sys
import traceback

import discord
from discord.ext import commands

import settings
from embedhelp import EmbedHelpCommand


class LeoBot(commands.AutoShardedBot):
    async def on_ready(self):
        print(f'Logged on as {self.user}! (id: {self.user.id})')
        print('Ready for operation!')

    async def on_command_error(self, context, exception):
        color = discord.Color.dark_red()
        title = ':x: **_ERROR!!!_**'
        description = str(exception)
        if isinstance(exception, commands.CommandOnCooldown):
            color = discord.Color.teal()
            title = ':snowflake: **_CHILL!!!_**'
        elif isinstance(exception, commands.CheckFailure):
            title = ':no_entry_sign: **_NO WAY!!!_**'
        elif not isinstance(exception, commands.CommandNotFound):
            print('Exception in command "{}":'.format(context.command.qualified_name), file=sys.stderr)
            traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
        embed = discord.Embed(color=color,
                              title=title,
                              description=description)
        await context.send(embed=embed)


async def get_prefix(bot: commands.Bot, message: discord.Message):
    extras = settings.prefixes
    if settings.prefixes_dm is not None and isinstance(message.channel, (discord.DMChannel, discord.GroupChannel)):
        extras = settings.prefixes_dm
    if settings.mention_prefix:
        return commands.when_mentioned_or(*extras)(bot, message)
    else:
        return extras


if __name__ == '__main__':
    _bot = LeoBot(command_prefix=get_prefix, help_command=EmbedHelpCommand())
    try:
        _bot.load_extension('cogs.system')
    except commands.ExtensionError as e:
        print('Failed to load essential extension "cogs.system".', file=sys.stderr)
        traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
        exit(-1)
    for ext in settings.startup_extensions:
        try:
            _bot.load_extension(ext)
        except commands.ExtensionError as e:
            print(f'Failed to load extension "{ext}".', file=sys.stderr)
            traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
    try:
        f = open('.token')
    except OSError as e:
        print('Failed to open .token file. Please make sure it exists.', file=sys.stderr)
        traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
        exit(-1)
    else:
        _token = f.readline()
        f.close()
        _bot.run(_token)
