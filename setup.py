from __future__ import annotations

from Cython.Build import cythonize
from setuptools import Extension
from setuptools import setup

setup(
    ext_modules=cythonize(
        [
            Extension(
                "kcp.extension",
                sources=["kcp/extension.pyx", "kcp/ikcp.c"],
            ),
        ],
        compiler_directives={
            "language_level": 3,
            "binding": True,
            "embedsignature": True,
            "cdivision": True,
            "wraparound": False,
            "boundscheck": False,
        },
    ),
)
