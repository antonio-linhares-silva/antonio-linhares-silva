# Shadow Detection

[Documentation index](../README.md) · [Data contracts](../articles/geospatial-data-contracts.md) · [Shipping GeoAI](../articles/shipping-geoai.md)

**Project:** shadow-detection. **Role:** packaging and workflow engineering. **Status:** private Python package and CLI.

## Problem and project scope

Shadow information can support image interpretation and segmentation workflows, but the mask must remain connected to the source imagery's band meaning and spatial grid. A reusable implementation also needs a predictable way to process images that do not fit comfortably into one array.

The project packages analytical shadow-mask generation for RGB/NIR imagery with tiling, merging, logging and command-line execution. The public description focuses on these engineering boundaries rather than publishing the internal threshold logic.

## My contribution

My work includes turning processing components into a reusable package and CLI, organizing tiled workflows and outputs, adding tests and improving container usage documentation. These changes help another operator run the workflow without reproducing an interactive development session.

Related shadow-processing exploration also informed the broader portfolio, but this page does not claim authorship of external shadow models or published correction methods.

## Conceptual architecture

Raster and declared band roles → optional tiling → mask calculation → merge → georeferenced output and run record.

**Technologies:** Python, NumPy, Rasterio/GDAL, CLI tooling, pytest and Docker.

## Engineering decisions and limits

Band-role interpretation is a real input dependency. A fourth channel should not be assumed to have a particular spectral meaning without a documented basis. Invalid source pixels must also remain distinguishable from pixels classified as non-shadow.

A tiled workflow should preserve coverage at borders and state whether neighborhood context is needed. A successful mask calculation on one patch does not establish that a merged scene has the intended grid.

The public collection provides no shadow-detection benchmark and does not claim that one analytical rule works equally well across acquisition conditions. Imagery, coefficients and application-specific settings are excluded.

The companion tutorials demonstrate independent raster arithmetic and validity checks. They are deliberately simpler than the private shadow workflow, allowing readers to inspect spatial preservation and packaging principles without receiving a reimplementation of company processing logic.

## Independent public-data demonstration

[Notebook 04: geospatial data contracts](../../notebooks/04-geospatial-data-contracts.ipynb) demonstrates related methods using public observations and original code. It does not reproduce this private project or its operational results.
