# import python library to interact with Discord API
# first, install package by running command line as admin, then pip install ....

import discord # documentation here: https://discordpy.readthedocs.io/en/latest/api.html
from discord.ext import commands,tasks

import asyncpraw  # https://praw.readthedocs.io/en/latest/index.html
import string  # for removing punctuation
import shlex  # want shlex.split(), so we dont split on separators within double quotes
from datetime import datetime,timedelta,timezone  # for getting time from unix time
import time
import asyncio
import traceback
import asyncprawcore
import json

with open('config.json') as f:
    config=json.load(f)

# creates a read-only Reddit instance called "reddit"
# We need one in order to do ANYTHING with PRAW
reddit= asyncpraw.Reddit(
    client_id=config['CLIENT_ID'],
    client_secret=config['CLIENT_SECRET'],
    user_agent=config['USER_AGENT']
)

# create an instance of Client object. our bot. can also use commands.bot instead to make it easier to do commands
bot = commands.Bot(command_prefix=config['COMMAND_PREFIX'])

#monitor_loops=[] #holds the task loops for each of the user's monitor commands
#monitor_data=[]#For every monitor stream, holds subreddits being monitored and search keywords
monitors_per_user={}
MAX_MONITORS=4

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

    # COMMAND: $monitor,<subreddits>,<search words>


@bot.command("monitor")
async def monitor(ctx):
    msg = ctx.message.content.split(" ", maxsplit=1)

    # TODO .strip() ?
    # TODO handle punctuation in keywords

    # Formatting of Command:
    # $monitor,<subreddit(s)> separated by space,keywords separated by space

    msg = msg[1].split(",")  # split the command into 3 parts:$monitor, subreddits to search through, search keywords

    msg = [msg[0]] + shlex.split(msg[1].strip())  # split the keywords by space and preserve spacing for multiple letter search words denoted by words in quotes "<word1> <word2> "

    subreds = msg[0].replace(
        " ", "+")  # get the subreddits string into the right formatting.
    subreddit = await reddit.subreddit(subreds)

    keywords = [x.lower() for x in msg[1:]]  # make all keywords lowercase

    print("command: " + ctx.command.name)
    print("Subreddits being searched through:", msg[0])
    print("Search Keywords:", keywords)

    loopObj = tasks.loop(seconds=60)(process_posts)
    tpl = (subreddit, keywords)
    monitor_data=(loopObj, tpl)
    if ctx.author.id in monitors_per_user:
        if(len(monitors_per_user[ctx.author.id])<MAX_MONITORS):
            monitors_per_user[ctx.author.id].append(monitor_data)
            monitors_per_user[ctx.author.id][-1][0].start(subreddit, keywords, ctx)
        else:
            await ctx.channel.send("Cannot create anymore streams. User reached maximum limit of 4 monitor streams")
    else:
        monitors_per_user[ctx.author.id] = [monitor_data]
        monitors_per_user[ctx.author.id][-1][0].start(subreddit, keywords, ctx)

        print(type(monitors_per_user[ctx.author.id]))

    # monitor_data[tpl]=tasks.loop(seconds=60)(process_post)
    # monitor_loops[tpl].start(subreddit,keywords,ctx)


#@tasks.loop(seconds=60)
async def process_posts(subreddit,keywords,ctx):
    print(f"----------------------we looping agane?(at {datetime.utcfromtimestamp(time.time())})----------------------------")
    try:
        async for submission in subreddit.stream.submissions(pause_after=7,skip_existing=True):#maybe use new posts instead of stream
            # print(time.time())
            if(submission is None):
                print(f"!!!!!!!!Submission is None, meaning no new submissions, so lets break(at {datetime.utcfromtimestamp(time.time())})!!!!!!!!!")
                break
            utc_time = str(
                datetime.utcfromtimestamp(submission.created_utc)
            )  # note: there is 20s~ delay between the creation time and the discord message being sent.
            # however, only a couple second delay btwn seeing the post actually being posted and then the discord message

            if (time.time() - submission.created_utc <= 60):  # make it so when we give the command, we don't get notified of older posts. current-time_created (in unix)
                s = submission.title.translate(str.maketrans('', '', string.punctuation))  # remove punctuation from title
                print(s, "-----FROM: r/" + submission.subreddit.display_name,
                      "AT: " + utc_time)
                title = s.lower().split()  # make title lowercase and split it word by word
                for word in title:  # Check if every word in the title is in the list of keywords
                    if word in keywords:
                        await ctx.channel.send(
                            "TITLE: " + submission.title + "\n" + "SENT AT: " +
                            utc_time + "\n" + submission.url
                            +  # direct link to img if there is one
                            "\nhttps://old.reddit.com" + submission.permalink
                            +  # permalink is r/subreddit format
                            "\nhttps://redeem.microsoft.com/"
                        )  # if so, send a message in the channel
                        break

    #when .cancel() is called on a LoopObject, CancelledError is thrown into this coroutine. Reraise the exception and the loop/task will be cancelled
    except (asyncio.CancelledError,asyncprawcore.exceptions.RequestException) as e:
        #traceback.print_exc()
        await ctx.channel.send("WOWOWOWOWOWOW")
        raise asyncio.CancelledError

    # except asyncprawcore.exceptions.RequestException as e:
    #     #traceback.print_exc()
    #     traceback.print_exc()
    #     print(repr(e))
    #     print('cancel_me(): cancel sleep')
    #     print(e)
    #     #raise asyncprawcore.exceptions.RequestException(e.original_exception,e.request_args,e.request_kwargs)
    #     raise asyncio.CancelledError

#https://stackoverflow.com/questions/56052748/python-asyncio-task-cancellation



@bot.command("StopMonitoring")#  $StopMonitoring stream #n
async def stop(ctx):
    msg=ctx.message.content.strip().split()
    n=int(msg[1])-1
    monitors_per_user[ctx.author.id][n][0].cancel()

    del monitors_per_user[ctx.author.id][n]
    await ctx.channel.send(f"Stopped monitoring subreddit stream #{n+1}")

@bot.command("MonitorList")
async def monitor_list(ctx):

    # estTimeDelta=timedelta(hours=-5)
    # estTimezone= timezone(estTimeDelta,name="EST")
    embed=discord.Embed(
        title="Subreddit Streams",
        type="rich",
        description="Here are the streams you are currently monitoring:",
        url="https://www.google.com/",
        timestamp=datetime.utcnow(),#.replace(tzinfo=estTimezone),
        colour=discord.Colour.dark_red())

    all_streams=monitors_per_user[ctx.author.id]
    for i in range(len(all_streams)):
        embed.add_field(name=f"Stream #{i+1}",value=f"Subreddits: {all_streams[i][1][0]}\nKeywords: {all_streams[i][1][1]}",inline=False)

    await ctx.channel.send(content="WOWEE Clapper, Does this work?",embed=embed)




# @bot.command("test")
# async def test(ctx):
#
#     loops["Jon"].start()


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