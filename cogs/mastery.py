import discord
from discord.ext import commands
from .helpers import HelperFunctions
import data
import api_calls


class Mastery(commands.Cog, HelperFunctions):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    # Commands
    @commands.command()
    async def mastery(self, ctx, summonerName=None, championName=None):
        if not (summonerName := await self.handleSummonerNameInput(ctx, summonerName, knownRequired=False)):
            return

        DEFAULT_LIST_SIZE = 5
        MAX_LIST_SIZE = 25
        text = ""
        summonerId = None
        if data.isKnownSummoner(summonerName) is True:
            summonerId = data.getSummoner(summonerName).SummonerDTO["id"]
        else:
            uri = api_calls.SUMMONER_API_URL.format(summonerName=summonerName)
            response = api_calls.call_api(uri)
            if response and response.status_code == 200:
                summonerDTO = response.json()
                summonerId = summonerDTO["id"]
            else:
                msg = "Could not find summoner '{}'".format(summonerName)
                await ctx.send(msg)
                return
        if championName is not None and not championName.startswith("lv") and not championName.isdigit():
            # Specific Champion Request
            championId = data.getChampionId(championName)
            if championId is None:
                msg = "Could not find champion '{}'".format(championName)
                await ctx.send(msg)
                return
            uri = api_calls.CHAMPION_MASTERY_CHAMP_URI.format(
                encryptedSummonerId=summonerId, championId=championId)
            response = api_calls.call_api(uri)
            if response and response.status_code == 200:
                masteryData = response.json()
                masteryLevel = int(masteryData["championLevel"])
                masteryPoints = int(masteryData["championPoints"])
                if masteryLevel == 5 or masteryLevel == 6:
                    tokens = int(masteryData["tokensEarned"])
                    text = "{} is mastery level {} with {} with {:,} mastery points and {} mastery {} tokens".format(
                        summonerName, masteryLevel, championName, masteryPoints, tokens, (masteryLevel+1))
                else:
                    text = "{} is mastery level {} with {} with {:,} mastery points".format(
                        summonerName, masteryLevel, championName, masteryPoints)
            else:
                msg = "Error obtaining mastery info for '{}' with {}".format(
                    summonerName, championName)
                await ctx.send(msg)
                return
        else:
            # List Request
            listSize = DEFAULT_LIST_SIZE
            lvRequest = False
            if championName is not None:
                if championName.startswith("lv"):
                    lvRequest = int(re.search("\d+", championName).group())
                    if lvRequest < 0 or lvRequest > 7:
                        msg = "Mastery Level {} is not valid".format(lvRequest)
                        await ctx.send(msg)
                        return
                else:
                    listSize = int(championName)

            uri = api_calls.CHAMPION_MASTERY_ALL_URI.format(
                encryptedSummonerId=summonerId)
            response = api_calls.call_api(uri)
            if response and response.status_code == 200:
                masteryList = response.json()
                if lvRequest is not False:
                    if lvRequest == 0:
                        numChampions = data.getNumChampions()
                        m0Champs = numChampions - len(masteryList)
                        text = "{} has {} mastery level {} champions:".format(
                            summonerName, m0Champs, lvRequest)
                        mList = []
                        for masteryData in masteryList:
                            championId = int(masteryData["championId"])
                            mList.append(championId)
                        for id in data.CHAMPION_ID_TO_NAME:
                            if id not in mList:
                                text += "\n  " + data.getChampionName(id)

                        listSize = 0
                    else:
                        masteryList = list(filter(lambda x, lv=lvRequest: int(
                            x["championLevel"]) == lv, masteryList))
                        listSize = len(masteryList)
                        if listSize > MAX_LIST_SIZE:
                            msg = "{} has {} champions at mastery level {}. Only showing top {} champions".format(
                                summonerName, listSize, lvRequest, MAX_LIST_SIZE)
                            listSize = MAX_LIST_SIZE
                            text = "{}'s top {} mastery level {} champions:".format(
                                summonerName, listSize, lvRequest)
                            await ctx.send(msg)
                        else:
                            text = "{} has {} mastery level {} champions:".format(
                                summonerName, listSize, lvRequest)
                else:
                    if listSize > MAX_LIST_SIZE:
                        msg = "Requested larger than max list size of {0}. Only showing top {0} champions".format(
                            MAX_LIST_SIZE)
                        listSize = MAX_LIST_SIZE
                        await ctx.send(msg)
                    if listSize > len(masteryList):
                        msg = "{} only has mastery on {} champions".format(
                            summonerName, len(masteryList))
                        listSize = len(masteryList)
                        await ctx.send(msg)
                    text = "{}'s top {} champions:".format(
                        summonerName, listSize)
                for i in range(listSize):
                    masteryData = masteryList[i]
                    championId = int(masteryData["championId"])
                    masteryLevel = int(masteryData["championLevel"])
                    masteryPoints = int(masteryData["championPoints"])

                    champName = data.getChampionName(championId)
                    line = ""
                    text += "\n"
                    if masteryLevel == 5 or masteryLevel == 6:
                        tokens = int(masteryData["tokensEarned"])
                        line = "  {} at mastery level {} with {:,} mastery points and {} mastery {} tokens".format(
                            champName, masteryLevel, masteryPoints, tokens, (masteryLevel+1))
                    else:
                        line = "  {} at mastery level {} with {:,} mastery points".format(
                            champName, masteryLevel, masteryPoints)
                    text += line
            else:
                msg = "Error obtaining mastery info for '{}'".format(
                    summonerName)
                await ctx.send(msg)
                return

        await ctx.send(text)
        return

# Connect cog to bot


def setup(bot):
    bot.add_cog(Mastery(bot))
