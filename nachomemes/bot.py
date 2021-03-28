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
from io import BufferedIOBase
from pathlib import Path
from typing import cast, List, Optional, Iterable, Generator, Union
from json.decoder import JSONDecodeError
from contextlib import AbstractContextManager

import discord
from discord import Member, Role
from discord.message import Message
from discord.ext import commands
from discord.ext.commands import Bot, Context

from nachomemes import Configuration, SimpleCache, Uploader
from nachomemes.template import TemplateError
from nachomemes.guild_config import GuildConfig
from nachomemes.store import Store, TemplateEncoder
from .util import contextmanager

# this description describes
DESCRIPTION = "A bot to generate custom memes using pre-loaded templates."

# this is the bot
bot = Bot(command_prefix="!", description=DESCRIPTION)

# this is where we keep the memes
STORE: Store

UPLOADER: Uploader

# Base directory from which paths should extend.
BASE_DIR = Path(__file__).parent.parent

# Debug mode (true or false)
DEBUG = False

UPLOAD_ALL = True

# recent meme requests (and the resulting meme message)
RECENT: SimpleCache[int,Message] = SimpleCache(200)

async def report(ctx: Union[Context,Message], ex: Exception, message: str="An error has occured"):
    """helper function to summarize or print the traceback of an error"""
    err = traceback.format_exc()
    print(err, file=sys.stderr)

    response = {"content": message + "```" + err[:1980] if DEBUG else str(ex) + "```"}
    if isinstance(ctx, Context):
        return await ctx.send(**response)
    else:
        await ctx.edit(**response)
        return ctx
    # re-raise the exception so it's printed to the console

@bot.event
async def on_ready():
    """print startup message on bot initialization"""
    print("Only memes can melt steel beams.\n\t--Shia LaBeouf")

@bot.event
async def on_message_delete(message: Message):
    if message.id in RECENT:
        await RECENT.pop(message.id).delete()

@bot.event
async def on_message_edit(before: Message, after: Message):
    msg = RECENT.pop(before.id, None)
    if not msg:
        return
    try:
        config = STORE.guild_config(after.guild)
        # await msg.clear_reactions()
        data = after.content.split();
        if not data or data.pop(0) != "!meme":
            return

        response = await generate(config, _get_member(after), data)

        if "buffer" in response:
            url = await UPLOADER.upload(response.pop("buffer", None), response.pop("key"))
            response["content"] = url
        react = response.pop("react", False)

        await msg.edit(**response)


        if react:
            for r in ("\N{THUMBS UP SIGN}", "\N{THUMBS DOWN SIGN}"):
                await msg.add_reaction(r)

    except TemplateError as err:
        await msg.edit(content=f"```{err}```")
    except Exception as ex:
        await report(msg, ex)
    # save the message for later modification
    RECENT[after.id] = msg

        

with open(os.path.join(BASE_DIR, "config/messages.json"), "rb") as c:
    statuses = json.load(c)["credits"]


def _get_member(ctx: Union[Message,Context]) -> Member:
    member = ctx.author
    assert isinstance(member, Member)
    return member

def _mentioned_members(ctx: Context) -> Iterable[Member]:
    "Returns the id of a memeber mentioned in a message."
    return (m for m in ctx.message.mentions if isinstance(m, Member))

def _mentions_or_author(ctx: Context) -> Iterable[Member]:
    return _mentioned_members(ctx) if ctx.message.mentions else (_get_member(ctx),)


def no_memes(config: GuildConfig, member: Member) -> str:
    return "```You get nothing! Good day sir!```"


def print_template(config: GuildConfig, template_name: str) -> str:
    if "*" not in template_name:
        # try to find the best match
        template = STORE.best_match(config.guild_id, template_name)
        return textwrap.dedent(f"""\
            Name: {template.name}
            Description: *{template.description}*
            Times used: {template.usage}
            Expects {len(template.textboxes)} strings
            Read more: {template.docs}"""
        )
    # otherwise list possible options
    memes = STORE.close_matches(config.guild_id, template_name, ("name", "description"))
    lines = (f"\n{m['name']}: *{m['description']}*" for m in memes)
    return "**Potential Templates**" + "".join(lines)




def list_templates(config: GuildConfig) -> str:
    memes = STORE.list_memes(config.guild_id, ("name", "description"))
    lines = [f"\n{m['name']}: *{m['description']}*" for m in memes]
    return "**Templates**" + "".join(lines)


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
async def dump(ctx: Context, template_name: str=None):
    if not template_name:
        return await ctx.send(textwrap.dedent(f"```No template name provided```"))
    try:
        config: GuildConfig = STORE.guild_config(ctx.guild)
        if not config.can_edit(_get_member(ctx)):
            raise RuntimeError("computer says no")
        template = STORE.best_match(template_name, config.guild_id)
        message = json.dumps(template, cls=TemplateEncoder)
        await ctx.send(textwrap.dedent(f"```{message}```"))
    except TemplateError as ex:
        await ctx.send(textwrap.dedent(f'```No template matching "{template_name}" found```'))
    except Exception as ex:
        await report(ctx, ex)


async def generate(config: GuildConfig, member: Member, data: Iterable[str]) -> dict:
    buffer: Optional[BufferedIOBase] = None
    try:
        if not config.can_use(member):
            return {"content": no_memes(config, member)}

        if not data:
            return {"content": list_templates(config)}

        (template_name, *text) = data
        if not text:
            return {"content": print_template(config, template_name)}

        template = STORE.best_match(config.guild_id, template_name, True)
        name = re.sub(r"\W+", "", str(text))
        key = f"{template.name}-{name}.png"
        buffer = io.BytesIO()
        template.render(text, buffer)
        buffer.flush()
        buffer.seek(0)
        url = await UPLOADER.upload(buffer, key)
        return {"content": url, "react": True}
    finally:
        if buffer:
            buffer.close()


@bot.command(description="Make a new meme.")
async def meme(ctx: Context, *data):
    """Main bot command for rendering/showing memes.

    If no template, or template but no text, then show info about
    the memes available.
    """
    try:
        await ctx.trigger_typing()
        config = STORE.guild_config(ctx.guild)
        response = await generate(config, _get_member(ctx), data)

        react = response.pop("react", False)

        msg = await ctx.send(**response)

        # save the message for later modification
        RECENT[ctx.message.id] = msg

        if react:
            for r in ("\N{THUMBS UP SIGN}", "\N{THUMBS DOWN SIGN}"):
                await msg.add_reaction(r)

    except TemplateError as err:
        RECENT[ctx.message.id] = await ctx.send(f"```{err}```")
    except Exception as ex:
        RECENT[ctx.message.id] = await report(ctx, ex)
        

def run(config: Configuration) -> None:
    """Starts an instance of the bot using the provided configuration."""
    config.discord_client = bot

    global DEBUG
    DEBUG = config.debug
    
    global STORE
    STORE = config.store

    global UPLOADER
    UPLOADER = config.uploader

    config.start_discord_client()

if __name__ == "__main__":
    run(Configuration())
