# Nacho Memes

Add [me](https://discordapp.com/oauth2/authorize?&client_id=628445658743046154&scope=bot&permissions=59392) to your server!

Get it? Because they're not your memes.

## Overview

This is a Discord bot to create memes with custom text on top of pre-loaded image templates. Use this to mess with your friends, or respond quickly without ever leaving the chat.

Need help getting started? Try `/helpmeme`:

```md
This is a bot to make memes from meme templates. To get more information try:
- /templates for a list of all supported templates.
- /templates <specific-template> for more information about each one.
- /meme <template-name> "UPPER TEXT" "LOWER TEXT" to make a meme from that *perfect* template.
```

## Run This Yourself

Make sure you have the Impact font installed. On Ubuntu you can get it through this package: `ttf-mscorefonts-installer`. Then clone this repository and `pip install -r requirements.txt`. Generate some keys (AWS and Discord), and put them in a `creds.json` file like so:

```json
{
    "access_key": <TOKEN>,
    "secret": <TOKEN>,
    "region": <REGION>,
    "discord_token": <TOKEN>
}
```

Now you're off to meme like a lord.
