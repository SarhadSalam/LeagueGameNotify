import discord
from discord.ext import commands
import settings
from .helpers import HelperFunctions

class Flex(commands.Cog, HelperFunctions):
    def __init__(self, bot):
        self.bot = bot
        self.flex_queue = []
        super().__init__()

    # Commands
    @commands.command()
    async def flex(self, ctx, action='tag', summoner1=None, summoner2=None, summoner3=None, summoner4=None, summoner5=None):
        def generateTag(ids):
            need_people = 5 - len(self.flex_queue)
            plural_person = "people" if need_people > 1 else "person"
            msg = f"Come for 5sum. We need {need_people} more {plural_person}. "
            for (k, v) in ids.items():
                if k != "RedHat1":
                    msg += f"{self.mentionUser(v)} "
            return msg

        if action == 'list':
            await ctx.send(f"People in lobby ({len(self.flex_queue)}): {self.flex_queue}")
            return

        if action == 'tag':  # tag all
            if summoner1 == 'all':
                msg = generateTag(settings.DISCORD_IDS)
            else:
                tags = {}
                for (k, v) in settings.DISCORD_IDS.items():
                    if k not in self.flex_queue:
                        tags[k] = v

                if len(self.flex_queue) < 5:
                    msg = f"""People in lobby: {self.flex_queue}\n{generateTag(tags)}"""
                else:
                    msg = f"""People in lobby: {self.flex_queue}\n Not tagging anyone new, as lobby is full."""

            await ctx.send(msg)
            return

        if action == 'clear':
            self.flex_queue.clear()
            await ctx.send("Cleared queue!")
            return

        if not summoner1:
            await ctx.send("Need a summoner name!")
            return

        summoners = [summoner1, summoner2, summoner3, summoner4, summoner5]

        for summoner in summoners:
            if not summoner:
                continue

            if summoner == "me":
                if ctx.message.author.id not in settings.SUMMONER_BY_DISCORD_IDS:
                    await ctx.send(f"{ctx.message.author.name} is not one of the bois.")
                    continue

                summoner = settings.SUMMONER_BY_DISCORD_IDS[ctx.author.id]

            if not await self.handleSummonerNameInput(ctx, summoner):
                return

            summoner = summoner.lower()

            if action == 'add':
                if len(self.flex_queue) >= 5:
                    await ctx.send(f"Flex lobby is full, please clear lobby first.")
                    return
                if summoner not in self.flex_queue:
                    self.flex_queue.append(summoner)
                    await ctx.send(f"Added {summoner} to lobby.")
                else:
                    await ctx.send(f"{summoner} is already in lobby. Not added to lobby.")
            elif action == 'remove':
                if summoner not in self.flex_queue:
                    await ctx.send(f"{summoner} is not in the lobby. Can't remove")
                else:
                    self.flex_queue.remove(summoner)
                    await ctx.send(f"Removed {summoner} from lobby.")

# Connect cog to bot
def setup(bot):
    bot.add_cog(Flex(bot))
