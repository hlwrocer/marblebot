from discord.ext import commands
import re

class Admin(commands.Cog):
    '''General marble bot commands'''
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(name="devgive")
    async def devgive(self, ctx, user, marbles):
        """Only the dev can use this"""
        userid = int(re.findall(r'[0-9]+', user)[0])
        self.bot.mongo.addMarbles(userid, float(marbles))

def setup(bot):
    bot.add_cog(Admin(bot))
