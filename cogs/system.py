import asyncio
import json
import sys
import traceback
from os import path
from typing import Dict, AnyStr, Any, NoReturn

import discord
from discord.ext import commands, tasks

ConfigDict = Dict[AnyStr, Any]


class System(commands.Cog):
    """Essential core cog. Provides the config service that stores settings per guild."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._configs = dict()
        self.config_flush_auto.start()

    def config_load(self, guild: discord.Guild) -> ConfigDict:
        """
        Loads the configuration for a guild.

        :param guild: guild to load config for
        :return: config for the specified guild.
        """
        guild_key = str(guild.id)
        if guild_key in self._configs:
            return dict(self._configs[guild_key])
        config_file = f'configs/{guild_key}.json'
        if path.exists(config_file):
            # read from file (and cache it)
            f = open(config_file, 'r')
            config_dict = self._configs[guild_key] = json.load(f)
            f.close()
        else:
            # create new store in cache
            config_dict = self._configs[guild_key] = dict()
        return config_dict

    def config_flush(self) -> NoReturn:
        """Flushes the configuration cache to disk."""
        for guild, config in self._configs.items():
            f = open(f'configs/{guild}.json', 'w')
            json.dump(config, f)
            f.close()

    @tasks.loop(minutes=5.0)
    async def config_flush_auto(self):
        self.config_flush()

    def cog_unload(self):
        try:
            self.config_flush_auto.cancel()
        except RuntimeError:
            pass
        self.config_flush()

    @commands.group(aliases=['sys'])
    @commands.is_owner()
    @commands.dm_only()
    async def system(self, ctx: commands.Context):
        """Commands that manage the bot's general operation."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.system)

    @system.command(name='exit', aliases=['shutdown'])
    async def sys_exit(self, ctx: commands.Context, force: bool = False):
        """
        Shuts the bot down.

        `[force]` - if True, skips confirmation.
        """
        if not force:
            await ctx.send('Are you sure you want to shut down the bot?\n'
                           'If yes, send "yes" in the next 5 seconds.')

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'yes'

            try:
                await self.bot.wait_for('message', check=check, timeout=5)
            except asyncio.TimeoutError:
                await ctx.send('Shutdown cancelled.')
                return

        await ctx.send("**_Unloading extensions..._**")
        exts = list(self.bot.extensions.keys())
        for ext in reversed(exts):
            self.bot.unload_extension(ext)
        await ctx.send('**_Shutting down..._**')
        await self.bot.close()

    @system.group(aliases=['cfgs', 'configs'])
    async def configurations(self, ctx: commands.Context):
        """Commands that manage the bot's configuration cache."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.configurations)

    @configurations.command(name='flush')
    async def cfgs_flush(self, ctx: commands.Context):
        """Flushes the config cache to disk."""
        was_running = True
        try:
            self.config_flush_auto.cancel()
        except RuntimeError:
            was_running = False
        self.config_flush()
        if was_running:
            self.config_flush_auto.start()

    @configurations.command(name='flush-auto')
    async def cfgs_flush_auto(self, ctx: commands.Context, state: bool):
        """
        Configures the auto flush loop, which runs every 5 minutes when enabled.

        `<state>` - new state: `True` for enabled, `False` for disabled
        """
        if state:
            try:
                self.config_flush_auto.start()
                await ctx.send('Auto flush loop has been started.')
            except RuntimeError:
                await ctx.send('Auto flush loop is already running.')
        else:
            try:
                self.config_flush_auto.cancel()
                await ctx.send('Auto flush loop has been cancelled.')
            except RuntimeError:
                await ctx.send('Auto flush loop has already been cancelled.')

    @configurations.command(name='clear-cache')
    async def cfgs_clear_cache(self, ctx: commands.Context, flush: bool = True):
        """
        Clears the configurations cache.

        `[flush]` - if `True`, flushes the cache to disk before clearing it."""
        if flush:
            try:
                self.config_flush_auto.cancel()
            except RuntimeError:
                pass
            self.config_flush()
            try:
                self.config_flush_auto.start()
            except RuntimeError:
                pass
        self._configs = dict()

    @configurations.command(name='reload-all')
    async def cfgs_reload_all(self, ctx: commands.Context):
        """Reloads all loaded configurations."""
        cfgs_to_del = []
        for guild in self._configs:
            config_file = f'configs/{guild}.json'
            if path.exists(config_file):
                f = open(config_file, 'r')
                self._configs[guild] = json.load(f)
                f.close()
            else:
                cfgs_to_del.append(guild)
        for guild in cfgs_to_del:
            del self._configs[guild]

    @system.group(aliases=['exts'])
    async def extensions(self, ctx: commands.Context):
        """Commands that manage the bot's loaded extensions."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.extensions)

    @extensions.command(name='list')
    async def exts_list(self, ctx: commands.Context):
        """Lists all loaded extensions."""
        exts = self.bot.extensions
        pag = commands.Paginator()
        pag.clear()
        for ext in exts:
            pag.add_line(ext)
        await ctx.send(f'{len(exts)} extensions currently loaded:\n')
        for page in pag.pages:
            await ctx.send(page)

    @extensions.command(name='load', aliases=['reload'])
    async def exts_load(self, ctx: commands.Context, *exts: str):
        """
        Loads the specified extensions. If one is already loaded, it is reloaded.

        `[exts...]` - extensions to load.
        if none are specified, selects all currently loaded extensions (reloads all extensions)
        """
        if len(exts) == 0:
            exts = tuple(self.bot.extensions)
        loaded = 0
        reloaded = 0
        pag = commands.Paginator()
        pag.clear()
        for ext in exts:
            try:
                self.bot.load_extension(ext)
            except commands.ExtensionAlreadyLoaded as e:
                try:
                    self.bot.reload_extension(ext)
                except commands.ExtensionError as e:
                    await ctx.send(f'Failed to reload extension "{ext}": {str(e)}')
                    print(f'Failed to reload extension "{ext}".', file=sys.stderr)
                    traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
                else:
                    reloaded += 1
                    pag.add_line(f'{ext} (reloaded)')
            except commands.ExtensionError as e:
                await ctx.send(f'Failed to load extension "{ext}": {str(e)}')
                print(f'Failed to load extension "{ext}".', file=sys.stderr)
                traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
            else:
                loaded += 1
                pag.add_line(f'{ext} (newly loaded)')
        await ctx.send(f'{loaded + reloaded}/{len(exts)} extensions successfully loaded '
                       f'({loaded} newly loaded, {reloaded} reloaded):')
        for page in pag.pages:
            await ctx.send(page)

    @extensions.command(name='unload')
    async def exts_unload(self, ctx: commands.Context, *exts: str):
        """
        Unloads the specified extensions.

        `[exts...]` - extensions to unload
        """
        unloaded = 0
        pag = commands.Paginator()
        pag.clear()
        for ext in exts:
            try:
                if ext == 'cogs.system':
                    raise commands.ExtensionError('Can\'t unload essential extension "cogs.system"', name='System')
                self.bot.unload_extension(ext)
            except commands.ExtensionError as e:
                await ctx.send(f'Failed to unload extension "{ext}": {str(e)}')
                print(f'Failed to unload extension "{ext}".', file=sys.stderr)
                traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
            else:
                unloaded += 1
                pag.add_line(f'{ext}')
        await ctx.send(f'{unloaded}/{len(exts)} extensions successfully unloaded:')
        for page in pag.pages:
            await ctx.send(page)


def setup(bot: commands.Bot):
    bot.add_cog(System(bot))
