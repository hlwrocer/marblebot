#!/usr/bin/python3
import os
import discord
import pymongo
import re
import random
import asyncio
import time
from discord.ext import commands
from datetime import datetime
from pytz import timezone
from bson.codec_options import CodecOptions
from threading import Timer



TOKEN = os.getenv("DISCORD_BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

prefix = "."
bot = commands.Bot(command_prefix=prefix)
mongo = pymongo.MongoClient(MONGODB_URI)
mydb = mongo["marbles"]
collection = mydb["marbleUsers"]
bot.remove_command("help")

#mongodb helpers?
def isRegistered(userID):
    #mongoDB check
    query = {"userID": int(userID)}
    if collection.find_one(query) is None:
        return False
    return True

def getMarbles(userID):
#assumes userID is registered
    return collection.find_one({"userID": userID}, {"_id":0, "marbles":1})['marbles']

def addMarbles(userID, amount):
    collection.update_one({"userID": userID}, {"$inc": {"marbles": amount}})

'''discord helpers'''

def getRole(guild, name):
    for role in guild.roles:
        if name == str(role.name):
            return role
    return None

async def addRole(ctx):
    hasRole = False
    for role in ctx.author.roles:
        if role.name == "marble-bois":
            hasRole = True
            break

    if not hasRole:
        role = getRole(ctx.guild, "marble-bois")
        await ctx.message.author.add_roles(role)

async def checkRegistered(ctx):
    #discord coroutine check for most commands
    userID = ctx.author.id
    query = {"userID": userID}
    if collection.find_one(query) is None:
        await ctx.send(f"{ctx.author.mention} please register to marble")
        return False
    return True

@bot.event
async def on_ready():
    print(f'{bot.user} has connected')
    for guild in bot.guilds:
        if getRole(guild, "marble-bois") is None:
            await guild.create_role(name="marble-bois")

@bot.command(name="register")
async def register(ctx):
    await addRole(ctx)
    query = {"userID" : ctx.author.id}
    if collection.count_documents(query, limit=1)==0:
        query = {"userID": ctx.author.id, "marbles": 100}
        collection.insert(query)
        await ctx.channel.send("{} is given 100 marbles".format(ctx.message.author.mention))
    else:
        await ctx.channel.send("{} you already registered noob".format(ctx.message.author.mention))

@bot.command(name="marbles")
async def marbles(ctx, user=None):
    await addRole(ctx)
    if user == None:
        userID = ctx.author.id
        user = ctx.message.author.mention
    else:
        if re.match('^<@!?[0-9]+>$', user) is None:
            await ctx.send("user not found")
            return

        userID = int(re.findall(r'[0-9]+', user)[0])
        if not isRegistered(userID):
            await ctx.send(f"{user} is not registered")
            return

    numMarbles = getMarbles(userID)
    await ctx.send(f"{user} has {numMarbles} marbles")

@bot.command(name="give")
@commands.check(checkRegistered)
async def give(ctx, mention, number):
    await addRole(ctx)
    authorid = ctx.message.author.id
    #parse mentionid
    if re.match('^<@!?[0-9]+>$', mention) is None:
        await ctx.send("user not found")
        return

    mentionid = int(re.findall(r'[0-9]+', mention)[0])
    

    #some failure conditions and very bad parsing this is a mess xd
    #TODO: change thos first condition to lookup user in guild
    if not isRegistered(mentionid):
        await ctx.send(f"{mention} is not registered, cannot give marbles")
        return
    elif mentionid == authorid:
        await ctx.send(f"{ctx.message.author.mention} you can't give yourself marbles")
        return

    try:
        number = int(number)
        if number <= 0:
            await ctx.send("You must give more than 0 marbles")
            return
    except:
        await ctx.send("Enter a valid number of marbles")
        return

    #give marbles
    marbleCount = getMarbles(authorid)
    if marbleCount < number:
        await ctx.send(f"{ctx.author.mention} get more marbles noob")
        return
    addMarbles(authorid, -1*number)
    addMarbles(mentionid, number)

    await ctx.send(f"{ctx.author.mention} gave {number} marbles to {mention}")

@bot.command(name="daily")
@commands.check(checkRegistered)
async def daily(ctx):
    await addRole(ctx)
    userID = ctx.message.author.id
    convertTime = collection.with_options(codec_options=CodecOptions(tz_aware=True,tzinfo=timezone("US/Eastern")))
    res=convertTime.find_one({"userID": userID}, {"marbles":0})
    curTime = datetime.now(timezone("US/Eastern"))
    if 'date' in res and res['date'].date() == curTime.date():
        secondsLeft = ((24 - curTime.hour - 1) * 60 * 60) + ((60 - curTime.minute - 1) * 60) + (60 - curTime.second)
        hoursLeft = secondsLeft // 3600
        secondsLeft %= 3600
        minutesLeft = secondsLeft // 60
        secondsLeft %= 60
        await ctx.send(f"{ctx.author.mention} you already claimed your marbles today. More marbles available in: {hoursLeft}:{minutesLeft:02d}:{secondsLeft:02d}")
        return

    collection.update_one({"userID": userID}, {"$set": {"date": curTime}})
    addMarbles(userID, 10)
    await ctx.send(f"{ctx.author.mention} you get 10 daily marbles")

    return

@bot.command(name="gamble")
@commands.check(checkRegistered)
async def gamble(ctx, numMarbles, multiplier):
    wager = 0
    if re.match('^[0-9]+$', numMarbles) is None:
        await ctx.send(f"{ctx.author.mention} wager a valid number of marbles")
        return
    elif re.match('^[0-9]+$', multiplier) is None:
        await ctx.send(f"{ctx.author.mention} enter a valid multiplier")
        return

    numMarbles = int(numMarbles)
    multiplier = int(multiplier)
    if getMarbles(ctx.author.id) < numMarbles:
        await ctx.send(f"{ctx.author.mention} you don't have enough marbles")
        return
    elif numMarbles <= 0:
        await ctx.send(f"{ctx.author.mention} you must bet at least one marble")
        return
    elif multiplier < 2 or multiplier > 10:
        await ctx.send(f"{ctx.author.mention} enter a multiplier between 2 and 10")
        return
    
    def check(msg):
        return msg.author.id == ctx.message.author.id and msg.channel == ctx.message.channel

    userID = ctx.message.author.id
    await ctx.send(f"{ctx.author.mention} I picked a number between 1 and {multiplier}. Guess what it is to get {multiplier} times more marbles than you bet. Or type `quit` to weenie out")
    number = random.randint(1, multiplier)
    try:
        while True:
            msg = await bot.wait_for('message', check=check, timeout=60.0)
            if msg.content == 'quit':
                role = getRole(ctx.guild, "marble-bois")
                await ctx.send(f"Hey {role.mention}, {ctx.author.mention} weenied out lmao. Taking a marble for that")
                addMarbles(ctx.author.id, -1)
                return
            elif re.match('^[0-9]$', msg.content) is None:
                await ctx.send(f"{ctx.author.mention} enter a valid number guess")
            else:
                guess = int(msg.content)
                if guess == number:
                    await ctx.send(f"Congrats {ctx.author.mention} you won {multiplier*numMarbles} marbles")
                    addMarbles(ctx.author.id, (multiplier-1)*numMarbles)
                    return
                else:
                    await ctx.send(f"fbm {ctx.author.mention} you lost {numMarbles} marbles")
                    addMarbles(ctx.author.id, -1*numMarbles)
                    return
    except asyncio.TimeoutError:
        await ctx.send(f"{ctx.author.mention} you took to long so I'm taking your marbles for wasting my time")
        addMarbles(ctx.author.id, -1*numMarbles)
        return

@bot.command(name="top")
async def top(ctx):
    users = ''
    numMarbles = ''
    records = collection.find().sort("marbles", -1)
    count = records.count() if records.count() < 10 else 10
    #for some reason the below duplicates a document
    '''
    for x in range(count):
        username = await bot.fetch_user(records[x]['userID'])
        print(x, records[x]['userID'], username)
        marbleCount = records[x]['marbles']
        users += f"{x+1}. {username}" + "\n"
        numMarbles += f"{marbleCount}" + "\n"
    '''
    pos = 0
    for doc in records:
        username = await bot.fetch_user(doc['userID'])
        marbleCount = doc['marbles']
        users += f"{pos+1}. {username}" + "\n"
        numMarbles += f"{marbleCount}" + "\n"
        pos+=1
        if pos == count:
            break

    em = discord.Embed(title = "Marble leaderboard", color=ctx.author.color)
    em.set_thumbnail(url=bot.user.avatar_url)
    em.add_field(name = "Top 10", value= users, inline=True)
    em.add_field(name = "Marbles", value=numMarbles, inline=True)
    
    await ctx.send(embed=em)

@bot.command(name="race")
async def race(ctx, wager=0):
    if wager < 0:
        await ctx.send("entry fee must be at least 0 marbles")
        return
    wager = int(wager)
    playerList = []
    marbles = ["⚫", "🔵", "🟤", "🟢", "🟠", "🟣", "🔴", "🟡"]
    random.shuffle(marbles)
    emojis = ["✅","🏁","❎"]
    message = await ctx.send(embed = raceLobbyEmbed(playerList , 30, wager))
    for emoji in emojis:
        await message.add_reaction(emoji)
    end = time.time() + 30
    timeOut = False
    canceled = False

    async def coro1():
        for x in range(0, 30, 1):
            if timeOut:
                break
            await message.edit(embed=raceLobbyEmbed(playerList, 30-x, wager))
            await asyncio.sleep(1)

    def check(reaction, user):
        username = user.name + "#" + user.discriminator
        if reaction.emoji == "🏁" and user.id == ctx.author.id:
            return True
        elif reaction.emoji == "✅":
            if (username, user.id) not in playerList and len(playerList) < 8 and isRegistered(user.id) and getMarbles(user.id) >= wager:
                playerList.append((username, user.id))
                addMarbles(user.id, -1*wager)
        elif reaction.emoji == "❎" and user.id == ctx.author.id:
            nonlocal canceled
            canceled = True
            return True
        return False
 
    await asyncio.wait([coro1(), bot.wait_for('reaction_add', check=check)], return_when=asyncio.FIRST_COMPLETED)
    timeOut = True
    if len(playerList) == 0 or canceled:
        for player in playerList:
            addMarbles(player[1], wager)
        await message.edit(embed=discord.Embed(Title = "Marble Race", description = "The race has been canceled"))
        return
    await message.clear_reaction("✅")
    await message.clear_reaction("🏁")
    await message.clear_reaction("❎")
 
    raceFinished = False
    countdown = 3
    racePositions = [0]*len(playerList)
    winners = []

    
    while not raceFinished:
        await message.edit(embed=raceEmbed(playerList, racePositions, marbles, countdown, len(playerList)*wager))
        if countdown > 0:
            if countdown == 3:
                await message.add_reaction('🔴')
            if countdown == 2:
                await message.add_reaction('🟡')
            if countdown == 1:
                await message.add_reaction('🟢')
            countdown -= 1
            await asyncio.sleep(1)
        else:
            if countdown == 0:
                countdown -= 1
                await message.add_reaction('🏳️')
            for x in range(len(racePositions)):
                racePositions[x] += random.randint(0,3)
                if racePositions[x] > 49:
                    raceFinished = True
                    winners.append(x)
            await asyncio.sleep(1)

    #TODO what to do in the case of a tie
    if len(winners) == 1:
        await ctx.send(f"<@{playerList[winners[0]][1]}> wins {wager*len(playerList)} marbles")
        await message.edit(embed=raceEmbed(playerList, racePositions, marbles, countdown, len(playerList)*wager, winners))
        addMarbles(playerList[winners[0]][1], wager*len(playerList))
        return
    else:
        numMarbles = (wager*len(playerList))//len(winners)
        for x in winners:
            addMarbles(playerList[winners[x]], numMarbles)
        await ctx.send(f"{'<@' + '>, <@'.join(str(playerList[x][1]) for x in winners) + '>'} tied for first, each winning {numMarbles} marbles")
        await message.edit(embed=raceEmbed(playerList, racePositions, marbles, countdown, numMarbles, winners))
        return

def raceLobbyEmbed(playerList, time, wager):
    em = discord.Embed(title = "Marble Race", description = f"React ✅ to join. Up to 8 people can join a race.\nYou must be registered to play. Entry fee {wager} marbles\nRace creator can react 🏁 to start instantly or ❎ to cancel the race")
    if len(playerList) != 0:
        em.add_field(name = f"Time to join: {time} seconds\nPlayer list", value = f"`{', '.join(player[0] for player in playerList)}`", inline=True)

    else:
        em.add_field(name = f"Time to join: {time} seconds\nPlayer list", value = "`\u200b`", inline=True)

    return em

def raceEmbed(playerList, racePositions, marbles, countdown, prize, winners = []):
    if countdown > 0:
        em = discord.Embed(title = "Marble Race", description = f"Starting in {countdown}...")
    elif len(winners) == 0:
        players = ""
        positions = ""
        for x in range(len(playerList)):
            players += f"{playerList[x][0]}\n"
            positions += f"{'-'*racePositions[x]}{marbles[x]}{'-'*(49-racePositions[x])}🏁\n"

        em = discord.Embed(title = "Marble Race", description = f"Prize: {prize} marbles")
        em.add_field(name = "Player", value = players, inline=True)
        em.add_field(name = "Position", value = positions, inline=True)
    else:
        players = ""
        positions = ""
        for x in range(len(playerList)):
            players += f"{playerList[x][0]}\n"
            if x not in winners:
                positions += f"{'-'*racePositions[x]}{marbles[x]}{'-'*(49-racePositions[x])}🏁\n"
            else:
                positions += f"{'-'*50}{marbles[x]}\n"

        em = discord.Embed(title = "Marble Race", description = f"Prize: {prize} marbles\nWinners: {', '.join(playerList[x][0] for x in winners)}")
        em.add_field(name = "Player", value = players, inline=True)
        em.add_field(name = "Position", value = positions, inline=True)


    return em

@bot.command(name="devgive")
async def devgive(ctx, user, marbles):
    userid = int(re.findall(r'[0-9]+', user)[0])
    print(userid)
    print(ctx.author.id)
    if ctx.message.author.id == 125828772363632640:
        print('hello')
        addMarbles(userid, int(marbles))


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
    em = discord.Embed(title = "give", description = "gamble your marbles", color = ctx.author.color)
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


@bot.event
async def on_command_error(ctx,error):
    error = getattr(error, 'original', error)
    print(error)
    if isinstance(error, pymongo.errors.ServerSelectionTimeoutError):
        await ctx.channel.send("{} failed. db probably down or something".format(ctx.command))
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"Incorrect command usage. Type {prefix}help for assistance idiot")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.channel.send("Command not found")
    else:
        raise error


'''
@bot.event
async def on_message(message):
    print("hello", message.author.id, message.channel, message.guild)
'''


    
bot.run(TOKEN)
  
