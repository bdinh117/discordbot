# import python library to interact with Discord API
# first, install package by running command line as admin, then pip install ....

import discord # documentation here: https://discordpy.readthedocs.io/en/latest/api.html
from discord.ext import commands,tasks
import os

import string  # for removing punctuation
import shlex  # want shlex.split(), so we dont split on separators within double quotes

import time
import asyncio
import traceback
import asyncprawcore
import json

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




# getting fields of a submission instance
# for submission in reddit.subreddit("xboxone").new(limit=1):
#     id=submission.id
#     dict=vars(submission)
#     for key in dict:
#         print(key+":",end=" ")
#         print(dict[key])
#         # if(key=="preview"):
#         #     print("WHAT SI THIS -----------------",dict[key]["images"][0]["source"]["url"])
#         #     break

# print(time.time())

# async def process_posts(subreddits,keywords,message):
#     for submission in subreddits.stream.submissions():
#         # print(time.time())
#         if (
#                 time.time() - submission.created_utc <= 540):  # make it so when we give the command, we don't get notified of older posts. current-time_created (in unix)
#             s = submission.title.translate(str.maketrans('', '', string.punctuation))  # remove punctuation from title
#             print(s, "-----FROM: r/" + submission.subreddit.display_name)
#             title = s.lower().split()  # make title lowercase and split it word by word
#             for word in title:  # Check if every word in the title is in the list of keywords
#                 if word in keywords:
#                     await message.channel.send(
#                         "TITLE: " + submission.title + submission.url + "\n" + "https://old.reddit.com" + submission.permalink + "\nhttps://redeem.microsoft.com/")  # if so, send a message in the channel
#                     break


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