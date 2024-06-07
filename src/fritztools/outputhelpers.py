"""
adhoc Tabellen, dirty
"""
import os
import click

def mask(something):
    return click.style(text=something, fg="black", bg="blue")


def tabello(
    data: list[list],
    headers: list = None,
    aligns: list = None,
    delimiter: str = " | ",
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
            max_lengths[idx] = (
                len(str(item))
                if len(str(item)) > max_lengths[idx]
                else max_lengths[idx]
            )

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

    for row in data:
        out += build_row(row) + os.linesep

    return out


def upline(n=1):
    return "\033[F" * n