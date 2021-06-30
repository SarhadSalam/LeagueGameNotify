import threading
import consts
import discord_bot
import logging
from datetime import datetime, timedelta
from cogs.helpers import HelperFunctions
import data
import utils

already_reported = False
helper = HelperFunctions()


def run_health_check():
    global already_reported
    all_threads = []
    for t in threading.enumerate():
        all_threads.append(t.getName())

    if consts.GAME_CHECK_THREAD_NAME not in all_threads:
        if not already_reported:
            msg = f"{consts.GAME_CHECK_THREAD_NAME} has stopped running. Games are not being reported."
            logging.error(msg)
            discord_bot.SendMessage(
                f"{msg} {helper.mentionUser(data.getDiscordIdFromSummonerName('sardaddy'))} {helper.mentionUser(data.getDiscordIdFromSummonerName('Nashweed'))}", utils.ColorCodes().RED)
            already_reported = True
