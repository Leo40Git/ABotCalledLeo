import random
from enum import IntEnum

import discord
from discord.ext import commands


class Gambling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    class SlotsReel(IntEnum):
        CHERRY = 1
        LEMON = 2
        ORANGE = 3
        PEACH = 4
        BELL = 5
        BAR = 6
        SEVEN = 7

    _slots_values = list(SlotsReel.__members__.values())

    _slots_payout = {
        SlotsReel.CHERRY: 7,
        SlotsReel.LEMON: 7,
        SlotsReel.ORANGE: 10,
        SlotsReel.PEACH: 14,
        SlotsReel.BELL: 20,
        SlotsReel.BAR: 250,
        SlotsReel.SEVEN: 'jackpot'
    }

    _slots_emotes = {
        SlotsReel.CHERRY: ':cherries:',
        SlotsReel.LEMON: ':lemon:',
        SlotsReel.ORANGE: ':orange_circle:',
        SlotsReel.PEACH: ':peach:',
        SlotsReel.BELL: ':bell:',
        SlotsReel.BAR: ':stop_button:',  # TODO find better emote for this one
        SlotsReel.SEVEN: ':seven:'
    }

    @commands.command()
    async def slots(self, ctx: commands.Context):
        print(self._slots_values)
        print(self._slots_emotes)
        result = []
        for i in range(0, 3):
            result_line = []
            for j in range(0, 3):
                result_line.append(random.choice(self._slots_values))
            result.append(result_line)
        print(result)
        out = ''
        for i in range(0, 3):
            for j in range(0, 3):
                out += f'{self._slots_emotes[result[i][j]]} '
            out += '\n'
        out += '\nCongrats! You got **{payout}** credits!'
        await ctx.send(out)


def setup(bot: commands.Bot):
    bot.add_cog(Gambling(bot))
