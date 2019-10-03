import io
import json
import random
import os
import uuid
from datetime import datetime, timedelta

import discord
import tinys3
from apscheduler.schedulers.background import BackgroundScheduler
from discord.ext import commands
from itertools import takewhile, chain

from memegenerator import MemeTemplate, TextBox

with open("config/creds.json", "rb") as f:
    creds = json.load(f)

sched = BackgroundScheduler()
sched.start()

s3 = tinys3.Connection(
    creds["access_key"], creds["secret"], tls=True, default_bucket="discord-memes"
)

# load meme layouts
with open("config/layouts.json", "rb") as t:
    layouts = json.load(t, object_hook=lambda d: TextBox.deserialize(d) if "face" in d else d)

# load memes
with open("config/templates.json", "rb") as t:
    memes = json.load(t, object_hook=lambda d: MemeTemplate.deserialize(d, layouts) if "source" in d else d)

credit_text = [
    "This meme brought to you by M. Zucc and the lizard people.",
    "Paid for by Trump for President 2020.",
    "Brought to you by MIS.",
    "China numba one!",
    "Why the fuck are you reading this?",
]

def partition_on(pred, seq):
    i = iter(seq)
    while True:
        n = next(i)
        yield takewhile(lambda v: not pred(v), chain([n], i))

def _write_stats():
    """ Periodically write template statistics to disk.
		"""
    with open("config/templates.json", "w") as t:
        json.dump(memes, t, default=lambda o: o.serialize())
    print("Wrote statistics to disk.")


def _s3_cleanup():
    """ Dump PNGs older than 1 week from S3 (on the hour).
		"""
    to_del = [meme for meme in s3.list() if ".png" in meme["key"]]
    count = 0
    for meme in to_del:
        if (meme["last_modified"] - datetime.utcnow()) >= timedelta(weeks=1):
            count += 1
            s3.delete(meme["key"], "discord-memes")
    print(f"Deleted {count} images from s3 @ {datetime.now()}")


# Setup scheduled operations.
sched.add_job(_write_stats, "interval", minutes=10)
sched.add_job(_s3_cleanup, "interval", hours=1)

# Bot configuration.
description = "A bot to generate custom memes using pre-loaded templates."
bot = commands.Bot(command_prefix="/", description=description)


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
    l = {template: memes[template]} if template else memes
    if len(l) <= 1:
        body = (
            f"Name: {name}\nDescription: *{data['description']}*\nTimes used: {data['usage']}\nRead more: {data['docs']}"
            for name, data in l.items()
        )
    else:
        body = (f"{name}: *{data['description']}*" for name, data in l.items())
    await ctx.send("\n" + "\n".join(body))


@bot.command(description="Make a new meme.")
async def meme(ctx, memename: str, *text):
    # Validate the meme.
    if memename in memes:
        meme = memes[memename]
        strings = _reflow_text(text, meme.box_count)
        meme.usage += 1
        key = f"{uuid.uuid4().hex}.png"
        with io.BytesIO() as memeobj:
            # Render the meme.
            meme.render(strings, memeobj)
            memeobj.flush()
            memeobj.seek(0)
            # Upload meme to S3.
            s3.upload(key, memeobj)
        # Send the meme as a message.
        await ctx.send(
            embed=discord.Embed()
            .set_image(url=f"http://discord-memes.s3.amazonaws.com/{key}")
            .set_footer(text=random.choice(credit_text))
        )
    else:
        await ctx.send("Invalid template.")


def _reflow_text(text, count):
    if len(text) == count:
        return text
    if "//" in text:
        result = ["/n".join(" ".join(l) for l in partition_on(lambda s: s=='/', b)) for b in partition_on(lambda s: s == '//', text)]
        assert len(result) == count
        return result
    elif "/" in text:
        result = [" ".join(l) for l in partition_on(lambda s: s == '/', text)]
        assert len(result) == count
        return result


bot.run(creds["discord_token"])
