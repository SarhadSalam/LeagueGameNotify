import discord
from discord import Webhook, RequestsWebhookAdapter
import settings

def SendMessage(msg):
    webhook = Webhook.from_url(settings.DISCORD_WEBHOOK, adapter=RequestsWebhookAdapter())
    webhook.send(msg)
    print("Sent Message: ", msg)
