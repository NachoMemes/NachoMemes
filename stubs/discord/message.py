from typing import List, Union

from discord import Member
from discord.abc import User

class Message: 
    id: int
    
    @property
    def mentions(self) -> List[User]: ...

    @property
    def author(self) -> Union[User, Member]: ...

    @property
    def content(self) -> str: ...