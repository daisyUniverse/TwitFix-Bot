# TwitFixBot by Robin Universe
# Licensed under Do What The Fuck You Want
import youtube_dl
import textwrap
import twitter
import discord
import asyncio
import pymongo
import json
import sys
import re
import os

prefix = '>>'

# Read config from config.json. If it does not exist, create new.
if not os.path.exists("config.json"):
    with open("config.json", "w") as outfile:
        default_config = {"config":{"admin":"128423195366785024","link_cache":"json","database":"[url to mongo database goes here]","method":"youtube-dl", "color":"#43B581", "appname": "TwitFix", "repo": "https://github.com/robinuniverse/twitfix", "url": "https://fxtwitter.com"},"api":{"token":"[Discord token goes here]","api_key":"[api_key goes here]","api_secret":"[api_secret goes here]","access_token":"[access_token goes here]","access_secret":"[access_secret goes here]"}}
        json.dump(default_config, outfile, indent=4, sort_keys=True)

    config = default_config
else:
    f = open("config.json")
    config = json.load(f)
    f.close()

# If method is set to API or Hybrid, attempt to auth with the Twitter API
if config['config']['method'] in ('api', 'hybrid'):
    auth = twitter.oauth.OAuth(config['api']['access_token'], config['api']['access_secret'], config['api']['api_key'], config['api']['api_secret'])
    twitter_api = twitter.Twitter(auth=auth)

link_cache_system = config['config']['link_cache']

if link_cache_system == "json":
    link_cache = {}
    if not os.path.exists("config.json"):
        with open("config.json", "w") as outfile:
            default_link_cache = {"test":"test"}
            json.dump(default_link_cache, outfile, indent=4, sort_keys=True)

    f = open('links.json',)
    link_cache = json.load(f)
    f.close()
elif link_cache_system == "db":
    client = pymongo.MongoClient(config['config']['database'], connect=False)
    db = client.TwitFix

def video_info(url, tweet="", desc="", thumb="", uploader=""): # Return a dict of video info with default values
    vnf = {
        "tweet"         :tweet,
        "url"           :url,
        "description"   :desc,
        "thumbnail"     :thumb,
        "uploader"      :uploader
    }
    return vnf

def link_to_vnf_from_api(video_link):
    print("Attempting to download tweet info from Twitter API")
    twid = int(re.sub(r'\?.*$','',video_link.rsplit("/", 1)[-1])) # gets the tweet ID as a int from the passed url
    tweet = twitter_api.statuses.show(_id=twid, tweet_mode="extended")

    # Check to see if tweet has a video, if not, make the url passed to the VNF the first t.co link in the tweet
    if 'extended_entities' in tweet:
        if 'video_info' in tweet['extended_entities']['media'][0]:
            if tweet['extended_entities']['media'][0]['video_info']['variants'][-1]['content_type'] == "video/mp4":
                url = tweet['extended_entities']['media'][0]['video_info']['variants'][-1]['url']
                thumb = tweet['extended_entities']['media'][0]['media_url']
            else:
                url = tweet['extended_entities']['media'][0]['video_info']['variants'][-2]['url']
                thumb = tweet['extended_entities']['media'][0]['media_url']

    if len(tweet['full_text']) > 200:
        text = textwrap.shorten(tweet['full_text'], width=200, placeholder="...")
    else:
        text = tweet['full_text']

    vnf = video_info(url, video_link, text, thumb, tweet['user']['name'])
    return vnf

def link_to_vnf_from_youtubedl(video_link):
    print("Attempting to download tweet info via YoutubeDL")
    with youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'}) as ydl:
        result = ydl.extract_info(video_link, download=False)
        vnf = video_info(result['url'], video_link, result['description'].rsplit(' ',1)[0], result['thumbnail'], result['uploader'])
        return vnf

