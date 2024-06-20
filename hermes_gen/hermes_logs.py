import sys

_Y = "\033[1;33m"
_R = "\033[1;31m"
_OFF = "\033[0m"


def enableColors(enable: bool):
    global _Y, _R, _OFF
    if not enable:
        _Y = ""
        _R = ""
        _OFF = ""


def info(*msg: str):
    print(f" ".join(msg), file=sys.stderr)


def warn(*msg: str):
    print(f'{_Y}Warn: {" ".join(msg)}{_OFF}', file=sys.stderr)


def err(*msg: str):
    print(f'{_R}Error: {" ".join(msg)}{_OFF}', file=sys.stderr)
