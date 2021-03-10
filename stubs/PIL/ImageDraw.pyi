from .Image import Image

def Draw(im: Image, mode=None) -> ImageDraw: ...


class ImageDraw(object):
    def rectangle(self, xy, fill=None, outline=None, width=0) -> None: ...
    def text(
        self,
        xy,
        text,
        fill=None,
        font=None,
        anchor=None,
        spacing=4,
        align="left",
        direction=None,
        features=None,
        language=None,
        stroke_width=0,
        stroke_fill=None,
        *args,
        **kwargs
    ) -> None: ...