# pylint: disable=broad-except,missing-function-docstring
# don't need docstrings for subcommands with descriptions

"""Discord bot go brrrr"""
import io
import json
import os
import re
import sys
import textwrap
import traceback
from pathlib import Path
from collections import OrderedDict
from typing import List, Optional, Iterable
from json.decoder import JSONDecodeError


import discord
from discord import Member, Role, Message
from discord.ext import commands
from discord.ext.commands import Context
from fuzzywuzzy import process

from nachomemes import get_creds, get_store, get_args
from nachomemes.template import TemplateError
from nachomemes.guild_config import GuildConfig
from nachomemes.store import Store, TemplateEncoder

# this description describes
DESCRIPTION = "A bot to generate custom memes using pre-loaded templates."

# this is the bot
bot = commands.Bot(command_prefix="!", description=DESCRIPTION)

# this is where we keep the memes
STORE: Store

# Base directory from which paths should extend.
BASE_DIR = Path(__file__).parent.parent

# Debug mode (true or false)
DEBUG = False

# recent meme requests (and the resulting meme message)
RECENT = OrderedDict()

MAX_RECENT = 200


async def report(ctx: Context, ex: Exception, message: str="An error has occured"):
    """helper function to summarize or print the traceback of an error"""
    err = traceback.format_exc()
    if DEBUG:
        await ctx.send(message + "```" + err[:1980] + "```")
    else:
        await ctx.send(message + "```" + str(ex) + "```")
    # re-raise the exception so it's printed to the console
    raise ex

@bot.event
async def on_ready():
    """print startup message on bot initialization"""
    print("Only memes can melt steel beams.\n\t--Shia LaBeouf")

@bot.event
async def on_message_delete(message: Message):
    if message.id in RECENT:
        await RECENT.pop(message.id).delete()




with open(os.path.join(BASE_DIR, "config/messages.json"), "rb") as c:
    statuses = json.load(c)["credits"]


def _match_template_name(name: str, guild: GuildConfig) -> str:
    """Matches input fuzzily against proper names."""
    fuzzed = process.extractOne(name, STORE.list_memes(guild.guild_id, ("name",)))
    if fuzzed[1] < 25:
        raise TemplateError(f"could not load a template matching {name}")
    return fuzzed[0]["name"]


def _find_close_matches(name: str, guild: GuildConfig) -> list:
    """Chooses top matches against input."""
    return [
        name[0]["name"]
        for name in process.extract(name, STORE.list_memes(guild.guild_id, ("name",)))
        if name[1] > 40
    ]

def _get_member(ctx: Context) -> Member:
    member = ctx.author
    assert isinstance(member, Member)
    return member

def _mentioned_members(ctx: Context) -> Iterable[Member]:
    "Returns the id of a memeber mentioned in a message."
    return (m for m in ctx.message.mentions if isinstance(m, Member))

def _mentions_or_author(ctx: Context) -> Iterable[Member]:
    return _mentioned_members(ctx) if ctx.message.mentions else (_get_member(ctx),)


async def fuzzed_templates(ctx: Context, template: str, guild: GuildConfig):
    """Fuzzy match multiple templates."""
    fuzzed_memes = _find_close_matches(template.strip("*"), guild)
    memes = [
        match
        for match in STORE.list_memes(guild.guild_id, ("name", "description"))
        if match["name"] in fuzzed_memes
    ]
    lines = [f"\n{m['name']}: *{m['description']}*" for m in memes]
    await ctx.send("**Potential Templates**" + "".join(lines))


async def single_fuzzed_template(ctx: Context, template: str, guild: GuildConfig):
    """Fuzzy match a single template"""
    fmeme = _match_template_name(template, guild)
    _meme = STORE.get_template(guild.guild_id, fmeme)
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
        config: GuildConfig = STORE.guild_config(ctx.guild)
        if not config.can_use(_get_member(ctx)):
            return await ctx.send(f"```{config.no_memes()}```")
        if template:
            # A fuzzy multiple match
            if "*" in template:
                return await fuzzed_templates(ctx, template, config)
            # A single fuzzy match.
            return await single_fuzzed_template(ctx, template, config)
        else:
            # The whole damn list.
            memes = STORE.list_memes(config.guild_id, ("name", "description"))
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
        config: GuildConfig = STORE.guild_config(ctx.guild)
        if is_hard:
            if not config.can_admin(_get_member(ctx)):
                return await ctx.send(
                    f"```{config.no_admin(_get_member(ctx))}```"
                )
        else:
            if not config.can_edit(_get_member(ctx)):
                return await ctx.send(
                    f"```{config.no_admin(_get_member(ctx),'refresh','edit')}```"
                )

        message = STORE.refresh_memes(config.guild_id, is_hard)
        await ctx.send(f"```{message}```")
    except Exception as ex:
        await report(ctx, ex)

@memebot.command(description="set the discord role for adminstrators")
async def admin_role(ctx: Context, role_id: str=None):
    try:
        config: GuildConfig = STORE.guild_config(ctx.guild)
        if not role_id:
            role: Optional[Role] = ctx.guild.get_role(config.admin_role) if config.admin_role else None
            await ctx.send(textwrap.dedent(
                f"```Members of '{role}' are authorized to administer the memes.```"))
        else:
            role = ctx.guild.get_role(int(role_id)) if role_id else None
            message = config.set_admin_role(_get_member(ctx), role)
            STORE.save_guild_config(config)
            await ctx.send(textwrap.dedent(f"```{message}```"))
    except Exception as ex:
        await report(ctx, ex)

