#!/usr/bin/env python
# encoding: UTF-8

import ast
from setuptools import setup
import os.path

__doc__ = open(
    os.path.join(os.path.dirname(__file__), "README.rst"),
    "r"
).read()

try:
    # For setup.py install
    from proclets import __version__ as version
except ImportError:
    # For pip installations
    version = str(ast.literal_eval(
        open(os.path.join(
            os.path.dirname(__file__),
            "proclets",
            "__init__.py"),
            "r"
        ).read().split("=")[-1].strip()
    ))

setup(
    name="proclets",
    version=version,
    description="A Lightweight Interacting Workflow library in Python.",
    author="D E Haynes",
    author_email="tundish@gigeconomy.org.uk",
    url="https://github.com/tundish/proclets",
    long_description=__doc__,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU General Public License v3"
        " or later (GPLv3+)"
    ],
    packages=["proclets", "proclets.test"],
    package_data={},
    install_requires=[],
    extras_require={
        "dev": [
            "flake8>=3.9.0",
            "wheel>=0.36.2",
        ],
    },
    entry_points={},
    zip_safe=True,
)
