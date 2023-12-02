import asyncio
import discord
import random
import re
from datetime import datetime, timedelta
from discord.ext import commands
from app.utils import *
from app.music.player import YTDLSource

@commands.command()
async def start_royal(ctx):
    global bot
    game_json = {'players': {}, 'player_ids': {}, 'settings': {}}
    await clear_last_msg(ctx, n_msgs=100)
    await ctx.send(f"{ctx.author}, welcome to Royal Game!\nWhat will be the theme of game?")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    game_json.update(await game_theme(bot, ctx, check=check))
    game_json['settings'].update(await game_players(bot, ctx, check=check))
    game_json['settings'].update(await game_settings(bot, ctx, check=check))
    game_json = await link_phase(bot, ctx, game_json)

    await start_game(bot, ctx, game_json)

async def game_theme(bot, ctx, check=None):
    msg = await bot.wait_for("message", check=check)
    response = await ctx.send(f"Ok, the Theme will be {msg.content.title()}, correct?")

    emojis = ['✅', '❌']
    for emoji in emojis:
        await response.add_reaction(emoji)

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=10, check=lambda reaction, user: str(reaction.emoji) in emojis)
    except asyncio.TimeoutError:
        await ctx.send("timeout")
    else:
        if reaction.emoji == '✅':
            await ctx.send('Ok! Theme saved')
            await clear_last_msg(ctx, n_msgs=5)
            return {'theme': msg.content.title()}
        elif reaction.emoji == '❌':
            await clear_last_msg(ctx)
            await ctx.send('ok, then please type the theme again')
            game_theme(check=check)

async def game_players(bot, ctx, check=None):
    react = ["🇦","🇧"]

    response = await ctx.send(
        (
            "Ok, next let's talk about the players.\n"
            'Do you prefer limit how many players will play (A),\n'
            'or wait then to join here in 5 minutes (B)?\n'
            'React with your choice.\n'
        )
    )

    def react_check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in react

    for emoji in react:
        await response.add_reaction(emoji)

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=10.0, check=react_check)
    except asyncio.TimeoutError:
        await channel.send('👎')
    else:
        i = react.index(str(reaction))
        entry = str(i) + "|" + str(ctx.author) + "\n"
        if i == 0:
            await ctx.send('How many players will participate?')
            limit_players = await bot.wait_for('message', check=check)
            await clear_last_msg(ctx, n_msgs=3)
            return {'limit_players': int(re.sub(r'\D', '', limit_players.content))}
        else:
            return {'limit_players': None}

async def game_settings(bot, ctx, check=None):
    await ctx.send(f'Send me the voice channel where do you want the game happens.')
    channel = await bot.wait_for("message", check=check)

    await ctx.send('Last question, how long should I wait to start the game from now? (In minutes, max. 1 hour)')
    duration = await bot.wait_for("message", check=check)
    await clear_last_msg(ctx, n_msgs=4)
    return {'voice_channel_id': re.sub(r'\D', '', channel.content), 'start_duration': int(re.sub(r'\D', '', duration.content))}

async def link_phase(bot, ctx, game_json):
    await ctx.send(
        (
            'Settings done!\n'
            f"Link Phase Start, you have {str(game_json['settings']['start_duration'])} minutes to send your link,\n"
            'each user can only send one link per game.'
        )
    )

    endTime = datetime.now() + timedelta(minutes=game_json['settings']['start_duration'])
    limit_players = game_json['settings']['limit_players']

    def check_msg(msg):
        return not msg.author.bot and msg.author.name not in game_json['players'].keys() and msg.channel == ctx.channel

    async def listen_links(msg):
        if not check_msg(msg):
            return

        await msg.edit(suppress=True)
        valid, error = await valid_yt_link(msg.content)

        if valid:
            game_json['players'][msg.author.name] = msg.content
            game_json['player_ids'][msg.author.name] = msg.author.id
            await clear_last_msg(ctx)
            await ctx.send(f'{msg.author.name}, your link was registered!')
        else:
            await ctx.send(error)

    bot.add_listener(listen_links, 'on_message')

    while True:
        reach_time_limit = datetime.now() > endTime
        reach_player_limit = limit_players and (len(game_json['players'].keys()) >= limit_players)
        if reach_time_limit:
            game_json['settings']['limit_players'] = len(game_json['players'].keys())
            break
        elif reach_player_limit:
            break

        await asyncio.sleep(2)

    bot.remove_listener(listen_links, 'on_message')
    await ctx.send(f"Link Phase Finished! Starting game in few seconds...\n**{'#'*50}**")

    return game_json

