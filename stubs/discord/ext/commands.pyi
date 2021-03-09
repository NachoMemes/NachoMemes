from discord import Guild

from types import Any

class Context: 
    @property
    def guild(self) -> Guild: ...

    async def send(self, content: Any=None, *, tts: bool=False, embed: Any=None, file: Any=None,
                                          files: Any=None, delete_after: Any=None, nonce: Any=None,
                                          allowed_mentions: Any=None, reference: Any=None,
                                          mention_author: Any=None): ...