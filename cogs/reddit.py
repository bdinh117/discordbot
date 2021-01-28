import asyncpraw
import json
from discord.ext import commands, tasks
import shlex
from datetime import datetime
import time
import string
import asyncprawcore
import asyncio
import discord
with open('config.json') as f:
    config=json.load(f)

# creates a read-only Reddit instance called "reddit"
# We need one in order to do ANYTHING with PRAW
reddit= asyncpraw.Reddit(
    client_id=config['CLIENT_ID'],
    client_secret=config['CLIENT_SECRET'],
    user_agent=config['USER_AGENT']
)
#monitor_loops=[] #holds the task loops for each of the user's monitor commands
#monitor_data=[]#For every monitor stream, holds subreddits being monitored and search keywords
monitors_per_user={}
MAX_MONITORS=4


class Reddit(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    # COMMAND: $monitor,<subreddits>,<search words>
    @commands.command()
    async def monitor(self, ctx):
        msg = ctx.message.content.split(" ", maxsplit=1)

        # TODO .strip() ?
        # TODO handle punctuation in keywords

        # Formatting of Command:
        # $monitor,<subreddit(s)> separated by space,keywords separated by space

        msg = msg[1].split(
            ",")  # split the command into 3 parts:$monitor, subreddits to search through, search keywords

        msg = [msg[0]] + shlex.split(msg[
                                         1].strip())  # split the keywords by space and preserve spacing for multiple letter search words denoted by words in quotes "<word1> <word2> "

        subreds = msg[0].replace(
            " ", "+")  # get the subreddits string into the right formatting.
        subreddit = await reddit.subreddit(subreds)

        keywords = [x.lower() for x in msg[1:]]  # make all keywords lowercase

        print("command: " + ctx.command.name)
        print("Subreddits being searched through:", msg[0])
        print("Search Keywords:", keywords)

        loopObj = tasks.loop(seconds=60)(process_posts)
        tpl = (subreddit, keywords)
        monitor_data = (loopObj, tpl)
        if ctx.author.id in monitors_per_user:
            if (len(monitors_per_user[ctx.author.id]) < MAX_MONITORS):
                monitors_per_user[ctx.author.id].append(monitor_data)
                monitors_per_user[ctx.author.id][-1][0].start(subreddit, keywords, ctx)
                await ctx.channel.send(f"Started monitoring subreddits: {subreds} for keywords: {keywords}")
            else:
                await ctx.channel.send("Cannot create anymore streams. User reached maximum limit of 4 monitor streams")
        else:
            monitors_per_user[ctx.author.id] = [monitor_data]
            monitors_per_user[ctx.author.id][-1][0].start(subreddit, keywords, ctx)
            await ctx.channel.send(f"Started monitoring subreddits: {subreds} for keywords: {keywords}")


        # monitor_data[tpl]=tasks.loop(seconds=60)(process_post)
        # monitor_loops[tpl].start(subreddit,keywords,ctx)
    @commands.command()
    async def listM(self, ctx):
        # estTimeDelta=timedelta(hours=-5)
        # estTimezone= timezone(estTimeDelta,name="EST")
        embed = discord.Embed(
            title="Subreddit Streams",
            type="rich",
            description="Here are the streams you are currently monitoring:",
            url="https://www.google.com/",
            timestamp=datetime.utcnow(),  # .replace(tzinfo=estTimezone),
            colour=discord.Colour.dark_red())

        all_streams = monitors_per_user[ctx.author.id]
        for i in range(len(all_streams)):
            embed.add_field(name=f"Stream #{i + 1}",
                            value=f"Subreddits: {all_streams[i][1][0]}\nKeywords: {all_streams[i][1][1]}",
                            inline=False)

        await ctx.channel.send(content="WOWEE Clapper, Does this work?", embed=embed)

    @commands.command()  # $StopMonitoring stream #n
    async def stopM(self,ctx):
        msg = ctx.message.content.strip().split()
        n = int(msg[1]) - 1
        monitors_per_user[ctx.author.id][n][0].cancel()

        del monitors_per_user[ctx.author.id][n]
        await ctx.channel.send(f"Stopped monitoring subreddit stream #{n + 1}")

def setup(bot):
    bot.add_cog(Reddit(bot))

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

    except (asyncprawcore.exceptions.ServerError):
        await ctx.channel.send("server error")
        asyncio.sleep(10)
    # except asyncprawcore.exceptions.RequestException as e:
    #     #traceback.print_exc()
    #     traceback.print_exc()
    #     print(repr(e))
    #     print('cancel_me(): cancel sleep')
    #     print(e)
    #     #raise asyncprawcore.exceptions.RequestException(e.original_exception,e.request_args,e.request_kwargs)
    #     raise asyncio.CancelledError

#https://stackoverflow.com/questions/56052748/python-asyncio-task-cancellation