async def start_game(bot, ctx, game_json):
    brackets = generate_tournament_brackets(list(game_json['players'].items()), shuffle=True)
    voice_client = await join_voice(bot, ctx.guild, game_json['settings']['voice_channel_id'])
    tournament_running = True
    round_number = 1

    while tournament_running:
        await print_tournament(ctx, brackets, round_number)
        brackets, tournament_running = await run_current_bracket(bot, ctx, voice_client, brackets, game_json)
        round_number += 1

    await voice_client.disconnect()
    brackets = sum(brackets, ())
    await ctx.send(f"Congratulations, <@{game_json['player_ids'][brackets[0]]}>! Your video \"{brackets[1]}\" wins!")

async def print_tournament(ctx, brackets, round_number):
    prepare_round = iter([username for bracket in brackets for username, _ in bracket])
    current_round = []
    for item in prepare_round:
        next_item = next(prepare_round, None)
        current_round.append(f'{item} vs {next_item}' if next_item else item)
    await ctx.send(f'Round {str(round_number)}º\n' + ' | '.join(current_round))

async def run_current_bracket(bot, ctx, voice, brackets, game_json):
    react = ["🇦","🇧"]
    future_bracket = []
    select_timeout = 30

    for bracket in brackets:
        react_index = 0

        if len(bracket) == 1:
            future_bracket.append(bracket[0])
            continue

        await print_current_match(ctx, bracket)

        for username, video_url in bracket:
            playing_msg = await ctx.send(f"{react[react_index]} Playing...")
            await playing_msg.add_reaction('⏭️')
            await play(bot, voice, video_url, game_json)
            react_index += 1

        response = await ctx.send(f'Which was better? You have {str(select_timeout)} seconds to decide, {react[0]} or {react[1]}?')

        for emoji in react:
            await response.add_reaction(emoji)

        await asyncio.sleep(select_timeout)

        msg = await ctx.channel.fetch_message(response.id)

        for reaction in msg.reactions:
            async for user in reaction.users():
                if user.id not in game_json['player_ids'].values():
                    await reaction.remove(user)

        choice_a = next((reaction.count-1 for reaction in msg.reactions if reaction.emoji == react[0]), 0)
        choice_b = next((reaction.count-1 for reaction in msg.reactions if reaction.emoji == react[1]), 0)
        highest_reaction = ''

        if choice_a == choice_b:
            random_choice = random.randint(0, 1)
            highest_reaction = react[random_choice]
            future_bracket.append(bracket[random_choice])
        elif choice_a > choice_b:
            highest_reaction = react[0]
            future_bracket.append(bracket[0])
        else:
            highest_reaction = react[1]
            future_bracket.append(bracket[1])

        if len(brackets) > 1:
            await ctx.send(f"{highest_reaction} wins {'by random' if choice_a == choice_b else ''}\n**{'#'*50}**")

    return (generate_tournament_brackets(future_bracket), len(future_bracket) != 1)

def generate_tournament_brackets(players, shuffle=False):
    bracket = []
    keys = players

    if len(keys) == 1:
        return keys

    if shuffle:
        random.shuffle(keys)

    def divide_chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    return list(divide_chunks(keys, 2))

async def join_voice(bot, guild, voice_channel_id):
    current_voice = discord.utils.get(bot.voice_clients, guild=guild)
    new_voice = bot.get_channel(int(voice_channel_id))

    if current_voice and current_voice.is_connected():
        await current_voice.move_to(new_voice)
    else:
        return await new_voice.connect(reconnect=False)

async def play(bot, voice, url, game_json):
    player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
    voice.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

    def emoji_check(reaction, user):
        return str(reaction.emoji) == '⏭️'

    while voice.is_playing():
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=player.duration, check=emoji_check)
            if reaction.count-1 >= game_json['settings']['limit_players']/2:
                voice.pause()
        except asyncio.TimeoutError:
            pass

        await asyncio.sleep(1)

async def setup(bot):
    bot.add_command(start_royal)
    globals()['bot'] = bot
