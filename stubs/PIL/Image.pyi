from typing import Tuple

BICUBIC: int
NEAREST: int

def new(mode: str, size: Tuple[int,int], color: Tuple[int,int,int,int]) -> Image: ...
def open(fp, mode="r") -> Image: ...

class Image: 

    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...

    @property
    def size(self) -> Tuple[int,int]: ...

    def paste(self, im, box=None, mask=None) -> None: ...

    def rotate(
        self,
        angle,
        resample=NEAREST,
        expand=0,
        center=None,
        translate=None,
        fillcolor=None,
    ) -> Image: ...

    def save(self, fp, format=None, **params) -> None: ...

    def thumbnail(self, size, resample) -> None: ...