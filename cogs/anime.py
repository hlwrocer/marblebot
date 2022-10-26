from discord.ext import commands
import discord
import yfinance as yf
import requests
from discord.ext import tasks
from datetime import datetime, time
from backports.zoneinfo import ZoneInfo
from pytz import timezone
from helpers import checks
import pytz
import re
#TODO
#possibly support variable day searches?
#tracking specific anime to see when it will air next?
    #shouldn't be user specific, so only i can do it (doon), don't want this to be MAL the bot or something
#idk other anime related stuff

class Anime(commands.Cog):
    """For anime commands"""
    def __init__(self, bot):
        self.bot = bot
        self.animeAlert.start()

    @commands.group(name="anime", aliases=["animemes"], case_insensitive=True, invoke_without_command=True)
    async def anime(self, ctx):
        '''anime related commands'''
        await ctx.send_help(ctx.command)

    @commands.cooldown(1, 30, commands.BucketType.user)
    @anime.command(name="airing", aliases=["air"], case_insensitive=True)
    async def airing(self, ctx):
        '''Get the list of anime airing today'''
        #TODO possibly do it for non today days

        query = '''
        query ($start: Int, $end: Int){
            Page{
                airingSchedules(sort:TIME, airingAt_lesser: $end, airingAt_greater: $start){
                    airingAt
                    media{
                        title{
                            userPreferred
                        }
                    }
                }
            }
        }
        '''
        curTime = datetime.now(timezone("US/Eastern"))
        epochTime = int(curTime.timestamp())
        endOfDay = epochTime + ((24 - curTime.hour - 1)*60*60) + ((60 - curTime.minute - 1)*60) + (60 - curTime.second)
        startOfDay = endOfDay - 86400

        variables = {
                "end": endOfDay,
                "start": startOfDay
                }

        url = 'https://graphql.anilist.co'
        response = requests.post(url, json={'query': query, 'variables': variables})
        todaysAnime = response.json()['data']['Page']['airingSchedules']

        em = discord.Embed(title = "Today's Airing Anime", description = "Anime airing today")

        titles = ''
        airTime = ''
        fmt = '%H:%M:%S'
        for anime in todaysAnime:
            titles += f"{anime['media']['title']['userPreferred']}\n"
            airing = anime['airingAt']
            dt = datetime.utcfromtimestamp(airing)
            dt = dt.replace(tzinfo=pytz.UTC)
            dt = dt.astimezone(timezone("US/Eastern"))
            airTime += f"{dt.strftime(fmt)}\n"


        em.add_field(name = "Title", value = titles, inline=True)
        em.add_field(name = "Air Time (EST)", value = airTime, inline=True)

        await ctx.send(embed=em)

    
    @commands.cooldown(1, 5, commands.BucketType.user)
    @anime.command(name="track", aliases=["t"], case_insensitive=True)
    @checks.registered()
    async def track(self, ctx, anime):
        '''Track an anime. Optionally specify the season and year to narrow down the search.
        **anime**: Name of anime you want to track
        '''

        #build the fields depending on args
        #i have no idea how the search field works, seems decent enough
        fields = "$search: String"
        mediaFields = "search: $search"
        variables = {
                "search": anime
                }

        url = 'https://graphql.anilist.co'
        query = '''
        query ($search: String){
            Page{
                media(search: $search, status_in: [RELEASING, NOT_YET_RELEASED], type: ANIME){
                    id
                    season
                    seasonYear
                    title {
                        userPreferred
                    }
                    endDate{
                        year
                        month
                        day
                    }
                    startDate{
                        year
                        month
                        day
                    }
                }
            }
        }
        '''
        response = requests.post(url, json={'query': query, 'variables': variables})
        JSONanimeInfo = response.json()['data']['Page']['media']
        if len(JSONanimeInfo) == 0:
            await ctx.send("No anime found")
            return
        animeInfo = []


        for anime in JSONanimeInfo:
            if anime['season'] is not None:
                animeInfo.append(anime)

        selection = ''
        name = ''
        if len(animeInfo) > 1:
            em = discord.Embed(title = "Anime search results", description = "Multiple anime. Type the number you would like to track.")
            for x in range(len(animeInfo)):
                name += f'{x+1}) {animeInfo[x]["title"]["userPreferred"]}' + "\n"
            em.add_field(name = 'Anime Title', value = name, inline=True)
            await ctx.send(embed=em)
            def check(msg):
                return msg.author.id == ctx.message.author.id and msg.channel == ctx.message.channel
            msg = await self.bot.wait_for('message', check=check, timeout=30)
            if re.match('^[0-9]*$', msg.content) is None:
                await ctx.send(f"{ctx.author.mention} pick a valid anime")
                return

            elif int(msg.content) > len(animeInfo) or int(msg.content) < 1:
                await ctx.send(f"{ctx.author.mention} pick a valid anime")
                return 

            else:
                choice = int(msg.content) - 1
 
            animeInfo = [animeInfo[choice]]



        #add anime
        authorid = ctx.message.author.id
        anime = self.bot.mongo.getField(authorid, "anime")
        if anime != {}:
            anime = anime['anime']
        animeID = str(animeInfo[0]['id'])

        if animeID in anime:
            await ctx.send(f"{ctx.author.mention} you're already tracking this anime")
            return

        #user is now tracking this anime
        anime[animeID] = animeInfo[0]['title']['userPreferred']
        self.bot.mongo.setField(authorid, "anime", anime)
        #update anime tracker list
        animeList = self.bot.mongo.getAnime(animeID)

        if animeInfo[0]['endDate']['year'] == None:
            endDate = None
        else:
            endDate = datetime(animeInfo[0]['endDate']['year'], animeInfo[0]['endDate']['month'], animeInfo[0]['endDate']['day'])

        print("END DATE", endDate)

        if animeList == None:
            animeList = {
                    'animeID': animeID,
                    'title': animeInfo[0]['title']['userPreferred'],
                    'users': {str(ctx.author.id): "1"},
                    'lastEpisode': endDate
                    }
            
            self.bot.mongo.createAnime(animeList)
        else:
            animeList['users'][str(ctx.author.id)] = '1'
            self.bot.mongo.setAnime(animeID, animeList)

        await ctx.send(f"{ctx.author.mention} you are now tracking {animeInfo[0]['title']['userPreferred']}")

        
    @commands.cooldown(1, 15, commands.BucketType.user)
    @anime.command(name="list", aliases=["l"], case_insensitive=True)
    @checks.registered()
    async def list(self, ctx):
        """Lists your tracked anime"""
        authorid = ctx.message.author.id
        anime = self.bot.mongo.getField(authorid, "anime")
        if anime == {}:
            await ctx.send(f"{ctx.author.mention} you are not tracking any anime.")
            return
        anime = anime['anime']
        em = discord.Embed(title = "Tracked anime", description = "Anime you're tracking. Type an untrack (Anime ID) to untrack it")

        def check(msg):
            return msg.author.id == ctx.message.author.id and msg.channel == ctx.message.channel

        
        embedAnime = ""
        for key,value in anime.items():
            embedAnime += f'({key}) {value}' + "\n"
        em.add_field(name = 'Tracked anime', value = embedAnime, inline=True)
        await ctx.send(embed = em)
        msg = await self.bot.wait_for('message', check=check, timeout=15)
        if re.match('^untrack [0-9]+$', msg.content) is not None:
            choice = msg.content.split(" ")[1]

            if choice in anime:
                self.bot.mongo.deleteField(authorid, f"anime.{choice}")
                animeList = self.bot.mongo.getAnime(choice)
                del animeList['users'][str(authorid)]
                self.bot.mongo.setAnime(choice, animeList)
                await ctx.send(f"{ctx.author.mention} removed {anime[choice]} from your tracking list.")

            else:
                await ctx.send(f"{ctx.author.mention} enter a valid id")




        #remove user from alert list
        
    #dt = time(hour=17, minute=0, second = 0, tzinfo = timezone("US/Eastern"))
    
    #Doesn't account for daylight savings, UTC
    @tasks.loop(time=time(hour=17, minute=0, second = 0, tzinfo=ZoneInfo('US/Eastern')))
    async def animeAlert(self):
        #hard coded channel id cause bot only runs in one server
        channelID = 851281506637709342
        #TODO: Handle updating when an end date gets added to an anime some how, possibly just requery server and see if there's an update?
        channel = self.bot.get_channel(channelID)
        await channel.send("Anime time onii-chans ( ˶ˆ꒳ˆ˵ ). Looking up what's airing today! ヾ( ˃ᴗ˂ )◞ • *✰")
        #day = datetime.now(timezone("US/Eastern")).strftime('%A')
        #cursor = self.bot.mongo.getDailyAnime(day)
        query = '''
        query ($start: Int, $end: Int){
            Page{
                airingSchedules(sort:TIME, airingAt_lesser: $end, airingAt_greater: $start){
                    media{
                        title{
                            userPreferred
                        }
                    }
                    mediaId
                }
            }
        }
        '''
        curTime = datetime.now(timezone("US/Eastern"))
        epochTime = int(curTime.timestamp())
        endOfDay = epochTime + ((24 - curTime.hour - 1)*60*60) + ((60 - curTime.minute - 1)*60) + (60 - curTime.second)
        startOfDay = endOfDay - 86400

        variables = {
                "end": endOfDay,
                "start": startOfDay
                }

        url = 'https://graphql.anilist.co'
        response = requests.post(url, json={'query': query, 'variables': variables})
        todaysAnime = response.json()['data']['Page']['airingSchedules']

        airingAnimeIDs = {}
        for anime in todaysAnime:
            airingAnimeIDs[str(anime['mediaId'])] = anime['media']['title']

        cursor = self.bot.mongo.anime.find({})
        trackedAnime = list(cursor)
        animeIDs = {}
        animeTime = False
        print(airingAnimeIDs)
        print(trackedAnime)
        for anime in trackedAnime:
            userIDs = ""
            if anime['animeID'] in airingAnimeIDs:
                for userID in anime['users'].keys():
                    userIDs += f"<@{userID}> "
                if userIDs != "":
                    animeTime = True
                    await channel.send(userIDs + f"{anime['title']} comes out today! o(≧∇≦o)")
            if anime['lastEpisode'] is not None and anime['lastEpisode'].date() <= datetime.today().date():
                #delete this track from stuff, should be last episode or somehow got past the date
                animeID = anime['animeID']
                print(anime)
                for userID in anime['users'].keys():
                    self.bot.mongo.deleteField(int(userID), f"anime.{animeID}")
                    userIDs += f"<@{userID}> "
                self.bot.mongo.deleteAnime(animeID)
            #TODO: if end date is none, check if there's a end date, and update


        if not animeTime:
            await channel.send("No anime today onii-chans‧º·(˚ ˃̣̣̥⌓˂̣̣̥ )‧º·˚")





        
        '''
        docList = list(cursor)
        if len(docList) == 0:
            await channel.send("No anime today onii-chans‧º·(˚ ˃̣̣̥⌓˂̣̣̥ )‧º·˚")
        else:
            for doc in docList:
                userIDs = ""
                if doc['lastEpisode'] is not None and doc['lastEpisode'].date() <= datetime.today().date():
                    #delete this track from stuff, should be last episode or somehow got past the date
                    animeID = doc['animeID']
                    print(doc)
                    for userID in doc['users'].keys():
                        self.bot.mongo.deleteField(int(userID), f"anime.{animeID}")
                        userIDs += f"<@{userID}> "
                    self.bot.mongo.deleteAnime(animeID)
                else:
                    for userID in doc['users'].keys():
                        userIDs += f"<@{userID}> "
                if userIDs != "":
                    await channel.send(userIDs + f"{doc['title']} comes out today! o(≧∇≦o)")
     
     '''






    @commands.Cog.listener()
    async def on_ready(self):
        print(self.animeAlert.is_running())
        if not self.animeAlert.is_running():
            self.animeAlert.start()












async def setup(bot):
    await bot.add_cog(Anime(bot))
