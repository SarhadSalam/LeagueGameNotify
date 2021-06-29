import discord
from discord.ext import commands
import data
import stream

class Stream(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stream_handler = stream.StreamHandler()

    # Commands
    @commands.command()
    async def stream(self, ctx, state=None, summoner_name=None):
        await ctx.send("Sorry, stream capability has not been setup yet. You can blame Naveed for being lazy.")
        return

        if not (summonerName := await handleSummonerNameInput(ctx, summonerName)):
            return

        if not state:
            await ctx.send("Need both state and summoner name")
            return

        if state == "stop":
            if not self.stream_handler.started_streaming:
                await ctx.send("No stream is running. Can't stop")
                return

            self.stream_handler.stopStreaming()
            await ctx.send("Stopped streaming")
            return

        if state in ["start", "change"] and not summoner_name:
            await ctx.send("Summoner name needs to be provided")
            return

        if summoner_name not in settings.SUMMONER_NAMES:
            await ctx.send("Summoner needs to be a preapproved summoner")
            return

        if state == "start":
            if self.stream_handler.started_streaming:
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
            self.stream_handler.tryStreaming(game_id, summoner_id)
            await ctx.send(f"Successfully started at https://twitch.com/dilf3")

        if state == "change":
            if not self.stream_handler.started_streaming:
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
            self.stream_handler.changeStream(game_id, summoner_id)
            await ctx.send(f"Successfully started at https://twitch.com/dilf3")

# Connect cog to bot
def setup(bot):
    bot.add_cog(Stream(bot))
