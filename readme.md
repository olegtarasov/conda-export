# conda-export
An alternative to `conda env export` that helps create portable environment 
specifications with minimal number of packages.

Resulting specification is similar to `conda env export --from-history`, but also 
includes packages that were installed using `pip`.

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

## Rationale
There are several options when you want to share conda environment specification:

1. You can use `conda env export -n [name] -f [file]`. This command will give you a 
   full yaml specification with build versions, which is ideal for reproducibility on 
   **the same machine**. Unfortunately, this specification will most likely fail on a 
   different machine or different OS.
2. `conda env export --no-builds` is a little better, but it still contains specific 
   versions for all the packages, and such specification can still fail on a different 
   OS. You can postprocess the spec with a simple regex, removing version info, but 
   the spec will still contain all the packages that are installed in the environment. 
   Such a spec proves hard to maintain and reason about, and can still fail on 
   different OS.
3. Finally, you can use `conda env export --from-history`, which will give you only 
   those packages that you explicitly installed with `conda`. Versions will be 
   included only if you explicitly requested them upon package installation. This 
   would be the ideal solution, but unfortunately this command will not include 
   packages that were installed with `pip`.
   
To circumvent all the above restrictions, I've created `conda-export` which generates 
a spec with `--from-history` and adds `pip` packages, trying to minimize the number of 
packages by including only leaves that no other packages depend on.

## OMG, it uses private pip API!

Yes, it does. Shame on me.