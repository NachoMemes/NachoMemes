from discord import Guild

class Context: 
    @property
    def guild(self) -> Guild: ...

    async def send(self, content=None, *, tts=False, embed=None, file=None,
                                          files=None, delete_after=None, nonce=None,
                                          allowed_mentions=None, reference=None,
                                          mention_author=None): ...