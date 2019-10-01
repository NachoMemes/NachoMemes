# Nacho Memes

<p align="center">
    <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Made%20With-Python%203.7-blue.svg?style=for-the-badge" alt="Made with Python 3.7">
  </a>
  <a href="https://github.com/Rapptz/discord.py/">
      <img src="https://img.shields.io/badge/discord-py-blue.svg" alt="discord.py">
  </a>
  <a href="https://github.com/ambv/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style: Black">
  </a>
  <a href="http://makeapullrequest.com">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg">
  </a>
</p>

Add [me](https://discordapp.com/oauth2/authorize?&client_id=628445658743046154&scope=bot&permissions=59392) to your server!

## Overview

This is a [Discord](https://discordapp.com) bot to create memes with custom text on top of pre-loaded image templates. Use this to mess with your friends and meme quickly without ever leaving the chat.

Need help getting started? Try `/helpmeme`:

```md
This is a bot to make memes from meme templates. To get more information try:

- /templates for a list of all supported templates.
- /templates <specific-template> for more information about each one.
- /meme <template-name> "UPPER TEXT" "LOWER TEXT" to make a meme from that _perfect_ template.
```

## Run This Yourself

Make sure you have the `Impact` font installed. On Ubuntu you can get it through this package: `ttf-mscorefonts-installer`. Then, clone this repository and `pip install -r requirements.txt`. Generate some keys (AWS and Discord), and put them in a `creds.json` file like so:

```json
{
    "access_key": <TOKEN>,
    "secret": <TOKEN>,
    "region": <REGION>,
    "discord_token": <TOKEN>
}
```

Run `python bot.py` and you're off to meme like a lord.

## Dependencies

Memes are generated using a forked version of the [Python Meme Generator](https://github.com/danieldiekmeier/memegenerator). Find the source [here](/memegenerator.py).
