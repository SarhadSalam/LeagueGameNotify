import settings
import data
import requests
import api_calls
import sys
import consts
import discord_bot
import utils
from periodic import PeriodicExecutor
from datetime import datetime

needsSave = False

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
    response = requests.get(url, headers={consts.API_KEY_HEADER: settings.API_KEY})
    if response.status_code == 200:
        json_data = response.json()
        participants = json_data["participants"]
        participantIDs = json_data["participantIdentities"]
        participantID = None
        participant = None
        lane = None
        totalKills = 0
        team = None
        for pid in participantIDs:
            summonerId = pid["player"]["summonerId"]
            if summonerId == summoner.SummonerDTO["id"]:
                participantID = pid["participantId"]
                break
        if participantID is None:
            print("Could not find", summoner.SummonerDTO["name"], "in participant list")
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
        kp = str((100 * (kills + assists)) // totalKills)
        win = stats["win"]
        result = "won" if win else "lost"
        msg = "GAME END: " + summoner.SummonerDTO["name"] + " " + result + " a game as " + champion + ". He went " + str(kills) + "/" + str(deaths) + "/" + str(assists) + " with a kp of " + kp + "%."

        # Rank Change
        if summoner.CurrentRank != None:
            url = api_calls.BASE_API_URL + api_calls.LEAGUE_API_URL.format(encryptedSummonerId=summoner.SummonerDTO["id"])
            response = requests.get(url, headers={consts.API_KEY_HEADER: settings.API_KEY})
            if response.status_code == 200:
                leagueEntrySet = response.json()
                rank = {}
                for entry in leagueEntrySet:
                    if (entry["queueType"] != consts.RANKED_SOLO_QUEUE_TYPE):
                        continue
                    rank["tier"] = entry["tier"]
                    rank["division"] = entry["rank"]
                    rank["lp"] = entry["leaguePoints"]
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
                    msg += "\n" + summoner.SummonerDTO["name"] + " " + result + " " + str(lpDiff) + "lp for this game. He is currently " + str(rank["tier"]) + " " + str(rank["division"]) + " " + str(rank["lp"]) + "lp."
        color = utils.ColorCodes.GREEN if win else utils.ColorCodes.RED
        discord_bot.SendMessage(msg, color)
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
        msg = "GAME START: " + summoner.SummonerDTO["name"] + " has started a ranked game as " + champion + "!"
        discord_bot.SendMessage(msg, utils.ColorCodes.YELLOW)
    else:
        print("Could not obtain participant for current game of " + summoner.SummonerDTO["name"])


def querySummonerCurrentRank(summoner):
    encryptedId = summoner.SummonerDTO["id"]
    url = api_calls.BASE_API_URL + api_calls.LEAGUE_API_URL.format(encryptedSummonerId=encryptedId)
    response = requests.get(url, headers={consts.API_KEY_HEADER: settings.API_KEY})
    if response.status_code == 200:
        leagueEntrySet = response.json()
        rank = {}
        for entry in leagueEntrySet:
            if (entry["queueType"] != consts.RANKED_SOLO_QUEUE_TYPE):
                continue
            rank["tier"] = entry["tier"]
            rank["division"] = entry["rank"]
            rank["lp"] = entry["leaguePoints"]
            break
        change = summoner.updateCurrentRank(rank)
        if change == 2:
            # Promoted to new Tier!
            discord_bot.SendMessage("PROMOTION: " + summoner.SummonerDTO["name"] + " has promoted to " + rank["tier"] + " " + rank["division"] + " !!! <3", utils.ColorCodes.GREEN)
        elif change == 1:
            # Promoted to new Division
            discord_bot.SendMessage("PROMOTION: " + summoner.SummonerDTO["name"] + " has promoted to " + rank["tier"] + " " + rank["division"] + " <3", utils.ColorCodes.GREEN)
        elif change == -1:
            # Demoted to new Division
            discord_bot.SendMessage("DEMOTION: " + summoner.SummonerDTO["name"] + " has demoted to " + rank["tier"] + " " + rank["division"] + " :(", utils.ColorCodes.RED)
        elif change == -2:
            # Demoted to new Tier
            discord_bot.SendMessage("DEMOTION: " + summoner.SummonerDTO["name"] + " has demoted to " + rank["tier"] + " " + rank["division"] + " :( :(\nCan we get an F in the chat", utils.ColorCodes.RED)
        elif change == 3:
            # Newly assigned rank
            requestDataSave()

def querySummonerCurrentGame(summoner):
    encryptedId = summoner.SummonerDTO["id"]
    url = api_calls.BASE_API_URL + api_calls.SPECTATOR_API_URL.format(encryptedSummonerId=encryptedId)
    response = requests.get(url, headers={consts.API_KEY_HEADER: settings.API_KEY})
    if response.status_code == 200:
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
    # Need to run this loop every 5 mins
    current_time = datetime.now().strftime("%d %b %Y - %H:%M:%S")
    print("Querying Data For Summoners =>", current_time)
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
            discord_bot.SendMessage("```Starting Up Bot With Refreshed Data```")
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
    FIVE_MINUTES = 5 * 60
    TWO_MINUTES = 2 * 60
    run_thread = PeriodicExecutor(TWO_MINUTES, run, summonerData)
    run_thread.run()
