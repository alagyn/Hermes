import re
from typing import List

COMMENT_RE = re.compile(r'[^#\'"]*(("[^"]*")|(\'[^\']*\'))?[^#]*#')


def read_and_clean(filename: str) -> List[str]:
    out = []
    with open(filename, mode='r') as f:
        for line in f:
            line = line.strip()
            m = COMMENT_RE.search(line)
            if m is not None and m.end() > 0:
                line = line[0:m.end() - 1].strip()

            if len(line) > 0:
                out.append(line)

    return out


def combine_lines(grammerLines: List[str]) -> List[str]:
    out = []
    curLine = ""
    needCloseSQuote = False
    needCloseDQuote = False
    needCloseBrace = False
    idx = 0
    while idx <= len(grammerLines):
        if curLine == '':
            if idx == len(grammerLines):
                break
            curLine = grammerLines[idx]
            idx += 1
            # Automatically take directives
            if curLine.startswith('%'):
                out.append(curLine)
                curLine = ''
                continue

        foundEnd = False
        for cidx, char in enumerate(curLine):
            if char == '{' and not needCloseSQuote and not needCloseDQuote:
                needCloseBrace = True
            elif char == '}' and not needCloseSQuote and not needCloseDQuote:
                if needCloseBrace:
                    needCloseBrace = False
                else:
                    raise RuntimeError(f"Bad line {idx}: Missing opening brace")
            elif char == '"' and not needCloseSQuote and not needCloseBrace:
                needCloseDQuote = not needCloseDQuote
            elif char == "'" and not needCloseDQuote and not needCloseBrace:
                needCloseSQuote = not needCloseSQuote
            elif char == ';':
                if not needCloseBrace and not needCloseDQuote and not needCloseSQuote:
                    newline = curLine[:cidx + 1]
                    out.append(newline)
                    curLine = curLine[cidx + 1:]
                    foundEnd = True
                    break

        if not foundEnd:
            curLine += f' {grammerLines[idx]}'
            idx += 1

    if len(curLine) > 0:
        raise RuntimeError("Grammer does not end with a semicolon")

    return out