from typing import Callable, Any, Optional, Union

from discord import Guild, Member
from discord.message import Message
from discord.abc import User


class Command: ...

class Group: ...


class Bot:
    def __init__(self, command_prefix: str, help_command:str = None, description:str=None, **options): ...

    def event(self, coro): ...

    def command(self, *args, **kwargs) -> Callable[..., Command]: ...

    def group(self, *args, **kwargs) -> Callable[..., Group]: 
        def command(self, *args, **kwargs) -> Callable[..., Command]: ...

class Context: 
    message: Message
    subcommand_passed: Optional[str]

    @property
    def command(self) -> Command: ...

    @property
    def guild(self) -> Guild: ...

    @property
    def author(self) -> Union[User, Member]: ...

    async def send(self, content: Any=None, *, tts: bool=False, embed: Any=None, file: Any=None,
                                          files: Any=None, delete_after: Any=None, nonce: Any=None,
                                          allowed_mentions: Any=None, reference: Any=None,
                                          mention_author: Any=None): ...