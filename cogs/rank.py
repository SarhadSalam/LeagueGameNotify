import discord
from discord.ext import commands
from utils import getSummonerRankValue
import consts
import settings
import data
from .helpers import HelperFunctions

class Rank(commands.Cog, HelperFunctions):
    def __init__(self, bot):
        self.bot = bot

    # Commands
    @commands.command()
    async def rank(self, ctx, summonerName=None):
        if summonerName == "all" or not summonerName:
            summonerName = settings.SUMMONER_NAMES[:]
        else:
            summonerName = [summonerName]

        summoners = []
        data.loadSummonerData()
        for summoner in summonerName:
            if not (summoner := await self.handleSummonerNameInput(ctx, summoner)):
                continue
            summoners.append(data.getSummoner(summoner))

        summoners.sort(key=getSummonerRankValue, reverse=True)
        msg = ""
        for summoner in summoners:
            currentRank = summoner.CurrentRank
            name = summoner.getName()
            if currentRank is None:
                msg += f"{name} is unranked.\n"
                continue
            msg += f"{name} is currently {currentRank['tier']} {currentRank['division']} {str(currentRank['lp'])}lp."

            if "miniSeries" in currentRank:
                wins = str(currentRank["miniSeries"]["wins"])
                losses = str(currentRank["miniSeries"]["losses"])
                nextRank = consts.TIERS.index(currentRank['tier'])
                nextRank = consts.TIERS[nextRank+1]
                msg += f" Currently {wins}-{losses} in promos to {nextRank}."

            msg += "\n"

        await ctx.send(msg)
        return

    @commands.command()
    async def lp(self, ctx, summonerName=None):
        await self.rank(ctx, summonerName)

    @commands.command()
    async def elo(self, ctx, summonerName=None):
        await self.rank(ctx, summonerName)

# Connect cog to bot
def setup(bot):
    bot.add_cog(Rank(bot))
