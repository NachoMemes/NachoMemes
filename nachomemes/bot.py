"""Discord bot go brrrr"""
import io
import json
import os
import re
import sys
import traceback
from io import BufferedIOBase
from textwrap import dedent
from pathlib import Path
from typing import cast, List, Optional, Iterable, Generator, Union
from json.decoder import JSONDecodeError
from contextlib import AbstractContextManager

import discord
from discord import Member, Role, Embed
from discord.message import Message
from discord.ext import commands
from discord.ext.commands import Bot, Context, Group

from nachomemes import Configuration, SimpleCache, Uploader
from nachomemes.template import TemplateError
from nachomemes.guild_config import GuildConfig
from nachomemes.store import Store, TemplateEncoder, update_serialization


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

def print_all_templates(config: GuildConfig) -> dict:
    memes = STORE.list_memes(config.guild_id, ("name", "description"))
    return {"embed": Embed(
        title="Available Templates",
        description = "".join((f"\n{m['name']}: *{m['description']}*" for m in memes))
    )}

def print_matching_templates(config: GuildConfig, template_name: str) -> dict:
    memes = STORE.close_matches(config.guild_id, template_name, ("name", "description"))
    return {"embed": Embed(
        title="Matching templates",
        description = "".join(f"\n{m['name']}: *{m['description']}*" for m in memes)
    )}

async def print_template(config: GuildConfig, template_name: str) -> dict:
    template = await STORE.best_match_with_preview(config.guild_id, template_name)
    response = {"embed": Embed(
        title="Template info",
        description = dedent(f"""\
        Name: {template.name}
        Description: *{template.description}*
        Times used: {template.usage}
        Expects {len(template.textboxes)} strings
        Read more: {template.docs}""")
        )}
    if template.preview_url:
        response["embed"] = response["embed"].set_image(url=template.preview_url.full_url)
    return response        


async def generate(config: GuildConfig, member: Member, data: Iterable[str]) -> dict:
    buffer: Optional[BufferedIOBase] = None
    try:
        if not config.can_use(member):
            return {"embed": Embed(
                title="NO",
                description = no_memes(config, member)
            )}
        if not data:
            return print_all_templates(config)

        (template_name, *text) = data
        if not text:
            if "*" in template_name:
                return print_matching_templates(config, template_name)
            else:
                return await print_template(config, template_name)

        template = STORE.best_match(config.guild_id, template_name, True)
        name = re.sub(r"\W+", "-", str(text))
        key = f"{template.name}-{name}.png"
        buffer = io.BytesIO()
        template.render(text, buffer)
        buffer.flush()
        buffer.seek(0)
        url = await UPLOADER.upload(buffer, key)

        return {
            "embed": Embed(type="image").set_image(url=url),
            "react": True
         }
    finally:
        if buffer:
            buffer.close()

async def report(ctx: Union[Context,Message], ex: Exception, message: str="An error has occured") -> Union[Context,Message]:
    """helper function to summarize or print the traceback of an error"""
    err = traceback.format_exc()
    print(err, file=sys.stderr)
    response: dict = {"embed": Embed(
        title = getattr(ex, "title", message),
        description = f"```{err[:1980]}```" if DEBUG else str(ex)
    )}
    if isinstance(ctx, Context):
        msg = await ctx.send(**response)
        return msg
    else:
        await ctx.edit(**response)
        return ctx

with open(os.path.join(BASE_DIR, "config/messages.json"), "rb") as c:
    statuses = json.load(c)["credits"]


def _get_member(ctx: Union[Message,Context]) -> Member:
    if isinstance(ctx, Context):
        return cast(Member, ctx.author)
    elif isinstance(ctx, Message):
        return cast(Member, ctx.author)

def _mentioned_members(ctx: Context) -> Iterable[Member]:
    "Returns the id of a memeber mentioned in a message."
    return (m for m in ctx.message.mentions if isinstance(m, Member))

def _mentions_or_author(ctx: Context) -> Iterable[Member]:
    return _mentioned_members(ctx) if ctx.message.mentions else (_get_member(ctx),)


def no_memes(config: GuildConfig, member: Member) -> str:
    return "You get nothing! Good day sir!"


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
        try:
            await msg.clear_reactions()
        except:
            pass

        data = after.content.split()
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
        

@bot.group(description="Administrative functions group")
async def memebot(ctx: Context):
    if ctx.subcommand_passed:
        return
    try:
        message = "\n".join((f"**`{s.name}`**: {s.description}"
            for s in cast(Group, ctx.command).walk_commands()))
        return await ctx.send(embed=Embed(
            title = "Available commands", 
            description = message
        ))
    except Exception as ex:
        await report(ctx, ex, "error listing commands")


