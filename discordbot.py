#import python library to interact with Discord API
#first, install package by running command line as admin, then pip install ....

import discord # documentation here: https://discordpy.readthedocs.io/en/latest/api.html
import praw # https://praw.readthedocs.io/en/latest/index.html
import string # for removing punctuation
import shlex #want shlex.split(), so we dont split on separators within double quotes
from datetime import datetime #for getting time from unix time
import time
import json

with open('config.json') as f:
    config=json.load(f)

#creates a read-only Reddit instance called "reddit"
#We need one in order to do ANYTHING with PRAW
reddit= praw.Reddit(
    client_id=config['CLIENT_ID'],
    client_secret=config['CLIENT_SECRET'],
    user_agent=config['USER_AGENT']
)

#create an instance of Client object. our bot. can also use commands.bot instead to make it easier to do commands
client = discord.Client()

@client.event
async def on_ready():#triggers when bot turns on
    print('We have logged in as {0.user}'.format(client))#format() is a string function that just replaces the placeholder with the parameter
    #'0' refers to the first parameter which is the client object. which has a user attribute
    for chan in client.get_all_channels():
        if(chan.name=="general"):
            await chan.send("BOTTO IS ONLINE!")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello, '+message.author.name +"!")

    #COMMAND: $monitor,<subreddits>,<search words>
    if message.content.startswith('$monitor'):
        #TODO .strip() ?
        #TODO handle punctuation in keywords

        #Formatting of Command:
        # $monitor,<subreddit(s)> separated by space,keywords separated by space


        msg=message.content.split(",") #split the command into 3 parts:$monitor, subreddits to search through, search keywords
        msg=msg[0:2]+shlex.split(msg[2]) #split the keywords by space and preserve spacing for multiple letter search words denoted by words in quotes "<word1> <word2> "

        subreds=msg[1].replace(" ","+") #get the subreddits string into the right formatting.
        subreddit= reddit.subreddit(subreds)

        keywords=[x.lower() for x in msg[2:]]#make all keywords lowercase
        print(msg)
        print("command:",msg[0])
        print("Subreddits being searched through:",msg[1])
        print("Search Keywords:",keywords)


        for submission in subreddit.stream.submissions():
            #print(time.time())
            utc_time=str(datetime.utcfromtimestamp(submission.created_utc)) #note: there is 20s~ delay between the creation time and the discord message being sent.
            # however, only a couple second delay btwn seeing the post actually being posted and then the discord message

            if(time.time()-submission.created_utc<=540):#make it so when we give the command, we don't get notified of older posts. current-time_created (in unix)
                s=submission.title.translate(str.maketrans('', '', string.punctuation))#remove punctuation from title
                print(s,"-----FROM: r/"+submission.subreddit.display_name,"AT: "+utc_time)
                title = s.lower().split()#make title lowercase and split it word by word
                for word in title:#Check if every word in the title is in the list of keywords
                    if word in keywords:
                        await message.channel.send(
                            "TITLE: "+submission.title +"\n"+
                            "SENT AT: "+utc_time+"\n"+
                            submission.url+#direct link to img if there is one
                            "\nhttps://old.reddit.com"+submission.permalink+#permalink is r/subreddit format
                            "\nhttps://redeem.microsoft.com/"
                        )#if so, send a message in the channel
                        break

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

#print(time.time())

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


client.run(config['DISCORD_TOKEN'])#the token









