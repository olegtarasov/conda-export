import argparse
import sys
from pathlib import Path
from typing import List

from conda.base.context import locate_prefix_by_name
from conda.cli.main import init_loggers
from conda.common.serialize import yaml_safe_dump
from conda_env.env import from_environment
from pip._vendor.pkg_resources import DistInfoDistribution
from pip._internal.utils.misc import get_installed_distributions

__version__ = "0.0.1"


def find_site_packages(prefix: str) -> str:
    """A naive hacky way to find site_packages directory for use with `pip`."""

    lib_dir = Path(prefix).joinpath("lib")
    if not lib_dir.exists():
        raise Exception(f"{lib_dir} does not exist!")

    site_packages = [
        str(path)
        for path in map(
            lambda x: x.joinpath("site-packages"),
            lib_dir.glob("python*.*"),
        )
        if path.exists()
    ]
    if len(site_packages) != 1:
        raise Exception(f"Could not reliably find site-packages!")

    return site_packages[0]


def get_not_required(
    packages: List[DistInfoDistribution],
) -> List[DistInfoDistribution]:
    """Filter pip packages so that only leaf packages are left."""

    dep_keys = set()
    for dist in packages:
        dep_keys.update(requirement.key for requirement in dist.requires())

    return list({pkg for pkg in packages if pkg.key not in dep_keys})


def main() -> None:
    parser = argparse.ArgumentParser()
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
    site_packages = find_site_packages(prefix)

    # All the packages in the environment: conda and pip (with versions)
    env_all = from_environment(args.name, prefix, no_builds=True)

    # Conda packages that were explicitly installed (but not pip packages).
    env_hist = from_environment(args.name, prefix, no_builds=True, from_history=True)

    # Get packages that no one depends on (leaves) from pip.
    pip_leaves = {
        dist.key
        for dist in get_not_required(get_installed_distributions(paths=[site_packages]))
    }

    # Strip version info from full conda packages.
    conda_packages = {
        pkg.split("=")[0] for pkg in env_all.dependencies.get("conda", [])
    }

    # Leave just those pip packages that were not installed through conda.
    pip_leaves = pip_leaves.difference(conda_packages)

    # Additionaly filter pip packages with conda's version of things.
    if "pip" in env_all.dependencies:
        conda_pip = {pkg.split("==")[0] for pkg in env_all.dependencies["pip"]}
        pip_leaves = pip_leaves.intersection(conda_pip)

    final_dict = env_hist.to_dict()
    final_dict["channels"] = env_all.channels
    del final_dict["prefix"]

    if len(pip_leaves) > 0:
        final_dict["dependencies"].append({"pip": list(pip_leaves)})

    result = yaml_safe_dump(final_dict)

    if args.file is None:
        print(result)
    else:
        with open(args.file, "w") as file:
            file.write(result)


if __name__ == "__main__":
    main()
