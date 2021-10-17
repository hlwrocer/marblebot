from discord.ext import commands
from helpers import checks, util
import re
import discord
import asyncio
import threading

class Competitive(commands.Cog):
    '''General marble bot commands'''
    def __init__(self, bot):
        self.bot = bot
        self.supportedGames = ['legion']
        self.lobbies = {}

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.id != self.bot.user.id:
            if reaction.message not in self.lobbies:
                return
            mongo = self.bot.mongo
            lobbyDoc = self.lobbies[reaction.message][0]
            lobby = lobbyDoc['lobby']
            lobbyOwner = lobby['lobbyOwner']
            started = lobby['started']
            game = lobby['game']
            result = lobby['result']
            lobbyID = lobbyDoc['_id']
            timer = self.lobbies[reaction.message][1]
            ctx = await self.bot.get_context(reaction.message)
            if started:
                #result screen
                elos = mongo.getField(user.id, "elos")
                userElo = elos['elos'][game]['elo']
                userInfo = {'userID': user.id, 'elo': userElo}
                if elos['elos']['lobby'] != lobbyID:
                    await ctx.send(f'{user.mention} you are not part of this lobby')
                    return
                if reaction.emoji == "1️⃣":
                    #vote team 1
                    if userInfo in result['team1']:
                        #user already voted team 1
                        return
                    elif userInfo in result['team2']:
                        #user voted team 2 and wants to change it to team 1
                        result['team2'].remove(userInfo)
                    elif userInfo in result['cancel']:
                        result['cancel'].remove(userInfo)
                    result['team1'].append(userInfo)

                elif reaction.emoji == "2️⃣":
                    #vote team 2
                    if userInfo in result['team1']:
                        #user voted team 1 and wants to change it to team 2
                        result['team1'].remove(userInfo)
                    elif userInfo in result['cancel']:
                        result['cancel'].remove(userInfo)
                    elif userInfo in result['team2']:
                        #user has already voted
                        return
                    result['team2'].append(userInfo)

                elif reaction.emoji == "❎":
                    #vote cancel
                    if userInfo in result['team1']:
                        #user voted team 1 change to cancel
                        result['team1'].remove(userInfo)
                    elif userInfo in result['team2']:
                        #user voted team 2 change to cancel
                        result['team2'].remove(userInfo)
                    elif userInfo in result['cancel']:
                        return
                    result['cancel'].append(userInfo)

                numPlayers = len(lobby['team1']) + len(lobby['team2'])
                if len(result['team1']) > numPlayers/2:
                    #team 1 wins give them elo  
                    results = {'team1':[],'team2':[]}
                    team2Average = 0
                    team1Average = 0
                    for userDict in lobby['team2']:
                        team2Average += userDict['elo']['elo']
                    team2Average = round(team2Average/len(lobby['team2']))

                    
                    for userDict in lobby['team1']:
                        #team 1 wins
                        team1Average += userDict['elo']['elo']
                        userElo = userDict['elo']['elo']
                        change = self.calculateEloChange(userElo, team2Average, 1)
                        results['team1'].append(change)
                        userDict['elo']['elo'] += change
                        userDict['elo']['wins'] += 1
                        mongo.updateElo(game, userDict['userID'], userDict['elo'])
                    team1Average = round(team1Average/len(lobby['team1']))


                    for userDict in lobby['team2']:
                        #team2 loses
                        userElo = userDict['elo']['elo']
                        change = self.calculateEloChange(userElo, team1Average, 0)
                        results['team2'].append(change)
                        userDict['elo']['elo'] += change
                        userDict['elo']['losses'] += 1
                        mongo.updateElo(game, userDict['userID'], userDict['elo'])

                    self.closeLobby(lobby, lobbyID, reaction.message)
                    await reaction.message.edit(embed = await self.resultEmbed(game, lobby, results, "Team 1"))
                    return
                elif len(result['team2']) > numPlayers/2:
                    results = {'team1':[],'team2':[]}
                    team2Average = 0
                    team1Average = 0
                    for userDict in lobby['team2']:
                        team2Average += userDict['elo']['elo']
                    team2Average = round(team2Average/len(lobby['team2']))

                    for userDict in lobby['team1']:
                        #team 1 loses
                        team1Average += userDict['elo']['elo']
                        userElo = userDict['elo']['elo']
                        change = self.calculateEloChange(userElo, team2Average, 0)
                        results['team1'].append(change)
                        userDict['elo']['elo'] += change
                        userDict['elo']['losses'] += 1
                        mongo.updateElo(game, userDict['userID'], userDict['elo'])
                    team1Average = round(team1Average/len(lobby['team1']))

                    for userDict in lobby['team2']:
                        #team 2 wins give them elo
                        userElo = userDict['elo']['elo']
                        change = self.calculateEloChange(userElo, team1Average, 1)
                        results['team2'].append(change)
                        userDict['elo']['elo'] += change
                        userDict['elo']['wins'] += 1
                        mongo.updateElo(game, userDict['userID'], userDict['elo'])

                    self.closeLobby(lobby, lobbyID, reaction.message)
                    await reaction.message.edit(embed = await self.resultEmbed(game, lobby, results, "Team 2"))
                    return
                elif len(result['cancel']) > numPlayers/2:
                    #agree on cancel

                    self.closeLobby(lobby, lobbyID, reaction.message)
                    await reaction.message.edit(embed = await self.lobbyEmbed(game, lobby, canceled=True))
                    return

                else:
                    await reaction.message.edit(embed = await self.lobbyEmbed(game, lobby, started=True, result=lobby['result']))

            else:
                #lobby screen
                if not mongo.isRegistered(user.id):
                    await ctx.send(f'{user.mention} register to join the lobby')
                    return False
                elos = mongo.getField(user.id, "elos")
                if 'elos' not in elos:
                    #users first time using elos create some record
                    elos['elos'] = {game: {'elo': 1000, 'wins':0, 'losses': 0, 'draws': 0}, 'lobby': lobbyID}
                    mongo.createElo(user.id, elos['elos'])
                    mongo.joinLobby(lobbyID, user.id)
                    elos = mongo.getField(user.id, "elos")

                if game not in elos['elos']:
                    #users first time playing this game
                    elos['elos'][game] = {'elo': 1000, 'wins':0, 'losses': 0, 'draws': 0}
                    mongo.createElo(user.id, elos['elos'])

                if 'lobby' not in elos['elos'] or elos['elos']['lobby'] == -1:
                    #user is not in a lobby
                    mongo.joinLobby(lobbyID, user.id)

                userElo = elos['elos'][game]
                userInfo = {'userID': user.id, 'elo': userElo}

                if reaction.emoji == "✅" and user.id == lobbyOwner:
                    #start the lobby
                    if len(lobby['team1']) + len(lobby['team2']) == 1:
                        await ctx.send(f'{user.mention} you cannot start the lobby with only 1 player')
                        return
                    elif len(lobby['team2']) == 0:
                        await ctx.send(f'{user.mention} you cannot start the lobby with 1 team')
                        return

                    lobby['started'] = 1
                    emojis = ["1️⃣", "2️⃣", "0️⃣", "✅", "❎"]
                    await reaction.message.edit(embed = await self.lobbyEmbed(game, lobby, started=True))
                    for emoji in emojis:
                        await reaction.message.clear_reaction(emoji)
                    await reaction.message.add_reaction(emojis[0])
                    await reaction.message.add_reaction(emojis[1])
                    await reaction.message.add_reaction(emojis[4])

                elif reaction.emoji == "❎" and user.id == lobbyOwner:
                    #close lobby
                    self.closeLobby(lobby, lobbyID, reaction.message)
                    await reaction.message.edit(embed = await self.lobbyEmbed(game,lobby, canceled=True))
                    return

                elif reaction.emoji == "1️⃣":
                    if elos['elos']['lobby'] != -1 and elos['elos']['lobby'] != lobbyID:
                        await ctx.send(f'{user.mention} you are already in a ranked lobby. Finish that one before starting a new one')
                        return False
                    if userInfo in lobby['team1']:
                        #user already joined team 1 do nothing
                        return
                    elif userInfo in lobby['team2']:
                        #user joined team 2, swapping to team 1
                        lobby['team1'].append(userInfo)
                        lobby['team2'].remove(userInfo)
                    else:
                        lobby['team1'].append(userInfo)
                        #user has not joined a team yet
                    mongo.joinLobby(lobbyID, user.id)
                    await reaction.message.edit(embed = await self.lobbyEmbed(game, lobby))
                    return

                elif reaction.emoji == "2️⃣":
                    if elos['elos']['lobby'] != -1 and elos['elos']['lobby'] != lobbyID:
                        await ctx.send(f'{user.mention} you are already in a ranked lobby. Finish that one before starting a new one')
                        return
                    if userInfo in lobby['team2']:
                        #user already joined team 2 do nothing
                        return
                    elif userInfo in lobby['team1']:
                        #user joined team 1, swapping to team 2
                        lobby['team2'].append(userInfo)
                        lobby['team1'].remove(userInfo)
                    else:
                        lobby['team2'].append(userInfo)
                        #user has not joined a team yet
                    mongo.joinLobby(lobbyID, user.id)
                    await reaction.message.edit(embed = await self.lobbyEmbed(game, lobby))
                    return

                elif reaction.emoji == "0️⃣" and user.id != lobbyOwner: #leave lobby
                    #technically can leave from any lobby, no checks that you're leaving the specific lobby
                    if userInfo in lobby['team2']:
                        lobby['team2'].remove(userInfo)
                    elif userInfo in lobby['team1']:
                        lobby['team1'].remove(userInfo)
                    mongo.leaveLobby(user.id)
                    await reaction.message.edit(embed = await self.lobbyEmbed(game, lobby))
                    return

        
        

    @commands.command(name="createLobby", case_insensitive=True)
    @checks.registered()
    async def createLobby(self, ctx, game):
        '''Create a ranked lobby for the specified `game`
        `game`: ranked game you are playing
        Currently supports: Legion'''
        game = game.lower()
        lobbyOwner = ctx.author.id
        users = []
        lobby = {'team1':[], 'team2':[], 'lobbyOwner': ctx.author.id, 'game': game, 'started': 0, 'result':{'team1':[], 'team2':[], 'cancel':[]}}

        if game not in self.supportedGames:
            await ctx.send(f'{game} is not supported. Type `.help ranked` for a list of supported games')
            return
        
        mongo = self.bot.mongo
        elos = mongo.getField(ctx.author.id, "elos")
        if 'elos' not in elos:
            #users first time using elos create some record
            elos['elos'] = {game: {'elo': 1000, 'wins':0, 'losses': 0, 'draws': 0}, 'lobby': -1}
            mongo.createElo(ctx.author.id, elos['elos'])
            elos = mongo.getField(ctx.author.id, "elos")
        elif elos['elos']['lobby'] != -1:
            #otherwise if the user is already in a lobby, don't allow them to make another one
            await ctx.send(f'{ctx.author.mention} you are currently in a ranked lobby. Finish that one first before starting a new one')
            return

        if game not in elos['elos']:
            #users first time playing this game
            elos['elos'][game] = {'elo': 1000, 'wins':0, 'losses': 0, 'draws': 0}
            mongo.createElo(ctx.author.id, elos['elos'])

        async def timeOutCallback(message):
            lobby = self.lobbies[message][0]['lobby']
            lobbyID = self.lobbies[message][0]['_id']
            game = lobby['game']
            await message.edit(embed=await self.lobbyEmbed(game, lobby, True, started=lobby['started'], result = lobby['result']))
            mongo.saveLobbyField(lobbyID, {"lobby": lobby})
            del self.lobbies[message]

        #create the lobby
        lobbyID = mongo.createLobby({'lobby': lobby}).inserted_id
        #Lobby owner must join their own lobby
        mongo.joinLobby(lobbyID, ctx.author.id)
        
        lobby['team1'].append({'userID': ctx.author.id, 'elo': elos['elos'][game]})
        lobbyDoc = {"_id": lobbyID, "lobby": lobby}

        lobbyMessage = await ctx.send(embed = await self.lobbyEmbed(game, lobby))
        timer = util.Timer(60, timeOutCallback, lobbyMessage)
        self.lobbies[lobbyMessage] = [lobbyDoc, timer]

        emojis = ["1️⃣", "2️⃣", "0️⃣", "✅", "❎"]
        for emoji in emojis:
            await lobbyMessage.add_reaction(emoji)



    @commands.command(name="lobby", case_insensitive=True)
    @checks.registered()
    async def lobby(self, ctx):
        '''Bring back the lobby you are currently in'''
        mongo = self.bot.mongo
        lobbyDoc = mongo.getUserLobby(ctx.author.id)
        if lobbyDoc == -1:
            await ctx.send(f'{ctx.author.mention} you are currently not in a lobby')
            return
        lobby = lobbyDoc['lobby']
        lobbyID = lobbyDoc['_id']
        game = lobby['game']
        lobbyOwner = lobby['lobbyOwner']
        result = lobby['result']
        emojis = ["1️⃣", "2️⃣", "0️⃣", "✅", "❎"]

        async def timeOutCallback(message):
            lobby = self.lobbies[message][0]['lobby']
            lobbyID = self.lobbies[message][0]['_id']
            game = lobby['game']
            await message.edit(embed=await self.lobbyEmbed(game, lobby, True, started=lobby['started'], result = lobby['result']))
            mongo.saveLobbyField(lobbyID, {"lobby": lobby})
            del self.lobbies[message]

        for message in self.lobbies:
            if self.lobbies[message][0]['_id'] == lobbyID:
                await ctx.send(f'{ctx.author.mention} that lobby is already open here: {message.jump_url}')
                return

        if lobby['started']:
            lobbyMessage = await ctx.send(embed = await self.lobbyEmbed(game, lobby, started = True, result = result))
            timer = util.Timer(60, timeOutCallback, lobbyMessage)
            self.lobbies[lobbyMessage] = [lobbyDoc, timer]

            await lobbyMessage.add_reaction(emojis[0])
            await lobbyMessage.add_reaction(emojis[1])
            await lobbyMessage.add_reaction(emojis[4])
            return

        else:
            lobbyMessage = await ctx.send(embed = await self.lobbyEmbed(game, lobby))
            #there aren't many lobbies but probably need a better way to index
                
            timer = util.Timer(60, timeOutCallback, lobbyMessage)
            self.lobbies[lobbyMessage] = [lobbyDoc,timer]

            for emoji in emojis:
                await lobbyMessage.add_reaction(emoji)

    async def lobbyEmbed(self, game, lobby, timeOut = False, started = False, result = None, canceled = False):
        team1 = []
        team2 = []
        lobbyOwner = lobby["lobbyOwner"]

        for userDict in lobby['team1']:
            user = await self.bot.fetch_user(userDict['userID'])
            team1.append(f"{user.name}#{user.discriminator}({userDict['elo']['elo']})")

        for userDict in lobby['team2']:
            user = await self.bot.fetch_user(userDict['userID'])
            team2.append(f"{user.name}#{user.discriminator}({userDict['elo']['elo']})")

        if timeOut:
            em = discord.Embed(title = "Lobby timed out", description = f"Use `.lobby` to bring it back up")
        elif canceled:
            em = discord.Embed(title = f"Ranked {game} lobby", description = f"This lobby has been canceled")
            return em
        elif started:
            em = discord.Embed(title = f"Ranked {game} lobby", description = f"Lobby Owner: <@{lobbyOwner}>.\nReact to a number to declare that team the winner, or vote ❎ to cancel the lobby.\n Needs majority of player votes to confirm")
        else: 
            em = discord.Embed(title = f"Ranked {game} results", description = f"Lobby Owner: <@{lobbyOwner}>.\nReact to a number to join that team.\nReact 0️⃣ to leave the lobby. The lobby owner cannot leave \n Lobby owner can react ✅ to start the lobby, and ❎ to close the lobby.")
            
        if len(team1) == 0:
            em.add_field(name="Team 1", value = '`\u200b`')
        else:
            em.add_field(name="Team 1", value = f'{chr(10).join(member for member in team1)}')
        if len(team2) == 0:
            em.add_field(name="Team 2", value = '`\u200b`')
        else:
            em.add_field(name="Team 2", value = f'{chr(10).join(member for member in team2)}')

        if result == None:
            numVotes = 0
        else:
            numVotes = len(result['team1']) + len(result['team2']) + len(result['cancel'])
        if started and numVotes > 0:
            res1 = []
            res2 = []
            resCancel = []
            for userDict in result['team1']:
                user = await self.bot.fetch_user(userDict['userID'])
                res1.append(f"{user.name}#{user.discriminator}")
            for userDict in result['team2']:
                user = await self.bot.fetch_user(userDict['userID'])
                res2.append(f"{user.name}#{user.discriminator}")
            for userDict in result['cancel']:
                user = await self.bot.fetch_user(userDict['userID'])
                resCancel.append(f"{user.name}#{user.discriminator}")

            em.add_field(name = "Votes", value = f"**Team 1**{chr(10)}"\
                f"{' '.join(res1)}{chr(10)}"\
                f"**Team 2**{chr(10)}"\
                f"{' '.join(res2)}{chr(10)}"\
                f"**Cancel**{chr(10)}"\
                f"{' '.join(resCancel)}{chr(10)}")

        return em
    async def resultEmbed(self, game, lobby, results, winner):
        team1 = []
        team2 = []
        lobbyOwner = lobby["lobbyOwner"]

        counter = 0
        for userDict in lobby['team1']:
            user = await self.bot.fetch_user(userDict['userID'])
            eloChange = results['team1'][counter]
            if eloChange >= 0:
                changeStr = f"+{eloChange}"
            else:
                changeStr = f"{eloChange}"
            team1.append(f"{user.name}#{user.discriminator}({userDict['elo']['elo']})({changeStr})")
            counter+= 1

        counter = 0
        for userDict in lobby['team2']:
            user = await self.bot.fetch_user(userDict['userID'])
            eloChange = results['team2'][counter]
            if eloChange >= 0:
                changeStr = f"+{eloChange}"
            else:
                changeStr = f"{eloChange}"
                
            team2.append(f"{user.name}#{user.discriminator}({userDict['elo']['elo']})({changeStr})")
            counter += 1
        em = discord.Embed(title = f"Ranked {game} results", description=f"Winner: {winner}")

        em.add_field(name="Team 1", value = f'{chr(10).join(member for member in team1)}')
        em.add_field(name="Team 2", value = f'{chr(10).join(member for member in team2)}')
        return em

    @commands.command(name="rank", case_insensitive=True)
    @checks.registered()
    async def rank(self, ctx, game, user):
        '''Check a players elo for a certain game
        **game**: game elo you want to look up
        **user**: A user you want to look up'''
        game = game.lower()
        mongo = self.bot.mongo
        if game not in self.supportedGames:
            await ctx.send(f"{game} is not a valid game")
            return

        if re.match('^<@!?[0-9]+>$', user) is None:
            await ctx.send("user not found")
            return

        userID = int(re.findall(r'[0-9]+', user)[0])
        if not self.bot.mongo.isRegistered(userID):
            await ctx.send(f"{user} is not registered")
            return

        elos = mongo.getField(userID, "elos")
        if 'elos' not in elos or game not in elos['elos']:
            await ctx.send(f"{user} does not have an elo for {game}")
            return
        else: 
            elo = elos['elos'][game]['elo']
            wins = elos['elos'][game]['wins']
            losses = elos['elos'][game]['losses']
            draws = elos['elos'][game]['draws']
            await ctx.send(f"{user}'s {game} stats are {elo} elo, {wins} wins, {losses} losses, and {draws} draws")

    @commands.command(name="rankTop", case_insensitive=True)
    @checks.registered()
    async def rankTop(self, ctx, game):
        '''Shows the users with the top 10 elos for the specified game
        **game**: game to show the leaderboards for
        '''
        if game not in self.supportedGames:
            await ctx.send(f"{game} is not a valid game")
            return
        collection = self.bot.mongo.collection
        users = ''
        stats = ''
        records = collection.find().sort(f"elos.{game}.elo", -1)
        count = records.count() if records.count() < 10 else 10

        pos = 0
        for doc in records:
            if 'elos' not in doc or game not in doc['elos']:
                break
            username = await self.bot.fetch_user(doc['userID'])
            elo = doc['elos'][game]['elo']
            wins = doc['elos'][game]['wins']
            losses = doc['elos'][game]['losses']
            draws = doc['elos'][game]['draws']

            users += f"{pos+1}. {username}" + "\n"
            stats += f"{elo}({wins}/{losses}/{draws})" + "\n"
            pos += 1

            if pos == count:
                break
        if users == '':
            await ctx.send(f'No rankings for {game}')
            return
        em = discord.Embed(title = f"{game} leaderboard", color=ctx.author.color)
        em.set_thumbnail(url=self.bot.user.avatar_url)
        em.add_field(name = "Top 10", value= users, inline=True)
        em.add_field(name = "Elo (W/L/D)", value=stats, inline=True)
        await ctx.send(embed=em)


    def calculateEloChange(self, elo, average, result):
        #updates elo1 against the average, according to result
        #if result == 0, then the player lost
        #if result == 1, then hte player won
        #if result == .5, then the player drew
        Ea = 1/(1+10**((average-elo)/400))
        K = 16
        change = 16*(result - Ea)
        return round(change)

    def closeLobby(self, lobby, lobbyID, message):
        mongo = self.bot.mongo
        for userDict in lobby['team1']:
            mongo.leaveLobby(userDict['userID'])
        for userDict in lobby['team2']:
            mongo.leaveLobby(userDict['userID'])

        mongo.closeLobby(lobbyID)
        self.lobbies[message][1].cancel()
        del self.lobbies[message]







def setup(bot):
    bot.add_cog(Competitive(bot))
