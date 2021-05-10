from typing import Callable, Iterable, List, Optional, Tuple, TypeVar, Sequence, Generator

from nachomemes.util import partition_on_value


def _find_unescaped(text: str, start: int, chars: str) -> int:
    for pos in range(start, len(text)):
        if text[pos] == "\\":
            # skip the backslash and the next char
            pos += 1
            continue
        if text[pos] in chars:
            return pos
    return 0

def _match(text, pos, chars) -> bool:
    if pos >= len(text):
        return False
    return text[pos] in chars

def _state_start(text: str, start : int, pos: int, tokens: list) -> Optional[Callable]:
    if pos == len(text):
        return None
    if _match(text, pos, "\'\""):
        end = _find_unescaped(text, pos+1, text[pos])
        if end:
            tokens.append(text[pos+1:end])
            return lambda: _state_start(text, end+1, end+1, tokens)
    if _match(text, pos, "\n"):
        if _match(text, pos+1, "\n"):
            tokens.append(text[pos:pos+2])
            return lambda: _state_start(text, pos+2, pos+2, tokens)
        else:
            tokens.append(text[pos:pos+1])
            return lambda: _state_start(text, pos+1, pos+1, tokens)

    if _match(text, pos, " "):
        return lambda: _state_whitespace(text,  pos, pos+1, tokens)
    else:
        return lambda: _state_other(text,  pos, pos+1, tokens)


def _state_whitespace(text: str, start : int, pos: int, tokens: list) -> Optional[Callable]:
    if pos == len(text):
        tokens.append(text[start:pos])
        return None
    if _match(text, pos, "\'\""):
        end = _find_unescaped(text, pos+1, text[pos])
        if end:
            tokens.append(text[start:pos])
            tokens.append(text[pos+1:end])
            return lambda: _state_start(text, end+1, end+1, tokens)
    if _match(text, pos, "\n"):
        if _match(text, pos+1, "\n"):
            tokens.append(text[start:pos])
            tokens.append(text[pos:pos+2])
            return lambda: _state_start(text, pos+2, pos+2, tokens)
        else:
            tokens.append(text[start:pos])
            tokens.append(text[pos:pos+1])
            return lambda: _state_start(text, pos+1, pos+1, tokens)
    if _match(text, pos, "/"):
        if _match(text, pos+1, " "):
            tokens.append(text[start:pos-1])
            tokens.append(text[pos-1:pos+2])
            return lambda: _state_start(text, pos+2, pos+2, tokens)
        elif _match(text, pos+1, "/") and _match(text, pos+2, " "):
            tokens.append(text[start:pos-1])
            tokens.append(text[pos-1:pos+3])
            return lambda: _state_start(text, pos+3, pos+3, tokens)
    if _match(text, pos, " "):
        return lambda: _state_whitespace(text, start, pos+1, tokens)
    else:
        tokens.append(text[start:pos])
        return lambda: _state_other(text, pos, pos+1, tokens)

def _state_other(text: str, start : int, pos: int, tokens: list) -> Optional[Callable]:
    if pos == len(text):
        tokens.append(text[start:pos])
        return None
    if _match(text, pos, "\'\""):
        end = _find_unescaped(text, pos+1, text[pos])
        if end:
            tokens.append(text[start:pos])
            tokens.append(text[pos+1:end])
            return lambda: _state_start(text, end+1, end+1, tokens)
    if _match(text, pos, "\n"):
        if _match(text, pos+1, "\n"):
            tokens.append(text[start:pos])
            tokens.append(text[pos:pos+2])
            return lambda: _state_start(text, pos+2, pos+2, tokens)
        else:
            tokens.append(text[start:pos])
            tokens.append(text[pos:pos+1])
            return lambda: _state_start(text, pos+1, pos+1, tokens)
    if _match(text, pos, " "):
        tokens.append(text[start:pos])
        return lambda: _state_whitespace(text,  pos, pos+1, tokens)
    else:
        return lambda: _state_other(text,  start, pos+1, tokens)
    


def _tokenize(text: str) -> list[str]:
    tokens: list[str]  = []

    trampoline: Optional[Callable] = lambda: _state_start(text, 0, 0, tokens)
    while trampoline:
        trampoline = trampoline()

    return list(filter(None, tokens))



def _linebreak(tokens: list[str]) -> str:
    if '\n\n' in tokens:
        return ''.join(tokens)
    if '\n' in tokens:
        return ''.join(tokens)
    if ' / ' in tokens:
        return "\n".join(" ".join(l) for l in partition_on_value(" / ", tokens))
    return ''.join(tokens)

def reflow_text(message: str, count: int) -> List[str]:
    tokens = _tokenize(message)
    if count == 1:
        return [_linebreak(tokens)]
    if tokens.count("\n\n") == count-1:
        return [_linebreak(list(t)) for t in partition_on_value("\n\n", tokens)]
    if tokens.count("\n") == count-1:
        return [_linebreak(list(t)) for t in partition_on_value("\n", tokens)]
    if tokens.count(" // ") == count-1:
        return [_linebreak(list(t)) for t in partition_on_value(" // ", tokens)]
    if tokens.count(" / ") == count-1:
        return [_linebreak(list(t)) for t in partition_on_value(" / ", tokens)]
    if len(tokens) == count + count-1:
        if not any((s.strip()) for s in tokens[1::2]):
            return tokens[::2]
    raise ValueError(f"could not fit provided text into {count} boxes")
