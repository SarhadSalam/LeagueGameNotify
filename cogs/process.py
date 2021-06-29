import discord
from discord.ext import commands
import os
from .helpers import HelperFunctions

class Process(commands.Cog, HelperFunctions):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def cog_check(self, ctx):
        return self.is_admin(ctx)

    # Commands
    @commands.command()
    async def start(self, ctx):
        os.system("pm2 restart LeagueDiscordBot")

    @commands.command()
    async def stop(self, ctx):
        os.system("pm2 restart LeagueDiscordBot")

# Connect cog to bot
def setup(bot):
    bot.add_cog(Process(bot))
