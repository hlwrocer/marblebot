from discord.ext import commands
from helpers.util import *
def registered():
    #discord coroutine check for most commands
    async def predicate(ctx):
        userID = ctx.author.id
        query = {"userID": userID}
        if ctx.bot.mongo.collection.find_one(query) is None:
            await ctx.send(f"{ctx.author.mention} please register to marble")
            return False
        return True

    return commands.check(predicate)

def addRole():
    async def predicate(ctx):
        hasRole = False
        for role in ctx.author.roles:
            if role.name == "marble-bois":
                hasRole = True
                break

        if not hasRole:
            role = getRole(ctx.guild, "marble-bois")
            await ctx.message.author.add_roles(role)
        return True

    return commands.check(predicate)

