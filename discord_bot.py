# import python library to interact with Discord API
# first, install package by running command line as admin, then pip install ....

import discord # documentation here: https://discordpy.readthedocs.io/en/latest/api.html
from discord.ext import commands,tasks
import os
import json

#Open the config.json file for all the keys.
with open('config.json') as f:
    config=json.load(f)


# create an instance of Client object. our bot. can also use commands.bot instead to make it easier to do commands
bot = commands.Bot(command_prefix=config['COMMAND_PREFIX'])

@bot.event
async def on_ready():  # triggers when bot turns on
    print(
        'We have logged in as {0.user}'.format(bot)
    )  # format() is a string function that just replaces the placeholder with the parameter
    # '0' refers to the first parameter which is the client object. which has a user attribute
    for chan in bot.get_all_channels():
        if (chan.name == "general"):
            await chan.send("BOTTO IS ONLINE!")


@bot.command("hello")
async def hello(ctx):
    if ctx.message.author == bot.user:
        return

    await ctx.channel.send('Hello, ' + ctx.author.name + "!")

#error handler for errors raised inside a command
@bot.event
async def on_command_error(ctx,error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f'"{ctx.prefix+ctx.invoked_with}" command not found')

#load all cogs and their commands
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")



bot.run(config['DISCORD_TOKEN'])  # the token

# So when you make a Loop Object. you call the tasks.loop() function , passing it in the coroutine you want to make Loop Object with
#tasks.loop(seconds=60)(process_posts) like i did above. and then when you start it by doing LoopObj.start(). it creates a task
# and somehow starts the task (through awaiting?) idk , i couldnt find out how in the github code. It creates the task out of the
# internal _loop coroutine. and this _loop coroutine basically keeps on calling/awaiting your coroutine, the one you passed into the decorator loop() function when you created
# the task, . when you call loopObj.cancel(), it calls .cancel() on the internal task which causes a CancelledError to be thrown inside the wrapped coroutine.
# wrapped coroutine is the coro the task was created from. so our _loop() function. which is continuously calling OUR coroutine.
# If i was monitoring r/all, and have basically an endless stream of posts. then 1 iteration of my loop will basically last forever, and so calling .cancel()
# will throw the exception while the _loop() is currently running the PRAW stuff inside my coroutine. idk why, but I have to catch and reraise this exception,
# and then the coroutine will be cancelled. the raise will cause it to bubble up and go up the call stack. so the excpetion will go to the _loop() function,
# where it is caught and raised again. And idk where it goes and what handles it after that, but essentially now the task is cancelled.