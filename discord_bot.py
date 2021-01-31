import discord
from discord import Webhook, RequestsWebhookAdapter
import settings

def SendMessage(msg, color=None):
    print("Sending Message: ", msg)
    if color != None:
        msg = "```" + color + "\n" + msg + "\n```"
    webhook = Webhook.from_url(settings.DISCORD_WEBHOOK, adapter=RequestsWebhookAdapter())
    webhook.send(msg)
