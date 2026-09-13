# Hi, I'm António Silva 👋

**GeoAI · Python · Machine Learning Engineering · Geospatial Software**

I build software that turns satellite imagery and geospatial data into tools for vegetation monitoring and infrastructure analysis. My experience includes land-cover classification, tree-species mapping, segmentation, object detection, image super-resolution, canopy-height estimation, and LiDAR processing.

I enjoy connecting applied machine learning with Python engineering: moving experiments into reusable packages, processing large rasters within memory limits, and making workflows reproducible and recoverable.

## Explore my technical portfolio

[**GeoAI Engineering Notes →**](docs/README.md)

A collection of **10 executed public-data notebooks, 10 technical articles, 4 runnable tutorials, and 15 project case studies**. Explore real Sentinel-2, EuroSAT and AHN data through visible experiments, maps, model outputs and engineering checks. The case studies describe my contributions to collaborative projects.

| Start here | What it covers |
| --- | --- |
| [Reusable GeoAI frameworks](docs/articles/reusable-geoai-framework.md) | Shared interfaces across datasets, experiments, and inference |
| [Processing rasters within memory limits](docs/articles/memory-bounded-rasters.md) | Windows, output grids, masks, and bounded intermediate arrays |
| [Multispectral experiments](docs/articles/multispectral-experiments.md) | Train-region preprocessing, feature comparisons, and spatial validation |
| [Model artifacts with MLflow](docs/articles/model-artifacts-mlflow.md) | Packaging, environment definitions, and independent reload checks |
| [Recoverable workflows](docs/articles/resumable-workflows.md) | Completion records, input identity, and safe retries |
| [Evidence in LiDAR reconstruction](docs/articles/lidar-evidence.md) | Observed points, fitted geometry, and uncertainty |

## Selected project experience

**[GAIA framework](docs/projects/gaia.md).** I co-developed a modular Python/PyTorch prototype for applied GeoAI experimentation, contributing dataset handling, multiclass compatibility fixes, geospatial postprocessing, and development automation.

**[Land Use & Land Cover](docs/projects/land-use-land-cover.md).** I co-developed a Python package connecting conventional machine learning, optical and radar features, raster inference, and MLflow model management. The source repository is private; the public case study explains the engineering scope.

**[Canopy delineation](docs/projects/canopy-delineation.md) and [canopy height](docs/projects/canopy-height.md).** My work includes bounded prediction merging, recovery from interruptions, model integration, reference-data validation utilities, and packaging.

**[Tree metrics](docs/projects/tree-height-estimation.md) and [powerline reconstruction](docs/projects/powerline-reconstruction.md).** I contributed workflows connecting crown geometry, height estimates, and infrastructure features, alongside exploratory reconstruction from point clouds with explicit provenance.

**[Kestra workflows](docs/projects/kestra-workflows.md).** I proposed recoverable batch queues and completion tracking in a pull request. That contribution remains under review as of 13 September 2026.

[**Browse all 15 case studies →**](docs/README.md#project-case-studies)

## What I bring to a team

- **Geospatial machine learning:** integrate imagery models and conventional classifiers with geospatial data preparation and inference.
- **Python software engineering:** develop reusable packages and CLIs with tests, data contracts, logging, and delivery workflows.
- **Large-image processing:** work on tiled inference, GPU batching, bounded raster merging, and resumable execution.
- **MLOps and infrastructure:** contribute MLflow integration, Terraform infrastructure, Docker packaging, and workflow orchestration.

| Area | Technologies used across these projects |
| --- | --- |
| Python and machine learning | NumPy, pandas, PyTorch, scikit-learn, XGBoost, LightGBM, RAPIDS/cuML |
| Geospatial processing | GDAL, Rasterio, GeoPandas, Shapely, PyProj, laspy |
| MLOps and delivery | MLflow, Terraform, Docker, GitHub Actions, Git LFS, uv, Kestra |
| Development | pytest, Ruff, Typer, Jupyter |

## Run the public-data notebooks

[**Browse all 10 notebooks and setup instructions**](notebooks/README.md)

Start with [a short EuroSAT fine-tune](notebooks/01-reusable-geoai-framework.ipynb), [windowed Sentinel-2 processing](notebooks/02-memory-bounded-rasters.ipynb), [tree boxes and public height surfaces](notebooks/08-tree-crowns-height-distance.ipynb), or [observed LiDAR and fitted geometry](notebooks/10-lidar-evidence.ipynb). Saved results are visible on GitHub; CPU and NVIDIA GPU installation options are documented.

[Data sources and licences](docs/DATA_SOURCES.md) accompany the versioned download packs.

## Try the small synthetic examples

1. [Windowed raster processing and COG output](docs/tutorials/windowed-raster-processing.md)
2. [Preprocessing fitted only on training regions](docs/tutorials/train-only-preprocessing.md)
3. [Packaging and reloading a local MLflow model](docs/tutorials/local-mlflow-model.md)
4. [Resuming a batch after an interruption](docs/tutorials/resuming-a-batch.md)

The examples run locally with Python 3.12 and a locked dependency environment. They need no company data, cloud account, or credentials. See the [setup and validation instructions](docs/README.md#runnable-tutorials).

## About this portfolio

Most source projects are private collaborative repositories. Their case studies describe my contributions without reproducing private code, data, deployment settings, or operational results. Third-party models and libraries retain their original authorship. The public examples were written independently for this collection.

If you're hiring for **GeoAI, geospatial software, Python engineering, or ML engineering**, I'd be happy to discuss the technical decisions behind this work.

[GitHub profile](https://github.com/antonio-linhares-silva)
