#!/usr/bin/python3
import os
import discord
import re
import time
import cogs
import pymongo

from discord.ext import commands
from helpers import util, checks


owner_id = owner_id = 125828772363632640
prefix = "."
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class MarblesBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for cog in cogs.default:
            self.load_extension(f"cogs.{cog}")

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
            await ctx.channel.send(f"tell hanny you got this error: {error}")
            raise error

    @property
    def mongo(self):
        return self.get_cog("Mongo")




bot = MarblesBot(command_prefix=prefix, owner_id = owner_id)
bot.run(TOKEN)



'''
@bot.group(invoke_without_command=True)
async def help(ctx):
    em = discord.Embed(title = "Help", description = f"use {prefix}help <command> for extended information on a command",color = ctx.author.color)
    em.add_field(name = "Commands", value = "register, daily, marbles, give, gamble, top")

    await ctx.send(embed = em)

@help.command()
async def register(ctx):
    em = discord.Embed(title = "register", description = "registers for marbles", color = ctx.author.color)
    em.add_field(name = "Usage", value = f"{prefix}register")

    await ctx.send(embed = em)
    
@help.command()
async def daily(ctx):
    em = discord.Embed(title = "daily", description = "get your daily marbles", color = ctx.author.color)
    em.add_field(name = "Usage", value = f"{prefix}daily")

    await ctx.send(embed = em)

@help.command()
async def give(ctx):
    em = discord.Embed(title = "give", description = "give a member marbles", color = ctx.author.color)
    em.add_field(name = "Usage", value = f"{prefix}give @user numMarbles")
    em.add_field(name = "Parameters", value = "@user -- user you want to give marbles to\nnumMarbles -- number of marbles you want to give")

    await ctx.send(embed = em)

@help.command()
async def gamble(ctx):
    em = discord.Embed(title = "gamble", description = "gamble your marbles", color = ctx.author.color)
    em.add_field(name = "Usage", value = f"{prefix}gamble numMarbles multiplier")
    em.add_field(name = "Parameters", value = "numMarbles -- number of marbles you want to gamble \nmultiplier -- multiplier between 2 and 10")

    await ctx.send(embed = em)

@help.command()
async def marbles(ctx):
    em = discord.Embed(title = "marbles", description = "check your mable count", color = ctx.author.color)
    em.add_field(name = "Usage", value = f"{prefix}marbles [user]")
    em.add_field(name = "Parameters", value = "[user] -- optionally look up user")

    await ctx.send(embed = em)

@help.command()
async def top(ctx):
    em = discord.Embed(title = "top", description = "check the marble leaderboard", color = ctx.author.color)
    em.add_field(name = "Usage", value = f"{prefix}top")

    await ctx.send(embed = em)

@help.command()
async def race(ctx):
    em = discord.embed(title = "race", description = "start a marble race", color = ctx.author.color)
    em.add_field(name = "Usage", value = f"{prefix}race [entry fee]")
    em.add_field(name = "Parameters", value = "[entry fee] -- number of marbles required to enter the race, defaults 0")

    await ctx.send(embed = em)
    '''



'''
@bot.event
async def on_message(message):
    print("hello", message.author.id, message.channel, message.guild)
'''


    
  
