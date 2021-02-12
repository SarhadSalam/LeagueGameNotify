import discord
from discord import Webhook, RequestsWebhookAdapter
from discord.ext import commands
import settings
from utils import applyColorToMsg
import data
import stream
import time
from datetime import datetime
from datetime import timedelta
import api_calls
import re

COMMAND_TIMESTAMPS = {}

# Webhook discord message bot
def SendMessage(msg, color=None, postMsg=None):
    msgText = msg
    if postMsg is not None:
        msgText += "\n" + postMsg
    print("Sending Message: ", msgText)
    if color != None:
        msg = applyColorToMsg(msg, color)
    if postMsg is not None:
        msg += "\n" + postMsg
    webhook = Webhook.from_url(settings.DISCORD_WEBHOOK, adapter=RequestsWebhookAdapter())
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
def start_bot():
    import discord
    from discord import Webhook, RequestsWebhookAdapter
    from discord.ext import commands
    import settings
    from utils import applyColorToMsg
    import data
    import stream

    stream_handler = stream.StreamHandler()
    bot = commands.Bot(command_prefix='$')

    data.load()

    async def handleSummonerNameInput(ctx, summonerName):
        summonerName = summonerName.lower()
        status = data.isKnownSummoner(summonerName)
        if status is not True:
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
                clash_data = sorted(clash_data, key = lambda i: i["schedule"][0]["registrationTime"])
                msg = "Current Clash Dates:"
                for clash in clash_data:
                    ts = int(clash["schedule"][0]["registrationTime"]) // 1000
                    date = (datetime.utcfromtimestamp(ts) - timedelta(hours=5)).strftime('%d %b %Y at %I:%M %p')
                    name = clash["nameKey"].capitalize() + " Cup " + clash["nameKeySecondary"].capitalize().replace("_", " ")
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
        if not (summonerName := await handleSummonerNameInput(ctx, summonerName)):
            return
        uri = api_calls.MMR_URI.format(summonerName=summonerName)
        response = api_calls.call_api(uri)
        if response and response.status_code == 200:
            history = option is not None and option.lower() == "-history"
            mmr_data = response.json()
            msg = summonerName + "'s MMR:\n  Ranked: "
            avg = mmr_data["ranked"]["avg"]
            if not avg:
                msg += "N/A."
            else:
                err = mmr_data["ranked"]["err"]
                ts = int(mmr_data["ranked"]["timestamp"])
                date = (datetime.utcfromtimestamp(ts) - timedelta(hours=5)).strftime('%d %b %Y at %I:%M %p')
                msg += str(avg) + " +/- " + str(err) + " (Last Updated " + date + ")"
                try:
                    summaryText = mmr_data["ranked"]["summary"]
                    pattern = "(.+)\<b\>(.+)\<\/b\>.*\<\/span>(.*)"
                    match = re.search(pattern, summaryText)
                    brief = match.group(1) + match.group(2)
                    details = match.group(3).replace("<b>", "").replace("</b>", "")
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
                        for entry in timeline:
                            val = entry["avg"]
                            if val:
                                msg += str(val) + " -> "
                        msg += str(avg)
            msg += "\n  Gayram: "
            avg = mmr_data["ARAM"]["avg"]
            if not avg:
                msg += "N/A."
            else:
                err = mmr_data["ARAM"]["err"]
                date = (datetime.utcfromtimestamp(ts) - timedelta(hours=5)).strftime('%d %b %Y at %I:%M %p')
                msg += str(avg) + " +/- " + str(err) + " (Last Updated " + date + ")"
                if history:
                    msg += "\n    History: "
                    timeline = mmr_data["ARAM"]["historical"]
                    if len(timeline) == 0:
                        msg += "Not Enough Solo Games For History"
                    else:
                        for entry in timeline:
                            val = entry["avg"]
                            if val:
                                msg += str(val) + " -> "
                        msg += str(avg)
            await ctx.send(msg)
        else:
            await ctx.send("Failed to obtain mmr data for " + summonerName + ".")

    @bot.command()
    async def summon(ctx):
        cooldown = 5
        isReady = updateTimestamp("summon", ctx, cooldown)
        if isReady:
            summoner = data.getRandomSummoner()
            discordMentionId = data.getDiscordIdFromSummonerName(summoner)
            if discordMentionId is None:
                await ctx.send(summoner + ", you have been summoned to play a ranked game")
            else:
                await ctx.send(mentionUser(discordMentionId) + ", " + summoner + " has been summoned to play a ranked game")

    @bot.command()
    async def rank(ctx, summonerName=None):
        if not (summonerName := await handleSummonerNameInput(ctx, summonerName)):
            return
        data.loadSummonerData()
        currentRank = data.getSummoner(summonerName).CurrentRank
        if currentRank is None:
            await ctx.send(summonerName + " is unranked.")
            return
        msg = summonerName + " is currently " + currentRank["tier"] + " " + currentRank["division"] + " " + str(currentRank["lp"]) + "lp."
        if "miniSeries" in currentRank:
            wins = str(currentRank["miniSeries"]["wins"])
            loss = str(CurrentRank["miniSeries"]["losses"])
            msg += "\nHe is " + wins + "-" + losses + " in promos."
        await ctx.send(msg)
        return

    @bot.command()
    async def lp(ctx, summonerName=None):
        await rank(ctx, summonerName)

    @bot.command()
    async def elo(ctx, summonerName=None):
        await rank(ctx, summonerName)

    @bot.command()
    async def notify(ctx, action=None, summonerName=None):
        if not action:
            await ctx.send("Need an action and summoner name")
            return

        if action == "help":
            doc_string = """
                Available Commands:
                - !notify add $SUMMONER_NAME  =>  Subscribe to summoner's notify list
                - !notify remove $SUMMONER_NAME  =>  Unsubscribe from summoner's notify list
                - !notify list  =>  List your current subscriptions
                - !notify help  =>  Shows this help text

                Use /all in place of $SUMMONER_NAME to sub/unsub from all summoners
            """
            await ctx.send(doc_string)
            return

        mentionId = ctx.author.id
        data.loadNotifyData()

        if action == "list":
            subs = data.getNotifyList(mentionId)
            if subs and len(subs) > 0:
                msg = mentionUser(mentionId) + " is simping for the following summoners:"
                for summoner in subs:
                    msg += "\n" + summoner
            else:
                msg = mentionUser(mentionId) + " is currently not simping for anyone."
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

        if state == "help":
            doc_string = """
                Available Commands:
                - !stream start $SUMMONER_NAME
                - !stream change $SUMMONER_NAME
                - !stream stop
                - !stream help
            """
            await ctx.send(doc_string)

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

    bot.run(settings.DISCORD_APP_TOKEN)
    print("Discord Bot Started!")
