# Canopy Height

[Documentation index](../README.md) · [Tree metrics article](../articles/tree-crowns-height-distance.md)

**Project:** spotlite-canopy-height. **Role:** model integration, workflow development and packaging. **Status:** maintained private package.

## Problem and project scope

Height inference from imagery becomes more useful when the estimated raster can be processed at scene scale, inspected against suitable references and associated with individual tree geometries. These are separate steps with different requirements.

The project integrates pretrained canopy-height models, including CHMv2-related tooling, into a Python package and CLI. Its broader scope includes tiled execution, reference-data comparison utilities, correction experiments and tree-instance workflows.

## My contribution

My work includes model integration, validation utilities, MLflow-related support, artifact packaging, AOI handling and sparse tiled processing. These contributions connect external models with reproducible geospatial execution.

The distinction between model authorship and integration matters here. I do not claim to have developed the pretrained foundation models. My contribution concerns their use within a package, the spatial workflow around them and the software needed to run and inspect that workflow.

## Conceptual architecture

Image and area of interest → validated preparation → height inference → tile assembly → georeferenced height output. Optional stages compare suitable reference surfaces or attach sampled values to tree instances.

**Technologies:** Python, pretrained deep-learning models, Rasterio/GDAL, geospatial vector tools, MLflow and Docker.

## Engineering decisions and limits

An estimated height raster should carry its spatial reference and validity information. A missing prediction must remain distinguishable from a valid zero. Comparing it with a reference surface additionally requires compatible meanings, dates and vertical references.

Correction and validation utilities are capabilities, not proof that an arbitrary output is accurate. A correction fitted to one area requires separate evaluation before use elsewhere.

This public description excludes model caches, private evaluation datasets and performance numbers. It also avoids publishing operational preprocessing settings. The related articles explain the engineering concepts using generic diagrams. Their examples do not distribute pretrained weights or require access to company model infrastructure.

## Independent public-data demonstration

[Notebook 08: tree crowns height distance](../../notebooks/08-tree-crowns-height-distance.ipynb) demonstrates related methods using public observations and original code. It does not reproduce this private project or its operational results.
