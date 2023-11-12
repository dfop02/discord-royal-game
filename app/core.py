import discord
from discord.ext import commands

# Enable ALL intents then everything will work fine
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

@bot.command()
async def setup(ctx, arg):
    await ctx.send(arg)
