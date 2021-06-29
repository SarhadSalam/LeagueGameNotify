import discord
from discord.ext import commands
import api_calls
import logging
from datetime import datetime, timedelta
import time
import consts
from .helpers import HelperFunctions

class Clash(commands.Cog, HelperFunctions):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    # Commands
    @commands.command()
    async def clash(self, ctx):
        cooldown = 60
        if self.update_timestamp("clash", ctx, cooldown):
            uri = api_calls.BASE_API_URL + api_calls.CLASH_API_URI
            response = api_calls.call_api(uri)
            if response and response.status_code == 200:
                clash_data = response.json()
                if len(clash_data) == 0:
                    await ctx.send("There are no clash dates currently set :(")
                    return
                clash_data = sorted(
                    clash_data, key=lambda i: i["schedule"][0]["registrationTime"])
                msg = "Current Clash Dates:"
                for clash in clash_data:
                    ts = int(clash["schedule"][0]["registrationTime"]) // 1000
                    date = (datetime.utcfromtimestamp(ts) +
                            timedelta(hours=consts.TIMEZONE_DELTA)).strftime('%d %b %Y at %I:%M %p')
                    name = clash["nameKey"].capitalize(
                    ) + " Cup " + clash["nameKeySecondary"].capitalize().replace("_", " ")
                    text = "\n  " + name + " => " + date
                    if clash["schedule"][0]["cancelled"]:
                        text += " (CANCELLED)"
                    msg += text
                logging.info(msg)
                await ctx.send(msg)
            else:
                self.clear_timestamp("clash")
                await ctx.send("Error obtaining clash info. Please try again")
        else:
            await ctx.send("Please wait " + str(cooldown) + " seconds from last successful call to use this command again")

# Connect cog to bot
def setup(bot):
    bot.add_cog(Clash(bot))
