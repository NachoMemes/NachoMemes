# pylint: disable=broad-except,missing-function-docstring
# don't need docstrings for subcommands with descriptions

"""Discord bot go brrrr"""
import argparse
import io
import json
import os
import re
import sys
import textwrap
import traceback
from pathlib import Path
from typing import List, Union

import discord
from discord import Guild
from discord.ext import commands
from discord.ext.commands import Context
from fuzzywuzzy import process

from nachomemes import get_creds, get_store
from nachomemes.template import TemplateError
from nachomemes.guild_config import GuildConfig

DESCRIPTION = "A bot to generate custom memes using pre-loaded templates."
bot = commands.Bot(command_prefix="!", description=DESCRIPTION)

# Used for calculating memes/minute.
MEMES = 0

# Base directory from which paths should extend.
BASE_DIR = Path(__file__).parent.parent

# Debug mode (true or false)
DEBUG = False


def mentioned_members(ctx: Context) -> Union[List[discord.Member], None]:
    "Returns the id of a memeber mentioned in a message."
    return [m for m in ctx.message.mentions]

async def report(ctx: Context, ex: Exception, message: str="An error has occured"):
    """helper function to summarize or print the traceback of an error"""
    err = traceback.format_exc()
    if DEBUG:
        await ctx.send(message + "```" + err[:1990] + "```")
    else:
        await ctx.send(message + "```" + str(ex) + "```")
    # re-raise the exception so it's printed to the console
    raise ex

@bot.event
async def on_ready():
    """print startup message on bot initialization"""
    print("Only memes can melt steel beams.\n\t--Shia LaBeouf")

with open(os.path.join(BASE_DIR, "config/messages.json"), "rb") as c:
    statuses = json.load(c)["credits"]


def _match_template_name(name: str, guild: Guild) -> str:
    """Matches input fuzzily against proper names."""
    fuzzed = process.extractOne(name, store.list_memes(guild, ("name",)))
    if fuzzed[1] < 25:
        raise TemplateError(f"could not load a template matching {name}")
    return fuzzed[0]["name"]


def _find_close_matches(name: str, guild: GuildConfig) -> list:
    """Chooses top matches against input."""
    return [
        name[0]["name"]
        for name in process.extract(name, store.list_memes(guild, ("name",)))
        if name[1] > 40
    ]


async def fuzzed_templates(ctx: Context, template: str, guild: GuildConfig):
    """Fuzzy match multiple templates."""
    fuzzed_memes = _find_close_matches(template.strip("*"), guild)
    memes = [
        match
        for match in store.list_memes(guild, ("name", "description"))
        if match["name"] in fuzzed_memes
    ]
    lines = [f"\n{m['name']}: *{m['description']}*" for m in memes]
    await ctx.send("**Potential Templates**" + "".join(lines))


async def single_fuzzed_template(ctx: Context, template: str, guild: GuildConfig):
    """Fuzzy match a single template"""
    fmeme = _match_template_name(template, guild)
    _meme = store.get_template(guild, fmeme)
    await ctx.send(
        textwrap.dedent(
            f"""\
        Name: {_meme.name}
        Description: *{_meme.description}*
        Times used: {_meme.usage}
        Expects {len(_meme.textboxes)} strings
        Read more: {_meme.docs}"""
        )
    )


async def templates(ctx: Context, template: str = None):
    try:
        config: GuildConfig = store.guild_config(ctx.guild)
        if not config.can_use(ctx.author):
            return await ctx.send(f"```{config.no_memes()}```")
        if template:
            # A fuzzy multiple match
            if "*" in template:
                return await fuzzed_templates(ctx, template, config)
            # A single fuzzy match.
            return await single_fuzzed_template(ctx, template, config)
        else:
            # The whole damn list.
            memes = store.list_memes(config, ("name", "description"))
            lines = [f"\n{m['name']}: *{m['description']}*" for m in memes]
            await ctx.send("**Templates**" + "".join(lines))
    except TemplateError:
        await ctx.send(f"```Could not load '{template}'```")
    except Exception as ex:
        await report(ctx, ex, "error listing templates")


@bot.group(description="Administrative functions group")
async def memebot(ctx: Context):
    if ctx.subcommand_passed:
        return
    try:
        message = "\n".join((f"**{s.name}**: {s.description}"
            for s in ctx.command.walk_commands()))
        await ctx.send("Available commands\n"+message)
    except Exception as ex:
        await report(ctx, ex, "error listing commands")


