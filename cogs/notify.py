import discord
from discord.ext import commands
from .helpers import HelperFunctions
import data

class Notify(commands.Cog, HelperFunctions):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    # Commands
    @commands.command()
    async def notify(self, ctx, action=None, summonerName=None):
        if not action:
            await ctx.send("Need an action and summoner name")
            return

        mentionId = ctx.author.id
        data.loadNotifyData()

        if action == "list":
            subs = data.getNotifyList(mentionId)
            if subs and len(subs) > 0:
                msg = self.mentionUser(mentionId) + \
                    " is simping for the following summoners:"
                for summoner in subs:
                    msg += "\n" + summoner
            else:
                msg = self.mentionUser(mentionId) + \
                    " is currently not simping for anyone."
            await ctx.send(msg)
            return

        if action == "add":
            if summonerName == "/all":
                data.addToAllNotifyList(mentionId)
                await ctx.send("Added " + self.mentionUser(mentionId) + " to all notify lists.")
                return
            elif not (summonerName := await self.handleSummonerNameInput(ctx, summonerName)):
                return
            status = data.addToNotifyList(summonerName, mentionId)
            if status is True:
                await ctx.send(self.mentionUser(mentionId) + " has been added to the notify list for " + summonerName)
            else:
                await ctx.send("Error adding to notify list.\nReason: " + status)
            return

        if action == "remove":
            if summonerName == "/all":
                data.removeFromAllNotifyList(mentionId)
                await ctx.send("Removed " + self.mentionUser(mentionId) + " from all notify lists.")
                return
            elif not (summonerName := await self.handleSummonerNameInput(ctx, summonerName)):
                return
            status = data.removeFromNotifyList(summonerName, mentionId)
            if status is True:
                await ctx.send(self.mentionUser(mentionId) + " has been removed from the notify list for " + summonerName)
            else:
                await ctx.send("Error removing from notify list.\nReason: " + status)
            return

        await ctx.send("Invalid action '" + action + "'")
        return

# Connect cog to bot
def setup(bot):
    bot.add_cog(Notify(bot))
