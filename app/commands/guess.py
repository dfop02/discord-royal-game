import asyncio
import discord
import os
import re
import random
import json
from discord.ext import commands
from app.utils import *
from app.music.player import YTDLSource

json_settings_path = os.path.join(os.getcwd(), 'settings.json')
json_anime_path = os.path.join(os.getcwd(), 'animes.json')

@commands.command()
async def guess(ctx, video_limit=5):
    global bot

    voice_channel_id = await ask_voice_channel(bot, ctx)

    with open(json_anime_path) as json_file:
        animes = json.load(json_file)

    random_animes = random.sample(list(animes['animes']), video_limit)
    voice = await join_voice(bot, ctx.guild, voice_channel_id)
    for index, anime_source in enumerate(random_animes):
        anime_name = anime_source['name']
        difficult = anime_source['difficult']
        anime_url = anime_source['url']
        playing_msg = await ctx.send(f'Playing anime {index+1} | difficult {difficult}')
        await play(bot, voice, anime_url, anime_name, ctx)

async def ask_voice_channel(bot, ctx):
    await ctx.send(f'Send me the voice channel where do you want the game happens.')
    voice_channel = await bot.wait_for('message', check=lambda msg: msg.author == ctx.author and msg.channel == ctx.channel)
    return re.sub(r'\D', '', voice_channel.content)

async def join_voice(bot, guild, voice_channel_id):
    current_voice = discord.utils.get(bot.voice_clients, guild=guild)
    new_voice = bot.get_channel(int(voice_channel_id))

    if current_voice and current_voice.is_connected():
        await current_voice.move_to(new_voice)
    else:
        return await new_voice.connect(reconnect=False)

async def play(bot, voice, url, anime_name, ctx):
    global answer_found
    player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
    voice.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
    answer_found = False

    def check_msg(msg):
        return not msg.author.bot and msg.channel == ctx.channel

    async def listen_answers(msg):
        if not check_msg(msg):
            return

        if msg.content.lower() == anime_name.lower():
            global answer_found
            answer_found = True
            await ctx.send(f'{msg.author.name}, correct! Next start in 5 seconds!', reference=msg)

    bot.add_listener(listen_answers, 'on_message')
    while voice.is_playing():
        if answer_found:
            await asyncio.sleep(5)
            voice.pause()

        await asyncio.sleep(1)

    if not answer_found:
        await ctx.send(f'Anyone found the name, the anime was {anime_name}!')
    bot.remove_listener(listen_answers, 'on_message')

async def setup(bot):
    bot.add_command(guess)
    globals()['bot'] = bot
