import itertools
import sys
import traceback
from typing import List
import textwrap

import discord
from discord.ext import commands

import settings


class EmbedHelpCommand(commands.HelpCommand):
    def __init__(self):
        super(EmbedHelpCommand, self).__init__(verify_checks=True,
                                               command_attrs=dict(help='Provides help on the bot\'s various commands.'
                                                                       '\n'
                                                                       '\n`[command]` - Cog/group/command to provide '
                                                                       'help for. If not specified, shows a list of '
                                                                       'all the bot\'s commands.'))

    def make_help_values(self, cmd_list: List[commands.Command]):
        first = True
        names = ''
        briefs = ''
        for command in cmd_list:
            if first:
                first = False
            else:
                names += '\n'
                briefs += '\n'
            name_w = textwrap.wrap(command.name, width=46)
            brief_w = textwrap.wrap('(no description)' if command.short_doc == '' else command.short_doc, width=46)
            n = max(len(name_w), len(brief_w))
            name_w += [''] * (n - len(name_w))
            brief_w += [''] * (n - len(brief_w))
            names += '\n'.join(name_w)
            briefs += '\n'.join(brief_w)
        return names, briefs

    def add_commands_to_embed(self, embed: discord.Embed, raw_cmds: List[commands.Command], name: str = '**Names:**'):
        group_list = list()
        commands_list = list()

        def keyfunc(value):
            return isinstance(value, commands.Group)

        for k, v in itertools.groupby(raw_cmds, key=keyfunc):
            if k:
                group_list.extend(v)
            else:
                commands_list.extend(v)

        has_groups = len(group_list) > 0
        has_commands = len(commands_list) > 0

        cmd_names = '**Groups:**' if has_groups else '**Commands:**'
        cmd_briefs = '\u200B'
        if has_groups:
            value_n, value_b = self.make_help_values(group_list)
            cmd_names += '\n' + value_n
            cmd_briefs += '\n' + value_b
        if has_commands:
            if has_groups:
                cmd_names += '\n\n**Commands:**'
                cmd_briefs += '\n\n'
            value_n, value_b = self.make_help_values(commands_list)
            cmd_names += '\n' + value_n
            cmd_briefs += '\n' + value_b

        embed.add_field(name=name, value=cmd_names)
        embed.add_field(name='**Briefs:**', value=cmd_briefs)
        embed.add_field(name='\u200B', value='\u200B')  # new 'line'

    async def send_bot_help(self, mapping):
        appinfo = await self.context.bot.application_info()
        embed = discord.Embed(color=discord.Color.dark_blue(),
                              title=f'Sending aid for **{appinfo.name}**!',
                              description=bot.description if appinfo.description is None else appinfo.description)
        if appinfo.icon is not None:
            embed.set_thumbnail(url=f'https://cdn.discordapp.com/app-icons/{appinfo.id}/{appinfo.icon}.png')

        for cog, raw_cmds in mapping.items():
            command_list = await self.filter_commands(raw_cmds, sort=True)
            if len(command_list) == 0:
                continue
            if cog is None:
                name = '**Uncategorized:**'
            else:
                name = f'**{cog.qualified_name}:**'
            self.add_commands_to_embed(embed, command_list, name)
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(color=discord.Color.dark_blue(),
                              title=f'Sending aid for cog **{cog.qualified_name}**!',
                              description='(no description)' if cog.description is None else cog.description)
        command_list = await self.filter_commands(cog.get_commands(), sort=True)
        if len(command_list) > 0:
            self.add_commands_to_embed(embed, command_list)
        await self.get_destination().send(embed=embed)

    async def command_can_run(self, command: commands.Command):
        try:
            root_parent = command.root_parent
            if root_parent is None:
                return await command.can_run(self.context)
            else:
                return await root_parent.can_run(self.context)
        except commands.CommandError:
            return False

    async def send_group_help(self, group):
        if not await self.command_can_run(group):
            string = await discord.utils.maybe_coroutine(self.command_not_found,
                                                         self.context.kwargs['command'].split()[0])
            return await self.send_error_message(string)
        embed = discord.Embed(color=discord.Color.dark_blue(),
                              title=f'Sending aid for group **{group.name}**!',
                              description='(no description)' if group.help == '' else group.help)
        command_list = await self.filter_commands(group.commands, sort=True)
        if len(command_list) > 0:
            self.add_commands_to_embed(embed, command_list)
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
    bot = LeoBot(command_prefix=get_prefix, help_command=EmbedHelpCommand())
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
