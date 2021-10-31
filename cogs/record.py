import discord
from discord.ext import commands
from .helpers import HelperFunctions
import data
import api_calls
import consts

class Record(commands.Cog, HelperFunctions):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    # Commands
    @commands.command()
    async def record(self, ctx, summonerName=None, numGames=10):
        async with ctx.typing():    # Long operation so this lets us know the bot is actually doing something
            if not (summonerName := await self.handleSummonerNameInput(ctx, summonerName, knownRequired=True)):
                return

            MAX_NUM_GAMES = 30

            if numGames > MAX_NUM_GAMES:
                await ctx.send("Request exceeded max number of games (" + str(MAX_NUM_GAMES) + ")")
                return
            if numGames <= 0:
                await ctx.send("Must request at least 1 game")
                return
            summonerPuuid = data.getSummoner(summonerName).SummonerDTO["puuid"]

            url = url = api_calls.BASE_API_URL_V5 + \
                api_calls.MATCHLIST_URL.format(puuid=summonerPuuid)
            query_params = {}
            query_params["queue"] = consts.RANKED_SOLO_QUEUE_ID
            query_params["start"] = 0
            query_params["count"] = numGames
            query = "?" + "&".join(["{key}={value}".format(key=item[0], value=item[1]) for item in query_params.items()])
            url += query

            response = api_calls.call_api(url)
            if response and response.status_code == 200:
                gameIds = response.json()

            if not gameIds:
                await ctx.send("Failed to obtain match history")
                return

            history = ""
            championGames = {}
            wins = 0
            losses = 0
            unknown = 0

            MAX_RETRIES = 5

            for gameId in gameIds:
                url = url = api_calls.BASE_API_URL_V5 + \
                    api_calls.MATCH_API_URL.format(matchId=gameId)
                retries = 0
                while retries < MAX_RETRIES:
                    response = api_calls.call_api(url)
                    if response:
                        break
                    else:
                        retries += 1
                if response and response.status_code == 200:
                    matchData = response.json()
                    participants = matchData["info"]["participants"]
                    participant = None
                    for p in participants:
                        if p["puuid"] == summonerPuuid:
                            participant = p
                            break
                    if participant:
                        result = participant["win"]
                        if result:
                            wins += 1
                            history += "W"
                        else:
                            losses += 1
                            history += "L"
                        champion = participant["championName"]
                        if champion not in championGames:
                            championGames[champion] = 0
                        championGames[champion] += 1
                    else:
                        unknown += 1
                else:
                    unknown += 1

            totalGames = len(gameIds)
            history = history[::-1]
            sortedChampionGames = dict(sorted(championGames.items(), key=lambda x:x[1], reverse=True))

            text = "Results for the past {} for {}:\n  Wins: {}\n  Losses: {}\n".format(totalGames, summonerName, wins, losses)
            if unknown > 0:
                text += "  (Could not obtain results for {} games)\n".format(unknown)
            text += "  Form (Oldest games first): {}\n".format(history)
            if len(sortedChampionGames) > 0:
                text += "  Played Champions:\n"
                for champion in sortedChampionGames:
                    pluralCheckKekw = "games" if sortedChampionGames[champion] > 1 else "game"
                    text += "    {} ({} {})\n".format(champion, sortedChampionGames[champion], pluralCheckKekw)

        await ctx.send(text)
        return


# Connect cog to bot


def setup(bot):
    bot.add_cog(Record(bot))
