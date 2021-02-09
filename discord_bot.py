import discord
from discord import Webhook, RequestsWebhookAdapter
from discord.ext import commands
import settings
from utils import applyColorToMsg
import data
import stream

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
    async def hello(ctx):
        await ctx.send('Hello')

    @bot.command()
    async def stream(ctx, state=None, summoner_name=None):
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


    bot.run(settings.DISCORD_APP_TOKEN)
    print("Discord Bot Started!")
