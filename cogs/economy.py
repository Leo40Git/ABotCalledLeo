from datetime import datetime, timedelta, timezone
from typing import NoReturn, Optional, Dict, AnyStr, Any

import discord
from discord.ext import commands


class Economy(commands.Cog):
    """Provides the credits service, allowing users to manage useless virtual balances across guilds. Fun!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def economy_get_dict(self, user: discord.User) -> Dict[AnyStr, Any]:
        """
        Retrieves a user's credits data store.

        :param user: user
        :return: credits service data store
        """
        userdata = self.bot.get_cog('UserData')
        if userdata is None:
            raise Exception('Economy cog requires UserData cog')
        u_dict = userdata.userdata_load(None, user)
        if 'economy' not in u_dict:
            u_dict['economy'] = dict()
        return u_dict['economy']

    def credits_get(self, user: discord.User, init: bool = True) -> Optional[int]:
        """
        Retrieves the balance of a user's account.

        :param user: user
        :param init: if True, initialize the user's account if it doesn't exist
        :return: balance of user's account (or None if the account doesn't exist and init is False)
        """
        u_dict = self.economy_get_dict(user)
        if 'credits' not in u_dict:
            if init:
                u_dict['credits'] = 0
            else:
                return None
        return u_dict['credits']

    def credits_set(self, user: discord.User, new_value: int) -> NoReturn:
        """
        Sets the balance of a user's account.

        :param user: user
        :param new_value: new balance
        """
        u_dict = self.economy_get_dict(user)
        u_dict['credits'] = new_value

    def credits_deposit(self, user: discord.User, amount: int) -> NoReturn:
        """
        Deposits an amount of credits into a user's account.

        :param user: user
        :param amount: amount to deposit
        """
        u_dict = self.economy_get_dict(user)
        if 'credits' not in u_dict:
            u_dict['credits'] = 0
        u_dict['credits'] += amount

    def credits_withdraw(self, user: discord.User, amount: int) -> bool:
        """
        Attempts to withdraw an amount of credits out of a user's account.

        If the user doesn't have enough credits to cover the withdrawal, the withdrawal will fail.

        :param user: user
        :param amount: amount to withdraw
        :return: True if withdrawal is successful, False otherwise.
        """
        u_dict = self.economy_get_dict(user)
        if 'credits' not in u_dict:
            u_dict['credits'] = 0
        if u_dict['credits'] < amount:
            return False
        u_dict['credits'] -= amount
        return True

    @commands.group(aliases=['creds'])
    @commands.is_owner()
    @commands.dm_only()
    async def credits(self, ctx: commands.Context):
        """Commands for managing the credits service."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.credits)

    @credits.command(name='set')
    async def creds_set(self, ctx: commands.Context, users: commands.Greedy[discord.User], amount: int):
        """
        Sets users' credit amount.

        `<users>` - users
        `<amount>` - new amount
        """
        pag = commands.Paginator()
        pag.clear()
        for user in users:
            old = self.credits_get(user, False)
            self.credits_set(user, amount)
            pag.add_line(f'{user} ({old} -> {amount})')
        await ctx.send(f'Successfully set the account balance of the following users to {amount}:')
        for page in pag.pages:
            await ctx.send(page)

    @credits.command(name='add')
    async def creds_add(self, ctx: commands.Context, users: commands.Greedy[discord.User], amount: int):
        """
        Adds credits to a users' accounts.

        `<users>` - users to add to
        `<amount>` - amount to add
        """
        pag = commands.Paginator()
        pag.clear()
        for user in users:
            old = self.credits_get(user, False)
            new = 0 if old is None else old + amount
            if new < 0:
                new = 0
            self.credits_set(user, new)
            pag.add_line(f'{user} ({old} -> {new})')
        await ctx.send(f'Successfully added {amount} to the account balance of the following users:')
        for page in pag.pages:
            await ctx.send(page)

    @commands.command(name='account-create')
    async def acc_create(self, ctx: commands.Context):
        """Creates an account for you, if you don't already have one."""
        balance = self.credits_get(ctx.author, False)
        if balance is not None:
            await ctx.send('You already have an account!')
            return
        self.credits_set(ctx.author, 0)

    @commands.command()
    async def balance(self, ctx: commands.Context, user: Optional[discord.User]):
        """
        Checks yours or another user's account balance.

        `[user]` - user to check. if not specified, checks your own balance
        """
        if user is None:
            user = ctx.author
        balance = self.credits_get(user, False)
        if balance is None:
            if user == ctx.author:
                await ctx.send('You don\'t have an account!')
            else:
                await ctx.send(f'`{str(user)}` doesn\'t have an account!')
        else:
            if user == ctx.author:
                await ctx.send(f'You have **{str(balance)}** credits in your account.')
            else:
                await ctx.send(f'`{str(user)}` has **{str(balance)}** credits in their account.')

    @commands.command()
    async def payday(self, ctx: commands.Context):
        """Get paid! Gives you 500 credits, but has a 24 hour cooldown."""
        u_dict = self.economy_get_dict(ctx.author)
        now = datetime.now(timezone.utc)
        delta_24h = timedelta(hours=24)
        if 'last_payday' not in u_dict:
            u_dict['last_payday'] = now.isoformat()
        else:
            last_payday = datetime.fromisoformat(u_dict['last_payday'])
            delta = datetime.now(timezone.utc) - now
            if delta < delta_24h:
                next_payday = last_payday + timedelta(hours=24)
                next_delta = next_payday - now
                mm, ss = divmod(next_delta.seconds, 60)
                hh, mm = divmod(mm, 60)
                embed = discord.Embed(title='Not yet!',
                                      description=f'Your next payday is in **{hh}h {mm}m {ss}s**!',
                                      color=discord.Color.dark_gold())
                await ctx.send(embed=embed)
                return
            else:
                u_dict['last_payday'] = now
        if 'credits' not in u_dict:
            u_dict['credits'] = 0
        u_dict['credits'] += 500
        embed = discord.Embed(title='Payday redeemed!',
                              description=f'You earned **500** credits!\n'
                                          f'Your next payday is in **24h 0m 0s**!',
                              color=discord.Color.dark_gold())
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Economy(bot))