def link_to_vnf(video_link): # Return a VideoInfo object or die trying
    if config['config']['method'] == 'hybrid':
        try:
            return link_to_vnf_from_api(video_link)
        except Exception as e:
            print("API has determined that this is not a video link")
            return link_to_vnf_from_youtubedl(video_link)
    elif config['config']['method'] == 'api':
        try:
            return link_to_vnf_from_api(video_link)
        except Exception as e:
            print("API has determined that this is not a video link")
            return None
    elif config['config']['method'] == 'youtube-dl':
        try:
            return link_to_vnf_from_youtubedl(video_link)
        except Exception as e:
            print("Youtube-DL has determined that this is not a video link")
            return None
    else:
        print("Please set the method key in your config file to 'api' 'youtube-dl' or 'hybrid'")
        return None

def get_vnf_from_link_cache(video_link):
    if link_cache_system == "db":
        collection = db.linkCache
        vnf = collection.find_one({'tweet': video_link})
        if vnf != None: 
            print("Link located in DB cache")
            return vnf
        else:
            print("Link not in DB cache")
            return None
    elif link_cache_system == "json":
        if video_link in link_cache:
            print("Link located in json cache")
            vnf = link_cache[video_link]
            return vnf
        else:
            print("Link not in json cache")
            return None

def add_vnf_to_link_cache(video_link, vnf):
    if link_cache_system == "db":
        try:
            out = db.linkCache.insert_one(vnf)
            print("Link added to DB cache")
            return True
        except Exception:
            print("Failed to add link to DB cache")
            return None
    elif link_cache_system == "json":
        link_cache[video_link] = vnf
        with open("links.json", "w") as outfile: 
            json.dump(link_cache, outfile, indent=4, sort_keys=True)
            return None

class MyClient(discord.Client):
    async def on_ready(self):
      print ('\033[1mWelcome to the TwitFixBot by \33[31mRobin Universe\033[0m')
      print ('Bot core loaded as user:', self.user)

    async def on_message(self, message):
        msgCaps = message.content
        msg     = message.content.lower()

        if message.author == self.user:
            return

        if 'https://twitter.com/' in msg:
            # Check if tweet is video
            
            tweet = re.search("(?P<url>https?://[^\s]+)", msg).group("url")
            cached_vnf = get_vnf_from_link_cache(tweet)
            if cached_vnf == None: # Is this link not in the cache?
                vnf = link_to_vnf(tweet) # Get the tweet info from the API to determine if it's a video
                if vnf is not None:
                    if msg.startswith('>>'):
                        await message.edit(suppress=True)
                        await message.reply(vnf['url'], mention_author=False)
                        add_vnf_to_link_cache(tweet, vnf)
                        print("Replaced uncached video link with direct link")
                    else:
                        reply = tweet.replace('https://twitter.com', 'https://fxtwitter.com')
                        await message.edit(suppress=True)
                        await message.reply(reply, mention_author=False)
                        add_vnf_to_link_cache(tweet, vnf) # Add the tweet to the link cache
                        print("Replaced uncached video link with TwitFix link")
                        
            else:
                if msg.startswith('>>'):
                    await message.edit(suppress=True)
                    await message.reply(cached_vnf['url'], mention_author=False)   
                    print("Replaced cached video link with direct link") 
                else:
                    reply = tweet.replace('https://twitter.com', 'https://fxtwitter.com') # Otherwise, just assume the link is a video and replace the embed
                    await message.edit(suppress=True)
                    await message.reply(reply, mention_author=False)
                    print("Replaced cached video link with TwitFix link")


        if str(message.author.id) == config['config']['admin']: 
            if msg.startswith(prefix):
                try:
                    msg = msg[len(prefix):]

                    if msg.startswith('reload'):
                        await print("Bot Reload command used!")
                        await message.channel.send("Restarting TwitFixBot...")
                        os.execl(sys.executable, sys.executable, *sys.argv)
                except Exception as e: # returns error meesages to discord in a python codeblock for debugging
                    print(traceback.format_exc())
                    if hasattr(e, 'message'):
                        await channel.send("```python\nError on line " + str(sys.exc_info()[-1].tb_lineno) + "\n" + str(e.message) + "```")
                    else:
                        await channel.send("```python\nError on line " + str(sys.exc_info()[-1].tb_lineno) + "\n" + str(e) + "```")

client = MyClient()
client.run(config['api']['token'])