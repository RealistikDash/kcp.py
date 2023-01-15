from __future__ import annotations

from os import getenv
from pathlib import Path
from shutil import copyfile as copy_file

from entrypoint import entrypoint
from setuptools import Distribution
from setuptools import Extension
from setuptools.command.build_ext import build_ext  # type: ignore

_TRUE_SET = frozenset(("1", "true", "t", "yes", "y"))
_FALSE_SET = frozenset(("0", "false", "f", "no", "n"))


def parse_bool(string: str) -> bool:
    string = string.casefold()

    if string in _TRUE_SET:
        return True

    if string in _FALSE_SET:
        return False

    raise ValueError(f"Can't parse {string!r} into `bool`")


# C Extensions
EXTENSIONS = getenv("KCP_PY_EXTENSIONS")

if EXTENSIONS is None:
    with_extensions = True

else:
    with_extensions = parse_bool(EXTENSIONS)


LANGUAGE_LEVEL = "3"


extensions = []

if with_extensions:
    from Cython.Build import cythonize  # type: ignore

    extensions += cythonize(
        [Extension("kcp.extension", ["kcp/extension.pyx", "kcp/ikcp.c"])],
        language_level=LANGUAGE_LEVEL,
    )


PACKAGE = "kcp.py"
DIRECTORY = "kcp"


def build() -> None:
    distribution = Distribution(
        {
            "name": PACKAGE,
            "ext_modules": extensions,
        },
    )

    command = build_ext(distribution)
    command.ensure_finalized()  # type: ignore
    command.run()

    # Copy built extensions back to the project
    for output in map(Path, command.get_outputs()):  # type: ignore
        relative_extension = output.relative_to(command.build_lib)

        if not output.exists():
            continue

        copy_file(output, relative_extension)


@entrypoint(__name__)
def main() -> None:
    build()
