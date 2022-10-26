#!/usr/bin/python3
import os
import discord
import re
import time
import cogs
import pymongo
import asyncio

from discord.ext import commands
from helpers import util, checks


owner_id = owner_id = 125828772363632640
prefix = "."
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class MarblesBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def on_ready(self):
        print(f'{bot.user} has connected')
        for guild in bot.guilds:
            if util.getRole(guild, "marble-bois") is None:
                await guild.create_role(name="marble-bois")

    async def on_command_error(self, ctx, error):
        error = getattr(error, 'original', error)
        print(error)
        if isinstance(error, pymongo.errors.ServerSelectionTimeoutError):
            await ctx.channel.send("{} failed. db probably down or something".format(ctx.command))
        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.channel.send(f"Incorrect command usage: {error}")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.channel.send("Command not found")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.channel.send(error)
        else:
            await ctx.channel.send(f"<@125828772363632640> {ctx.message.content}: {error}")
            raise error

    async def setup_hook(self):
        for cog in cogs.default:
            await bot.load_extension(f"cogs.{cog}")
        

    @property
    def mongo(self):
        return self.get_cog("Mongo")





intents = discord.Intents.all()
bot = MarblesBot(command_prefix=prefix, owner_id = owner_id, case_insensitive=True, intents=intents)
async def main():
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())






    
  
