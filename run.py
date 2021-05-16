import settings
import data
import data_updater
import requests
import api_calls
import sys
import consts
import discord_bot
import utils
from periodic import PeriodicExecutor
from datetime import datetime
import signal
from api_calls import call_api
from multiprocessing import Process, Queue
import bot_comms

needsSave = False
BOT_COMM_QUEUE = Queue()

def requestDataSave():
    global needsSave
    needsSave = True


def saveSummonerData():
    global needsSave
    needsSave = False
    print("Saving new summoner data")
    data.saveSummonerData()


def notifyGameEnd(summoner, gameId):
    if gameId is None:
        return
    url = api_calls.BASE_API_URL + api_calls.MATCH_API_URL.format(matchId=gameId)
    response = call_api(url)
    if response and response.status_code == 200:
        json_data = response.json()
        participants = json_data["participants"]
        participantIDs = json_data["participantIdentities"]
        participantID = None
        participant = None
        lane = None
        totalKills = 0
        team = None
        matchHistoryUri = None
        for pid in participantIDs:
            summonerId = pid["player"]["summonerId"]
            if summonerId == summoner.SummonerDTO["id"]:
                participantID = pid["participantId"]
                matchHistoryUri = pid["player"]["matchHistoryUri"]
                break
        if participantID is None:
            print("Could not find",
                  summoner.SummonerDTO["name"], "in participant list")
        for p in participants:
            if p["participantId"] == participantID:
                participant = p
                team = p["teamId"]
                break
        for p in participants:
            if p["teamId"] == team:
                totalKills += int(p["stats"]["kills"])
        lane = participant["timeline"]["lane"]

        # participant now has the summoner stats for the game
        champion = data.getChampionName(participant["championId"])
        stats = participant["stats"]
        kills = int(stats["kills"])
        deaths = int(stats["deaths"])
        assists = int(stats["assists"])
        if totalKills > 0:
            kp = str((100 * (kills + assists)) // totalKills)
        else:
            kp = "0"
        win = stats["win"]
        result = "won" if win else "lost"
        msg = "GAME END: " + summoner.SummonerDTO["name"] + " " + result + " a game as " + champion + ". He went " + str(
            kills) + "/" + str(deaths) + "/" + str(assists) + " with a kp of " + kp + "%."

        # Rank Change
        if summoner.CurrentRank != None:
            promos = None
            url = api_calls.BASE_API_URL + api_calls.LEAGUE_API_URL.format(encryptedSummonerId=summoner.SummonerDTO["id"])
            response = call_api(url)
            if response and response.status_code == 200:
                leagueEntrySet = response.json()
                rank = {}
                for entry in leagueEntrySet:
                    if (entry["queueType"] != consts.RANKED_SOLO_QUEUE_TYPE):
                        continue
                    rank["tier"] = entry["tier"]
                    rank["division"] = entry["rank"]
                    rank["lp"] = entry["leaguePoints"]
                    if "miniSeries" in entry:
                        promos = entry["miniSeries"]
                    break
                if rank["tier"] == summoner.CurrentRank["tier"] and rank["division"] == summoner.CurrentRank["division"]:
                    prevLp = int(summoner.CurrentRank["lp"])
                    newLp = int(rank["lp"])
                    lpDiff = 0
                    if win:
                        lpDiff = newLp - prevLp
                    else:
                        lpDiff = prevLp - newLp
                    result = "gained" if win else "lost"
                    if promos is None or lpDiff != 0:
                        msg += "\n" + summoner.SummonerDTO["name"] + " " + result + " " + str(lpDiff) + "lp for this game. He is currently " + str(rank["tier"]) + " " + str(rank["division"]) + " " + str(rank["lp"]) + "lp."
                    if promos is not None:
                        wins = str(promos["wins"])
                        losses = str(promos["losses"])
                        nextRankIndex = consts.TIERS.index(summoner.CurrentRank["tier"]) + 1
                        nextRank = consts.TIERS[nextRankIndex]
                        msg += "\n" + summoner.SummonerDTO["name"] + " is currently " + wins + "-" + losses + " in promos to " + nextRank + "."

        # Match History Uri:
        postMsg = None
        if matchHistoryUri is not None:
            playerCode = matchHistoryUri.split("/")[-1]
            uri = api_calls.MATCH_HISTORY_URI.format(gameId=gameId, playerCode=playerCode)
            postMsg = "View Game Details Here: " + uri
        else:
            print("Error Obtaining Match Uri for match#", gameId)

        color = utils.ColorCodes.GREEN if win else utils.ColorCodes.RED
        discord_bot.SendMessage(msg, color, postMsg)
    else:
        print("Error Obtaining Game Info for match#", gameId)


def notifyGameStart(summoner, gameInfo):
    participants = gameInfo["participants"]
    participant = None
    for p in participants:
        summonerId = p["summonerId"]
        if summonerId == summoner.SummonerDTO["id"]:
            participant = p
            break
    if participant != None:
        champion = data.getChampionName(participant["championId"])
        msg = "GAME START: " + \
            summoner.SummonerDTO["name"] + \
            " has started a ranked game as " + champion + "!"
        data.loadNotifyData()
        notifyList = data.getNotifyListForSummoner(summoner.SummonerDTO["name"])
        postMsg = None
        if notifyList and len(notifyList) > 0:
            postMsg = "Notifying Simps:"
            for user in notifyList:
                postMsg += " " + discord_bot.mentionUser(user)
        discord_bot.SendMessage(msg, utils.ColorCodes.YELLOW, postMsg)
    else:
        print("Could not obtain participant for current game of " +
              summoner.SummonerDTO["name"])


def updateSummonerCurrentRank(summoner, response):
    if response and response.status_code == 200:
        leagueEntrySet = response.json()
        rank = {}
        for entry in leagueEntrySet:
            if (entry["queueType"] != consts.RANKED_SOLO_QUEUE_TYPE):
                continue
            rank["tier"] = entry["tier"]
            rank["division"] = entry["rank"]
            rank["lp"] = entry["leaguePoints"]
            if "miniSeries" in entry:
                rank["miniSeries"] = entry["miniSeries"]
            break
        change = summoner.updateCurrentRank(rank)
        if change == 2:
            # Promoted to new Tier!
            discord_bot.SendMessage("PROMOTION: " + summoner.SummonerDTO["name"] + " has promoted to " +
                                    rank["tier"] + " " + rank["division"] + " !!! <3", utils.ColorCodes.GREEN)
        elif change == 1:
            # Promoted to new Division
            discord_bot.SendMessage(
                "PROMOTION: " + summoner.SummonerDTO["name"] + " has promoted to " + rank["tier"] + " " + rank["division"] + " <3", utils.ColorCodes.GREEN)
        elif change == -1:
            # Demoted to new Division
            discord_bot.SendMessage(
                "DEMOTION: " + summoner.SummonerDTO["name"] + " has demoted to " + rank["tier"] + " " + rank["division"] + " :(", utils.ColorCodes.RED)
        elif change == -2:
            # Demoted to new Tier
            discord_bot.SendMessage("DEMOTION: " + summoner.SummonerDTO["name"] + " has demoted to " + rank["tier"] +
                                    " " + rank["division"] + " :( :(\nCan we get an F in the chat", utils.ColorCodes.RED)
        if change != 0:
            # Newly assigned rank
            requestDataSave()


def updateSummonerCurrentGame(summoner, response):
    if response and response.status_code == 200:
        # Current Game Found
        newGameInfo = response.json()
    else:
        newGameInfo = None
    status = summoner.updateCurrentGame(newGameInfo)
    notifyGameEnd(summoner, status["notifyEnd"])
    if status["notifyStart"]:
        notifyGameStart(summoner, newGameInfo)
    if status["requestSave"]:
        requestDataSave()

def run(summonerData):
    # Need to run this loop every x mins
    while not BOT_COMM_QUEUE.empty():
        # Process method call request from LeagueAssistant Bot
        request = BOT_COMM_QUEUE.get()
        if type(request) is tuple:
            method = request[0]
            args = request[1] if len(request) > 1 else ()
        elif type(request) is str:
            method = request
            args = ()
        else:
            print("Invalid Request:", request)
            continue

        if hasattr(bot_comms, method):
            try:
                getattr(bot_comms, method)(*args)
            except Exception as e:
                print(f"Could not execute method '{method}'")
                print("Reason:", e)
        else:
            print("Invalid method:", method)

    current_time = datetime.now().strftime("%d %b %Y - %H:%M:%S")
    print("Querying Data For Summoners =>", current_time)
    for summonerName in summonerData:
        summoner = summonerData[summonerName]
        encryptedId = summoner.SummonerDTO["id"]
        gameUrl = api_calls.BASE_API_URL + api_calls.SPECTATOR_API_URL.format(encryptedSummonerId=encryptedId)
        rankUrl = api_calls.BASE_API_URL + api_calls.LEAGUE_API_URL.format(encryptedSummonerId=encryptedId)
        gameResponse = call_api(gameUrl)
        rankResponse = call_api(rankUrl)
        updateSummonerCurrentGame(summoner, gameResponse)
        updateSummonerCurrentRank(summoner, rankResponse)

    if needsSave:
        saveSummonerData()

    print("Query Complete.")
    # Repeat every 5 mins upto here


def sysExit(signal, frame):
    discord_bot.SendMessage("```Bot is going to sleep.```")
    bot_process.terminate()
    sys.exit(0)


def printHelp():
    print("The following arguments are accepted:")
    print("  --refresh, --r: Refresh Summoner Data Before Running")
    print()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sysExit)
    options = (["--refresh", "--r"])
    args = sys.argv[1:]

    bot_process = Process(target=discord_bot.start_bot, args=(BOT_COMM_QUEUE,))
    bot_process.start()

    if len(args) > 0:
        if args[0] in options[0]:
            # Run with Refresh
            discord_bot.SendMessage(
                "```Starting Up Bot With Refreshed Data```")
            data.refreshSummonerData()
        else:
            # Invalid args
            print("Invalid arguments")
            printHelp()
            sys.exit()
    summonerData = data.loadSummonerData()
    if summonerData is None:
        print("No summoner data file found. Refreshing summoner data to generate data")
        summonerData = data.refreshSummonerData()
    data.loadChampionData()
    data.loadNotifyData()
    FIVE_MINUTES = 5 * 60
    TWO_MINUTES = 2 * 60
    run_thread = PeriodicExecutor(TWO_MINUTES, run, summonerData)
    discord_bot.SendMessage("```Bot is now awake and ready to report games```")
    run_thread.run()
