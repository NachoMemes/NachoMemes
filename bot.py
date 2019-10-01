import os
import uuid

import discord
from discord.ext import commands

import json
import tinys3
from memegenerator import make_meme

with open("creds.json", "w+") as f:
    creds = json.load(f)

description = "A bot to generate custom memes using pre-loaded templates."
bot = commands.Bot(command_prefix="/", description=description)

s3 = tinys3.Connection(creds["access_key"], creds["secret"],tls=True, default="discord-memes")

@bot.event
async def on_ready():
    print("Logged in.")

@bot.command(description="Make a new meme.")
async def generate_meme(ctx, memename:str, upper:str, lower:str):
    # make the meme
    key = f'{uuid.uuid4().hex}.png'
    memeobj = make_meme(upper, lower, f'{memename}.jpg')
    # upload the meme to s3
    meme = open(memeobj, "rb")
    s3.upload(key, meme)
    # generate the embed
    embed = discord.Embed(image=f'http://s3.amazonaws.com/discord-memes/{key}')
    # return the embed
    await ctx.send(embded=embed)

# DISCORDTOKEN ENV VAR MUST BE SET OR SERVER WILL NOT RUN
# EXPORT DISCORDTOKEN=XXXXXXXXXXXXXXX
bot.run(creds["discord_token"])