@memebot.command(description="updates the database with template data")
async def refresh(ctx: Context, refresh_type: str=None):
    is_hard = refresh_type == "--hard"
    title = "Executing hard refresh" if is_hard else "Executing refresh"
    try:
        await ctx.trigger_typing()
        config: GuildConfig = STORE.guild_config(ctx.guild)
        if is_hard:
            if not config.can_admin(_get_member(ctx)):
                return await ctx.send(embed=Embed(
                    title = title, 
                    description = config.no_admin(_get_member(ctx))
                ))
        else:
            if not config.can_edit(_get_member(ctx)):
                return await ctx.send(embed=Embed(
                    title = title, 
                    description = config.no_admin(_get_member(ctx),'refresh','edit')
                ))
        return await ctx.send(embed=Embed(
                title = title, 
                description = STORE.refresh_memes(config.guild_id, is_hard)
        ))
    except Exception as ex:
        await report(ctx, ex)


@memebot.command(description="set the discord role for adminstrators")
async def admin_role(ctx: Context, role_id: str=None):
    try:
        if ctx.guild is None:
            raise ValueError ("no guild") 
        config: GuildConfig = STORE.guild_config(ctx.guild)
        if not role_id:
            return await ctx.send(embed=Embed(
                title = "Getting current discord admin role",
                description = f"Members of '{ctx.guild.get_role(config.admin_role)}' are authorized to administer the memes." 
                    if config.admin_role else 
                    "Nobody is authorized to administer the memes."
            ))
        else:
            role = ctx.guild.get_role(int(role_id)) if role_id else None
            description = config.set_admin_role(_get_member(ctx), role)
            STORE.save_guild_config(config)
            return await ctx.send(embed=Embed(
                title = "Setting discord admin role to " + role_id,
                description = description
            ))
    except Exception as ex:
        await report(ctx, ex)


@memebot.command(description="set the discord role for editors")
async def edit_role(ctx: Context, role_id: str=None):
    try:
        if ctx.guild is None:
            raise ValueError ("no guild") 
        config: GuildConfig = STORE.guild_config(ctx.guild)
        if not role_id:
            return await ctx.send(embed=Embed(
                title = "Getting current discord edit role",
                description = f"Members of '{ctx.guild.get_role(config.edit_role)}' are authorized to edit the memes." 
                    if config.edit_role else 
                    "Nobody is authorized to administer the memes."
            ))
        else:
            role = ctx.guild.get_role(int(role_id)) if role_id else None
            description = config.set_edit_role(_get_member(ctx), role)
            STORE.save_guild_config(config)
            return await ctx.send(embed=Embed(
                title = "Setting discord edit role to " + role_id,
                description = description
            ))
    except Exception as ex:
        await report(ctx, ex)


@memebot.command(description="prevent user from interacting with bot")
async def shun(ctx: Context):
    try:
        config: GuildConfig = STORE.guild_config(ctx.guild)
        for subject in _mentioned_members(ctx):
            await ctx.send(embed=Embed(
                title = "Shunning " + subject.display_name,
                description = config.shun(_get_member(ctx), subject)
            ))
        STORE.save_guild_config(config)
    except Exception as ex:
        await report(ctx, ex)
    

@memebot.command(description="permit user to interact with bot")
async def endorse(ctx: Context):
    try:
        config: GuildConfig = STORE.guild_config(ctx.guild)
        for subject in _mentioned_members(ctx):
            await ctx.send(embed=Embed(
                title = "Endorsing " + subject.display_name,
                description = config.endorse(_get_member(ctx), subject)
            ))
        STORE.save_guild_config(config)
    except Exception as ex:
        await report(ctx, ex)


@memebot.command(description="userinfo")
async def whoami(ctx: Context):
    try:
        config: GuildConfig = STORE.guild_config(ctx.guild)
        for subject in _mentions_or_author(ctx):
            await ctx.send(embed=Embed(
                title = "User info for " + subject.display_name,
                description = dedent(f"""
                    Name: {config.member_full_name(subject)}
                    Can use: {config.can_use(subject)}, Can edit: {config.can_edit(subject)}, Can admin: {config.can_admin(subject)}""")
            ))
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
        await ctx.send(embed=Embed(
            title = "Saving meme",
            description = STORE.save_meme(config.guild_id, json.loads(value))
        ))
    except JSONDecodeError as ex:
        await report(ctx, ex, "Invalid JSON provided")
    except Exception as ex:
        await report(ctx, ex)


@memebot.command(description="dump template json")
async def dump(ctx: Context, template_name: str=None):
    try:
        config: GuildConfig = STORE.guild_config(ctx.guild)
        if not config.can_edit(_get_member(ctx)):
            raise RuntimeError("computer says no")
        template = STORE.best_match(config.guild_id, template_name, )
        result = json.dumps(update_serialization(template.__dict__), indent=2, cls=TemplateEncoder)
        await ctx.send(embed=Embed(
            title = "Exporting meme",
            description = f"```{result}```"
        ))
    except Exception as ex:
        await report(ctx, ex)


@bot.command(description="Make a new meme.")
async def meme(ctx: Context):
    """Main bot command for rendering/showing memes.

    If no template, or template but no text, then show info about
    the memes available.
    """
    try:
        data = ctx.message.content.split()
        if not data or data.pop(0) != "!meme":
            return
            
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
