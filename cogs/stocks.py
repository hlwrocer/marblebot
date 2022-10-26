from discord.ext import commands
import discord
import yfinance as yf
from helpers import checks

class Stocks(commands.Cog):
    """For stock commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="stocks", aliases=["stonks"], case_insensitive=True, invoke_without_command=True)
    async def stocks(self, ctx):
        '''Buy and sell stocks'''
        await ctx.send_help(ctx.command)

    @checks.registered()
    @stocks.command(name="lookup", aliases=["lu"], case_insensitive=True)
    async def lookup(self, ctx, ticker: str):
        '''Lookup a stock ticker
        **ticker**: Ticker you want to lookup'''
        stock = yf.Ticker(ticker)
        info = stock.history("1d")
        if len(info) == 0:
            await ctx.send(f"Ticker not found")
        else:
            price = info["Close"][0]
            await ctx.send(f"{ticker.upper()}: ${round(price,2)}")

    @checks.registered()
    @stocks.command(name="buy", aliases=["b"], case_insensitive=True)
    async def buy(self, ctx, ticker: str, quantity: int):
        '''Buy *quantity* amount of a stock
        **ticker**: ticker of the stock you want to buy
        **quantity**: amount of the stock you want to buy'''
        quantity = int(quantity)
        ticker = ticker.upper()
        stockInfo = yf.Ticker(ticker).history("1d")
        userID = ctx.author.id
        collection = self.bot.mongo.collection
        costBasis = owned = 0
    
        if len(stockInfo) == 0:
            await ctx.send(f"Ticker not found")
            return
        else:
            price = round(stockInfo["Close"][0],2)

        cost = price * quantity
        marbleCount = self.bot.mongo.getMarbles(userID)

        if marbleCount < cost:
            await ctx.send(f"Not enough marbles.")
            return

        portfolio = self.bot.mongo.getField(ctx.author.id, "portfolio")
        if len(portfolio) != 0 and ticker in portfolio['portfolio']:
            costBasis = portfolio['portfolio'][ticker]["costBasis"]
            totalCost = (costBasis * portfolio['portfolio'][ticker]['quantity']) + cost

            owned = portfolio['portfolio'][ticker]["quantity"] + quantity
            costBasis = round(totalCost / owned, 2)
        else:
            owned = quantity
            costBasis = price


        self.bot.mongo.addMarbles(userID, -1*cost)
        collection.update_one({"userID": userID}, {"$set": {f"portfolio.{ticker}.quantity": owned,
                                                            f"portfolio.{ticker}.costBasis": costBasis}})
        await ctx.send(f"{ctx.author.mention}, {quantity} shares of {ticker} bought for {round(cost,2)} marbles.")

    @checks.registered()
    @stocks.command(name="sell", aliases=["s"], case_insensitive=True)
    async def sell(self, ctx, ticker: str, quantity: int):
        '''Sell *quantity* amount of a stock
        **ticker**: ticker of the stock you want to sell
        **quantity**: amount of the stock you want to sell'''
        quantity = int(quantity)
        ticker = ticker.upper()
        userID = ctx.author.id
        collection = self.bot.mongo.collection

        portfolio = self.bot.mongo.getField(ctx.author.id, "portfolio")
        owned = portfolio['portfolio'][ticker]['quantity']

        #Some checks
        if portfolio == None or len(portfolio) == 0:
            await ctx.send(f"{ctx.author.mention} you don't own any stocks")
            return

        if ticker not in portfolio['portfolio']:
            await ctx.send(f"{ctx.author.mention} you don't own any {ticker}")
            return

        if quantity > owned:
            await ctx.send(f"{ctx.author.mention} you only have {owned} shares of {ticker}")
            return

        stockInfo = yf.Ticker(ticker).history("1d")
        price = round(stockInfo["Close"][0],2)
        
        owned -= quantity
        if owned == 0:
            collection.update_one({"userID": userID}, {"$unset": {f"portfolio.{ticker}": 1}})
        else:
            collection.update_one({"userID": userID}, {"$set": {f"portfolio.{ticker}.quantity": owned}})

    
        self.bot.mongo.addMarbles(userID, price*quantity)
        await ctx.send(f"{ctx.author.mention}, {quantity} shares of {ticker} sold for {round(price*quantity,2)} marbles.")

    @commands.cooldown(1, 60, commands.BucketType.user)
    @checks.registered()
    @stocks.command(name="portfolio", aliases=["p"], case_insensitive=True)
    async def portfolio(self, ctx):
        '''Get your stock portfolio'''
        portfolio = self.bot.mongo.getField(ctx.author.id, "portfolio")
        if portfolio == {} or len(portfolio['portfolio']) == 0:
            await ctx.send(f"{ctx.author.mention} you don't own any stocks")
            return

        embed = discord.Embed()
        embed.title = f"{ctx.author.name}'s portfolio"
        embed.description = None
        stocks = quantity = value = costBasis = ""

        for stock, info in portfolio['portfolio'].items():
            stocks += f"{stock}\n"
            price = yf.Ticker(stock).history("1d")["Close"][0]
            quantity += f"{info['quantity']}\n"
            value += f"{round(price,2)} ({info['costBasis']})\n"

        embed.add_field(name = "Stock", value = stocks, inline=True)
        embed.add_field(name = "Quantity", value = quantity, inline=True)
        embed.add_field(name = "Value (Cost Basis)", value = value, inline=True)

        await ctx.send(embed = embed)


        





async def setup(bot):
    await bot.add_cog(Stocks(bot))
