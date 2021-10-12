from discord.ext import commands
import discord
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

    @commands.is_owner()
    @commands.command(name='reload')
    async def reload(self, ctx, cog):
        self.bot.reload_extension(f"cogs.{cog}")
        embed = discord.Embed(title='Reload', description=f'{cog} successfully reloaded')
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Admin(bot))
