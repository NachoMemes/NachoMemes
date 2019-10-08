import io
import json
import os
import random
import uuid
import sys
from datetime import datetime, timedelta
import traceback
from typing import Iterable

import discord
import tinys3
from discord.ext import commands
from discord.ext.commands import Context
from render import MemeTemplate, TextBox, default_templates
from dynamo import TemplateStore, TemplateError
from localstore import LocalTemplateStore


description = "A bot to generate custom memes using pre-loaded templates."
bot = commands.Bot(command_prefix="/", description=description)


# Load credit messages to put in the footer.
with open("config/messages.json", "rb") as c:
    credit_text = json.load(c)["credits"]


def _s3_cleanup():
    """ Dump PNGs older than 1 week from S3 (on the hour).
        """
    to_del = [meme for meme in s3.list() if ".png" in meme["key"]]
    count = 0
    for meme in to_del:
        if (meme["last_modified"] - datetime.utcnow()) >= timedelta(weeks=1):
            count += 1
            s3.delete(meme["key"], "discord-memes")
    if count > 0:
        print(f"Deleted {count} images from s3 @ {datetime.now()}")


@bot.event
async def on_ready():
    print("Only memes can melt steel beams.\n\t--Shia LaBeouf")


@bot.command(description="Help a user get setup.")
async def helpmeme(ctx):
    await ctx.send(
        """This is a bot to make memes from meme templates. To get more information try:  
- `/templates` for a list of all supported templates.
- `/templates <specific-template>` for more information about each one.
- `/meme <template-name> "UPPER TEXT" "LOWER TEXT"` to make a meme from that *perfect* template.
"""
    )


@bot.command(description="List templates.")
async def templates(ctx, template=None):
    try:
        guild = str(ctx.message.guild.id)
        if template:
            meme = store.read_meme(guild, template)
            await ctx.send(f"""
                Name: {meme.name}
                Description: *{meme.description}*
                Times used: {meme.usage}
                Expects {len(meme.textboxes)} strings
                Read more: {meme.docs}"""
            )
        else:
            await ctx.send(
                "".join(
                    f"\n{meme['name']}: *{meme['description']}*"
                    for meme in store.list_memes(guild)
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
async def refresh_templates(ctx: Context, arg: str=None):
    guild = str(ctx.message.guild.id)
    message = store.refresh_memes(guild, arg == "--hard")
    await ctx.send(f"```{message}```")


@bot.command(description="Make a new meme.")
async def meme(ctx: Context, template: str, *text):
    try:
        guild = str(ctx.message.guild.id)
        meme = store.read_meme(guild, template, True)
        key = f"{uuid.uuid4().hex}.png"

        if testing:
            with io.BytesIO() as buffer:
                meme.render(text, buffer)
                buffer.flush()
                buffer.seek(0)

                msg = await ctx.send(file = discord.File(buffer, "meme.png"))
        else:
            with io.BytesIO() as buffer:
                # Render the meme.
                meme.render(text, buffer)
                buffer.flush()
                buffer.seek(0)
                # Upload meme to S3.
                s3.upload(key, buffer)
            # Send the meme as a message.
            e = discord.Embed().set_image(
                url=f"http://discord-memes.s3.amazonaws.com/{key}"
            )
            if random.randrange(8) == 0:
                e.set_footer(text=random.choice(credit_text))
            msg = await ctx.send(embed=e)

        for r in ('\N{THUMBS UP SIGN}', '\N{THUMBS DOWN SIGN}'):
            await msg.add_reaction(r)
    except TemplateError:
        await ctx.send(f"```Could not load '{template}'```")
    except:
        err = traceback.format_exc()
        if testing:
            await ctx.send("```" + err[:1990] + "```")
        print(err, file=sys.stderr)


if __name__ == "__main__":
    global testing
    testing = True

    if not testing:
        with open("config/creds.json", "rb") as f:
            creds = json.load(f)

    global store
    store = LocalTemplateStore(default_templates) if testing else TemplateStore(creds["access_key"], creds["secret"], creds["region"], default_templates)

    global s3
    if not testing:
        s3 = tinys3.Connection(
            creds["access_key"], creds["secret"], tls=True, default_bucket="discord-memes"
        )

    try:
        token = creds["discord_token"]
    except NameError:
        token = os.environ.get("DISCORD_TOKEN")
        if token == None:
            print("Could not get Discord token from config/creds.json environment variable $DISCORD_TOKEN!")
            sys.exit(1)

    bot.run(token)
