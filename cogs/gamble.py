from discord.ext import commands
from helpers import checks, util
from threading import Timer

import time
import discord
import re
import os
import asyncio
import random

class Gamble(commands.Cog):
    """All the gambling commands"""
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name='rps')
    @checks.registered()
    async def rps(self, ctx, numMarbles:float):
        '''Play Rock Paper Scissors against the bot. Win and double your marbles
        **numMarbles**: Number of marbles you want to wager. Must be > 0
        '''
        numMarbles = round(numMarbles, 2)
        result = -1 # 0 win, 1 loss, 2 tie
        if self.bot.mongo.getMarbles(ctx.author.id) < numMarbles:
            await ctx.send(f"{ctx.author.mention} you don't have enough marbles")
            return
        elif numMarbles <= 0:
            await ctx.send(f"{ctx.author.mention} you must bet a positive number of marbles")
            return
        self.bot.mongo.addMarbles(ctx.author.id, -1*numMarbles)
        def check(msg):
            return msg.author.id == ctx.message.author.id and msg.channel == ctx.message.channel

        userID = ctx.message.author.id
        choice = random.randint(0,2)
        emojis = ['✊','🖐️','✌️']
        msg = await ctx.send(f"{ctx.author.mention} I picked my choice, waiting for you to pick {emojis[0]}, {emojis[1]}, or {emojis[2]}")
        for emoji in emojis:
            await msg.add_reaction(emoji)

        def check(reaction, user):
            print('check', reaction, user)
            print(reaction.emoji == emojis[0], user.id == ctx.author.id)
            if reaction.emoji == emojis[0] and user.id == ctx.author.id:
                return True
            elif reaction.emoji == emojis[1] and user.id == ctx.author.id:
                return True
            elif reaction.emoji == emojis[2] and user.id == ctx.author.id:
                return True
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60.0)
            print(reaction, user)
            print(choice)
            if reaction.emoji == emojis[choice]:
                self.bot.mongo.addMarbles(ctx.author.id, numMarbles)
                await ctx.send(f"{ctx.author.mention} We both picked {emojis[choice]}. It's a tie so I'll give you your marbles back")
            else:
                print('?')
                print('hello?', reaction.emoji == emojis[0])
                if reaction.emoji == emojis[0]: #user chooses roc
                    if choice == 1: #bot picks paper
                        await ctx.send(f"{ctx.author.mention} picked {reaction} and I chose {emojis[choice]}. Thanks for the marbles")
                    elif choice == 2: #bot picks scissors
                        self.bot.mongo.addMarbles(ctx.author.id, 2*numMarbles)
                        await ctx.send(f"{ctx.author.mention} picked {reaction} and I chose {emojis[choice]}. You got lucky this time and won {numMarbles} marbles.")
                elif reaction.emoji == emojis[1]: #user choose paper:
                    if choice == 0: #bot picks rock
                        await ctx.send(f"{ctx.author.mention} picked {reaction} and I chose {emojis[choice]}. Thanks for the marbles")
                    elif choice == 2: #bot picks scissors
                        self.bot.mongo.addMarbles(ctx.author.id, 2*numMarbles)
                        await ctx.send(f"{ctx.author.mention} picked {reaction} and I chose {emojis[choice]}. You got lucky this time and won {numMarbles} marbles.")
                elif reaction.emoji == emojis[2]: #user chooses scissors:
                    if choice == 0: #bot picks rock
                        await ctx.send(f"{ctx.author.mention} picked {reaction} and I chose {emojis[choice]}. Thanks for the marbles")
                    elif choice == 1: #bot picks paper
                        self.bot.mongo.addMarbles(ctx.author.id, 2*numMarbles)
                        await ctx.send(f"{ctx.author.mention} picked {reaction} and I chose {emojis[choice]}. You got lucky this time and won {numMarbles} marbles.")
            return

        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention} you took to long so I'm taking your marbles for wasting my time")
            return





    @commands.command(name="gamble")
    @checks.registered()
    async def gamble(self, ctx, numMarbles: float, multiplier: int):
        '''Gamble your marbles
        **numMarbles**: Number of marbles you want to wager. Must be > 0
        **multiplier**: Multiplier for the number of marbles you wagered. Must be between 2 and 10'''
        #if re.match('^[0-9]*\.?[0-9]{0,2}$', numMarbles) is None:
        #    await ctx.send(f"{ctx.author.mention} wager a valid number of marbles")
        #    return
        #elif re.match('^[0-9]+$', multiplier) is None:
        #    await ctx.send(f"{ctx.author.mention} enter a valid multiplier")
        #    return

        numMarbles = round(numMarbles, 2)
        multiplier = int(multiplier)
        if self.bot.mongo.getMarbles(ctx.author.id) < numMarbles:
            await ctx.send(f"{ctx.author.mention} you don't have enough marbles")
            return
        elif numMarbles <= 0:
            await ctx.send(f"{ctx.author.mention} you must bet a positive number of marbles")
            return
        elif multiplier < 2 or multiplier > 10:
            await ctx.send(f"{ctx.author.mention} enter a multiplier between 2 and 10")
            return
        self.bot.mongo.addMarbles(ctx.author.id, -1*numMarbles)
        
        def check(msg):
            return msg.author.id == ctx.message.author.id and msg.channel == ctx.message.channel

        userID = ctx.message.author.id
        await ctx.send(f"{ctx.author.mention} I picked a number between 1 and {multiplier}. Guess what it is to get {multiplier} times more marbles than you bet. Or type `quit` to weenie out")
        number = random.randint(1, multiplier)
        try:
            while True:
                msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                if msg.content == 'quit':
                    role = util.getRole(ctx.guild, "marble-bois")
                    await ctx.send(f"Hey {role.mention}, {ctx.author.mention} weenied out lmao. Taking a marble for that")
                    self.bot.mongo.addMarbles(ctx.author.id, numMarbles-1)
                    return
                elif re.match('^[0-9]$', msg.content) is None:
                    await ctx.send(f"{ctx.author.mention} enter a valid number guess")
                else:
                    guess = int(msg.content)
                    if guess == number:
                        await ctx.send(f"Congrats {ctx.author.mention} you won {multiplier*numMarbles} marbles")
                        self.bot.mongo.addMarbles(ctx.author.id, (multiplier)*numMarbles)
                        return
                    else:
                        await ctx.send(f"fbm {ctx.author.mention} you lost {numMarbles} marbles")
                        return
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention} you took to long so I'm taking your marbles for wasting my time")
            return

    @checks.registered()
    @commands.command(name="race")
    async def race(self, ctx, wager: float=0.0):
        '''Start a marble race. Pot split amongst the winners.
        **wager**: Entry fee for the race, default 0.
        '''
        wager = round(wager,2)
        #if re.match('^[0-9]*\.?[0-9]{0,2}$', wager) is None:
        #    await ctx.send(f"{ctx.author.mention} wager a valid number of marbles")
        #    return

        if wager < 0:
            await ctx.send("entry fee must be at least 0 marbles")
            return
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

        #set up race
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
                if (username, user.id) not in playerList and len(playerList) < 8 and self.bot.mongo.isRegistered(user.id) and self.bot.mongo.getMarbles(user.id) >= wager:
                    playerList.append((username, user.id))
                    self.bot.mongo.addMarbles(user.id, -1*wager)
            elif reaction.emoji == "❎" and user.id == ctx.author.id:
                nonlocal canceled
                canceled = True
                return True
            return False
        await asyncio.wait([coro1(), self.bot.wait_for('reaction_add', check=check)], return_when=asyncio.FIRST_COMPLETED)
        timeOut = True
        if len(playerList) == 0 or canceled:
            for player in playerList:
                self.bot.mongo.addMarbles(player[1], wager)
            await message.edit(embed=discord.Embed(Title = "Marble Race", description = "The race has been canceled"))
            return
        await message.clear_reaction("✅")
        await message.clear_reaction("🏁")
        await message.clear_reaction("❎")
     
        #start race
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
            self.bot.mongo.addMarbles(playerList[winners[0]][1], wager*len(playerList))
            return
        else:
            numMarbles = (wager*len(playerList))//len(winners)
            for x in winners:
                self.bot.mongo.addMarbles(playerList[playerList[x]], numMarbles)
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

def setup(bot):
    bot.add_cog(Gamble(bot))
