# Tree Distance to Conductors

[Documentation index](../README.md) · [Tree metrics article](../articles/tree-crowns-height-distance.md)

**Project:** spotlite-tree-distance-conductor. **Role:** workflow integration and packaging. **Status:** private geospatial package.

## Problem and project scope

Tree geometries become more informative when related to nearby infrastructure geometry. Computing that relationship requires a clear distinction between horizontal footprints, estimated tree heights and the representation of the conductor.

The package connects tree-instance and height processing with conductor features, then writes enriched spatial outputs. It builds on separate canopy components rather than embedding every stage into a new model.

## My contribution

My work includes developing and extending the integration, coordinating the dependent packages and improving container and dependency behavior. The goal is to make the geometry and height components usable together through a repeatable execution path.

This role should not be read as authorship of the underlying pretrained models or as a claim that a derived distance constitutes an infrastructure assessment by itself.

## Conceptual architecture

Imagery → tree instances and estimated heights → compatible conductor geometry → declared spatial-distance calculation → enriched tree output.

**Technologies:** Python, raster/vector processing, canopy packages and Docker.

## Engineering decisions and limits

A distance field needs a definition. Distance to a two-dimensional line differs from distance to three-dimensional sampled points or a fitted curve. A height statistic attached to a crown does not reconstruct the complete three-dimensional tree surface.

Units and coordinate references need to agree. Above-ground height and absolute elevation also require a compatible terrain reference before they can participate in the same vertical calculation.

Failures of support should remain visible. Missing conductor coverage, an unresolved height or incompatible metadata should not become a confident numerical result simply to fill an output column.

The public description excludes operational clearance rules, asset locations and private measurements. It makes no safety-certification or universal accuracy claim. The linked article explains the interpretation of these geometric quantities and the difference between testing an integration with synthetic fixtures and validating a real-world measurement process.

This project illustrates a recurring software-engineering task in GeoAI: preserving meaning while composing independently useful components into a workflow that another person can operate.

## Independent public-data demonstration

[Notebook 10: lidar evidence](../../notebooks/10-lidar-evidence.ipynb) demonstrates related methods using public observations and original code. It does not reproduce this private project or its operational results.
