import itertools
import textwrap
from typing import List

import discord
from discord.ext import commands


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
        desc = appinfo.description
        if desc is None:
            desc = self.context.bot
        if desc is None:
            desc = ''
        embed = discord.Embed(color=discord.Color.dark_blue(),
                              title=f'Sending aid for **{appinfo.name}**!',
                              description=desc)
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
