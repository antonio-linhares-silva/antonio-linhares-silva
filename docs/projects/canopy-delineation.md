# Canopy Delineation

[Documentation index](../README.md) · [Memory article](../articles/memory-bounded-rasters.md) · [Change article](../articles/vegetation-change.md)

**Project:** spotlite-canopy-delineation. **Role:** pipeline development, integration and reliability work. **Status:** maintained private package.

## Problem and project scope

Tree-crown delineation turns high-resolution imagery into individual canopy geometries. Large scenes make the surrounding engineering demanding: preprocessing, tiled inference, overlap handling and polygon extraction all have their own resource requirements.

The project integrates model-based prediction with a CLI and spatial outputs. It also contains workflows for reviewing results and comparing crowns across observations. These capabilities should be distinguished from independently confirmed tree events or survey measurements.

## My contribution

My work includes inference orchestration, memory-bounded prediction merging, recovery of interrupted runs, batching controls and packaging fixes. I have also worked on integration with canopy-height information and review-oriented temporal workflows.

The contribution is in making the components work together and making execution more recoverable. The underlying third-party models retain their original authorship.

## Conceptual architecture

Input imagery → spatially declared preparation → tiled model prediction → bounded merge → crown geometry → optional enrichment and review outputs. A run record connects the model, input identity and processing configuration.

**Technologies:** Python, PyTorch-compatible model tooling, Rasterio/GDAL, vector processing and container delivery.

## Engineering decisions and limits

Tiling model input does not automatically bound the final merge. The implementation work addresses the working set across stages, while preserving the intended grid and output coverage.

Resume behavior also needs compatibility checks. An existing file can be incomplete or belong to a different invocation. Reusing it requires stronger evidence than a matching filename.

A crown polygon remains a prediction whose quality depends on imagery, preprocessing, model suitability and post-processing. Temporal review candidates are not confirmed removals. No private thresholds, benchmarks, imagery or checkpoints are published here.

The public [windowed raster tutorial](../tutorials/windowed-raster-processing.md) illustrates the numerical and spatial checks behind bounded processing with a small independent example. It does not reproduce the private delineation algorithm or claim its model accuracy.

## Independent public-data demonstration

[Notebook 08: tree crowns height distance](../../notebooks/08-tree-crowns-height-distance.ipynb) demonstrates related methods using public observations and original code. It does not reproduce this private project or its operational results.
