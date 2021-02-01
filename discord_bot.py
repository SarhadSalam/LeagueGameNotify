import discord
from discord import Webhook, RequestsWebhookAdapter
import settings
from utils import applyColorToMsg

def SendMessage(msg, color=None):
    print("Sending Message: ", msg)
    if color != None:
        msg = applyColorToMsg(msg, color)
    webhook = Webhook.from_url(settings.DISCORD_WEBHOOK, adapter=RequestsWebhookAdapter())
    webhook.send(msg)
