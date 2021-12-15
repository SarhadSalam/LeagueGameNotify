import discord
from discord.ext import commands
from datetime import datetime, timedelta
import api_calls
from .helpers import HelperFunctions
import consts
import settings
import data

class Aram(commands.Cog, HelperFunctions):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    # Commands
    @commands.command()
    async def aram(self, ctx):
        aramMMRData = []
        summoners = settings.SUMMONER_NAMES[:]

        for summonerName in summoners:
            uri = api_calls.MMR_URI.format(summonerName=summonerName)
            response = api_calls.call_api(uri)
            if response and response.status_code == 200:
                mmr_data = response.json()
                avg = mmr_data["ARAM"]["avg"]
                err = mmr_data["ARAM"]["err"]
                rank = mmr_data["ARAM"]["closestRank"]
                percentile = mmr_data["ARAM"]["percentile"]
                ts = int(mmr_data["ARAM"]["timestamp"])
                date = (datetime.utcfromtimestamp(ts) -
                        timedelta(hours=consts.TIMEZONE_DELTA)).strftime('%d %b %Y at %I:%M %p')
                aramMMRData.append({"summonerName": summonerName, 
                                    "avg": avg, 
                                    "err": err, 
                                    "rank": rank, 
                                    "percentile": percentile, 
                                    "date": date})

        aramMMRData.sort(key=lambda d: d["avg"], reverse=True)
        msg = ""
        for aramData in aramMMRData:
            if not avg:
                msg += str(aramData["summonerName"]) + " does not have enough games played."
            else:
                msg += str(aramData["summonerName"]) + " currently has " + str(aramData["avg"]) + " +/- " + str(aramData["avg"]) + \
                        ", Approximately " + str(aramData["percentile"]) + " of " + str(aramData["rank"]) + " as of " + date
            
            msg += "\n"
        
        await ctx.send(msg)
        return

# Connect cog to bot
def setup(bot):
    bot.add_cog(Aram(bot))
