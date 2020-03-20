from typing import Iterable

class Guild:
    id: int
    name: str

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

class Permissions:
    @property
    def administrator(self) -> bool: ...