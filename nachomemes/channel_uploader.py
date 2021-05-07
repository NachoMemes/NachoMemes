from typing import cast, Optional, BinaryIO

import discord
from discord import TextChannel, Client, Message

from nachomemes import Uploader, SimpleCache

class DiscordChannelUploader(Uploader):
    channel: Optional[TextChannel] = None

    def __init__(self, client: Client, channel_id: int):
        self.client = client
        self.channel_id = channel_id
        self.recent: SimpleCache[int,Message] = SimpleCache(200)

    async def upload(self, buffer: BinaryIO, key: str=None) -> str: 
        if not  self.channel:
            self.channel = cast(TextChannel, self.client.get_channel(self.channel_id))
        msg = await cast(TextChannel, self.channel).send(file=discord.File(buffer, key))
        url = msg.attachments[0].url
        self.recent[url] = msg
        return url
        
    