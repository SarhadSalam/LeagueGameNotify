import discord
from discord.ext import commands
import discord
import image_handler

class Match(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Commands
    @commands.command()
    async def match(self, ctx, gameId):
        await ctx.send(f"Obtaining image for game ID {gameId}")

        image_handler.get_image(gameId)
        image_handler.crop_image_post_game(gameId)

        await ctx.send(f"image obtained for game ID {gameId}")

        await ctx.send(file=discord.File(f"cropped_{gameId}.png"))
        image_handler.remove_images(gameId)

# Connect cog to bot
def setup(bot):
    bot.add_cog(Match(bot))
