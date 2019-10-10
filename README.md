# Nacho Memes

<p align="center">
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Made%20With-Python%203.7-blue.svg?style=for-the-badge" alt="Made with Python 3.7">
  </a>
</p>
<p align="center">
  <a href="https://github.com/Rapptz/discord.py/">
    <img src="https://img.shields.io/badge/discord-py-blue.svg" alt="discord.py">
  </a>
  <a href="https://github.com/ambv/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style: Black">
  </a>
  <a href="http://makeapullrequest.com">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg">
  </a>
  <a href="https://github.com/cooperpellaton/NachoMemes/tree/v1.0">
    <img src="https://img.shields.io/badge/version-1.0-bright%20green" alt="Version 1.0">
  </a>
</p>

Add [me](https://discordapp.com/oauth2/authorize?&client_id=628445658743046154&scope=bot&permissions=387136) to your server!

![A demo of the bot being used.](/watchme.gif)

## Overview

[This](https://discordapp.com/oauth2/authorize?&client_id=628445658743046154&scope=bot&permissions=387136) is a [Discord](https://discordapp.com) bot to create memes with custom text on top of pre-loaded image templates. Use this to mess with your friends and meme quickly without ever leaving the chat.

Need help getting started? Try `/helpmeme`:

```md
This is a bot to make memes from meme templates. To get more information try:

- /templates for a list of all supported templates.
- /templates <specific-template> for more information about each one.
- /meme <template-name> "UPPER TEXT" "LOWER TEXT" to make a meme from that _perfect_ template.
```

## Run This Yourself
### Local Development
The bot can be run in local development mode in order to test functionality without having to connect to AWS. In this mode, debug information will be printed and the bot will send images locally instead of uploading to AWS. Additionally, the images will be sent as images instead of embeds. To setup local development mode you must do the following:
1. Setup a bot on the [Discord Developers website](https://discordapp.com/developers/applications/)
2. Ensure that `testing = True` is set in `bot.py`. This should be located in the `if __name__ == "__main__"` section.
3. Run the bot with either the `"discord_token"` filled in in `config/creds.json` or the `$DISCORD_TOKEN` environment variable set:
```sh
DISCORD_TOKEN=<TOKEN> python bot.py
```

### Production
Make sure you have the `Impact` font installed. On Ubuntu you can get it through this package: `ttf-mscorefonts-installer`. Then, clone this repository and `pip install -r requirements.txt`. Generate some keys (AWS and Discord), and put them in a `config/creds.json` file like so:

```json
{
    "access_key": <TOKEN>,
    "secret": <TOKEN>,
    "region": <REGION>,
    "discord_token": <TOKEN>
}
```

Additionally, randomized footer messages are stored in [`config/messages.json`](config/messages.json). For more personality try editing the contents.

To add custom templates and layouts (i.e. photos and the textboxes that go over them) look into [`config/templates.json`](config/templates.json) and [`config/layouts.json`](config/layouts.json) respectively. *In the future the bot will support dynamic addition without editing these files.*

Run `python bot.py` and you're off to meme like a lord.

## Dependencies

Memes were originally generated using a forked version of the [Python Meme Generator](https://github.com/danieldiekmeier/memegenerator). Find the source [here](/memegenerator.py).

Now, however, memes are created using a custom [implementation](memegenerator.py).
