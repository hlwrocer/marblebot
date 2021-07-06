from discord.ext import commands
import os
import pymongo

class Mongo(commands.Cog):
    """For DB operations"""
    def __init__(self, bot):
        self.bot = bot
        MONGODB_URI = os.getenv("MONGODB_URI")
        mongo = pymongo.MongoClient(MONGODB_URI)
        self.db = mongo["marbles"]
        self.collection = self.db["marbleUsers"]
    def isRegistered(self, userID):
        #mongoDB check
        query = {"userID": int(userID)}
        if self.collection.find_one(query) is None:
            return False
        return True

    def getMarbles(self, userID):
    #assumes userID is registered
        return self.collection.find_one({"userID": userID}, {"_id":0, "marbles":1})['marbles']

    def addMarbles(self, userID, amount):
        self.collection.update_one({"userID": userID}, {"$inc": {"marbles": amount}})



def setup(bot):
    bot.add_cog(Mongo(bot))
