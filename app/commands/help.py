import discord
from discord.ext import commands
    
@commands.command()
async def help(ctx):
    embed = discord.Embed(title="Help commands", description="Shows various help commands")
    embed.add_field(name="Show this help", value = "`$help`", inline=False)
    embed.add_field(name="Start Royal Game", value="`$start_royal`", inline=False)
    await ctx.send(embed=embed)

async def setup(bot):
    bot.add_command(help)
