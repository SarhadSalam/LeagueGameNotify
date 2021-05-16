import discord
from discord import Webhook, RequestsWebhookAdapter
from discord.ext import commands
import settings
from utils import applyColorToMsg
from utils import getSummonerRankValue
import data
import data_updater
import stream
import time
from datetime import datetime
from datetime import timedelta
import api_calls
import re
import os
import matplotlib.pyplot as plt
import random
import consts
from multiprocessing import Queue

COMMAND_TIMESTAMPS = {}

# Webhook discord message bot


def SendMessage(msg, color=None, postMsg=None):
    msgText = msg
    if postMsg is not None:
        msgText += "\n" + postMsg
    print("Sending Message: ", msgText)
    if not settings.PROD_MODE:
        return
    if color != None:
        msg = applyColorToMsg(msg, color)
    if postMsg is not None:
        msg += "\n" + postMsg
    webhook = Webhook.from_url(
        settings.DISCORD_WEBHOOK, adapter=RequestsWebhookAdapter())
    webhook.send(msg)


def mentionUser(mentionId):
    return "<@!" + str(mentionId) + ">"


def updateTimestamp(command, ctx, cooldown=None):
    current_time = time.time()
    if command not in COMMAND_TIMESTAMPS:
        COMMAND_TIMESTAMPS[command] = (current_time, ctx)
        return float('inf')
    last_call = COMMAND_TIMESTAMPS[command][0]
    if cooldown is None:
        COMMAND_TIMESTAMPS[command] = (current_time, ctx)
        return current_time - last_call
    elif (current_time - last_call) > cooldown:
        COMMAND_TIMESTAMPS[command] = (current_time, ctx)
        return True
    else:
        return False


def clearTimestamp(command):
    if command in COMMAND_TIMESTAMPS:
        del COMMAND_TIMESTAMPS[command]

# League Assistant Bot


