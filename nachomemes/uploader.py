from abc import ABC, abstractmethod
from io import BufferedIOBase

class Uploader(ABC):

    @abstractmethod
    async def upload(self, buffer: BufferedIOBase, key: str=None) -> str: 
        pass

    def expire(self, url: str) -> None:
        pass