@memebot.command(description="set the discord role for editors")
async def edit_role(ctx: Context, role_id: str=None):
    try:
        config: GuildConfig = STORE.guild_config(ctx.guild)
        if not role_id:
            role: Optional[Role] = ctx.guild.get_role(config.edit_role) if config.edit_role else None
            await ctx.send(textwrap.dedent(f"```Members of '{role}' are authorized to edit the memes.```"))
        else:
            role = ctx.guild.get_role(int(role_id)) if role_id else None
            message = config.set_edit_role(_get_member(ctx), role)
            STORE.save_guild_config(config)
            await ctx.send(textwrap.dedent(f"```{message}```"))
    except Exception as ex:
        await report(ctx, ex)

@memebot.command(description="prevent user from interacting with bot")
async def shun(ctx: Context):
    try:
        config: GuildConfig = STORE.guild_config(ctx.guild)
        for subject in _mentioned_members(ctx):
            message: str = config.shun(_get_member(ctx), subject)
            await ctx.send(textwrap.dedent(f"```{message}```"))
        STORE.save_guild_config(config)
    except Exception as ex:
        await report(ctx, ex)
    

@memebot.command(description="permit user to interact with bot")
async def endorse(ctx: Context):
    try:
        config: GuildConfig = STORE.guild_config(ctx.guild)
        for subject in _mentioned_members(ctx):
            message: str = config.endorse(_get_member(ctx), subject)
            await ctx.send(textwrap.dedent(f"```{message}```"))
        STORE.save_guild_config(config)
    except Exception as ex:
        await report(ctx, ex)

@memebot.command(description="userinfo")
async def whoami(ctx: Context):
    try:
        config: GuildConfig = STORE.guild_config(ctx.guild)
        for member in _mentions_or_author(ctx):
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
        config: GuildConfig = STORE.guild_config(ctx.guild)
        if not config.can_edit(_get_member(ctx)):
            raise RuntimeError("computer says no")
        value = ctx.message.content
        value = ctx.message.content[value.index("save")+4:].strip().strip('`')
        message = STORE.save_meme(config.guild_id, json.loads(value))
        await ctx.send(textwrap.dedent(f"```{message}```"))
    except JSONDecodeError:
        await ctx.send(textwrap.dedent(f"```invalid JSON provided```"))
    except Exception as ex:
        await report(ctx, ex)

@memebot.command(description="dump template json")
async def dump(ctx: Context, template_name: str):
    try:
        config: GuildConfig = STORE.guild_config(ctx.guild)
        if not config.can_edit(_get_member(ctx)):
            raise RuntimeError("computer says no")
        match = _match_template_name(template_name, config)
        data = STORE.get_template_data(config.guild_id, match)
        message = json.dumps(data, cls=TemplateEncoder)
        await ctx.send(textwrap.dedent(f"```{message}```"))
    except Exception as ex:
        await report(ctx, ex)

@bot.command(description="Make a new meme.")
async def meme(ctx: Context, template: str = None, /, *text):
    """Main bot command for rendering/showing memes.

    If no template, or template but no text, then show info about
    the memes available.
    """
    if not isinstance(template, str) or len(text) == 0:
        return await templates(ctx, template)
    # We have text now, so make it a meme.
    try:
        await ctx.trigger_typing()
        config = STORE.guild_config(ctx.guild)
        if not config.can_use(_get_member(ctx)):
            return await ctx.send(f"```{config.no_memes()}```")
        match = _match_template_name(template, config)
        # Have the meme name be reflective of the contents.
        name = re.sub(r"\W+", "", str(text))
        key = f"{match}-{name}.png"
        _meme = STORE.get_template(config.guild_id, match, True)
        with io.BytesIO() as buffer:
            _meme.render(text, buffer)
            buffer.flush()
            buffer.seek(0)
            msg = await ctx.send(file=discord.File(buffer, key))

        # same the message for later deletion
        RECENT[ctx.message.id] = msg
        if len(RECENT) > MAX_RECENT:
            RECENT.popitem(last=False)

        for r in ("\N{THUMBS UP SIGN}", "\N{THUMBS DOWN SIGN}"):
            await msg.add_reaction(r)
    except TemplateError:
        await ctx.send(f"```Could not load '{match}'```")
    except Exception as ex:
        await report(ctx, ex)
        


def run(debug: bool, local: bool) -> None:
    """
    Starts an instance of the bot using the passed-in options.
    """
    global DEBUG
    DEBUG = debug

    creds = get_creds(debug)

    global STORE
    STORE = get_store(local, debug)

    try:
        token = creds["discord_token"]
    except NameError:
        print(
            "Could not get Discord token from config/creds.json environment variable $DISCORD_TOKEN!"
        )
        sys.exit(1)

    bot.run(token)


if __name__ == "__main__":
    args = get_args()
    run(args.debug, args.local)
