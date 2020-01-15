import json
import os
from os import path
from typing import Optional, Dict, Any, AnyStr, NoReturn

import discord
from discord.ext import commands, tasks

UserDict = Dict[AnyStr, Any]


class UserData(commands.Cog):
    """Provides the userdata service, allowing the bot to store information about specific users, with each user
    having a separate data store for each guild."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._guild_dicts = dict()
        self.user_flush_auto.start()

    def user_load(self, guild: Optional[discord.Guild], user: discord.User) -> UserDict:
        """
        Loads data for a user, in the scope of a guild.

        :param guild: guild to scope in. if None, loads global data
        :param user: user to load data for
        :return: data for the specified user, in the scope of the specified guild.
        """
        guild_key = '_GLOBAL' if guild is None else str(guild.id)
        if guild_key in self._guild_dicts:
            guild_dict = self._guild_dicts[guild_key]
        else:
            guild_dict = self._guild_dicts[guild_key] = dict()
        user_key = str(user.id)
        # try to locate in cache first
        if user_key in guild_dict:
            return dict(guild_dict[user_key])
        user_file = f'userdata/{guild_key}/{str(user.id)}.json'
        if path.exists(user_file):
            # read from file (and cache it)
            f = open(user_file, 'r')
            user_dict = guild_dict[user_key] = json.load(f)
            f.close()
        else:
            # create new store in cache
            user_dict = guild_dict[user_key] = dict()
        return dict(user_dict)

    def user_save(self, guild: Optional[discord.Guild], user: discord.User, data: UserDict) -> NoReturn:
        """
        Saves data for a user, in the scope guild.

        :param guild: guild to scope in. if None, saves as global data
        :param user: user to load data for
        :param data: data for the specified user, in the scope of the specified guild
        """
        guild_key = '_GLOBAL' if guild is None else str(guild.id)
        if guild_key in self._guild_dicts:
            guild_dict = self._guild_dicts[guild_key]
        else:
            guild_dict = self._guild_dicts[guild_key] = dict()
        user_key = str(user.id)
        # save to cache
        guild_dict[user_key] = dict(data)

    def user_flush(self) -> NoReturn:
        """Flushes the data store cache to disk."""
        for guild in self._guild_dicts.keys():
            guild_dict = self._guild_dicts[guild]
            for user in guild_dict.keys():
                user_file_dir = f'userdata/{guild}'
                os.makedirs(user_file_dir, exist_ok = True)
                user_file = f'{user_file_dir}/{user}.json'
                f = open(user_file, 'w')
                json.dump(guild_dict[user], f)
                f.close()

    def cog_unload(self):
        try:
            self.user_flush_auto.cancel()
        except RuntimeError:
            pass
        self.user_flush()

    @tasks.loop(minutes=5.0)
    async def user_flush_auto(self):
        self.user_flush()

    @commands.group(aliases=['ud'], hidden=True)
    @commands.is_owner()
    @commands.dm_only()
    async def userdata(self, ctx: commands.Context):
        """Commands for managing the userdata service."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.userdata)

    @userdata.command(name='flush')
    async def ud_flush(self, ctx: commands.Context):
        """Flushes the userdata cache to disk."""
        was_running = True
        try:
            self.user_flush_auto.cancel()
        except RuntimeError:
            was_running = False
        self.user_flush()
        if was_running:
            try:
                self.user_flush_auto.start()
            except RuntimeError:
                pass

    @userdata.command(name='flush-auto')
    async def ud_flush_auto(self, ctx: commands.Context, state: bool):
        """
        Configures the auto flush loop, which runs every 5 minutes when enabled.

        <state> - new state: `True` for enabled, `False` for disabled
        """
        if state:
            try:
                self.user_flush_auto.start()
                await ctx.send('Auto flush loop has been started.')
            except RuntimeError:
                await ctx.send('Auto flush loop is already running.')
        else:
            try:
                self.user_flush_auto.cancel()
                await ctx.send('Auto flush loop has been cancelled.')
            except RuntimeError:
                await ctx.send('Auto flush loop has already been cancelled.')

    @userdata.command(name='clear-cache')
    async def ud_clrcache(self, ctx: commands.Context, flush: bool = True):
        """
        Clears the userdata cache.

        [flush] - if `True`, flushes the cache to disk before clearing it."""
        if flush:
            try:
                self.user_flush_auto.cancel()
            except RuntimeError:
                pass
            self.user_flush()
            try:
                self.user_flush_auto.start()
            except RuntimeError:
                pass
        self._guild_dicts = dict()

    @userdata.command(name='reload-all')
    async def ud_reload_all(self, ctx: commands.Context):
        """Reloads all loaded data stores."""
        guilds_to_del = []
        users_to_del = dict()
        for guild in self._guild_dicts.keys():
            if not path.exists(f'userdata/{guild}'):
                guilds_to_del.append(guild)
                continue
            guild_dict = self._guild_dicts[guild]
            for user in guild_dict.keys():
                user_file = f'userdata/{guild}/{user}.json'
                if path.exists(user_file):
                    f = open(user_file, 'r')
                    guild_dict[user] = json.load(f)
                    f.close()
                else:
                    if guild in users_to_del:
                        users_to_del[guild].append(user)
                    else:
                        users_to_del[guild] = [user]
        for guild in guilds_to_del:
            del self._guild_dicts[guild]
        for guild in users_to_del.keys():
            for user in users_to_del[guild]:
                del self._guild_dicts[guild][user]


def setup(bot: commands.Bot):
    bot.add_cog(UserData(bot))
