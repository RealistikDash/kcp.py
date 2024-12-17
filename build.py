from __future__ import annotations

from os import getenv
from pathlib import Path
from shutil import copyfile as copy_file

from entrypoint import entrypoint
from setuptools import Distribution, Extension
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


# Decide whether to build C extensions
EXTENSIONS = getenv("KCP_PY_EXTENSIONS")
with_extensions = True if EXTENSIONS is None else parse_bool(EXTENSIONS)

extensions = []

if with_extensions:
    from Cython.Build import cythonize  # type: ignore

    # Define your extension module(s). For Cython 3, you can use compiler_directives.
    ext = Extension(
        "kcp.extension",
        sources=["kcp/extension.pyx", "kcp/ikcp.c"],
        extra_compile_args=["-O3"],
    )

    extensions += cythonize(
        [ext],
        compiler_directives={
            "language_level": 3,
            "binding": True,
            "embedsignature": True,
            "cdivision": True,
            "wraparound": False,
            "boundscheck": False,
        },
    )


PACKAGE = "kcp"
DIRECTORY = "kcp"


def build() -> None:
    """Build the extension modules and copy them back into the package."""
    distribution = Distribution(
        {
            "name": PACKAGE,
            "ext_modules": extensions,
        }
    )
    command = build_ext(distribution)
    command.ensure_finalized()  # type: ignore
    command.run()

    # Copy built extensions back to the project (so they're importable directly)
    for output in map(Path, command.get_outputs()):  # type: ignore
        if not output.exists():
            continue
        relative_extension = output.relative_to(command.build_lib)
        copy_file(output, relative_extension)


@entrypoint(__name__)
def main() -> None:
    build()