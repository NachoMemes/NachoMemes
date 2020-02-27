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

from .dynamo_store import DynamoTemplateStore
from .local_store import LocalTemplateStore
from .store import Store
from . import get_store, get_creds
from .template import Template, TextBox, TemplateError

DESCRIPTION = "A bot to generate custom memes using pre-loaded templates."
bot = commands.Bot(command_prefix="/", description=DESCRIPTION)

# Used for calculating memes/minute.
MEMES = 0

# Base directory from which paths should extend.
BASE_DIR = Path(__file__).parent.parent

# Debug mode (true or false)
DEBUG = False

def mentioned_members(ctx: Context):
    "Returns the id of a memeber mentioned in a message."
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


def _find_close_matches(name, guild: Guild):
    "Chooses top matches against input."
    return [
        name[0]["name"]
        for name in process.extract(name, store.list_memes(guild, ("name",)))
        if name[1] > 40
    ]


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


async def fuzzed_templates(ctx, template, guild):
    "Fuzzy match multiple templates."
    fuzzed_memes = _find_close_matches(template.strip("*"), guild)
    memes = [
        match
        for match in store.list_memes(guild, ("name", "description"))
        if match["name"] in fuzzed_memes
    ]
    lines = [f"\n{m['name']}: *{m['description']}*" for m in memes]
    await ctx.send("**Potential Templates**" + "".join(lines))


async def single_fuzzed_template(ctx, template, guild):
    "Fuzzy match a single template"
    fmeme = _match_template_name(template, guild)
    meme = store.get_template(guild, fmeme)
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


async def templates(ctx, template=None):
    try:
        guild = ctx.message.guild
        config = store.guild_config(guild)
        if not config.can_use(ctx.message.author):
            return await ctx.send(f"```{config.no_memes(ctx.message.author)}```")
        if template:
            # A fuzzy multiple match
            if "*" in template:
                return await fuzzed_templates(ctx, template, guild)
            # A single fuzzy match.
            return await single_fuzzed_template(ctx, template, guild)
        else:
            # The whole damn list.
            memes = store.list_memes(guild, ("name", "description"))
            lines = [f"\n{m['name']}: *{m['description']}*" for m in memes]
            await ctx.send("**Templates**" + "".join(lines))
    except TemplateError:
        await ctx.send(f"```Could not load '{template}'```")
    except:
        err = traceback.format_exc()
        if DEBUG:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)


async def refresh_templates(ctx: Context, arg: str = None):
    try:
        await ctx.trigger_typing()
        hard = arg == "--hard"
        if hard:
            if not ctx.message.author.guild_permissions.administrator:
                config = store.guild_config(ctx.message.guild)
                if not config.can_admin(ctx.message.author):
                    return await ctx.send(
                        f"```{config.no_admin(ctx.message.author)}```"
                    )
        else:
            config = store.guild_config(ctx.message.guild)
            if not config.can_edit(ctx.message.author):
                return await ctx.send(
                    f"```{config.no_admin(ctx.message.author,'refresh','edit')}```"
                )

        message = store.refresh_memes(ctx.message.guild, hard)
        await ctx.send(f"```{message}```")
    except:
        err = traceback.format_exc()
        if DEBUG:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)


async def set_admin_role(ctx: Context, roleid: str):
    try:
        config = store.guild_config(ctx.message.guild)
        role = ctx.guild.get_role(int(roleid))
        message = config.set_admin_role(ctx.message.author, role)
        store.save_guild_config(config)
        await ctx.send(textwrap.dedent(f"```{message}```"))
    except:
        err = traceback.format_exc()
        if DEBUG:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)


async def set_edit_role(ctx: Context, roleid: str):
    try:
        config = store.guild_config(ctx.message.guild)
        role = ctx.guild.get_role(int(roleid))
        message = config.set_edit_role(ctx.message.author, role)
        store.save_guild_config(config)
        await ctx.send(textwrap.dedent(f"```{message}```"))
    except:
        err = traceback.format_exc()
        if DEBUG:
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
        if DEBUG:
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
        if DEBUG:
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
        if DEBUG:
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
        if DEBUG:
            await ctx.send("```" + err[:1990] + "```")
        else:
            await ctx.send("```" + str(e) + "```")
        raise e


@bot.command(description="Administrative functions.")
async def memebot(ctx: Context, *args):
    """ Top level administrative function for bot."""
    num_args = 0 if args == None else len(args)
    try:
        if num_args > 0:
            if args[0] == "refresh":
                # Refreshes templates.
                return await refresh_templates(ctx, args[1] if len(args) > 1 else None)
            elif args[0] == "set_admin_role":
                # Sets an admin role.
                return await set_admin_role(ctx, str(args[1]))
            elif args[0] == "set_edit_role":
                # Sets edit role.
                return await set_edit_role(ctx, str(args[1]))
        await ctx.send("You used this command incorrectly. Try again.")
    except:
        err = traceback.format_exc()
        if DEBUG:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)


@bot.command(description="Make a new meme.")
async def meme(ctx: Context, template: str = None, *text):
    "Main bot command for rendering/showing memes."

    """
    If no template, or template but no text, then show info about
    the memes available.
    """
    if (template is None or template) and len(text) == 0:
        return await templates(ctx, template)
    # We have text now, so make it a meme.
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

        meme = store.get_template(ctx.message.guild, match, True)
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
        if DEBUG:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)


def run(debug, local):
    """
    Starts an instance of the bot using the passed-in options.
    """
    global DEBUG
    DEBUG = debug
    
    creds = get_creds(args.debug)

    global store
    store = get_store(args.local, args.debug)

    try:
        token = creds["discord_token"]
    except NameError:
        print(
            "Could not get Discord token from config/creds.json environment variable $DISCORD_TOKEN!"
        )
        sys.exit(1)

    bot.run(token)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Runs the bot with the passed in arguments."
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Run state::debug. True or false. Runs different credentials and logging level.",
    )

    parser.add_argument(
        "-l", "--local", action="store_true", help="Run locally without DynamoDB."
    )

    args = parser.parse_args()
    run(args.debug, args.local)
