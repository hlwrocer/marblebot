from discord.ext import commands
from helpers import checks, util
from bson.codec_options import CodecOptions
from datetime import datetime
from pytz import timezone
import re
import discord

class Bot(commands.Cog):
    '''General marble bot commands'''
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="register", case_insensitive=True)
    @checks.addRole()
    async def register(self, ctx):
        '''Register to use the bot and get 100 marbles'''
        query = {"userID" : ctx.author.id}
        collection = self.bot.mongo.collection
        if collection.count_documents(query, limit=1)==0:
            query = {"userID": ctx.author.id, "marbles": 10000}
            collection.insert(query)
            await ctx.channel.send("{} is given 100 marbles".format(ctx.message.author.mention))
        else:
            await ctx.channel.send("{} you already registered noob".format(ctx.message.author.mention))

    @commands.command(name="marbles", case_insensitive=True)
    @checks.addRole()
    async def marbles(self, ctx, user=None):
        '''Check how many marbles you or a user has
        **user** (optional): A user you want to look up'''
        if user == None:
            if not self.bot.mongo.isRegistered(ctx.author.id):
                await ctx.send(f"{ctx.author.mention} you are not registered.")
                return
            userID = ctx.author.id
            user = ctx.message.author.mention
        else:
            if re.match('^<@!?[0-9]+>$', user) is None:
                await ctx.send("user not found")
                return

            userID = int(re.findall(r'[0-9]+', user)[0])
            if not self.bot.mongo.isRegistered(userID):
                await ctx.send(f"{user} is not registered")
                return

        numMarbles = self.bot.mongo.getMarbles(userID)
        await ctx.send(f"{user} has {numMarbles} marbles")

    @commands.command(name="give", case_insensitive=True)
    @checks.registered()
    @checks.addRole()
    async def give(self, ctx, user, number: float):
        '''Give a user marbles
        **user**: User you want to give marbles to
        **number**: Number of marbles you want to give'''

        authorid = ctx.message.author.id
        #parse mentionid
        if re.match('^<@!?[0-9]+>$', user) is None:
            await ctx.send("user not found")
            return

        mentionid = int(re.findall(r'[0-9]+', user)[0])
        

        #some failure conditions and very bad parsing this is a mess xd
        #TODO: change thos first condition to lookup user in guild
        if not self.bot.mongo.isRegistered(mentionid):
            await ctx.send(f"{user} is not registered, cannot give marbles")
            return
        elif mentionid == authorid:
            await ctx.send(f"{ctx.message.author.mention} you can't give yourself marbles")
            return

            #if re.match('^[0-9]*\.?[0-9]{0,2}$', number) is None:
            #    raise commands.BadArgument
        number = round(number)
        if number <= 0:
            await ctx.send("You must give more than 0 marbles")
            return

        #give marbles
        marbleCount = self.bot.mongo.getMarbles(authorid)
        if marbleCount < number:
            await ctx.send(f"{ctx.author.mention} get more marbles noob")
            return
        self.bot.mongo.addMarbles(authorid, -1*number)
        self.bot.mongo.addMarbles(mentionid, number)

        await ctx.send(f"{ctx.author.mention} gave {number} marbles to {user}")

    @commands.command(name="daily", case_insensitive=True)
    @checks.registered()
    @checks.addRole()
    async def daily(self, ctx):
        '''Collect your daily 10 marbles'''
        collection = self.bot.mongo.collection
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
        self.bot.mongo.addMarbles(userID, 10)
        await ctx.send(f"{ctx.author.mention} you get 10 daily marbles")

        re


    @commands.command(name="top", case_insensitive=True)
    async def top(self, ctx):
        '''Show the top 10 marble holders'''
        collection = self.bot.mongo.collection
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
            username = await self.bot.fetch_user(doc['userID'])
            marbleCount = doc['marbles']/100
            users += f"{pos+1}. {username}" + "\n"
            numMarbles += f"{marbleCount}" + "\n"
            pos+=1
            if pos == count:
                break

        em = discord.Embed(title = "Marble leaderboard", color=ctx.author.color)
        em.set_thumbnail(url=self.bot.user.avatar_url)
        em.add_field(name = "Top 10", value= users, inline=True)
        em.add_field(name = "Marbles", value=numMarbles, inline=True)
        
        await ctx.send(embed=em)

    @commands.command(name="notrazzle", case_insensitive=True)
    async def notrazzle(self, ctx):
        '''get the not razzle role if you aren't razzle'''

        if ctx.author.id == 135641637740085248:
            await ctx.send(f"nice try {ctx.author.mention}")
        else:
            for role in ctx.author.roles:
                if role.name == "not razzle":
                    await f"{ctx.author.mention}, you are already not razzle"
                    return

            role = getRole(ctx.guild, "not razzle")
            await ctx.message.author.add_roles(role)
            await ctx.send(f"{ctx.author.mention}, you are officially not razzle")



def setup(bot):
    bot.add_cog(Bot(bot))
