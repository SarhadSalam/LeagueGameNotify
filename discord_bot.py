import discord
from discord import Webhook, RequestsWebhookAdapter
import settings
from utils import applyColorToMsg

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
