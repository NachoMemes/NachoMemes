from typing import Tuple, Union, IO, Optional

def truetype(font: Union[str,IO], size: int=10, index: int=0, encoding: str="", layout_engine: Optional[int]=None) -> FreeTypeFont: ...

class FreeTypeFont:
    size: int

    def getsize(self, text: str,  direction: Optional[str]=None, features: Optional[str]=None, language: Optional[str]=None, stroke_width: int=0) -> Tuple[int,int]: ...
