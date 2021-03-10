import io
import sys
from itertools import chain, takewhile
from math import cos, pi, sin
from os import PathLike
from typing import IO, Callable, Iterable, List, Optional, Tuple, TypeVar, Sequence, Generator

from PIL import Image as ImageModule, ImageFont, ImageDraw, ImageFont
from PIL.Image import Image
from PIL.ImageFont import FreeTypeFont

from nachomemes.template import Color, Font, Template, TextBox

T = TypeVar('T')

def partition_on(pred: Callable[[T],bool], seq: Iterable[T]) -> Iterable[Iterable[T]]:
    "Split a sequence into multuple sub-sequences using a provided value as the boundary"
    i = iter(seq)
    while True:
        # note that we need to do an explicit StopIteration check because
        # takewhile returns an empty sequence if it encounters StopIteration
        try:
            n = next(i)
        except StopIteration:
            return
        # return the next sub-sequence up to the boundary.
        yield takewhile(lambda v: not pred(v), chain([n], i))


def partition_on_value(value: T, seq: Iterable[T]) -> Iterable[Iterable[T]]:
    pred: Callable[[T],bool] = lambda v: v == value
    return partition_on(pred, seq)


def _reflow_text(text, count) -> List[str]:
    """Using slashes, break up the provided text into the requested number of boxes"""

    if len(text) == count:
        return text

    # if we are expecting a single string, smash everything together replacing
    # slash with newline
    if count == 1:
        return ["\n".join(" ".join(l) for l in partition_on_value("/", text))]

    # if we see a double slash, use that as the text box boundary, and smash
    # the sub-sequences together replacing slash with newline
    if "//" in text:
        result = [
            "\n".join(" ".join(l) for l in partition_on_value("/", b))
            for b in partition_on_value("//", text)
        ]
        assert len(result) == count
        return result

    # if we just see a single slash, use that as the text box boundary
    if "/" in text:
        result = [" ".join(l) for l in partition_on_value("/", text)]
        assert len(result) == count
        return result

    raise ValueError(f"could not fit provided text into {count} boxes")


def _text_width(font: Font, size: int, string: str) -> int:
    """Returns the width of the provided text at the given font size in pixels"""
    return font.load(size).getsize(string)[0]


def _render_text(img: Image, font: FreeTypeFont, color: Color, x, y, string) -> None:
    """Render plain colored text with a transparent background"""
    ImageDraw.Draw(img).text((x, y), string, color.value, font)


def _render_outlined(
    img: Image, font: FreeTypeFont, color: Color, outline: Color, x, y, string: str
) -> None:
    """Render text with an outline by repeatedly rendering text in the outline
     color offset by 1/15 of the font size at 30 degree intervals"""
    offset = font.size / 15
    draw = ImageDraw.Draw(img)
    for angle in range(0, 360, 30):
        r = angle / 360 * 2 * pi
        pos = (x + (cos(r) * offset), y + (sin(r) * offset))
        draw.text(pos, string, outline.value, font)
    _render_text(img, font, color, x, y, string)


def _render_rotated(img: Image, font: FreeTypeFont, color: Color, x, y, 
        angle, string: str) -> None:
    """render text rotated by an angle by creating a seperate image with the 
    text, rotating it, and pasting it onto the target image"""

    # create a new image with a transparent alpha channel
    txt = ImageModule.new("RGBA", (800, 400), (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt)
    draw.text((0, 0), string, (*color.value, 255), font)
    w = txt.rotate(angle, resample=ImageModule.BICUBIC, expand=True)
    img.paste(w, (x, y), w)


def _box_size(width: int, height: int, tb: TextBox) -> Tuple[int, int]:
    """Calcutate the size of the textbox based on percent of the target image"""
    return (int((tb.right - tb.left) * width), int((tb.bottom - tb.top) * height))


def _font_size(width, height, tb: TextBox, lines: List[str]) -> int:
    """Calcuates the largest possible font size that allows the provided text 
    to fit in the box"""

    # starting with the box size divded by the number of lines
    # OR the defined max size (whichever is smaller)
    start = min(height // len(lines), tb.max_font_size or sys.maxsize)

    # find the largest font size that allows all the text to fit (give up at
    # 5 pixels)
    return next(
        size
        for size in range(start, 5, -1)
        if all(_text_width(tb.font, size, s) < width for s in lines)
    )


def _offset(width: int, height: int, tb: TextBox, x: int, y: int) -> Tuple[int, int]:
    """Calculate offset position relative to a textbox on an image"""
    return int(tb.left * width) + x, int(tb.top * height) + y


def _render_box(img: Image, tb: TextBox, lines: List[str], base_size: int) -> None:
    "Would you kindly render some text on an image"

    # get the size of the bounding box in pixels
    bw, bh = _box_size(*img.size, tb)

    # if this is independently sized, calculate the size
    size = base_size if not tb.ind_size else _font_size(bw, bh, tb, lines)
    font = tb.font.load(size)

    # find the offset of the first line of text
    top = (bh - size * len(lines)) // 2
    for num, line in enumerate(lines):

        width = font.getsize(line)[0]

        # find the start x coordinate of the text within the bounding box
        # based on the text alignment
        tx = tb.justify(bw, width)
        ty = top + size * num

        # translate the text position relative to the position of the text box
        # in the image
        x, y = _offset(*img.size, tb, tx, ty)
        # render at that position
        if tb.rotation:
            _render_rotated(img, font, tb.color, x, y, tb.rotation, line)
        elif tb.outline:
            _render_outlined(img, font, tb.color, tb.outline, x, y, line)
        else:
            _render_text(img, font, tb.color, x, y, line)


def _debug_box(img: Image, tb: TextBox) -> None:
    """draw an outline around the TextBox for debugging"""

    coords = ((img.width * tb.left, img.height * tb.top),
              (img.width * tb.right, img.height * tb.bottom))
    ImageDraw.Draw(img).rectangle(coords, outline=(0, 0, 0))


def render_template(
    template: Template, message: Iterable[str], output: IO, debug: bool = False
) -> None:
    """This is the thing that does the thing"""

    # combine the strings into the required number of textboxes
    strings = _reflow_text(message, len(template.textboxes))

    # zip the strings up with the corrosponding textbox
    texts: List[Tuple[TextBox, List[str]]] = list(
        zip(template.textboxes, [s.split("\n") for s in strings])
    )

    with io.BytesIO() as buffer:

        img = template.read_source_image(buffer)

        # Find the smallest required font size for all non-independent textboxes
        shared_size = min(
            _font_size(*_box_size(*img.size, tb), tb, s)
            for tb, s in texts
            if not tb.ind_size
        )

        for tb, s in texts:
            _render_box(img, tb, s, shared_size)
            if debug:
                _debug_box(img, tb)

        img.save(output, format="PNG")
