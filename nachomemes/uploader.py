from abc import ABC, abstractmethod
from typing import BinaryIO

class Uploader(ABC):

    @abstractmethod
    async def upload(self, buffer: BinaryIO, key: str=None) -> str: 
        pass

    def expire(self, url: str) -> None:
        pass
