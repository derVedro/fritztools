"""
Helpers for text output, tables, etc.
"""

import os
import click
from typing import List


def mask(something):
    return click.style(text=something, fg="white", bg="blue")


def heighlight(something):
    return click.style(text=something, fg="green")


def active_mark(flag=True):
    return "[x]" if flag else "[ ]"


def tabello(
    data: List[list],
    headers: List = None,
    aligns: List = None,
    delimiter: str = "  ",
    border: str = " ",
    line_after_header=False,
) -> str:

    out = ""

    if headers is None:
        headers = []
    else:
        assert all(len(row) == len(headers) for row in data)

    if aligns is None:
        aligns = ["<"] * len(data[0])
    else:
        if 1 == len(aligns) != len(data):  # das kann nicht gut gehen
            aligns = [aligns] * len(data[0])

    # determine max size for cells
    max_lengths = [0] * len(data[0])
    for row in [headers] + data:
        for idx, item in enumerate(row):
            max_lengths[idx] = max(max_lengths[idx], len(str(item)))

    def build_row(row):
        return (
            border
            + delimiter.join(
                f"{str(item):{aligns[idx]}{max_lengths[idx]}.{max_lengths[idx]}}"
                for idx, item in enumerate(row)
            )
            + border
        )

    if headers:
        out += mask(build_row(headers)) + os.linesep

    if line_after_header:
        line_lengths = (
            sum(max_lengths) + len(delimiter) * (len(max_lengths) - 1) + len(border) * 2
        )
        out += "-" * line_lengths + os.linesep

    out += os.linesep.join([build_row(row) for row in data])

    return out


def upline(n=1):
    return "\033[F" * n


def charbar(value, max_value, min_value=0):
    if max_value == 0:
        return "X"

    scale = " _▂▃▅▇█"                         # if no unicode " _▄█"
    ratio = value / (max_value - min_value)
    pos = min(int(ratio * len(scale)), len(scale) - 1)
    return scale[pos]
