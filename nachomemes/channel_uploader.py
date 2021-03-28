from io import BufferedIOBase

import discord
from discord import TextChannel, Client

from nachomemes import Uploader, SimpleCache

class DiscordChannelUploader(Uploader):
    channel: TextChannel

    def __init__(self, client: Client, channel_id: int):
        self.client = client
        self.channel_id = channel_id
        self.recent = SimpleCache(200)

    async def upload(self, buffer: BufferedIOBase, key: str=None) -> str: 
        if not  self.channel:
            self.channel = self.client.get_channel(self.channel_id)
        msg = await self.channel.send(file=discord.File(buffer, key))
        url = msg.attachments[0].url
        self.recent[url] = msg
        return url
        
    