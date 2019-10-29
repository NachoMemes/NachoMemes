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
from pathlib import Path
from typing import Iterable

import discord
import psutil
from discord import Guild
from discord.ext import commands
from discord.ext.commands import Context, has_permissions
from fuzzywuzzy import process

from nachomemes import DynamoTemplateStore, LocalTemplateStore, MemeTemplate, TextBox, Store, TemplateError

description = "A bot to generate custom memes using pre-loaded templates."
bot = commands.Bot(command_prefix="/", description=description)

# Used for calculating memes/minute.
global MEMES
MEMES = 0

# Base directory from which paths should extend.
global BASE_DIR
BASE_DIR = Path(__file__).parent.parent


def mentioned_members(ctx: Context):
    return (ctx.guild.get_member(m.id) for m in ctx.message.mentions)


@bot.event
async def on_ready():
    print("Only memes can melt steel beams.\n\t--Shia LaBeouf")
    bot.loop.create_task(status_task())


with open(os.path.join(BASE_DIR, "config/messages.json"), "rb") as c:
    statuses = json.load(c)["credits"]


def _match_template_name(name, guild: Guild):
    "Matches input fuzzily against proper names."
    fuzzed = process.extractOne(name, store.list_memes(guild, ("name",)))
    if fuzzed[1] < 25:
        raise TemplateError(f"could not load a template matching {name}")
    return fuzzed[0]["name"]


@bot.event
async def status_task():
    while True:
        global MEMES
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(
                name=f"{MEMES} memes/minute! "
                + "Load AVG - CPU: {0:.2f}% ".format(psutil.getloadavg()[0])
                + "RAM: {0:.2f}% ".format(psutil.virtual_memory()._asdict()["percent"])
            ),
        )
        MEMES = 0
        await asyncio.sleep(60)


@bot.command(description="List templates.")
async def templates(ctx, template=None):
    try:
        guild = ctx.message.guild
        config = store.guild_config(guild)
        if not config.can_use(ctx.message.author):
            return await ctx.send(f"```{config.no_memes(ctx.message.author)}```")
        if template:
            fmeme = _match_template_name(template, guild)
            meme = store.read_meme(guild, fmeme)
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
            memes = store.list_memes(guild, ("name", "description"))
            lines = [f"\n{m['name']}: *{m['description']}*" for m in memes]
            await ctx.send("**Templates**" + "".join(lines))
    except TemplateError:
        await ctx.send(f"```Could not load '{template}'```")
    except:
        err = traceback.format_exc()
        if testing:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)


# Only allows an administrator to refresh templates.
@bot.command(description="refresh templates.")
async def refresh_templates(ctx: Context, arg: str = None):
    try:
        await ctx.trigger_typing()
        hard = arg == "--hard"
        if hard:
            if not ctx.message.author.guild_permissions.administrator:
                config = store.guild_config(ctx.message.guild)
                if not config.can_admin(ctx.message.author):
                    return await ctx.send(f"```{config.no_admin(ctx.message.author)}```")
        else:
            config = store.guild_config(ctx.message.guild)
            if not config.can_edit(ctx.message.author):
                return await ctx.send(f"```{config.no_admin(ctx.message.author,'refresh','edit')}```")
                 
        message = store.refresh_memes(ctx.message.guild, hard)
        await ctx.send(f"```{message}```")
    except:
        err = traceback.format_exc()
        if testing:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)

@bot.command(description="Who am I?!?")
async def whoami(ctx: Context):
    try:
        config = store.guild_config(ctx.message.guild)

        if ctx.message.mentions:
            members = mentioned_members(ctx)
        else:
            members = (ctx.message.author,)

        for member in members:
            name = config.member_full_name(member)
            await ctx.send(
                textwrap.dedent(
                    f"""\
                    ```Name: {name}
                    Can use: {config.can_use(member)}, Can edit: {config.can_edit(member)}, Can admin: {config.can_admin(member)}```"""
                )
            )
    except:
        err = traceback.format_exc()
        if testing:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)

@bot.command(description="set admin role")
async def set_admin_role(ctx: Context, roleid: str):
    try:
        config = store.guild_config(ctx.message.guild)
        role = ctx.guild.get_role(int(roleid))
        message = config.set_admin_role(ctx.message.author, role)
        store.save_guild_config(config)
        await ctx.send(textwrap.dedent(f"```{message}```"))
    except:
        err = traceback.format_exc()
        if testing:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)

@bot.command(description="set edit role")
async def set_edit_role(ctx: Context, roleid: str):
    try:
        config = store.guild_config(ctx.message.guild)
        role = ctx.guild.get_role(int(roleid))
        message = config.set_edit_role(ctx.message.author, role)
        store.save_guild_config(config)
        await ctx.send(textwrap.dedent(f"```{message}```"))
    except:
        err = traceback.format_exc()
        if testing:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)

@bot.command(description="ban a user")
async def shun(ctx: Context):
    try:
        config = store.guild_config(ctx.message.guild)
        for subject in mentioned_members(ctx):
            message = config.shun(ctx.message.author, subject)
            await ctx.send(textwrap.dedent(f"```{message}```"))
        store.save_guild_config(config)
    except:
        err = traceback.format_exc()
        if testing:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)

@bot.command(description="unban a user")
async def endorse(ctx: Context):
    try:
        config = store.guild_config(ctx.message.guild)
        for subject in mentioned_members(ctx):
            message = config.endorse(ctx.message.author, subject)
            await ctx.send(textwrap.dedent(f"```{message}```"))
        store.save_guild_config(config)
    except:
        err = traceback.format_exc()
        if testing:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)

@bot.command(description="Make a new template.")
async def save(ctx: Context):
    try:
        config = store.guild_config(ctx.message.guild)
        if not config.can_edit(ctx.message.author):
            raise RuntimeError("computer says no")
        d = json.loads(ctx.message.content.lstrip("/save").strip().strip('`'))
        message = store.save_meme(ctx.message.guild, d)
        await ctx.send(textwrap.dedent(f"```{message}```"))
    except Exception as e:
        err = traceback.format_exc()
        if testing:
            await ctx.send("```" + err[:1990] + "```")
        else:
            await ctx.send("```" + str(e) + "```")
        raise e


@bot.command(description="Make a new meme.")
async def meme(ctx: Context, template: str, *text):

    try:
        await ctx.trigger_typing()
        config = store.guild_config(ctx.message.guild)
        if not config.can_use(ctx.message.author):
            return await ctx.send(f"```{config.no_memes(ctx.message.author)}```")
        # Log memes/minute.
        global MEMES
        MEMES += 1
        match = _match_template_name(template, ctx.message.guild)
        # Have the meme name be reflective of the contents.
        name = re.sub(r"\W+", "", str(text))
        key = f"{match}-{name}.png"

        meme = store.read_meme(ctx.message.guild, match, True)
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
        with open(os.path.dirname(__file__) + "/../" + creds_file_name, "rb") as f:
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
            creds["access_key"], creds["secret"], creds["region"], store, args.debug
        )

    try:
        token = creds["discord_token"]
    except NameError:
        print(
            "Could not get Discord token from config/creds.json environment variable $DISCORD_TOKEN!"
        )
        sys.exit(1)

    bot.run(token)
