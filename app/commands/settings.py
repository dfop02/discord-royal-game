import discord
import os
import json
from discord.ext import commands

json_settings_path = os.path.join(os.getcwd(), 'settings.json')

@commands.command()
async def test(ctx):
    async for entry in ctx.guild.audit_logs(limit=10):
        print(entry)
    # t = await ctx.channel.create_thread(name='bot test', type=None)
    # await t.send("Message in a thread")
    # threads = ctx.channel.threads
    # await threads[0].send("Message in a thread")
    # print(ctx.author)
    # print(threads)
    # if any(ctx.author in thread.members for thread in threads):
    #     print('user in some threads')
    #     return
    # print('user in any thread')

# @commands.command()
# async def settings(ctx, json_settings):
#     settings = json.loads(json_settings)
#     if update_settings(settings):
#         ctx.send('Settings updated!')
#     else:
#         ctx.send('Settings failed to update.')

# @bot.event
# async def on_guild_join(guild):
#     with open(json_settings_path, 'a+') as settings:
#         try:
#             json_settings = json.load(settings)
#             if str(guild.id) not in json_settings:
#                 settings.write(json.dumps(json_settings.update({str(guild.id): {'settings': {}}}), default=str))
#         except Exception as error:
#             print(error)

# def update_settings(new_settings_json):
#     with open(json_settings_path, 'a+') as settings:
#         try:
#             json_settings = json.load(settings)
#             if str(guild.id) in json_settings:
#                 settings.write(
#                     json.dumps(
#                         json_settings[str(guild.id)]['settings'].update(new_settings_json),
#                         default=str
#                     )
#                 )
#             return True
#         except Exception as error:
#             print(error)
#             return False

async def setup(bot):
    bot.add_command(test)
    globals()['bot'] = bot