@memebot.command(description="updates the database with template data")
async def refresh(ctx: Context, refresh_type: str=None):
    try:
        await ctx.trigger_typing()
        is_hard = refresh_type == "--hard"
        config: GuildConfig = store.guild_config(ctx.guild)
        if is_hard:
            if not config.can_admin(ctx.message.author):
                return await ctx.send(
                    f"```{config.no_admin(ctx.message.author)}```"
                )
        else:
            if not config.can_edit(ctx.message.author):
                return await ctx.send(
                    f"```{config.no_admin(ctx.message.author,'refresh','edit')}```"
                )

        message = store.refresh_memes(ctx.guild, is_hard)
        await ctx.send(f"```{message}```")
    except Exception as ex:
        await report(ctx, ex)

@memebot.command(description="set the discord role for adminstrators")
async def admin_role(ctx: Context, role_id: str=None):
    try:
        config: GuildConfig = store.guild_config(ctx.guild)
        if not role_id:
            role = ctx.guild.get_role(config.admin_role)
            await ctx.send(textwrap.dedent(f"```Members of '{role}' are authorized to administer the memes.```"))
        else:
            role = ctx.guild.get_role(int(role_id))
            message = config.set_admin_role(ctx.message.author, role)
            store.save_guild_config(config)
            await ctx.send(textwrap.dedent(f"```{message}```"))
    except Exception as ex:
        await report(ctx, ex)

@memebot.command(description="set the discord role for editors")
async def edit_role(ctx: Context, role_id: str=None):
    try:
        config: GuildConfig = store.guild_config(ctx.guild)
        if not role_id:
            role = ctx.guild.get_role(config.admin_role)
            await ctx.send(textwrap.dedent(f"```Members of '{role}' are authorized to edit the memes.```"))
        else:
            role = ctx.guild.get_role(int(role_id))
            message = config.set_edit_role(ctx.message.author, role)
            store.save_guild_config(config)
            await ctx.send(textwrap.dedent(f"```{message}```"))
    except Exception as ex:
        await report(ctx, ex)

@memebot.command(description="prevent user from interacting with bot")
async def shun(ctx: Context):
    try:
        config: GuildConfig = store.guild_config(ctx.guild)
        for subject in mentioned_members(ctx):
            message: str = config.shun(ctx.message.author, subject)
            await ctx.send(textwrap.dedent(f"```{message}```"))
        store.save_guild_config(config)
    except Exception as ex:
        await report(ctx, ex)
    

@memebot.command(description="permit user to interact with bot")
async def endorse(ctx: Context):
    try:
        config: GuildConfig = store.guild_config(ctx.guild)
        for subject in mentioned_members(ctx):
            message: str = config.endorse(ctx.message.author, subject)
            await ctx.send(textwrap.dedent(f"```{message}```"))
        store.save_guild_config(config)
    except Exception as ex:
        await report(ctx, ex)

@memebot.command(description="userinfo")
async def whoami(ctx: Context):
    try:
        config: GuildConfig = store.guild_config(ctx.guild)
        if ctx.message.mentions:
            members: List[discord.Member] = ctx.message.mentions
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
    except Exception as ex:
        await report(ctx, ex)

@memebot.command(description="Make a new template.")
async def save(ctx: Context):
    try:
        config: GuildConfig = store.guild_config(ctx.guild)
        if not config.can_edit(ctx.message.author):
            raise RuntimeError("computer says no")
        value = ctx.message.content
        value = ctx.message.content[value.index("save")+4:].strip().strip('`')
        message = store.save_meme(ctx.guild, json.loads(value))
        await ctx.send(textwrap.dedent(f"```{message}```"))
    except Exception as ex:
        await report(ctx, ex)

@bot.command(description="Make a new meme.")
async def meme(ctx: Context, template: str = None, /, *text):
    """Main bot command for rendering/showing memes.

    If no template, or template but no text, then show info about
    the memes available.
    """
    if (template is None or template) and len(text) == 0:
        return await templates(ctx, template)
    # We have text now, so make it a meme.
    try:
        await ctx.trigger_typing()
        config: GuildConfig = store.guild_config(ctx.guild)
        if not config.can_use(ctx.author):
            return await ctx.send(f"```{config.no_memes()}```")
        match = _match_template_name(template, ctx.guild)
        # Have the meme name be reflective of the contents.
        name = re.sub(r"\W+", "", str(text))
        key = f"{match}-{name}.png"

        _meme = store.get_template(ctx.guild, match, True)
        with io.BytesIO() as buffer:
            _meme.render(text, buffer)
            buffer.flush()
            buffer.seek(0)
            msg = await ctx.send(file=discord.File(buffer, key))
        for r in ("\N{THUMBS UP SIGN}", "\N{THUMBS DOWN SIGN}"):
            await msg.add_reaction(r)
    except TemplateError:
        await ctx.send(f"```Could not load '{match}'```")
    except Exception as ex:
        await report(ctx, ex)
        


def run(debug, local):
    """
    Starts an instance of the bot using the passed-in options.
    """
    global DEBUG
    DEBUG = debug

    creds = get_creds(debug)

    global store
    store = get_store(local, debug)

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
