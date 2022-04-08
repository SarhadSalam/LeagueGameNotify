import discord
from discord import Webhook, RequestsWebhookAdapter
from discord.ext import commands
import settings
from utils import applyColorToMsg
import data
import data_updater
import os
import logging
import random

# Webhook discord message bot


def SendMessage(msg, color=None, postMsg=None, file = None):
    msgText = msg
    if postMsg is not None:
        msgText += "\n" + postMsg
    logging.info(f"Sending Message: {msgText}")
    if not settings.PROD_MODE:
        return
    if color != None:
        msg = applyColorToMsg(msg, color)
    if postMsg is not None:
        msg += "\n" + postMsg
    webhook = Webhook.from_url(
        settings.DISCORD_WEBHOOK, adapter=RequestsWebhookAdapter())
    webhook.send(msg, file = file)

# League Assistant Bot


def start_bot(parent_comm_queue):
    bot = commands.Bot(command_prefix='$', help_command=None)
    data.load()

    # Load the Cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != "helpers.py":
            bot.load_extension(f'cogs.{filename[:-3]}')

    def is_admin():
        def predicate(ctx):
            return ctx.message.author.id == settings.DISCORD_IDS["SayNoToWards"] or ctx.message.author.id == settings.DISCORD_IDS["Nashweed"] or ctx.message.author.id == settings.DISCORD_IDS["marginallyTall"]

        return commands.check(predicate)

    @bot.command()
    @is_admin()
    async def update(ctx, option=None):
        forceUpdate = False
        forceFlags = ["f", "-f", "--f", "/f"]
        versionFlags = ["v", "-v", "--v", "/v"]
        if option in versionFlags:
            currentVersion = data_updater.getCurrentDDVersion()
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
        data_updater.reloadData(refresh=True)
        parent_comm_queue.put("reloadData")
        await ctx.send("Reloaded Data")

    @bot.command()
    async def randomize(ctx, list):
        if not list:
            return await ctx.send("Send space separated list")
        
        list = list.split(" ")

        if not len(list):
            return await ctx.send("List needs to contain elements")
        

        await ctx.send(f"selected: {random.choice(list)}")
        

    @bot.event
    async def on_ready():
        await bot.change_presence(activity=discord.Game(name=settings.BOT_STATUS))

    SendMessage(msg="```$help to get help on using different commands```")
    bot.run(settings.DISCORD_APP_TOKEN)
    logging.info("Discord Bot Started!")
