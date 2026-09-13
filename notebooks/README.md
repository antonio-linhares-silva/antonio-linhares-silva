# Public-data GeoAI notebooks

[Profile](../README.md) · [Engineering notes](../docs/README.md) · [Data sources](../docs/DATA_SOURCES.md)

Ten independently executable notebooks connect the technical articles to real public data. Saved tables and static figures are visible directly on GitHub. Each notebook explains its assumptions, runs actual processing, checks its outputs, and states what the results support.

| Notebook | Data and visible result | Compute |
| --- | --- | --- |
| [01 · Reusable framework](01-reusable-geoai-framework.ipynb) | EuroSAT; short pretrained ResNet18 fine-tune, spatial split, curves, confusion matrix and errors | CPU or CUDA |
| [02 · Memory-bounded rasters](02-memory-bounded-rasters.ipynb) | Sentinel-2; windowed NDVI COG checked against a whole-array reference | CPU |
| [03 · Resumable workflows](03-resumable-workflows.ipynb) | Sentinel-2 windows; controlled failure, verified restart and corrupt-output recovery | CPU |
| [04 · Geospatial contracts](04-geospatial-data-contracts.ipynb) | Sentinel-2 and WorldCover; rejected grid shift, continuous and categorical resampling | CPU |
| [05 · Multispectral experiments](05-multispectral-experiments.ipynb) | EuroSAT; RGB versus 13-band forests, spatial evaluation and permutation importance | CPU |
| [06 · Model artifacts](06-model-artifacts-mlflow.ipynb) | EuroSAT; local MLflow model, explicit schema and fresh-process reload | CPU |
| [07 · Shipping software](07-shipping-geoai.ipynb) | Build a wheel, install locked dependencies in a separate environment and run the raster CLI | CPU; uv |
| [08 · Tree boxes and heights](08-tree-crowns-height-distance.ipynb) | Dutch orthophoto and AHN4; pretrained DeepForest, surface-height summaries and GeoPackage | CPU or CUDA |
| [09 · Vegetation change](09-vegetation-change.ipynb) | Two Sentinel-2 dates; common mask, ΔNDVI and threshold sensitivity | CPU |
| [10 · LiDAR evidence](10-lidar-evidence.ipynb) | AHN4 conductor observations; bounded catenary fit, withheld blocks and separate evidence layers | CPU |

## Install and run

Clone the repository and install [uv](https://docs.astral.sh/uv/getting-started/installation/). Run from the repository root. Python 3.12 is downloaded automatically if necessary.

For all notebooks on CPU:

~~~text
uv sync --frozen --extra cpu
uv run --frozen --extra cpu jupyter lab notebooks
~~~

For a compatible NVIDIA GPU and driver supporting the CUDA 13.0 wheels:

~~~text
uv sync --frozen --extra cuda
uv run --frozen --extra cuda jupyter lab notebooks
~~~

Choose one extra; they are mutually exclusive. Notebooks 01 and 08 select CUDA when available. Set `GEOAI_DEVICE=cpu` to force CPU, or `GEOAI_DEVICE=cuda` to require a GPU and fail clearly if it is unavailable. CPU-only notebooks can also use the smaller base installation, `uv sync --frozen`.

Each notebook supports **Restart Kernel and Run All**, including when launched from `notebooks/`. No preceding notebook is required. For automated execution with a separate fresh kernel per notebook:

~~~text
uv run --frozen --extra cpu python scripts/execute_notebooks.py
~~~

Use `--select 02 03 04` to execute selected notebooks. GPU execution uses the same command with `--extra cuda`. The runner saves outputs into the notebook files; `--output-dir outputs/cpu-notebooks` keeps an alternative execution outside Git. Re-running the notebook-source generator clears outputs and is a maintainer operation, not part of normal setup.

## Downloads, storage, and outputs

Three versioned [release packs](https://github.com/antonio-linhares-silva/antonio-linhares-silva/releases/tag/public-data-v1) total approximately **236 MB**: EuroSAT about 200 MB, AHN/orthophoto about 31 MB, and Sentinel/WorldCover about 4 MB. Only the required pack is fetched. [The manifest](../data/manifest.json) pins archive and member checksums; cached members are verified on reuse. Cache and prepared data remain under ignored `data/` subdirectories. No accounts or access tokens are needed.

Model weights and the Python environment are separate downloads. CUDA PyTorch is considerably larger than the data packs. Allow several GB of free disk space and preferably 8 GB or more of RAM. The published CPU/CUDA execution evidence is described in [validation](../docs/validation.md); runtime depends on hardware, cache and network. Notebook 07 creates a temporary environment and copies cached packages to avoid Windows/OneDrive hardlink restrictions.

Outputs include COGs, local MLflow artifacts, a wheel, experiment metadata and GeoPackages under `outputs/notebooks/`. The notebooks carry static results for reading; large data, model weights and local tracking databases are not committed. The original four [synthetic tutorials](../docs/README.md#runnable-tutorials) remain useful for small edge-case demonstrations.

## Reading the results

EuroSAT partitions follow geographic splits and a 2 km footprint exclusion. Bootstrap intervals resample spatial groups. Pretrained models retain their original authorship. Tree boxes do not establish crown boundaries or validated tree heights; spectral change is an indicator; fitted conductor geometry remains distinct from measured XYZ. These examples use public data and original implementation, independently of the private projects described in the case studies.
