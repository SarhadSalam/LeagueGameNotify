import discord_bot
import data_updater

def updateData():
    _, status = data_updater.updateDDVersionFiles(True)
    discord_bot.SendMessage(status)

def reloadData(flag=None):
    if flag == "s":
        data_updater.reloadSummonerData()
        discord_bot.SendMessage("Reloaded Summoner Data")
    elif flag == "c":
        data_updater.reloadChampionData()
        discord_bot.SendMessage("Reloaded Champion Data")
    else:
        data_updater.reloadSummonerData()
        data_updater.reloadChampionData()
        discord_bot.SendMessage("Reloaded All Data")
