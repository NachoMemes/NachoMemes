from io import BufferedIOBase

import discord
from discord import TextChannel

from nachomemes import Uploader, SimpleCache

class DiscordChannelUploader(Uploader):
    def __init__(self, channel: TextChannel):
        self.channel = channel
        self.recent = SimpleCache(200)

    async def upload(self, buffer: BufferedIOBase, key: str=None) -> str: 
        msg = await self.channel.send(file=discord.File(buffer, key))
        url = msg.attachments[0].url
        self.recent[url] = msg
        return url
        
    