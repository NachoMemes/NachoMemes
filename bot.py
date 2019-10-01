import io
import json
import os
import uuid
from datetime import datetime

import discord
import tinys3
from apscheduler.schedulers.background import BackgroundScheduler
from discord.ext import commands

import memegenerator

with open("creds.json", "rb") as f:
	creds = json.load(f)

sched = BackgroundScheduler()
sched.start()

s3 = tinys3.Connection(
	creds["access_key"], creds["secret"], tls=True, default_bucket="discord-memes"
)

with open("templates.json", "rb") as t:
	template_list = json.load(t) 

def _write_stats():
		""" Periodically write template statistics to disk.
		"""
		with open("templates.json", 'w') as t:
			json.dump(template_list, t)
		print("Wrote statistics to disk.")

def _s3_cleanup():
		""" Every hour dump the PNGs from the S3 bucket.
		"""
		s3.delete("*.png", "discord-memes")
		print("Deleted images from s3 @", datetime.now())

# Setup scheduled operations.
sched.add_job(_write_stats, "interval", minutes=10)
sched.add_job(_s3_cleanup, "interval", hours=1)

description = "A bot to generate custom memes using pre-loaded templates."
bot = commands.Bot(command_prefix="/", description=description)

@bot.event
async def on_ready():
	print(
		"""
	Only memes can melt steel beams.
						--Shia LaBeouf
	"""
	)


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
	l = {template: template_list[template]} if template else template_list
	if len(l) <= 1:
		body = (
			f"Name: {name}\nDescription: *{data['description']}*\nTimes used: {data['usage']}\nRead more: {data['docs']}"
			for name, data in l.items()
		)
	else:
		body = (f"{name}: *{data['description']}*" for name, data in l.items())
	await ctx.send("\n" + "\n".join(body))


@bot.command(description="Make a new meme.")
async def meme(ctx, memename: str, upper: str, lower: str, *rest):
	if rest:
		upper, lower = _reflow_text(upper, lower, rest)
	if memename in template_list:
		template_list[memename]["usage"]+=1
		# make the meme
		key = f"{uuid.uuid4().hex}.png"
		with io.BytesIO() as memeobj:
			memegenerator.make_meme(memeobj, upper, lower, f"{memename}.jpg")
			memeobj.flush()
			memeobj.seek(0)
			s3.upload(key, memeobj)
		await ctx.send(
			embed=discord.Embed()
			.set_image(url=f"http://discord-memes.s3.amazonaws.com/{key}")
			.set_footer(text="This meme brought to you by M. Zucc and the lizard people")
		)
	else:
		await ctx.send("Invalid template.")


def _reflow_text(s1, s2, sl):
	if "/" in sl:
		return (
			f"{s1} {s2} {' '.join(sl[:sl.index('/')])}",
			" ".join(sl[sl.index("/") + 1 :]),
		)


bot.run(creds["discord_token"])
