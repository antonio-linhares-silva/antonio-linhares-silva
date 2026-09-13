# Hi, I'm António Silva 👋

**GeoAI · Python · Machine Learning Engineering · Geospatial Software**

I build software that turns satellite imagery and geospatial data into tools for vegetation monitoring and infrastructure analysis. My experience spans land-use and land-cover classification, tree-species mapping, semantic segmentation, object detection, image super-resolution, canopy height estimation, and LiDAR processing, alongside reusable Python packages and workflow automation.

I enjoy connecting applied machine learning with practical software engineering: taking a workflow from a notebook to a documented CLI, handling large rasters within memory limits, and making processing reproducible and recoverable.

[GitHub](https://github.com/antonio-linhares-silva)

## Project experience — GAIA Framework

I co-developed **GAIA — Geo Artificial Intelligence for Applications**, a modular Python/PyTorch framework for experimenting with satellite-imagery models. It brings datasets, model configurations, training, evaluation, inference, and preprocessing into a shared structure.

The framework covers several complementary areas:

| Area | Scope and examples |
| --- | --- |
| **Tree-species and forest-group mapping** | Multiclass semantic segmentation with UPerNet/BEiT configurations for four-band Pleiades imagery. Dataset labels distinguish coniferous forests, a Quercus forest category, eucalyptus forests, other species, and background. |
| **Tree-crown detection** | Object-detection workflows and RetinaNet/FCOS configurations, with dataset labels including larch and spruce alongside generic tree and other categories. |
| **Land cover and scene classification** | LandCoverNet segmentation and an experimental EuroSAT/Swin Transformer classification workflow. |
| **Road and agricultural segmentation** | Configurations for road/asphalt and vineyard segmentation using architectures such as U-Net, U-Net++, and UPerNet/BEiT across the framework. |
| **Image super-resolution** | Super-resolution pipelines and EDSR, RCAN, and HAT configurations, supported by tools for creating paired high- and low-resolution datasets. |
| **Geospatial data preparation** | Dataset adapters, raster patches, multichannel normalization and augmentation, label preparation, and patch merging. |
| **Experiment and development tooling** | YAML-driven pipelines, checkpoint loading and training resume, hyperparameter-search scripts, results documentation, and package/build/test automation. |

**Engineering focus:** reusable components across different tasks, configurable experiments, multispectral data handling, and a consistent interface from dataset preparation to inference. GAIA is a prototype framework for applied research and experimentation.

## Featured public project — Land Use & Land Cover

[**Explore land-use-land-cover →**](https://github.com/antonio-linhares-silva/land-use-land-cover)

I co-developed **landcover**, a Python package for land-use and land-cover classification. It connects geospatial data preparation, classifier training and tuning, raster inference, temporal change detection, and MLflow-based model management.

| Area | Scope and examples |
| --- | --- |
| **Land-cover classification** | Training and inference with Random Forest and other scikit-learn classifiers, plus XGBoost and LightGBM integration. |
| **Optical and radar inputs** | Tools to combine Sentinel-2 optical imagery with Sentinel-1 SAR composites, with configurable band selection and temporal features. |
| **CPU and GPU workflows** | Optional RAPIDS/cuML support, batched inference, and chunked GPU transfers to manage large geospatial datasets. |
| **Tuning and feature analysis** | Hyperparameter tuning, cross-validation utilities, and permutation importance for exploring the contribution of input features. |
| **MLOps and model reuse** | MLflow experiment tracking and model loading, a PyFunc wrapper for cuML models, compressed model artifacts, local caching, and version-specific environment definitions. |
| **Raster outputs and change analysis** | Georeferenced classification outputs, post-processing that preserves NoData regions, and workflows for identifying changes between dates. |

**Engineering focus:** connecting conventional machine learning with geospatial processing through a reusable package, command-line tools, and documented model environments.

## What I bring to a team

- **Geospatial machine learning:** develop and integrate workflows for tree-species groups, land cover, tree-crown detection, super-resolution, and canopy-height estimation using PyTorch and specialist geospatial models.
- **Python software engineering:** develop reusable packages and CLIs with automated tests, clear data contracts, logging, and release workflows.
- **Large-image processing:** work on tiled inference, GPU batching, memory-bounded raster merging, and resumable execution.
- **MLOps and cloud infrastructure:** contribute MLflow integration, Terraform infrastructure, Docker packaging, and GitHub Actions delivery.
- **Workflow automation:** connect geospatial processing components through Kestra and container-based jobs.

## Engineering highlights

**Making canopy processing recoverable.** My contributions to canopy delineation include memory-bounded prediction merging, recovery from interrupted runs, GPU batching controls, and packaging fixes. These changes address practical failures that can prevent large imagery workflows from completing.

**Connecting tree geometry with height.** I developed and extended workflows that combine crown segmentation with canopy-height estimates, enrich individual tree polygons, and calculate distances to conductor geometries.

**Bringing models into repeatable workflows.** My canopy-height work includes CHMv2 integration, reference-data validation utilities, MLflow registry support, and container packaging for model assets.

**Making experiments traceable.** I contributed a multispectral feature-selection pipeline with train-region normalization, permutation importance, feature-subset experiments, and configuration-based run identities.

**Turning processing components into operator workflows.** My Kestra contributions include idempotent batch queues and completion tracking so interrupted batches can resume without repeating completed work.

## My work at Spotlite — private project catalogue

Much of my work at Spotlite lives in private company repositories. The catalogue below describes projects I have contributed to; it does not imply sole authorship of every component. The summaries focus on engineering scope and omit source code, internal data, and deployment details.

### GeoAI, computer vision, and vegetation analytics

| Private repository | Project scope |
| --- | --- |
| `spotlite-canopy-delineation` | Tree-crown segmentation from high-resolution imagery, with tiled inference, training workflows, height filtering, and temporal crown comparison. |
| `spotlite-canopy-height` | Canopy-height estimation using pretrained models, with reference-data validation, correction utilities, tree-instance integration, and MLflow support. |
| `spotlite-annotation-tool` | Geospatial annotation and segmentation workflows using SAM3, including image tiling, text prompts, shadow handling, and polygon export. |
| `spotlite-feature-permutation-importance` | Multispectral segmentation experiments, permutation importance, and feature-subset comparisons through a reproducible Python pipeline. |
| `spotlite-forest-cut-classifier` | Vegetation-change and forest-cut intensity classification from NDVI differences, with area-based analysis and geospatial exports. |
| `shadow-detection` | Analytical shadow masks from RGB and near-infrared imagery, packaged with tiling, merging, a CLI, and automated tests. |
| `spotlite-ml-canopyshadowheight-legacy` | A legacy tree-and-shadow workflow converted into a CLI and Docker pipeline, including tree-height outputs when suitable solar metadata is available. |

### Tree metrics, LiDAR, and infrastructure analysis

| Private repository | Project scope |
| --- | --- |
| `spotlite-tree-height-estimation` | Integration of crown delineation and canopy-height inference to attach height estimates to individual tree polygons. |
| `spotlite-tree-distance-conductor` | Integration of tree geometry, estimated heights, and conductor features to calculate spatial distances and export enriched tree data. |
| `spotlite-powerline-reconstruction` | Exploratory powerline reconstruction from LAS/LAZ point clouds using adaptive catenary fitting, traceable outputs, and explicit separation of observations from synthetic geometry. |

### MLOps, infrastructure, and orchestration

| Private repository | Project scope |
| --- | --- |
| `mlflow-ovh-terraform` | Infrastructure as code for MLflow experiment tracking and model-management workflows. |
| `mltrain-ovh-terraform` | Infrastructure as code supporting reproducible GPU-accelerated model training. |
| `spotlite-kestra-workflows` | Kestra orchestration around geospatial processing containers, including batch execution, input staging, and recoverable processing queues. |

*The private repositories listed here require authorized access. This profile provides a summary of my work; it does not grant access to company code or data. Third-party models and libraries retain their original authorship.*

## Technologies used across these projects

| Area | Technologies |
| --- | --- |
| Languages and scientific computing | Python, Bash, NumPy, SciPy, pandas |
| Machine learning and computer vision | PyTorch, torchvision, segmentation-models-pytorch, scikit-learn, XGBoost, LightGBM, RAPIDS/cuML, timm, Albumentations, DeepTrees, SAM3, CHMv2, DINOv3 |
| Geospatial processing | GDAL, Rasterio, GeoPandas, Shapely, PyProj, laspy |
| Data formats | Cloud-Optimized GeoTIFF, GeoPackage, GeoJSON, LAS/LAZ |
| MLOps and infrastructure | MLflow, Terraform |
| Packaging and delivery | Docker, GitHub Actions, GitHub Container Registry, Git LFS, uv, Hatch |
| Developer tooling and orchestration | pytest, Ruff, Typer, Jupyter, TensorBoard, Kestra |

## Let's connect

If you're hiring for **GeoAI, geospatial software, Python engineering, or ML engineering**, I'd be happy to discuss my contributions, technical decisions, and the challenges behind these projects at a level consistent with company confidentiality.
