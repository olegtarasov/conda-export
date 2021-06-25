import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Set

from conda.base.context import locate_prefix_by_name
from conda.cli.main import init_loggers
from conda.common.serialize import yaml_safe_dump
from conda_env.env import from_environment

__version__ = "0.0.3"


def get_pip_leaves(prefix: str) -> Set[str]:
    pip_path = (
        Path(prefix).joinpath("Scripts").joinpath("pip.exe")
        if sys.platform == "win32"
        else Path(prefix).joinpath("bin").joinpath("pip")
    )
    if not pip_path.exists():
        raise Exception(f"Failed to find pip binary at {pip_path}")

    args = [str(pip_path), "list", "--not-required", "--format=json"]

    output = subprocess.check_output(args)

    try:
        packages = json.loads(output)
    except:
        raise Exception(f"Failed to parse packages list: {output}")

    return {package["name"] for package in packages}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Platform agnostic conda environment export"
    )
    parser.add_argument(
        "-n", "--name", default=None, required=True, help="Conda environment name"
    )
    parser.add_argument("-f", "--file", default=None, help="Output file name")
    parser.add_argument(
        "-V", "--version", action="version", version="%(prog)s " + __version__
    )

    args = parser.parse_args()

    init_loggers()

    prefix = locate_prefix_by_name(args.name)

    # Get packages with `pip list --not-required`.
    pip_leaves = get_pip_leaves(prefix)

    # All the packages in the environment: conda and pip (with versions)
    env_all = from_environment(args.name, prefix, no_builds=True)

    # Conda packages that were explicitly installed, but not pip packages (--from-history mode).
    env_hist = from_environment(args.name, prefix, no_builds=True, from_history=True)

    # Strip version info from full conda packages.
    conda_packages = {
        pkg.split("=")[0] for pkg in env_all.dependencies.get("conda", [])
    }

    # Leave just those pip packages that were not installed through conda.
    pip_leaves = pip_leaves.difference(conda_packages)

    # Additionally filter pip packages with conda's version of things.
    if "pip" in env_all.dependencies:
        conda_pip = {pkg.split("==")[0] for pkg in env_all.dependencies["pip"]}
        pip_leaves = pip_leaves.intersection(conda_pip)

    final_dict = env_hist.to_dict()
    final_dict["channels"] = env_all.channels
    del final_dict["prefix"]

    if len(pip_leaves) > 0:
        final_dict["dependencies"].append({"pip": list(sorted(pip_leaves))})

    result = yaml_safe_dump(final_dict)

    if args.file is None:
        print(result)
    else:
        with open(args.file, "w") as file:
            file.write(result)


if __name__ == "__main__":
    main()
