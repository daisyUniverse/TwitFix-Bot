 

# TwitFix Bot

Share your videos faster

I have a version of this bot running on the same server that runs TwitFix, you can add it to your server by [Clicking Here](https://discord.com/api/oauth2/authorize?client_id=867670280054505522&permissions=10240&scope=bot)

This is a small discord bot that scans messages for twitter links, and on finding one, it tries various methods to determine if its a video link, if it is, it kills the messages embed, and replies to it with a fxtwitter link, fixing the video embed

![TwitFixBot](TwitFixBot.gif)



This project is licensed under the **WTFPL**



## Config

A Default config file will be generated when you first run the script. This needs to be filled out before the bot can run (mostly the token).

### **API**

- **token**: This is your discord bot token
- **api_key**, **api_secret**, **access_token**, **access_secret**: This is API info required to use the Twitter API if that is the method you choose

### **Config**

- **admin**: This is the discord user ID of the person you want access to the one admin command, reload
- **database**: Link to your mongoDB link cache database if you use this method for link caching
- **link_cache**: (db, json) This determines if you would like to use a local json file for the link cache, or use a mongoDB database
- **method**: (api, youtube-dl, hyrbid) This determines if you want to use the twitter API, youtube-dl, or to start off with the Twitter API and fall back on youtube-dl to determine if the link is a video or not



The rest of the options aren't really relevant yet.



**notes:**

This is built to work with the TwitFix link cache database, meaning that any video linked using that before, will not need to be rescanned.

