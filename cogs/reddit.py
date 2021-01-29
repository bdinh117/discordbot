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

monitors_per_user={} #dict to hold every unique user's monitor loops
MAX_MONITORS=4 #set limit of monitor streams per user.


class Reddit(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    # COMMAND: $monitor,<subreddits>,<search words>
    @commands.command()
    async def monitor(self, ctx):
        msg = ctx.message.content.split(" ", maxsplit=1) #split "$monitor" from parameters

        # Formatting of Command:
        # $monitor,<subreddit(s)> separated by space,keywords separated by space

        msg = msg[1].split(",")  # split up subreddits and keywords

        msg = [msg[0]] + shlex.split(msg[1].strip().lower())  # split the keywords by space and preserve spacing for multiple letter search words denoted by words in quotes "<word1> <word2> "

        subreds = msg[0].replace(" ", "+")  # get the subreddits string into the right formatting.
        subreddit = await reddit.subreddit(subreds)

        keywords = msg[1:]  # make all keywords lowercase

        print("command: " + ctx.command.name)
        print("Subreddits being searched through:", msg[0])
        print("Search Keywords:", keywords)

        loopObj = tasks.loop(seconds=60)(process_posts) #a loop object made from the process_posts coroutine
        tpl = (subreddit, keywords)
        monitor_data = (loopObj, tpl)
        if ctx.author.id in monitors_per_user:
            if (len(monitors_per_user[ctx.author.id]) < MAX_MONITORS):
                monitors_per_user[ctx.author.id].append(monitor_data) #monitors_per_user dict contains a tpl of a loopObj and the command details: (loop,(subred,keywords))
                monitors_per_user[ctx.author.id][-1][0].start(subreddit, keywords, ctx)
                await ctx.channel.send(f"Started monitoring subreddits: {subreds} for keywords: {keywords}")
            else:
                await ctx.channel.send("Cannot create anymore streams. User reached maximum limit of 4 monitor streams")
        else:
            monitors_per_user[ctx.author.id] = [monitor_data]
            monitors_per_user[ctx.author.id][-1][0].start(subreddit, keywords, ctx)
            await ctx.channel.send(f"Started monitoring subreddits: {subreds} for keywords: {keywords}")


    @commands.command()
    async def listM(self, ctx):#Check the list of current subreddit streams
        embed = discord.Embed(
            title="Subreddit Streams",
            type="rich",
            description="Here are the streams you are currently monitoring:",
            url="https://www.google.com/",
            timestamp=datetime.utcnow(),  # .replace(tzinfo=estTimezone),
            colour=discord.Colour.dark_red())

        all_streams = monitors_per_user[ctx.author.id] #all streams a user is monitoring
        for i in range(len(all_streams)):
            embed.add_field(name=f"Stream #{i + 1}",
                            value=f"Subreddits: {all_streams[i][1][0]}\nKeywords: {all_streams[i][1][1]}",
                            inline=False)

        await ctx.channel.send(content="Here all the streams you are monitoring:", embed=embed)

    @commands.command()  # $cancel a stream
    async def stopM(self,ctx):
        msg = ctx.message.content.strip().split()
        n = int(msg[1]) - 1
        monitors_per_user[ctx.author.id][n][0].cancel() #cancel() instead of stop() because , may be monitoring high density stream like r/all where will never get the next iteration

        del monitors_per_user[ctx.author.id][n]
        await ctx.channel.send(f"Stopped monitoring subreddit stream #{n + 1}")

def setup(bot):
    bot.add_cog(Reddit(bot))

#helper function that processes subreddit stream
async def process_posts(subreddit,keywords,ctx):
    print(f"----------------------we looping agane?(at {datetime.utcfromtimestamp(time.time())})----------------------------")
    try:
        async for submission in subreddit.stream.submissions(pause_after=7,skip_existing=True):
            # print(time.time())
            if(submission is None):
                print(f"!!!!!!!!Submission is None, meaning no new submissions, so lets break(at {datetime.utcfromtimestamp(time.time())})!!!!!!!!!")
                break
            utc_time = str( datetime.utcfromtimestamp(submission.created_utc))
            # note: there is 20s~ delay between the creation time and the discord message being sent.
            # however, only a couple second delay btwn seeing the post actually being posted and then the discord message

            if (time.time() - submission.created_utc <= 60):  # make it so when we give the command, we don't get notified of older posts. current-time_created (in unix)
                s = submission.title.translate(str.maketrans('', '', string.punctuation))  # remove punctuation from title
                print(f"{s}-----FROM: r/{submission.subreddit.display_name} AT: {utc_time}")
                title = s.lower().split()  # make title lowercase and split it word by word
                for word in title:  # Check if every word in the title is in the list of keywords
                    if word in keywords:
                        # if so, send a message in the channel
                        embed = discord.Embed(
                            title="NEW Post!",
                            type="rich",
                            description=f"From r/{submission.subreddit.display_name}",
                            url=submission.url,
                            timestamp=datetime.utcnow(),  # .replace(tzinfo=estTimezone),
                            colour=discord.Colour.green(),
                        )
                        embed.set_footer(text=f"POSTED AT: {utc_time}",icon_url="https://i.kym-cdn.com/photos/images/masonry/001/734/410/676.jpg")
                        embed.set_image(url=submission.url)
                        embed.set_thumbnail(url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS-qE0SRu_wMaDHaL0IGTygrvqejB4CMIatLQ&usqp=CAU")
                        embed.add_field(
                            name=submission.title, value=f"{submission.url}\n\nhttps://old.reddit.com/{submission.permalink}\n\nhttps://redeem.microsoft.com/",inline=False
                        )
                        await ctx.send("1 result from your search: ",embed=embed)
                        break

    #when .cancel() is called on a LoopObject, CancelledError is thrown into this coroutine. Reraise the exception and the loop/task will be cancelled
    except (asyncio.CancelledError,asyncprawcore.exceptions.RequestException) as e:
        #traceback.print_exc()
        await ctx.channel.send("WOWOWOWOWOWOW")
        raise asyncio.CancelledError

    except (asyncprawcore.exceptions.ServerError):
        await ctx.channel.send("server error")
        asyncio.sleep(10)


#https://stackoverflow.com/questions/56052748/python-asyncio-task-cancellation