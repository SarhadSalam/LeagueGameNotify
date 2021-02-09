import discord
from discord import Webhook, RequestsWebhookAdapter
from discord.ext import commands
import settings
from utils import applyColorToMsg
import data
import stream
import data

# Webhook discord message bot
def SendMessage(msg, color=None, postMsg=None):
    msgText = msg
    if postMsg is not None:
        msgText += "\n" + postMsg
    print("Sending Message: ", msg)
    if color != None:
        msg = applyColorToMsg(msg, color)
    if postMsg is not None:
        msg += "\n" + postMsg
    webhook = Webhook.from_url(settings.DISCORD_WEBHOOK, adapter=RequestsWebhookAdapter())
    webhook.send(msg)

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
    bot = commands.Bot(command_prefix='!')

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
            game_info = data.SUMMONER_DATA[summoner_name].CurrentGameInfo

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
            game_info = data.SUMMONER_DATA[summoner_name].CurrentGameInfo

            if not game_info:
                await ctx.send(f"{summoner_name} is not in game you cuck")
                return

            game_id = game_info['gameId']
            summoner_id = game_info['observers']['encryptionKey']

            await ctx.send(f"Changing stream to {summoner_name}")
            stream_handler.changeStream(game_id, summoner_id)
            await ctx.send(f"Successfully started at https://twitch.com/dilf3")

    def mentionUser(mentionId):
        return "<@!" + str(mentionId) + ">"

    bot.run(settings.DISCORD_APP_TOKEN)
    print("Discord Bot Started!")
