import data
import time
import settings

class HelperFunctions():
    def __init__(self):
        self.command_timestamps= {}

    def is_admin(self, ctx):
        #return ctx.message.author.id == settings.DISCORD_IDS["sardaddy"] or ctx.message.author.id == settings.DISCORD_IDS["Nashweed"] or ctx.message.author.id == settings.DISCORD_IDS["marginallyTall"]
        return ctx.message.author.id in settings.ADMINS

    def mentionUser(self, mentionId):
        return "<@!" + str(mentionId) + ">"

    def clear_timestamp(self, command):
        if command in self.command_timestamps:
            del self.command_timestamps[command]

    def update_timestamp(self, command, ctx, cooldown=None):
        current_time = time.time()
        if command not in self.command_timestamps:
            self.command_timestamps[command] = (current_time, ctx)
            return float('inf')
        last_call = self.command_timestamps[command][0]
        if cooldown is None:
            self.command_timestamps[command] = (current_time, ctx)
            return current_time - last_call
        elif (current_time - last_call) > cooldown:
            self.command_timestamps[command] = (current_time, ctx)
            return True
        else:
            return False

    async def handleSummonerNameInput(self, ctx, summonerName, knownRequired=True):
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
