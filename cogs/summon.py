import discord
from discord.ext import commands
from .helpers import HelperFunctions
import data


class Summon(commands.Cog, HelperFunctions):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    # Commands
    @commands.command()
    async def summon(self, ctx):
        cooldown = 1
        isReady = self.update_timestamp("summon", ctx, cooldown)
        if isReady:
            skipList = ["RedHat1", "TheReilGabe"]
            summoner = data.getRandomSummoner(skipList)
            discordMentionId = data.getDiscordIdFromSummonerName(summoner)
            if discordMentionId is None:
                await ctx.send(summoner + ", you have been summoned to play a ranked game")
            else:
                await ctx.send(self.mentionUser(discordMentionId) + ", " + summoner + " has been summoned to play a ranked game")

# Connect cog to bot

def setup(bot):
    bot.add_cog(Summon(bot))