def start_bot(parent_comm_queue):
    import discord
    from discord import Webhook, RequestsWebhookAdapter
    from discord.ext import commands
    import settings
    from utils import applyColorToMsg
    import data
    import os
    import stream

    stream_handler = stream.StreamHandler()
    bot = commands.Bot(command_prefix='$', help_command=None)
    flex_queue = []

    data.load()

    async def handleSummonerNameInput(ctx, summonerName, knownRequired=True):
        if summonerName is None:
            await ctx.send("Please input a summoner name")
            return None
        orig_name = summonerName
        summonerName = summonerName.lower()
        if (name := data.getSummonerNameFromName(summonerName)):
            summonerName = name
            orig_name = name
        status = data.isKnownSummoner(summonerName)
        if status is not True:
            if not knownRequired:
                return orig_name
            else:
                await ctx.send(status)
                return None
        else:
            return data.getSummonerName(summonerName)

    @bot.command()
    async def test(ctx):
        print("Received message:", ctx.message.content)
        print("Message Object:", ctx.message)
        print("Message Author Object:", ctx.author)
        await ctx.send("Received test message: " + ctx.message.content)

    @bot.command()
    async def mentionMe(ctx):
        mentionId = ctx.author.id
        msg = "Hello <@!" + str(mentionId) + ">!"
        await ctx.send(msg)

    @bot.command()
    async def hello(ctx):
        await ctx.send('Hello')

    @bot.command()
    async def clash(ctx):
        cooldown = 60
        if updateTimestamp("clash", ctx, cooldown):
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
                print(msg)
                await ctx.send(msg)
            else:
                clearTimestamp("clash")
                await ctx.send("Error obtaining clash info. Please try again")
        else:
            await ctx.send("Please wait " + str(cooldown) + " seconds from last successful call to use this command again")

    @bot.command()
    async def mmr(ctx, summonerName=None, option=None):
        if not (summonerName := await handleSummonerNameInput(ctx, summonerName, knownRequired=False)):
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
                    print("Error parsing summary")
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

    @bot.command()
    async def summon(ctx):
        cooldown = 1
        isReady = updateTimestamp("summon", ctx, cooldown)
        if isReady:
            skipList = ["RedHat1", "szmamjad", "TheReilGabe", "One True Tatsuya"]
            summoner = data.getRandomSummoner(skipList)
            discordMentionId = data.getDiscordIdFromSummonerName(summoner)
            if discordMentionId is None:
                await ctx.send(summoner + ", you have been summoned to play a ranked game")
            else:
                await ctx.send(mentionUser(discordMentionId) + ", " + summoner + " has been summoned to play a ranked game")

    @bot.command()
    async def rank(ctx, summonerName=None):
        if summonerName == "all" or not summonerName:
            summonerName = settings.SUMMONER_NAMES[:]
        else:
            summonerName = [summonerName]

        summoners = []
        data.loadSummonerData()
        for summoner in summonerName:
            if not (summoner := await handleSummonerNameInput(ctx, summoner)):
                continue
            summoners.append(data.getSummoner(summoner))

        summoners.sort(key=getSummonerRankValue, reverse=True)
        msg = ""
        for summoner in summoners:
            currentRank = summoner.CurrentRank
            name = summoner.getName()
            if currentRank is None:
                msg += f"{name} is unranked.\n"
                continue
            msg += f"{name} is currently {currentRank['tier']} {currentRank['division']} {str(currentRank['lp'])}lp."

            if "miniSeries" in currentRank:
                wins = str(currentRank["miniSeries"]["wins"])
                losses = str(currentRank["miniSeries"]["losses"])
                nextRank = consts.TIERS.index(currentRank['tier'])
                nextRank = consts.TIERS[nextRank+1]
                msg += f" Currently {wins}-{losses} in promos to {nextRank}."

            msg += "\n"

        await ctx.send(msg)
        return

    @bot.command()
    async def lp(ctx, summonerName=None):
        await rank(ctx, summonerName)

    @bot.command()
    async def elo(ctx, summonerName=None):
        await rank(ctx, summonerName)

    @bot.command()
    async def mastery(ctx, summonerName=None, championName=None):
        if not (summonerName := await handleSummonerNameInput(ctx, summonerName, knownRequired=False)):
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
            uri = api_calls.CHAMPION_MASTERY_CHAMP_URI.format(encryptedSummonerId=summonerId, championId=championId)
            response = api_calls.call_api(uri)
            if response and response.status_code == 200:
                masteryData = response.json()
                masteryLevel = int(masteryData["championLevel"])
                masteryPoints = int(masteryData["championPoints"])
                if masteryLevel == 5 or masteryLevel == 6:
                    tokens = int(masteryData["tokensEarned"])
                    text = "{} is mastery level {} with {} with {:,} mastery points and {} mastery {} tokens".format(summonerName, masteryLevel, championName, masteryPoints, tokens, (masteryLevel+1))
                else:
                    text = "{} is mastery level {} with {} with {:,} mastery points".format(summonerName, masteryLevel, championName, masteryPoints)
            else:
                msg = "Error obtaining mastery info for '{}' with {}".format(summonerName, championName)
                await ctx.send(msg)
                return
        else:
            # List Request
            listSize = DEFAULT_LIST_SIZE
            lvRequest = False
            if championName is not None:
                if championName.startswith("lv"):
                    lvRequest = int(championName[2:])
                    if lvRequest < 0 or lvRequest > 7:
                        msg = "Mastery Level {} is not valid".format(lvRequest)
                        await ctx.send(msg)
                        return
                else:
                    listSize = int(championName)

            uri = api_calls.CHAMPION_MASTERY_ALL_URI.format(encryptedSummonerId=summonerId)
            response = api_calls.call_api(uri)
            if response and response.status_code == 200:
                masteryList = response.json()
                if lvRequest is not False:
                    if lvRequest == 0:
                        numChampions = data.getNumChampions()
                        m0Champs = numChampions - len(masteryList)
                        text = "{} has {} mastery level {} champions:".format(summonerName, m0Champs, lvRequest)
                        mList = []
                        for masteryData in masteryList:
                            championId = int(masteryData["championId"])
                            mList.append(championId)
                        for id in data.CHAMPION_ID_TO_NAME:
                            if id not in mList:
                                text += "\n  " + data.getChampionName(id)

                        listSize = 0
                    else:
                        masteryList = list(filter(lambda x, lv=lvRequest: int(x["championLevel"]) == lv, masteryList))
                        listSize = len(masteryList)
                        if listSize > MAX_LIST_SIZE:
                            msg = "{} has {} champions at mastery level {}. Only showing top {} champions".format(summonerName, listSize, lvRequest, MAX_LIST_SIZE)
                            listSize = MAX_LIST_SIZE
                            text = "{}'s top {} mastery level {} champions:".format(summonerName, listSize, lvRequest)
                            await ctx.send(msg)
                        else:
                            text = "{} has {} mastery level {} champions:".format(summonerName, listSize, lvRequest)
                else:
                    if listSize > MAX_LIST_SIZE:
                        msg = "Requested larger than max list size of {0}. Only showing top {0} champions".format(MAX_LIST_SIZE)
                        listSize = MAX_LIST_SIZE
                        await ctx.send(msg)
                    if listSize > len(masteryList):
                        msg = "{} only has mastery on {} champions".format(summonerName, len(masteryList))
                        listSize = len(masteryList)
                        await ctx.send(msg)
                    text = "{}'s top {} champions:".format(summonerName, listSize)
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
                        line = "  {} at mastery level {} with {:,} mastery points and {} mastery {} tokens".format(champName, masteryLevel, masteryPoints, tokens, (masteryLevel+1))
                    else:
                        line = "  {} at mastery level {} with {:,} mastery points".format(champName, masteryLevel, masteryPoints)
                    text += line
            else:
                msg = "Error obtaining mastery info for '{}'".format(summonerName)
                await ctx.send(msg)
                return

        await ctx.send(text)
        return


    @bot.command()
    async def notify(ctx, action=None, summonerName=None):
        if not action:
            await ctx.send("Need an action and summoner name")
            return

        mentionId = ctx.author.id
        data.loadNotifyData()

        if action == "list":
            subs = data.getNotifyList(mentionId)
            if subs and len(subs) > 0:
                msg = mentionUser(mentionId) + \
                    " is simping for the following summoners:"
                for summoner in subs:
                    msg += "\n" + summoner
            else:
                msg = mentionUser(mentionId) + \
                    " is currently not simping for anyone."
            await ctx.send(msg)
            return

        if action == "add":
            if summonerName == "/all":
                data.addToAllNotifyList(mentionId)
                await ctx.send("Added " + mentionUser(mentionId) + " to all notify lists.")
                return
            elif not (summonerName := await handleSummonerNameInput(ctx, summonerName)):
                return
            status = data.addToNotifyList(summonerName, mentionId)
            if status is True:
                await ctx.send(mentionUser(mentionId) + " has been added to the notify list for " + summonerName)
            else:
                await ctx.send("Error adding to notify list.\nReason: " + status)
            return

        if action == "remove":
            if summonerName == "/all":
                data.removeFromAllNotifyList(mentionId)
                await ctx.send("Removed " + mentionUser(mentionId) + " from all notify lists.")
                return
            elif not (summonerName := await handleSummonerNameInput(ctx, summonerName)):
                return
            status = data.removeFromNotifyList(summonerName, mentionId)
            if status is True:
                await ctx.send(mentionUser(mentionId) + " has been removed from the notify list for " + summonerName)
            else:
                await ctx.send("Error removing from notify list.\nReason: " + status)
            return

        await ctx.send("Invalid action '" + action + "'")
        return

    @bot.command()
    async def stream(ctx, state=None, summoner_name=None):
        await ctx.send("Sorry, stream capability has not been setup yet. You can blame Naveed for being lazy.")
        return

        if not (summonerName := await handleSummonerNameInput(ctx, summonerName)):
            return

        if not state:
            await ctx.send("Need both state and summoner name")
            return

        if state == "stop":
            if not stream_handler.started_streaming:
                await ctx.send("No stream is running. Can't stop")
                return

            stream_handler.stopStreaming()
            await ctx.send("Stopped streaming")
            return

        if state in ["start", "change"] and not summoner_name:
            await ctx.send("Summoner name needs to be provided")
            return

        if summoner_name not in settings.SUMMONER_NAMES:
            await ctx.send("Summoner needs to be a preapproved summoner")
            return

        if state == "start":
            if stream_handler.started_streaming:
                await ctx.send("Stream already running. change streams!")
                return

            data.loadSummonerData()
            game_info = data.getSummoner(summoner_name).CurrentGameInfo

            if not game_info:
                await ctx.send(f"{summoner_name} is not in game you cuck")
                return

            game_id = game_info['gameId']
            summoner_id = game_info['observers']['encryptionKey']

            await ctx.send(f"Starting stream for {summoner_name}")
            stream_handler.tryStreaming(game_id, summoner_id)
            await ctx.send(f"Successfully started at https://twitch.com/dilf3")

        if state == "change":
            if not stream_handler.started_streaming:
                await ctx.send("Stream not running. start stream!")
                return

            data.loadSummonerData()
            game_info = data.getSummoner(summoner_name).CurrentGameInfo

            if not game_info:
                await ctx.send(f"{summoner_name} is not in game you cuck")
                return

            game_id = game_info['gameId']
            summoner_id = game_info['observers']['encryptionKey']

            await ctx.send(f"Changing stream to {summoner_name}")
            stream_handler.changeStream(game_id, summoner_id)
            await ctx.send(f"Successfully started at https://twitch.com/dilf3")

    @bot.command()
    async def flex(ctx, action='tag', summoner1=None, summoner2=None, summoner3=None, summoner4=None, summoner5=None):
        def generateTag(ids):
            need_people = 5 - len(flex_queue)
            plural_person = "people" if need_people > 1 else "person"
            msg = f"Come for 5sum. We need {need_people} more {plural_person}. "
            for (k, v) in ids.items():
                if k != "RedHat1":
                    msg += f"{mentionUser(v)} "
            return msg

        if action == 'list':
            await ctx.send(f"People in lobby ({len(flex_queue)}): {flex_queue}")
            return

        if action == 'tag':  # tag all
            if summoner1 == 'all':
                msg = generateTag(settings.DISCORD_IDS)
            else:
                tags = {}
                for (k, v) in settings.DISCORD_IDS.items():
                    if k not in flex_queue:
                        tags[k] = v

                if len(flex_queue) < 5:
                    msg = f"""People in lobby: {flex_queue}\n{generateTag(tags)}"""
                else:
                    msg = f"""People in lobby: {flex_queue}\n Not tagging anyone new, as lobby is full."""

            await ctx.send(msg)
            return

        if action == 'clear':
            flex_queue.clear()
            await ctx.send("Cleared queue!")
            return

        if not summoner1:
            await ctx.send("Need a summoner name!")
            return

        summoners = [summoner1, summoner2, summoner3, summoner4, summoner5]

        for summoner in summoners:
            if not summoner:
                continue

            if summoner == "me":
                if ctx.message.author.id not in settings.SUMMONER_BY_DISCORD_IDS:
                    await ctx.send(f"{ctx.message.author.name} is not one of the bois.")
                    continue

                summoner = settings.SUMMONER_BY_DISCORD_IDS[ctx.author.id]

            if not await handleSummonerNameInput(ctx, summoner):
                return

            summoner = summoner.lower()

            if action == 'add':
                if len(flex_queue) >= 5:
                    await ctx.send(f"Flex lobby is full, please clear lobby first.")
                    return
                if summoner not in flex_queue:
                    flex_queue.append(summoner)
                    await ctx.send(f"Added {summoner} to lobby.")
                else:
                    await ctx.send(f"{summoner} is already in lobby. Not added to lobby.")
            elif action == 'remove':
                if summoner not in flex_queue:
                    await ctx.send(f"{summoner} is not in the lobby. Can't remove")
                else:
                    flex_queue.remove(summoner)
                    await ctx.send(f"Removed {summoner} from lobby.")

    @bot.command()
    async def help(ctx, command=None):
        help_strings = {
            'test': """No options supported. Call by itself.""",
            'mentionMe': """No options supported. Call by itself.""",
            'hello': """No options supported. Call by itself.""",
            'clash': """No options supported. Call by itself.""",
            'mmr': """Availaible Commands:
                        - $mmr $SUMMONER_NAME  =>  Get MMR for summoner
                        - $mmr $SUMMONER_NAME -history  =>  Get MMR with graph for summoner""",
            'summon': """No options supported. Call by itself.""",
            'rank': """Availaible Commands:
                        - $rank $SUMMONER_NAME  =>  Get rank of summoner
                        - $rank  =>  Get rank of all the boiis, ordered highest to lowest
                        """,
            'notify': """
                        Available Commands:
                            - $notify add $SUMMONER_NAME  =>  Subscribe to summoner's notify list
                            - $notify remove $SUMMONER_NAME  =>  Unsubscribe from summoner's notify list
                            - $notify list  =>  List your current subscriptions

                        Use /all in place of $SUMMONER_NAME to sub/unsub from all summoners
                """,
            #stream': """
            #        Available Commands:
            #        - $stream start $SUMMONER_NAME => Start a stream for the summoner
            #        - $stream change $SUMMONER_NAME => Change a stream for a summoner to a different game
            #        - $stream stop => Stop streaming
            #        - $stream help => Start streaming
            #    """,
            'flex': """
                        Available Commands:
                        - $flex tag => Tag everyone not in the lobby
                        - $flex tag all => Ignore lobby members and tag everyone
                        - $flex clear => Clear out the lobby
                        - $flex add $SUMMONER_NAME1* $SUMMONER_NAME2?* $SUMMONER_NAME3?* $SUMMONER_NAME4?* $SUMMONER_NAME5?* => Add summoner's to the lobby list. Note only 1 summoner is required.
                        - $flex remove $SUMMONER_NAME1* $SUMMONER_NAME2?* $SUMMONER_NAME3?* $SUMMONER_NAME4?* $SUMMONER_NAME5?* => Remove summoner's from the lobby. Note only 1 summoner is required.
                        - $flex list => Shows who is in the lobby
                        - $flex help => Shows this help text
                        ? shows optional parameters.
                        * represents commands that can be filled with "me" and it will add your user object
                """,
            'logs': """
                        Available Commands:
                            - $logs -error  =>  Dump error log (Default option if no option applied)
                            - $logs -std  =>  Dump stdout
                """,
            'bois': """No options supported. Call by itself.""",
            'mastery': """
                        Available Commands:
                            - $mastery $SUMMONER_NAME $ARGUMENT  =>  Get mastery points for summoner

                        Possible $ARGUMENTs:
                            - $CHAMPION_NAME  =>  Get mastery for specific champion
                            - $X  =>  Get top X champions by mastery points (max 25)
                            - lv$X  =>  Get all (max top 25) mastery level X champions

                        examples:
                            $mastery sardaddy garen  =>  Garen mastery for sardaddy
                            $mastery nashweed 8  =>  nashweed's top 8 champions
                            $mastery marginallyTall lv7  =>  marginallyTall's mastery level 7 champions
                """,

        }

        default_string = """Availaible commands:
        01. (debug) $test => Send a test message containing some debug information about the message.
        02. (debug) $mentionMe => Mention yourself
        03. (debug) $hello => Send a hello message
        04. $clash => Get clash dates
        05. $mmr => Get your approximate MMR
        06. $summon => Summon a random summoner to play ranked
        07. $rank => Get a summoners rank
        08. $notify => Get tagged when a summoner is in game
        09. $flex => Tag people not in lobby to join for 5sum
        10. $logs => Dump debug logs
        11. $bois => List known summoners
        12. $mastery => Get mastery information for a summoner's champions
        13. $help => This help list

        Run "$help $COMMAND_NAME" to get information on how to run that command.
        """

        if not command:
            await ctx.send(default_string)
            return

        if command and command not in help_strings:
            await ctx.send("Wrong command name.")
            await ctx.send(default_string)
            return

        await ctx.send(help_strings[command])

    def is_admin():
        def predicate(ctx):
            return ctx.message.author.id == settings.DISCORD_IDS["sardaddy"] or ctx.message.author.id == settings.DISCORD_IDS["Nashweed"] or ctx.message.author.id == settings.DISCORD_IDS["marginallyTall"]

        return commands.check(predicate)

    @bot.command()
    @is_admin()
    async def start(ctx):
        os.system("pm2 restart LeagueDiscordBot")

    @bot.command()
    @is_admin()
    async def stop(ctx):
        os.system("pm2 stop LeagueDiscordBot")

    @bot.command()
    @is_admin()
    async def update(ctx, option=None):
        forceUpdate = False
        forceFlags = ["f", "-f", "--f", "/f"]
        versionFlags = ["v", "-v", "--v", "/v"]
        if option in versionFlags:
            currentVersion = data_updater.getCurrentVersion()
            if currentVersion is not None:
                await ctx.send(f"Current DD Version: {currentVersion}")
            else:
                await ctx.send("Error obtaining current DD Version")
            return
        if option in forceFlags:
            forceUpdate = True
        elif option is not None:
            await ctx.send(f"Incorrect flag: '{option}'")
            return
        success, status = data_updater.updateDDVersionFiles(forceUpdate)
        if success:
            parent_comm_queue.put("updateData")
        await ctx.send(status)

    @bot.command()
    @is_admin()
    async def reload(ctx, option=None):
        summonerReloadFlags = ["s", "-s", "--s", "summoner", "-summoner", "--summoner"]
        championReloadFlags = ["c", "-c", "--c", "champion", "-champion", "--champion"]
        if option in summonerReloadFlags:
            data_updater.reloadSummonerData(refresh=True)
            parent_comm_queue.put(("reloadData", ("s",)))
            await ctx.send("Reloaded Summoner Data")
            return
        if option in championReloadFlags:
            data_updater.reloadChampionData()
            parent_comm_queue.put(("reloadData", ("c",)))
            await ctx.send("Reloaded Champion Data")
            return
        if option is not None:
            await ctx.send(f"Incorrect flag: '{option}'")
            return
        data_updater.reloadData(refresh=True)
        parent_comm_queue.put("reloadData")
        await ctx.send("Reloaded All Data")

    @bot.command()
    @is_admin()
    async def logs(ctx, type="-error"):
        file_name = None
        if type == "-error":
            file_name = "/root/.pm2/logs/LeagueDiscordBot-error-0.log"
        elif type == "-std":
            file_name = "/root/.pm2/logs/LeagueDiscordBot-out-0.log"
        else:
            await ctx.send(f"Log file {type} not found. Please use -error or -std")
            return

        t = time.ctime(os.path.getmtime(file_name))
        await ctx.send(f"Log file last updated on: {t}", file=discord.File(file_name))

    @bot.command()
    async def bois(ctx):
        names_nicknames = {}

        for k, v in settings.NAME_IDS.items():
            if v in names_nicknames:
                names_nicknames[v].append(k)
            else:
                names_nicknames[v] = [k]

        await ctx.send(f"{names_nicknames}")

    @bot.event
    async def on_ready():
        await bot.change_presence(activity=discord.Game(name="with Lucky's Mom"))

    # @bot.event
    # async def on_voice_state_update(member, before, after):
    #     channel = bot.get_channel(832335754570498119)
    #     # someone joined the voice channel
    #     if after is not None:
    #         summoner_name = settings.SUMMONER_BY_DISCORD_IDS[member.id]

    #         summoner_to_nickname =dict((v,k) for k,v in settings.NAME_IDS.items())

    #         name = ""
    #         if summoner_to_nickname[summoner_name]:
    #             name = summoner_to_nickname[summoner_name]
    #         else:
    #             name = member.nick if member.nick else member.name

    #         greeting = settings.GREETINGS[random.randrange(0, len(settings.GREETINGS) + 1)]
    #         greeting = greeting.replace("$name", f"{name}")

    #         await channel.send(greeting)

    SendMessage(msg="```$help to get help on using different commands```")
    bot.run(settings.DISCORD_APP_TOKEN)
    print("Discord Bot Started!")
