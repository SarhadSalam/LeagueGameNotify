import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Commands
    @commands.command()
    async def help(self, ctx, command=None):
        help_strings = {
            'test': """No options supported. Call by itself.""",
            'mentionMe': """No options supported. Call by itself.""",
            'hello': """No options supported. Call by itself.""",
            'clash': """No options supported. Call by itself.""",
            'mmr': """Availaible Commands:
                        - $mmr $SUMMONER_NAME  =>  Get MMR for summoner
                        - $mmr $SUMMONER_NAME -history  =>  Get MMR with graph for summoner""",
            'summon': """No options supported. Call by itself.""",
            'rank': """Availaible Commands:
                        - $rank $SUMMONER_NAME  =>  Get rank of summoner
                        - $rank  =>  Get rank of all the boiis, ordered highest to lowest
                        """,
            'notify': """
                        Available Commands:
                            - $notify add $SUMMONER_NAME  =>  Subscribe to summoner's notify list
                            - $notify remove $SUMMONER_NAME  =>  Unsubscribe from summoner's notify list
                            - $notify list  =>  List your current subscriptions

                        Use /all in place of $SUMMONER_NAME to sub/unsub from all summoners
                """,
            # stream': """
            #        Available Commands:
            #        - $stream start $SUMMONER_NAME => Start a stream for the summoner
            #        - $stream change $SUMMONER_NAME => Change a stream for a summoner to a different game
            #        - $stream stop => Stop streaming
            #        - $stream help => Start streaming
            #    """,
            'flex': """
                        Available Commands:
                        - $flex tag => Tag everyone not in the lobby
                        - $flex tag all => Ignore lobby members and tag everyone
                        - $flex clear => Clear out the lobby
                        - $flex add $SUMMONER_NAME1* $SUMMONER_NAME2?* $SUMMONER_NAME3?* $SUMMONER_NAME4?* $SUMMONER_NAME5?* => Add summoner's to the lobby list. Note only 1 summoner is required.
                        - $flex remove $SUMMONER_NAME1* $SUMMONER_NAME2?* $SUMMONER_NAME3?* $SUMMONER_NAME4?* $SUMMONER_NAME5?* => Remove summoner's from the lobby. Note only 1 summoner is required.
                        - $flex list => Shows who is in the lobby
                        - $flex help => Shows this help text
                        ? shows optional parameters.
                        * represents commands that can be filled with "me" and it will add your user object
                """,
            'logs': """
                        Available Commands:
                            - $logs -error  =>  Dump error log (Default option if no option applied)
                            - $logs -std  =>  Dump stdout
                            - $logs -info =>  Dump info
                            - $logs -error =>  Dump error
                """,
            'bois': """No options supported. Call by itself.""",
            'mastery': """
                        Available Commands:
                            - $mastery $SUMMONER_NAME $ARGUMENT  =>  Get mastery points for summoner

                        Possible $ARGUMENTs:
                            - $CHAMPION_NAME  =>  Get mastery for specific champion
                            - $X  =>  Get top X champions by mastery points (max 25)
                            - lv$X  =>  Get all (max top 25) mastery level X champions

                        examples:
                            $mastery sardaddy garen  =>  Garen mastery for sardaddy
                            $mastery nashweed 8  =>  nashweed's top 8 champions
                            $mastery marginallyTall lv7  =>  marginallyTall's mastery level 7 champions
                """,

        }

        default_string = """Availaible commands:
        01. (debug) $test => Send a test message containing some debug information about the message.
        02. (debug) $mentionMe => Mention yourself
        03. (debug) $hello => Send a hello message
        04. $clash => Get clash dates
        05. $mmr => Get your approximate MMR
        06. $summon => Summon a random summoner to play ranked
        07. $rank => Get a summoners rank
        08. $notify => Get tagged when a summoner is in game
        09. $flex => Tag people not in lobby to join for 5sum
        10. $logs => Dump debug logs
        11. $bois => List known summoners
        12. $mastery => Get mastery information for a summoner's champions
        13. $help => This help list

        Run "$help $COMMAND_NAME" to get information on how to run that command.
        """

        if not command:
            await ctx.send(default_string)
            return

        if command and command not in help_strings:
            await ctx.send("Wrong command name.")
            await ctx.send(default_string)
            return

        await ctx.send(help_strings[command])

# Connect cog to bot


def setup(bot):
    bot.add_cog(Help(bot))
