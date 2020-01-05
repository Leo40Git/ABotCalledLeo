import itertools
import sys
import traceback

import discord
from discord.ext import commands

import settings


class EmbedHelpCommand(commands.MinimalHelpCommand):
    def __init__(self):
        super(EmbedHelpCommand, self).__init__(command_attrs=dict(help='Provides help on the bot\'s various commands.'
                                                                       '\n'
                                                                       '\n`[command]` - Cog/group/command to provide '
                                                                       'help for. If not specified, shows a list of '
                                                                       'all the bot\'s commands.'))

    async def send_bot_help(self, mapping):
        appinfo = await self.context.bot.application_info()
        embed = discord.Embed(color=discord.Color.dark_blue(),
                              title=f'Sending aid for **{appinfo.name}**!',
                              description=bot.description)
        if appinfo.icon is not None:
            embed.set_thumbnail(url=f'https://cdn.discordapp.com/app-icons/{appinfo.id}/{appinfo.icon}.png')

        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            if len(filtered) == 0:
                continue
            if cog is None:
                name = '**Uncategorized:**'
            else:
                name = f'**{cog.qualified_name}:**'
            value_first = True
            value_n = ''
            value_b = ''
            for command in filtered:
                if value_first:
                    value_first = False
                else:
                    value_n += '\n'
                    value_b += '\n'
                value_n += command.name
                value_b += '(no description)' if command.short_doc == '' else command.short_doc
            embed.add_field(name=name, value=value_n)
            embed.add_field(name='**Briefs:**', value=value_b)
            embed.add_field(name='\u200B', value='\u200B')  # new 'line'
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(color=discord.Color.dark_blue(),
                              title=f'Sending aid for cog **{cog.qualified_name}**!',
                              description='(no description)' if cog.description is None else cog.description)
        commands = await self.filter_commands(cog.get_commands(), sort=True)
        if len(commands) > 0:
            mapping = itertools.groupby(commands, )
            value_first = True
            value_n = ''
            value_b = ''
            for command in commands:
                if value_first:
                    value_first = False
                else:
                    value_n += '\n'
                    value_b += '\n'
                value_n += command.name
                value_b += '(no description)' if command.short_doc == '' else command.short_doc
            embed.add_field(name='**Commands:**', value=value_n)
            embed.add_field(name='**Briefs:**', value=value_b)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(color=discord.Color.dark_blue(),
                              title=f'Sending aid for group **{group.name}**!',
                              description='(no description)' if group.help == '' else group.help)
        old_show_hidden = self.show_hidden
        self.show_hidden = group.hidden
        commands = await self.filter_commands(group.commands, sort=True)
        self.show_hidden = old_show_hidden
        if len(commands) > 0:
            value_first = True
            value_n = ''
            value_b = ''
            for command in commands:
                if value_first:
                    value_first = False
                else:
                    value_n += '\n'
                    value_b += '\n'
                value_n += command.name
                value_b += '(no description)' if command.short_doc == '' else command.short_doc
            embed.add_field(name='**Commands:**', value=value_n)
            embed.add_field(name='**Briefs:**', value=value_b)
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(color=discord.Color.dark_blue(),
                              title=f'Sending aid for group **{command.name}**!')
        usage = f'`{self.context.prefix}{command.qualified_name}'
        signature = command.signature
        if signature == '':
            usage += '`'
        else:
            usage += f' {signature}`'
        embed.add_field(name='**Usage:**', value=usage, inline=False)
        embed.add_field(name='**Description:**', value='(no description)' if command.help == '' else command.help,
                        inline=False)
        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        embed = discord.Embed(color=discord.Color.dark_red(),
                              title=':x: **_ERROR!!!_**',
                              description=error)
        await self.get_destination().send(embed=embed)


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
            print('Exception in command "{}":'.format(context.command), file=sys.stderr)
            traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
        embed = discord.Embed(color=color,
                              title=title,
                              description=description)
        await context.send(embed=embed)


async def get_prefix(bot, message):
    extras = settings.prefixes
    if settings.prefixes_dm is not None and isinstance(message.channel, (discord.DMChannel, discord.GroupChannel)):
        extras = settings.prefixes_dm
    if settings.mention_prefix:
        return commands.when_mentioned_or(*extras)(bot, message)
    else:
        return extras


if __name__ == '__main__':
    bot = LeoBot(command_prefix=get_prefix, help_command=EmbedHelpCommand(),
                 description='General-purpose Discord bot written in Python.\nMore information can be found here: '
                             'https://github.com/Leo40Git/ABotCalledLeo')
    try:
        bot.load_extension('cogs.system')
    except commands.ExtensionError as e:
        print('Failed to load essential extension "cogs.system".', file=sys.stderr)
        traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
        exit(-1)
    for ext in settings.startup_extensions:
        try:
            bot.load_extension(ext)
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
        token = f.readline()
        f.close()
        bot.run(token)
