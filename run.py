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
import urllib
from cogs.helpers import HelperFunctions
import logging
import threading
import health
import image_handler
import discord

needsSave = False
BOT_COMM_QUEUE = Queue()
helper = HelperFunctions()
failed_game_end_ids = set()


def requestDataSave():
    global needsSave
    needsSave = True


def saveSummonerData():
    global needsSave
    needsSave = False
    logging.info("Saving new summoner data")
    data.saveSummonerData()


def notifyGameEnd(summoner, gameId, previouslyFailedCount=0):
    if gameId is None:
        return

    url = api_calls.BASE_API_URL_V5 + \
        api_calls.MATCH_API_URL.format(matchId=gameId)
    response = call_api(url)
    if response and response.status_code == 200:
        json_data = response.json()
        participants = json_data["participants"]
        participantID = None
        participant = None
        lane = None
        totalKills = 0
        totalDamage = 0
        damageRank = 1
        team = None

        for p in participants:
            if p["summonerId"] == summoner.SummonerDTO["id"]:
                summonerId = p["summonerId"]
                participantID = p["participantId"]
                participant = p
                team = p["teamId"]
                break
        if participantID is None:
            logging.info(
                f"Could not find {summoner.SummonerDTO['name']} in participant list")

        # participant now has the summoner stats for the game

        # personal stats
        champion = data.getChampionName(participant["championId"])
        stats = participant["stats"]
        kills = int(stats["kills"])
        deaths = int(stats["deaths"])
        assists = int(stats["assists"])
        damage = int(stats["totalDamageDealtToChampions"])

        # cumulative team stats
        for p in participants:
            if p["teamId"] == team:
                totalKills += int(p["stats"]["kills"])
                p_dmg = int(p["stats"]["totalDamageDealtToChampions"])
                totalDamage += p_dmg
                if p["participantId"] != participantID and p_dmg > damage:
                    damageRank += 1

        lane = participant["timeline"]["lane"]

        # kp
        if totalKills > 0:
            kp = str((100 * (kills + assists)) // totalKills)
        else:
            kp = "0"

        # damage share
        if totalDamage > 0:
            damageShare = str((100 * damage) // totalDamage)
        else:
            damageShare = 0
            damageRank = 5

        # Game End Stats Message
        win = stats["win"]
        result = "won" if win else "lost"
        dmg_text = ""
        if damageRank == 1:
            dmg_text = "highest in the team"
        elif damageRank == 5:
            dmg_text = "lowest in the team"
        else:
            pos = "2nd" if damageRank == 2 else "3rd" if damageRank == 3 else "4th" if damageRank == 4 else "NaN"
            dmg_text = pos + " highest in the team"
        msg = "GAME END: {} {} a game as {}. He went {}/{}/{} with a kp of {}% and dealt {:,} damage ({}% damage share, {})"
        msg = msg.format(summoner.getName(), result, champion, kills,
                         deaths, assists, kp, damage, damageShare, dmg_text)

        # Rank Change
        if summoner.CurrentRank != None:
            promos = None
            url = api_calls.BASE_API_URL + \
                api_calls.LEAGUE_API_URL.format(
                    encryptedSummonerId=summoner.SummonerDTO["id"])
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
                        msg += "\n" + summoner.SummonerDTO["name"] + " " + result + " " + str(lpDiff) + "lp for this game. He is currently " + str(
                            rank["tier"]) + " " + str(rank["division"]) + " " + str(rank["lp"]) + "lp."
                    if promos is not None:
                        wins = str(promos["wins"])
                        losses = str(promos["losses"])
                        nextRankIndex = consts.TIERS.index(
                            summoner.CurrentRank["tier"]) + 1
                        nextRank = consts.TIERS[nextRankIndex]
                        msg += "\n" + summoner.SummonerDTO["name"] + " is currently " + \
                            wins + "-" + losses + " in promos to " + nextRank + "."

        # Match History Uri:
        postMsg = None

        matchUrls = [
            ("Mobalytics", api_calls.MOBALYTICS_MATCH_URL.format(
                summonerName=urllib.parse.quote(summoner.SummonerDTO["name"]), gameId=gameId)),
            ("LeagueOfGraphs", api_calls.LOG_MATCH_URL.format(gameId=gameId))
        ]
        urlListText = " | ".join(["[{text}](<{url}>)".format(
            text=item[0], url=item[1]) for item in matchUrls])
        postMsg = "View Game Details Here: " + urlListText

        color = utils.ColorCodes.GREEN if win else utils.ColorCodes.RED
        discord_bot.SendMessage(msg, color, postMsg)
    else:
        msg = "Try #" + str(previouslyFailedCount + 1) + ": Error Obtaining Game Info for match# " + \
            str(gameId) + " (Game by " + summoner.SummonerDTO["name"] + ")"

        if previouslyFailedCount > 3:
            msg += " Stopping trying, match query failed. Look into it."
        else:
            failed_game_end_ids.add(
                (gameId, summoner, previouslyFailedCount + 1))

        logging.info(response)  # print response to see what is going on
        logging.info(msg)

        image_handler.get_image(gameId)
        image_handler.crop_image_post_game(gameId)

        discord_bot.SendMessage(
            msg, file=discord.File(f"cropped_{gameId}.png"))

        image_handler.remove_images(gameId)


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
        notifyList = data.getNotifyListForSummoner(
            summoner.SummonerDTO["name"])
        postMsg = None
        if notifyList and len(notifyList) > 0:
            postMsg = "Notifying Simps:"
            for user in notifyList:
                postMsg += " " + helper.mentionUser(user)
        discord_bot.SendMessage(msg, utils.ColorCodes.YELLOW, postMsg)
    else:
        logging.info(
            f"Could not obtain participant for current game of {summoner.SummonerDTO['name']}")


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
            logging.info(f"Invalid Request: {request}")
            continue

        if hasattr(bot_comms, method):
            try:
                getattr(bot_comms, method)(*args)
            except Exception as e:
                logging.info(f"Could not execute method '{method}'")
                logging.info(f"Reason:, {e}")
        else:
            logging.info(f"Invalid method: {method}")

    # Update failed games from previous iteration
    while failed_game_end_ids:
        gameId, summoner, previouslyFailedCount = failed_game_end_ids.pop()
        notifyGameEnd(summoner, gameId, previouslyFailedCount + 1)

    current_time = datetime.now().strftime("%d %b %Y - %H:%M:%S")
    logging.info(f"Querying Data For Summoners => {current_time}")
    for summonerName in summonerData:
        summoner = summonerData[summonerName]
        encryptedId = summoner.SummonerDTO["id"]
        gameUrl = api_calls.BASE_API_URL + \
            api_calls.SPECTATOR_API_URL.format(encryptedSummonerId=encryptedId)
        rankUrl = api_calls.BASE_API_URL + \
            api_calls.LEAGUE_API_URL.format(encryptedSummonerId=encryptedId)
        gameResponse = call_api(gameUrl)
        rankResponse = call_api(rankUrl)
        updateSummonerCurrentGame(summoner, gameResponse)
        updateSummonerCurrentRank(summoner, rankResponse)

    if needsSave:
        saveSummonerData()

    logging.info("Query Complete.")
    # Repeat every 5 mins upto here


def sysExit(signal, frame):
    discord_bot.SendMessage("```Bot is going to sleep.```")
    bot_process.terminate()
    sys.exit(0)


def printHelp():
    print("The following arguments are accepted:")
    print("  --refresh, --r: Refresh Summoner Data Before Running")
    print()


def configure_logger():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Log to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)  # Keep at info
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Log to file - ALL Debug Info - Disable Files too large
    # handler = logging.FileHandler(
    #    filename='debug.log', mode='a', encoding='utf-8')
    # handler.setLevel(logging.DEBUG)
    # formatter = logging.Formatter(
    #    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # handler.setFormatter(formatter)
    # root_logger.addHandler(handler)

    # Log to file - Only Info Info (this is more useful tbh, the other one shows)
    # information for other libraries too which might not be the most helpful
    handler = logging.FileHandler(
        filename='info.log', mode='a', encoding='utf-8')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sysExit)
    configure_logger()

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
        logging.info(
            "No summoner data file found. Refreshing summoner data to generate data")
        summonerData = data.refreshSummonerData()
    data.loadChampionData()
    data.loadNotifyData()
    FIVE_MINUTES = 5 * 60
    TWO_MINUTES = 2 * 60

    # Create a health check executor
    # Offset running by 10ish seconds
    health_check_executor = PeriodicExecutor(
        TWO_MINUTES + 10, health.run_health_check)
    health_check_thread = threading.Thread(target=health_check_executor.run)
    health_check_thread.setDaemon(True)
    health_check_thread.setName(consts.HEALTH_CHECK_THREAD_NAME)

    # Create a game checker executor
    game_checker_exectuor = PeriodicExecutor(TWO_MINUTES, run, summonerData)
    game_checker_thread = threading.Thread(target=game_checker_exectuor.run)
    game_checker_thread.setDaemon(True)
    game_checker_thread.setName(consts.GAME_CHECK_THREAD_NAME)

    # Start Threads
    game_checker_thread.start()
    health_check_thread.start()

    discord_bot.SendMessage("```Bot is now awake and ready to report games```")
