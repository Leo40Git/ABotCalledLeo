import discord
from discord.ext import commands, tasks

from typing import NoReturn, Optional, Dict, AnyStr, Any
from datetime import datetime, timedelta, timezone

import settings


class Economy(commands.Cog):
    """Provides the funds service, allowing users to manage useless virtual balances across guilds. Fun!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def funds_get_dict(self, user: discord.User) -> Dict[AnyStr, Any]:
        """
        Retrieves a user's funds data store.

        :param user: user
        :return: funds service data store
        """
        userdata = self.bot.get_cog('UserData')
        if userdata is None:
            raise Exception('Economy cog requires UserData cog')
        u_dict = userdata.user_load(None, user)
        if 'economy' not in u_dict:
            u_dict['economy'] = dict()
        return dict(u_dict['economy'])

    def funds_set_dict(self, user: discord.User, data: Dict[AnyStr, Any]) -> NoReturn:
        """
        Sets a user's funds data store.

        :param user: user
        :param dict: new funds service data store
        """
        userdata = self.bot.get_cog('UserData')
        if userdata is None:
            raise Exception('Economy cog requires UserData cog')
        u_dict = userdata.user_load(None, user)
        u_dict['economy'] = dict(data)
        userdata.user_save(None, user, u_dict)

    def funds_get(self, user: discord.User, init: bool = True) -> Optional[int]:
        """
        Retrieves the balance of a user's account.

        :param user: user
        :param init: if True, initialize the user's account if it doesn't exist
        :return: balance of user's account (or None if the account doesn't exist and init is False)
        """
        u_dict = self.funds_get_dict(user)
        if 'funds' not in u_dict:
            if init:
                u_dict['funds'] = 0
            else:
                return None
        self.funds_set_dict(user, u_dict)
        return u_dict['funds']

    def funds_set(self, user: discord.User, new_value: int) -> NoReturn:
        """
        Sets the balance of a user's account.

        :param user: user
        :param new_value: new balance
        """
        u_dict = self.funds_get_dict(user)
        u_dict['funds'] = new_value
        self.funds_set_dict(user, u_dict)

    def funds_deposit(self, user: discord.User, amount: int) -> NoReturn:
        """
        Deposits an amount of funds into a user's account.

        :param user: user
        :param amount: amount to deposit
        """
        u_dict = self.funds_get_dict(user)
        if 'funds' not in u_dict:
            u_dict['funds'] = 0
        u_dict['funds'] += amount
        self.funds_set_dict(user, u_dict)

    def funds_withdraw(self, user: discord.User, amount: int) -> bool:
        """
        Attempts to withdraw an amount of funds out of a user's account.

        If the user doesn't have enough funds to cover the withdrawal, the withdrawal will fail.

        :param user: user
        :param amount: amount to withdraw
        :return: True if withdrawal is successful, False otherwise.
        """
        u_dict = self.funds_get_dict(user)
        if 'funds' not in u_dict:
            u_dict['funds'] = 0
        if u_dict['funds'] < amount:
            return False
        u_dict['funds'] -= amount
        self.funds_set_dict(user, u_dict)
        return True

    @commands.group()
    @commands.is_owner()
    @commands.dm_only()
    async def funds(self, ctx: commands.Context):
        """Commands for managing the funds service."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.funds)

    @commands.command()
    async def payday(self, ctx: commands.Context):
        """oh boyo"""
        u_dict = self.funds_get_dict(ctx.author)
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
        if 'funds' not in u_dict:
            u_dict['funds'] = 0
        u_dict['funds'] += settings.payday_amount
        self.funds_set_dict(ctx.author, u_dict)
        embed = discord.Embed(title='Payday redeemed!',
                              description=f'You earned **{settings.payday_amount}** credits!\n'
                                          f'Your next payday is in **24h 0m 0s**!',
                              color=discord.Color.dark_gold())
        await ctx.send(embed=embed)

    @commands.command()
    async def balance(self, ctx: commands.Context, user: Optional[discord.User]):
        if user is None:
            user = ctx.author
        balance = self.funds_get(user, False)
        if balance is None:
            if user is ctx.author:
                await ctx.send('You don\'t have an account!')
            else:
                await ctx.send(f'`{str(user)}` doesn\'t have an account!')
        else:
            if user is ctx.author:
                await ctx.send(f'You have **{str(balance)}** credits in your account.')
            else:
                await ctx.send(f'`{str(user)}` has **{str(balance)}** credits in their account.')


def setup(bot: commands.Bot):
    bot.add_cog(Economy(bot))
