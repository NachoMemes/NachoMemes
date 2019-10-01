import os
import uuid

import discord
from discord.ext import commands

import json
import tinys3
import memegenerator

with open("creds.json", "rb") as f:
    creds = json.load(f)

description = "A bot to generate custom memes using pre-loaded templates."
bot = commands.Bot(command_prefix="/", description=description)

s3 = tinys3.Connection(
    creds["access_key"], creds["secret"], tls=True, default_bucket="discord-memes"
)


@bot.event
async def on_ready():
    print("Logged in.")


@bot.command(description="Make a new meme.")
async def generate_meme(ctx, memename: str, upper: str, lower: str):
    # make the meme
    key = f"{uuid.uuid4().hex}.png"
    memeobj = memegenerator.make_meme(upper, lower, f"{memename}.jpg")
    # upload the meme to s3
    s3.upload(key, memeobj)
    memeobj.close()
    # generate the embed
    embed = discord.Embed(image=f"http://discord-memes.s3.amazonaws.com/{key}")
    # return the embed
    await ctx.send(embed=embed)


# DISCORDTOKEN ENV VAR MUST BE SET OR SERVER WILL NOT RUN
# EXPORT DISCORDTOKEN=XXXXXXXXXXXXXXX
bot.run(creds["discord_token"])
