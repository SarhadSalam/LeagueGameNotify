import discord
from discord.ext import commands
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import api_calls
import os
from .helpers import HelperFunctions
import consts
import re
import random
import logging


class Mmr(commands.Cog, HelperFunctions):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    # Commands
    @commands.command()
    async def mmr(self, ctx, summonerName=None, option=None):
        if not (summonerName := await self.handleSummonerNameInput(ctx, summonerName, knownRequired=False)):
            return
        uri = api_calls.MMR_URI.format(summonerName=summonerName)
        response = api_calls.call_api(uri)
        if response and response.status_code == 200:
            history = option is not None and option.lower() == "-history"
            mmr_data = response.json()
            msg = summonerName + "'s MMR:\n  Ranked: "
            avg = mmr_data["ranked"]["avg"]
            file_name = None
            if not avg:
                msg += "N/A."
            else:
                err = mmr_data["ranked"]["err"]
                ts = int(mmr_data["ranked"]["timestamp"])
                date = (datetime.utcfromtimestamp(ts) +
                        timedelta(hours=consts.TIMEZONE_DELTA)).strftime('%d %b %Y at %I:%M %p')
                msg += str(avg) + " +/- " + str(err) + \
                    " (Last Updated " + date + ")"
                try:
                    summaryText = mmr_data["ranked"]["summary"]
                    pattern = "(.+)\<b\>(.+)\<\/b\>.*\<\/span>(.*)"
                    match = re.search(pattern, summaryText)
                    brief = match.group(1) + match.group(2)
                    details = match.group(3).replace(
                        "<b>", "").replace("</b>", "")
                    text = "(" + brief + ". " + details + ")"
                    msg += "\n    " + text
                except:
                    logging.error("Error parsing summary")
                if history:
                    msg += "\n    History: "
                    timeline = mmr_data["ranked"]["historical"]
                    if len(timeline) == 0:
                        msg += "Not Enough Solo Games For History"
                    else:
                        timeline.reverse()
                        avg = []
                        timestamp = []
                        high = []
                        low = []

                        for entry in timeline:
                            avg.append(entry["avg"])
                            high.append(int(entry["avg"]) + int(entry["err"]))
                            low.append(int(entry["avg"]) - int(entry["err"]))

                            timestamp.append(
                                datetime.utcfromtimestamp(entry["timestamp"]))

                        plt.plot_date(
                            timestamp, avg, label=f"Average", linestyle="-", color="green")
                        plt.plot_date(
                            timestamp, high, label=f"Higher Range", linestyle="-", color="blue")
                        plt.plot_date(
                            timestamp, low, label=f"Lower Range", linestyle="-", color="red")

                        plt.title(f"Ranked MMR timeline for {summonerName}")
                        plt.legend(loc="best")
                        plt.grid(True, which="major")
                        plt.grid(True, which="minor")
                        plt.xticks(rotation=45)

                        file_name = f"{summonerName}_{random.randint(0, 1000000000000000)}.png"
                        plt.savefig(
                            file_name, bbox_inches='tight', pad_inches=0)
                        plt.clf()

                        msg += str(avg)
            msg += "\n  Gayram: "
            avg = mmr_data["ARAM"]["avg"]
            if not avg:
                msg += "N/A."
            else:
                err = mmr_data["ARAM"]["err"]
                ts = int(mmr_data["ARAM"]["timestamp"])
                date = (datetime.utcfromtimestamp(ts) -
                        timedelta(hours=consts.TIMEZONE_DELTA)).strftime('%d %b %Y at %I:%M %p')
                msg += str(avg) + " +/- " + str(err) + \
                    " (Last Updated " + date + ")"
                if history:
                    msg += "\n    History: "
                    timeline = mmr_data["ARAM"]["historical"]
                    if len(timeline) == 0:
                        msg += "Not Enough Solo Games For History"
                    else:
                        timeline.reverse()
                        avg = []
                        for entry in timeline:
                            avg.append(entry["avg"])
                        msg += str(avg)

            if file_name:
                await ctx.send(msg, file=discord.File(file_name))
                os.remove(file_name)
            else:
                await ctx.send(msg)
        else:
            await ctx.send("Failed to obtain mmr data for " + summonerName + ".")

# Connect cog to bot


def setup(bot):
    bot.add_cog(Mmr(bot))
