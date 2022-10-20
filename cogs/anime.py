from discord.ext import commands
import discord
import yfinance as yf
import requests
from datetime import datetime
from pytz import timezone
from helpers import checks
import pytz
#TODO
#possibly support variable day searches?
#tracking specific anime to see when it will air next?
    #shouldn't be user specific, so only i can do it (doon), don't want this to be MAL the bot or something
#idk other anime related stuff

class Anime(commands.Cog):
    """For anime commands"""
    def __init__(self, bot):
        self.bot = bot

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


def setup(bot):
    bot.add_cog(Anime(bot))
