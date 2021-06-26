# conda-export

An alternative to `conda env export` that helps create portable environment 
specifications with minimum number of packages.

Conda-export creates environment specifications which contain only top-level 
(non-transient) dependencies. It tries to minimize specific version information and 
total number of packages, so that the resulting spec maximizes [upgradability](https://pythonspeed.com/articles/conda-dependency-management/#three-kinds-of-dependency-specification).
At the same time, it respects specific package versions that were used while creating 
the environment. If, at some point, you installed a package with explicit version (e. g. 
`conda install pytorch=1.9.0`), `conda-export` will include this specific version in 
the resulting spec file.

## Installation

It makes sense to install `conda-export` into `base` environment and call it from 
there, since it would be weird to install `conda` into your actual working env.

```shell
conda install conda-export -n base -c conda-forge
```

## Usage

```shell
conda-export -n [env name] -f [optional output file]
```

If `-f` is not specified, dumps the spec to the console.

## How it works

This is the exact algorithm that is used to export environment specifications:

1. `conda-leaves` ← make a dependency graph of all conda packages and select top-level 
   ones. Exclude packages that were installed with `pip`.
2. `versioned_hist` ← execute `conda env export --from-history` to get only those 
   packages that were explicitly installed by user with `conda create` or `conda 
   install`. Filter packages to leave only those with explicit version specified.
3. `conda_pip` ← execute `conda env export` and get packages that were installed with 
   `pip` and not `conda`.
4. `pip_leaves` ← execute `pip list --not-required` to get top-level packages from 
   pip's perspective.
5. Compile the final list as follows:
    * conda dependencies: `conda_leaves.union(versioned_hist)`
    * pip dependencies: `conda_pip.intersection(pip_leaves)`
    
## What about exactly reproducible environments?

`conda-export` is not suited for creating [reproducible](https://pythonspeed.com/articles/conda-dependency-management/#three-kinds-of-dependency-specification)
environments. Please use `conda-lock` with environment specs generated from 
`conda-export` in order to create multi-platform lock files that contain exact package 
versions.