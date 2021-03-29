from io import BufferedIOBase
from typing import Iterable, Optional, Union

from .channel import *
from .client import *
from .embeds import *
from .member import *
from .message import *
from .role import *

class Guild:
    id: int
    name: str


    def get_role(self, role_id: int) -> Optional[Role]: ...



class Permissions:
    @property
    def administrator(self) -> bool: ...




class File:
    def __init__(self, fp: Union[str, BufferedIOBase],
        filename: Optional[str], spoiler: bool=False): ...


