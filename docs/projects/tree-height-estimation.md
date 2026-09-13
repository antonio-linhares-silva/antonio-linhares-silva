# Tree Height Estimation

[Documentation index](../README.md) · [Tree metrics article](../articles/tree-crowns-height-distance.md)

**Project:** spotlite-tree-height-estimation. **Role:** package development and component integration. **Status:** private workflow.

## Problem and project scope

A canopy-height raster describes a surface, while many applications need attributes attached to individual tree instances. Connecting those representations requires crown geometries, compatible spatial support and an explicit sampling rule.

This package integrates crown delineation and canopy-height inference, then enriches individual polygons with sampled height information. It provides a command-line path through those existing components and exports a spatial dataset for downstream use.

## My contribution

My work includes creating the integration package, handling raster-band interpretation, coordinating the component calls, sampling height information and adapting the final spatial output. I have also worked on documentation and packaging requirements for those dependencies.

The contribution is in the composition and engineering of the workflow. The crown and height models remain distinct components, with their own authorship and validation requirements.

## Conceptual architecture

Input imagery → compatible model inputs → crown prediction and height prediction → polygon-based raster sampling → enriched tree geometries.

**Technologies:** Python, Rasterio/GDAL, vector geometry libraries, canopy packages and container execution.

## Engineering decisions and limits

The height statistic is part of the output meaning. A maximum sampled value does not have the same interpretation as a median, and it may be more sensitive to isolated artifacts. The method should be explicit to anyone consuming the exported field.

A crown without usable height coverage needs an unresolved value or status. Converting that case into a height of zero would hide an input-support problem.

The integration also depends on compatible coordinates, acquisition context and raster validity. Passing a file from one package to another does not by itself establish those conditions.

This case study describes the integration rather than publishing operational settings or field validation results. It includes no client geometry, imagery or model artifacts. The associated article explains the choices behind raster/vector enrichment and why testing the integration is separate from measuring model accuracy against real trees.
