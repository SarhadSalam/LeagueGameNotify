import discord
from discord.ext import commands
import settings

class Bois(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Commands
    @commands.command()
    async def bois(self, ctx):
        names_nicknames = {}

        for k, v in settings.NAME_IDS.items():
            if v in names_nicknames:
                names_nicknames[v].append(k)
            else:
                names_nicknames[v] = [k]

        await ctx.send(f"{names_nicknames}")

# Connect cog to bot
def setup(bot):
    bot.add_cog(Bois(bot))
