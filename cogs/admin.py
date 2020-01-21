import discord
from discord.ext import commands
from typing import Optional


class Administration(commands.Cog):
    """Provides administrative commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='delete-messages', aliases=['del-msgs'])
    @commands.has_permissions(manage_messages=True, read_message_history=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def del_msgs(self, ctx: commands.Context, first: Optional[discord.Message], count: int = 10):
        """
        Bulk deletes an amount of messages, starting from a specific message and going backwards.

        `[first]` - message to delete first. if not specified, uses the message that called the function
        `[count]` - amount of messages to delete before first message. default is 10
        """
        if first is None:
            first = ctx.message
        deleted = await ctx.channel.purge(limit=count, before=first)
        await first.delete()
        await ctx.send(f'Deleted {len(deleted) + 1} messages.')

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, members: commands.Greedy[discord.Member], reason: Optional[str]):
        """
        Kicks members.

        `[members]` - members to ban
        `[reason]` - ban reason
        """
        successes = 0
        pag = commands.Paginator()
        pag.clear()
        for member in members:
            try:
                await ctx.guild.kick(member, reason=reason)
            except discord.HTTPException:
                pass
            else:
                successes += 1
                pag.add_line(str(member))
        await ctx.send(f'Successfully kicked {successes}/{len(members)} members:')
        for page in pag.pages:
            await ctx.send(page)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, members: commands.Greedy[discord.Member], reason: Optional[str],
                  delete_message_days: int = 1):
        """
        Bans members.

        `[members]` - members to ban
        `[reason]` - ban reason
        `[delete_message_days]` - the number of days worth of messages to delete from the member in the guild.
        must be between 0 and 7
        """
        successes = 0
        pag = commands.Paginator()
        pag.clear()
        for member in members:
            try:
                await ctx.guild.ban(member, reason=reason, delete_message_days=delete_message_days)
            except discord.HTTPException:
                pass
            else:
                successes += 1
                pag.add_line(str(member))
        await ctx.send(f'Successfully banned {successes}/{len(members)} members:')
        for page in pag.pages:
            await ctx.send(page)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, users: commands.Greedy[discord.User], reason: Optional[str]):
        """
        Unbans users.

        `[users]` - users to unban
        `[reason]` - unban reason
        """
        successes = 0
        pag = commands.Paginator()
        pag.clear()
        for user in users:
            try:
                await ctx.guild.unban(user, reason=reason)
            except discord.HTTPException:
                pass
            else:
                successes += 1
                pag.add_line(str(user))
        await ctx.send(f'Successfully unbanned {successes}/{len(users)} members:')
        for page in pag.pages:
            await ctx.send(page)


def setup(bot: commands.Bot):
    bot.add_cog(Administration(bot))
