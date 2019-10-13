import argparse
import asyncio
import io
import json
import os
import random
import re
import sys
import textwrap
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Iterable

import discord
import psutil
import tinys3
from discord.ext import commands
from discord.ext.commands import Context

from dynamo import DynamoTemplateStore
from localstore import LocalTemplateStore
from render import MemeTemplate, TextBox
from store import Store, TemplateError

description = "A bot to generate custom memes using pre-loaded templates."
bot = commands.Bot(command_prefix="/", description=description)


@bot.event
async def on_ready():
    print("Only memes can melt steel beams.\n\t--Shia LaBeouf")
    bot.loop.create_task(status_task())

with open("config/messages.json", "rb") as c:
    statuses = json.load(c)["credits"]


# Needs work obv, going to add rich content for CPU and MEM and/or AVG LOAD usage
# Going to move to json config template
# Cycles through status changes: "Playing ..."
@bot.event
async def status_task():
    while True:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(
                name=random.choice(statuses)
                + """\nUsage - CPU: {}% RAM: {}%""".format(
                    psutil.getloadavg()[2], psutil.virtual_memory()._asdict()["percent"]
                )
            ),
        )
        await asyncio.sleep(90)


@bot.command(description="List templates.")
async def templates(ctx, template=None):
    try:
        guild = str(ctx.message.guild.id)
        if template:
            meme = store.read_meme(guild, template)
            await ctx.send(
                textwrap.dedent(
                    f"""\
                Name: {meme.name}
                Description: *{meme.description}*
                Times used: {meme.usage}
                Expects {len(meme.textboxes)} strings
                Read more: {meme.docs}"""
                )
            )
        else:
            await ctx.send(
                "== Templates =="
                + "".join(
                    f"\n{meme['name']}: *{meme['description']}*"
                    for meme in store.list_memes(guild, ("name", "description"))
                )
            )
    except TemplateError:
        await ctx.send(f"```Could not load '{template}'```")
    except:
        err = traceback.format_exc()
        if testing:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)


@bot.command(description="refresh templates.")
async def refresh_templates(ctx: Context, arg: str = None):
    await ctx.trigger_typing()
    guild = str(ctx.message.guild.id)
    message = store.refresh_memes(guild, arg == "--hard")
    await ctx.send(f"```{message}```")


@bot.command(description="Make a new meme.")
async def meme(ctx: Context, template: str, *text):
    await ctx.trigger_typing()
    try:
        # Case insensitive meme naming
        template = template.lower()
        guild = str(ctx.message.guild.id)
        meme = store.read_meme(guild, template, True)
        # Have the meme name be reflective of the contents.
        name = re.sub(r"\W+", "", str(text))
        key = f"{template}-{name}.png"

        with io.BytesIO() as buffer:
            meme.render(text, buffer)
            buffer.flush()
            buffer.seek(0)
            msg = await ctx.send(file=discord.File(buffer, key))
        if random.randrange(8) == 0:
            tmpmsg = msg
            e = discord.Embed().set_image(url=tmpmsg.attachments[0].url)
            e.set_footer(text=random.choice(statuses))
            msg = await ctx.send(embed=e)
            await tmpmsg.delete()
        for r in ("\N{THUMBS UP SIGN}", "\N{THUMBS DOWN SIGN}"):
            await msg.add_reaction(r)
    except TemplateError:
        await ctx.send(f"```Could not load '{template}'```")
    except:
        err = traceback.format_exc()
        if testing:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Runs the bot passed on input parameters."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Whether or not to run the bot in debug mode.",
    )
    parser.add_argument(
        "--local", action="store_true", help="Force running without Dynamo."
    )
    args = parser.parse_args()
    global testing
    testing = args.debug

    try:
        creds_file_name = (
            "config/creds.json" if not testing else "config/testing-creds.json"
        )
        with open(creds_file_name, "rb") as f:
            creds = json.load(f)
    except:
        creds = {}
    for k in ("DISCORD_TOKEN", "ACCESS_KEY", "SECRET", "REGION"):
        if k in os.environ:
            creds[k.lower()] = os.environ[k]

    global store
    store = LocalTemplateStore()
    if not args.local and "access_key" in creds:
        store = DynamoTemplateStore(
            creds["access_key"], creds["secret"], creds["region"], store
        )

    try:
        token = creds["discord_token"]
    except NameError:
        print(
            "Could not get Discord token from config/creds.json environment variable $DISCORD_TOKEN!"
        )
        sys.exit(1)

    bot.run(token)
