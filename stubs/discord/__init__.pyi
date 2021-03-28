from io import BufferedIOBase
from typing import Iterable, Optional, Union

from .channel import *
from .client import *

class Guild:
    id: int
    name: str


    def get_role(self, role_id: int) -> Optional[Role]: ...



class Permissions:
    @property
    def administrator(self) -> bool: ...

class Member:
    id: int
    discriminator: int
    name: str
    nick: str

    @property
    def guild_permissions(self) -> Permissions: ...

    @property
    def roles(self) -> Iterable[Role]: ...

class Role:
    id: int
    name: str


class File:
    def __init__(self, fp: Union[str, BufferedIOBase],
        filename: Optional[str], spoiler: bool=False): ...


