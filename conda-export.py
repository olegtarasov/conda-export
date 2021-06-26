import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Set

import conda.exports
from conda.base.context import locate_prefix_by_name
from conda.cli.main import init_loggers
from conda.common.serialize import yaml_safe_dump
from conda.models.enums import PackageType
from conda_env.env import from_environment

import networkx

__version__ = "0.0.4"


def get_conda_leaves(prefix: str) -> Set[str]:
    cache = dict(
        filter(
            lambda pair: pair[1].package_type
            not in [
                PackageType.VIRTUAL_PYTHON_WHEEL,
                PackageType.VIRTUAL_PYTHON_EGG_MANAGEABLE,
                PackageType.VIRTUAL_PYTHON_EGG_UNMANAGEABLE,
            ],
            conda.exports.linked_data(prefix=prefix).items(),
        )
    )
    graph = networkx.DiGraph()
    for k in cache.keys():
        n = cache[k]["name"]
        v = cache[k]["version"]
        graph.add_node(n, version=v)
        for j in cache[k]["depends"]:
            n2 = j.split(" ")[0]
            v2 = j.split(" ")[1:]
            graph.add_edge(n, n2, version=v2)
    return set(
        map(lambda i: i[0].lower(), (filter(lambda i: i[1] == 0, graph.in_degree)))
    )


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

    return {package["name"].lower() for package in packages}


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

    # All the packages in the environment: conda and pip (with versions)
    env_all = from_environment(args.name, prefix, no_builds=True)

    # Conda packages that were explicitly installed, but not pip packages (--from-history mode).
    env_hist = from_environment(args.name, prefix, no_builds=True, from_history=True)

    # Conda packages in the environment that no other packages depend on
    conda_leaves = get_conda_leaves(prefix)

    # Get packages with `pip list --not-required`.
    pip_leaves = get_pip_leaves(prefix)

    # Conda packages from history with explicit version specified, but not full package spec
    # from explicit environment file.
    versioned_hist = set(
        map(
            lambda pkg: pkg.lower(),
            filter(
                lambda pkg: "=" in pkg and "md5=" not in pkg,
                env_hist.dependencies.get("conda", []),
            ),
        )
    )

    # Exclude conda packages with explicitly specified versions from conda leaves
    conda_leaves = conda_leaves.difference(
        {pkg.split("=")[0] for pkg in versioned_hist}
    )

    # Intersect conda's list of pip packages with packages that pip itself considers leaves.
    pip_final = []
    if "pip" in env_all.dependencies:
        conda_pip = {pkg.split("=")[0].lower() for pkg in env_all.dependencies["pip"]}
        pip_final = list(sorted(conda_pip.intersection(pip_leaves)))

    final_dict = {
        "name": env_all.name,
        "channels": env_all.channels,
        "dependencies": list(sorted(conda_leaves.union(versioned_hist))),
    }

    if len(pip_final) > 0:
        if "pip" in final_dict["dependencies"]:
            final_dict["dependencies"].remove("pip")
        final_dict["dependencies"].append({"pip": pip_final})

    result = yaml_safe_dump(final_dict)

    if args.file is None:
        print(result)
    else:
        with open(args.file, "w") as file:
            file.write(result)


if __name__ == "__main__":
    main()
