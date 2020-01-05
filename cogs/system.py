import asyncio
import sys
import traceback

from discord.ext import commands


class System(commands.Cog):
    """Essential core cog. Provides commands that manage the bot's general operation."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=['sys'], hidden=True)
    @commands.is_owner()
    @commands.dm_only()
    async def system(self, ctx):
        """Commands that manage the bot's general operation."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.system)

    @system.command(name='exit', aliases=['shutdown'])
    async def sys_exit(self, ctx):
        """Shuts the bot down."""
        await ctx.send('Are you sure you want to shut down the bot?\n'
                       'If yes, send "yes" in the next 5 seconds.')

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'yes'

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=5)
        except asyncio.TimeoutError:
            await ctx.send('Shutdown cancelled.')
            return

        await ctx.send('**_Shutting down..._**')
        await self.bot.close()

    @system.group(aliases=['exts'])
    async def extensions(self, ctx):
        """Commands that manage the bot's loaded extensions."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.extensions)

    @extensions.command(name='list')
    async def exts_list(self, ctx):
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
    async def exts_load(self, ctx, *exts):
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
    async def exts_unload(self, ctx, *exts):
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


def setup(bot):
    bot.add_cog(System(bot))
