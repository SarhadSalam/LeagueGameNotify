import discord
from discord.ext import commands
import os
from .helpers import HelperFunctions

class File(commands.Cog, HelperFunctions):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def cog_check(self, ctx):
        return self.is_admin(ctx)

    # Commands
    @commands.command()
    async def file(self, ctx, action=None, arg=None):
        if action is None:
            await ctx.send("Please input action type\n  Actions available: get, add, delete, replace, list")
            return

        if action.lower() == "get":
            # get file
            if arg is None:
                await ctx.send("Please input file to receive")
                return
            filename = arg
            if not os.path.isfile(filename):
                await ctx.send(f"Could not find file '{filename}'")
                return
            await ctx.send(f"Here is your requested file '{filename}'", file=discord.File(filename))
            return

        if action.lower() == "add":
            # add new file
            attachments = ctx.message.attachments
            if len(attachments) == 0:
                await ctx.send("No attached file to add")
                return
            if len(attachments) == 1:
                attachment = attachments[0]
                filename = arg if arg is not None else attachment.filename
                if os.path.isfile(filename):
                    await ctx.send(f"File '{filename}' already exists. Please use replace command to replace an existing file")
                    return
                try:
                    await attachment.save(filename)
                    await ctx.send(f"Successfully uploaded '{filename}'")
                except Exception as e:
                    await ctx.send(f"Failed to upload file '{filename}'. Reason: {e}")
                return
            for attachment in attachments:
                filename = attachment.filename
                if os.path.isfile(filename):
                    await ctx.send(f"Filename '{filename}' already exists and is skipped. Please use replace command to replace existing file")
                    continue
                try:
                    await attachment.save(filename)
                    await ctx.send(f"Successfully uploaded '{filename}'")
                except Exception as e:
                    await ctx.send(f"Failed to upload file '{filename}'. Reason: {e}")
            return

        if action.lower() == "delete" or action.lower() == "remove":
            # delete existing file
            LOCKED_FILES = [".env", "data.json", "notifyMe.json"]   # Should not delete these files with this command
            if arg is None:
                await ctx.send("Please input file to delete")
                return
            filename = arg
            if not os.path.isfile(filename):
                await ctx.send(f"Could not find file '{filename}'")
                return
            if filename.endswith(".py"):
                await ctx.send("Cannot delete source files with this command")
                return
            if filename in LOCKED_FILES:
                await ctx.send(f"File '{filename}' cannot be deleted with this command")
                return
            try:
                os.remove(filename)
                await ctx.send(f"Removed '{filename}'")
            except Exception as e:
                await ctx.send(f"Could not remove file '{filename}'. Reason: {e}")
            return

        if action.lower() == "replace":
            # Replace existing file
            attachments = ctx.message.attachments
            if len(attachments) == 0:
                await ctx.send("No attached file to replace with")
                return
            if len(attachments) > 1:
                await ctx.send("Please attach only a single file to replace")
                return
            attachment = attachments[0]
            filename = arg if arg is not None else attachment.filename
            if not os.path.isfile(filename):
                await ctx.send(f"Could not find file '{filename}'. Please use add command to add a new file")
                return
            try:
                await attachment.save(filename)
                await ctx.send(f"Successfully replaced '{filename}'")
            except Exception as e:
                await ctx.send(f"Failed to replace file '{filename}'. Reason: {e}")
            return

        if action.lower() == "list":
            # List server files
            files = [f for f in os.listdir() if os.path.isfile(f)]
            msg = "Files: " + str(files)
            await ctx.send(msg)
            return

        # Invalid action
        await ctx.send(f"Invalid action type '{action}'.\n  Actions available: get, add, delete, replace, list")
        return

# Connect cog to bot
def setup(bot):
    bot.add_cog(File(bot))
