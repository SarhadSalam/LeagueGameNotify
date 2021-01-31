import settings
import data
import requests
import api_calls
import sys
import consts
import discord_bot
from periodic import PeriodicExecutor

needsSave = False

def requestDataSave():
    global needsSave
    needsSave = True

def saveSummonerData():
    global needsSave
    needsSave = False
    print("Saving new summoner data")
    data.saveSummonerData()

def querySummonerCurrentRank(summoner):
    encryptedId = summoner.SummonerDTO["id"]
    url = settings.API_URL + api_calls.LEAGUE_API_URL.format(encryptedSummonerId=encryptedId)
    response = requests.get(url, headers={consts.API_KEY_HEADER: settings.API_KEY})
    if response.status_code == 200:
        leagueEntrySet = response.json()
        for entry in leagueEntrySet:
            if (entry["queueType"] != consts.RANKED_SOLO_QUEUE_TYPE):
                continue
            rank = entry["tier"] + " " + entry["rank"]
            break
        change = summoner.updateCurrentRank(rank)
        if change == 2:
            # Promoted to new Tier!
            discord_bot.SendMessage(summoner.SummonerDTO["name"] + " has promoted to " + rank + "!!! <3")
        elif change == 1:
            # Promoted to new Division
            discord_bot.SendMessage(summoner.SummonerDTO["name"] + " has promoted to " + rank + " <3")
        elif change == -1:
            # Demoted to new Division
            discord_bot.SendMessage(summoner.SummonerDTO["name"] + " has demoted to " + rank + " :(")
        elif change == -2:
            # Demoted to new Tier
            discord_bot.SendMessage(summoner.SummonerDTO["name"] + " has demoted to " + rank + " :( :(\nCan we get an F in the chat")
        elif change == 3:
            # Newly assigned rank
            requestDataSave()

def querySummonerCurrentGame(summoner):
    encryptedId = summoner.SummonerDTO["id"]
    url = settings.API_URL + api_calls.SPECTATOR_API_URL.format(encryptedSummonerId=encryptedId)
    response = requests.get(url, headers={consts.API_KEY_HEADER: settings.API_KEY})
    if response.status_code == 200:
        # Current Game Found
        newGameInfo = response.json()
        notify, reqSave = summoner.updateCurrentGame(newGameInfo)
        if notify:
            discord_bot.SendMessage(summoner.SummonerDTO["name"] + " has started a ranked game!")
        if reqSave:
            requestDataSave()


def run(summonerData):
    # Need to run this loop every 5 mins
    print("Querying Data For Summoners")
    for summonerName in summonerData:
        summoner = summonerData[summonerName]
        querySummonerCurrentGame(summoner)
        querySummonerCurrentRank(summoner)

    if needsSave:
        saveSummonerData()
    # Repeat every 5 mins upto here

def printHelp():
    print("The following arguments are accepted:")
    print("  --refresh, --r: Refresh Summoner Data Before Running")
    print()

if __name__ == "__main__":
    options = (["--refresh", "--r"])
    args = sys.argv[1:]
    if len(args) > 0:
        if args[0] in options[0]:
            # Run with Refresh
            data.refreshSummonerData()
        else:
            # Invalid args
            print("Invalid arguments")
            printHelp()
            sys.exit()
    summonerData = data.loadSummonerData()
    FIVE_MINUTES = 5 * 60
    run_thread = PeriodicExecutor(FIVE_MINUTES, run, summonerData)
    run_thread.run()
