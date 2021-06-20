#!/usr/bin/env python

from setuptools import setup
import shutil


# we need to rename the script because it's not a valid module name
shutil.copyfile("conda-export.py", "conda_export.py")

setup(
    name="conda-export",
    version="0.0.1",
    description="Platform agnostic conda environment export",
    author="Oleg Tarasov",
    url="https://github.com/olegtarasov/conda-export",
    py_modules=["conda_export"],
    entry_points={"console_scripts": ["conda-export=conda_export:main"]},
)
