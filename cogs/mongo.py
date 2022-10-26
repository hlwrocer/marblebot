from discord.ext import commands
import os
import pymongo
#TODO: clean this up, this is so messy and inconsistent. idk if half of these take in int/strings anymore

class Mongo(commands.Cog):
    """For DB operations"""
    def __init__(self, bot):
        self.bot = bot
        MONGODB_URI = os.getenv("MONGODB_URI")
        mongo = pymongo.MongoClient(MONGODB_URI)
        self.db = mongo["marbles"]
        self.collection = self.db["marbleUsers"]
        self.lobbies = self.db["lobbies"]
        self.anime = self.db["anime"]
    def isRegistered(self, userID):
        #mongoDB check
        query = {"userID": int(userID)}
        if self.collection.find_one(query) is None:
            return False
        return True

    def getMarbles(self, userID):
    #assumes userID is registered
        return self.collection.find_one({"userID": userID}, {"_id":0, "marbles":1})['marbles']/100

    def addMarbles(self, userID, amount):
        self.collection.update_one({"userID": userID}, {"$inc": {"marbles": int(round(amount,2)*100)}})

    def getField(self, userID, field):
        return self.collection.find_one({"userID": userID}, {"_id":0, field:1})

    def setField(self, userID, field, value):
        return self.collection.update_one({"userID": userID}, {"$set": {field: value}})

    def deleteField(self, userID, field):
        return self.collection.update_one({"userID":userID}, {"$unset": {field: 1}})

    def getLobbies(self):
        return self.lobbies.find_one({},{})

    def createLobby(self, lobbyInfo):
        return self.lobbies.insert_one(lobbyInfo)

    def saveLobbyField(self, lobbyID, field):
        return self.lobbies.update_one({"_id": lobbyID}, {"$set": field})

    def startLobby(self, lobbyID):
        return self.lobbies.update_one({"_id": lobbyID}, {"$set": {"started": 1}})

    def getLobby(self, lobbyID):
        return self.lobbies.find_one({"_id": lobbyID})

    def getUserLobby(self, userID):
        #returns game lobby info for userID, or -1 if not available
        elos = self.collection.find_one({"userID": userID}, {"_id":0, "elos":1})
        if 'elos' not in elos or elos['elos']['lobby'] == -1:
            return -1
        lobbyID = elos['elos']['lobby']
        lobbyInfo = self.lobbies.find_one({"_id": lobbyID})
        return lobbyInfo

    def joinLobby(self, lobbyID, userID):
        return self.collection.update_one({"userID": userID}, {"$set": {f"elos.lobby": lobbyID}})

    def leaveLobby(self, userID):
        return self.collection.update_one({"userID": userID}, {"$set": {f"elos.lobby": -1}})

    def closeLobby(self, lobbyID):
        return self.lobbies.delete_one({"_id": lobbyID})

    def getElo(self, game, userID):
        return self.collection.find_one({"userID": userID}, {"_id":0, f"elos.{game}.elo": 1})

    def updateElo(self, game, user, record):
        return self.collection.update_one({"userID": user}, {"$set": {f"elos.{game}": record}})

    def createElo(self, user, record):
        return self.collection.update_one({"userID": user}, {"$set": {"elos": record}})

    def getAnime(self, animeID):
        return self.anime.find_one({"animeID": animeID})

    def setAnime(self, animeID, animeInfo):
        return self.anime.update_one({"animeID": animeID}, {"$set": animeInfo})

    def getDailyAnime(self, day):
        return self.anime.find({"day": day})

    def createAnime(self, animeInfo):
        return self.anime.insert_one(animeInfo)

    def deleteAnime(self, animeID):
        return self.anime.delete_one({"animeID": animeID})




async def setup(bot):
    await bot.add_cog(Mongo(bot))
