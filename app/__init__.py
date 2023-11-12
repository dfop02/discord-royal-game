import importlib
import asyncio
from os import getenv
import builtins
from dotenv import load_dotenv
import discord
from app.commands import __all__ as all_commands
from discord.ext import commands

load_dotenv()

def setup_commands(bot):
    for cmd in all_commands:
        asyncio.run(bot.load_extension(f'app.commands.{cmd}'))

def create_app():
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)
    builtins.bot = bot
    setup_commands(bot)
    bot.run(getenv('DISCORD_TOKEN'))
