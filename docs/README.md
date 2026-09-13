# GeoAI Engineering Notes

[Profile](../README.md)

Technical articles, runnable examples, and project case studies by António Silva. The collection focuses on the engineering behind geospatial machine learning: data contracts, bounded processing, experiment design, model packaging, and recoverable execution.

## Reading paths

- **Getting to know my work:** start with [GAIA](projects/gaia.md), [Land Use & Land Cover](projects/land-use-land-cover.md), and [canopy delineation](projects/canopy-delineation.md).
- **Python and MLOps:** read about [reusable frameworks](articles/reusable-geoai-framework.md), [model artifacts](articles/model-artifacts-mlflow.md), [delivery](articles/shipping-geoai.md), and [recovery](articles/resumable-workflows.md).
- **Geospatial methods:** explore [data contracts](articles/geospatial-data-contracts.md), [multispectral experiments](articles/multispectral-experiments.md), [tree metrics](articles/tree-crowns-height-distance.md), [change analysis](articles/vegetation-change.md), and [LiDAR evidence](articles/lidar-evidence.md).

## Technical articles

| Article | Engineering question |
| --- | --- |
| [Reusable GeoAI frameworks](articles/reusable-geoai-framework.md) | Which interfaces should experiments share? |
| [Memory-bounded raster processing](articles/memory-bounded-rasters.md) | How can large-image processing keep a predictable working set? |
| [Resumable workflows](articles/resumable-workflows.md) | What evidence makes a completed task safe to skip? |
| [Geospatial data contracts](articles/geospatial-data-contracts.md) | What must remain true as spatial data moves between components? |
| [Multispectral experiments](articles/multispectral-experiments.md) | How can feature comparisons avoid leaking held-out information? |
| [Model artifacts and MLflow](articles/model-artifacts-mlflow.md) | What belongs in a model package that another process can load? |
| [Shipping GeoAI software](articles/shipping-geoai.md) | What changes when a notebook becomes a reusable tool? |
| [Tree crowns, height, and distance](articles/tree-crowns-height-distance.md) | Which assumptions connect imagery outputs to tree-level metrics? |
| [Vegetation-change analysis](articles/vegetation-change.md) | When does a difference support a change interpretation? |
| [Evidence in LiDAR reconstruction](articles/lidar-evidence.md) | How should fitted geometry remain distinguishable from observations? |

## Runnable tutorials

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), download or clone this repository, and run these commands from its root. They work in PowerShell and POSIX shells. The first command downloads Python 3.12 if needed and installs the dependencies recorded in `uv.lock`.

~~~text
uv sync --frozen
uv run --frozen python -m docs.examples.raster_windows
uv run --frozen python -m docs.examples.train_only
uv run --frozen python -m docs.examples.local_mlflow
uv run --frozen python -m docs.examples.resume_batch
~~~

All data is synthetic. Generated files stay under the ignored `outputs/` directory. The MLflow tutorial uses a local database and local artifact storage; no remote tracking service is required. Installing dependencies requires internet access; running the examples afterward uses local resources.

| Tutorial | Observable result |
| --- | --- |
| [Windowed raster processing](tutorials/windowed-raster-processing.md) | A COG with the expected mask and georeferencing, matching a small whole-array reference |
| [Train-only preprocessing](tutorials/train-only-preprocessing.md) | Held-out perturbations leave fitted training statistics unchanged |
| [Local MLflow model](tutorials/local-mlflow-model.md) | A self-contained model package reloads and reproduces its expected predictions |
| [Resuming a batch](tutorials/resuming-a-batch.md) | A failed batch restarts, skips verified outputs, and invalidates changed inputs |

Run the checks with:

~~~text
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen python scripts/check_docs.py
~~~

See [validation scope and limitations](validation.md) for what these checks establish.

## Project case studies

These pages separate project scope from my own contributions. Source repositories are private. Repository names already present in my profile are retained where relevant; links lead to public summaries.

| Project | Focus |
| --- | --- |
| [GAIA](projects/gaia.md) | Modular experimentation and integration |
| [Land Use & Land Cover](projects/land-use-land-cover.md) | Conventional ML, raster inference, and model management |
| [Canopy delineation](projects/canopy-delineation.md) | Large-image prediction merging and recovery |
| [Canopy height](projects/canopy-height.md) | Model integration, validation utilities, and artifacts |
| [Annotation tool](projects/annotation-tool.md) | Assisted geospatial annotation and polygon export |
| [Feature importance](projects/feature-importance.md) | Multispectral feature experiments and preprocessing |
| [Forest-cut classifier](projects/forest-cut-classifier.md) | Vegetation-change indicators and area summaries |
| [Shadow detection](projects/shadow-detection.md) | Analytical masks and reusable packaging |
| [Legacy canopy and shadow workflow](projects/canopy-shadow-legacy.md) | CLI and container integration |
| [Tree-height estimation](projects/tree-height-estimation.md) | Joining crown geometry with height estimates |
| [Tree distance to conductors](projects/tree-distance-conductor.md) | Spatial distance outputs with explicit assumptions |
| [Powerline reconstruction](projects/powerline-reconstruction.md) | Point-cloud geometry and provenance |
| [MLflow infrastructure](projects/mlflow-infrastructure.md) | Infrastructure as code for experiment tracking |
| [Training infrastructure](projects/ml-training-infrastructure.md) | Repeatable GPU training environments |
| [Kestra workflows](projects/kestra-workflows.md) | Proposed batch recovery and completion tracking |

## How to interpret the collection

Articles describe general engineering reasoning. Diagrams are conceptual and do not reproduce private deployment architectures. Tutorials contain original examples rather than extracts from company repositories. Case studies draw on documented contributions and distinguish exploratory work and proposals from established functionality.

No private datasets, credentials, endpoints, customer identifiers, model weights, or operational benchmarks are included. Synthetic numerical results demonstrate software behavior; they are not measurements of model accuracy or production performance. Third-party models and libraries retain their original authorship.
