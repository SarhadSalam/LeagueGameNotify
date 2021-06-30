import discord
from discord.ext import commands
import logging

class DebugCommandSuite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Commands
    @commands.command()
    async def test(self, ctx):
        logging.info(f"Received message: {ctx.message.content}")
        logging.info(f"Message Object: {ctx.message}")
        logging.info(f"Message Author Object: {ctx.author}")
        logging.info(f"Message Attachments: {ctx.message.attachments}")
        await ctx.send("Received test message: " + ctx.message.content)

    @commands.command()
    async def mentionMe(self, ctx):
        mentionId = ctx.author.id
        msg = "Hello <@!" + str(mentionId) + ">!"
        await ctx.send(msg)

    @commands.command()
    async def hello(self, ctx):
        await ctx.send('Hello')

# Connect cog to bot
def setup(bot):
    bot.add_cog(DebugCommandSuite(bot))
