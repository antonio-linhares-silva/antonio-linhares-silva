# Legacy Canopy and Shadow Workflow

[Documentation index](../README.md) · [Shipping GeoAI](../articles/shipping-geoai.md)

**Project:** spotlite-ml-canopyshadowheight-legacy. **Role:** CLI conversion, integration and packaging. **Status:** maintained legacy workflow.

## Problem and project scope

An existing notebook combined tree and shadow processing, but operating it as a repeatable job required an explicit execution path. The project preserves that legacy context while providing a CLI and container-based workflow.

Its outputs include prepared raster tiles, tree masks, shadow masks and, when the required metadata are available, derived tree-height outputs. Those products have different prerequisites and should not all inherit the same success assumption.

## My contribution

My work includes converting the workflow into a focused command-line pipeline, organizing inputs and outputs, packaging required assets and stabilizing tests and container behavior. The aim is to make an existing method easier to execute and diagnose.

This is engineering around a legacy workflow. It does not imply that the original models or all notebook methods were authored by me, nor that packaging establishes their scientific accuracy.

## Conceptual architecture

Input raster → working tiles → tree and shadow prediction → mask assembly → optional height calculation with validated solar metadata.

**Technologies:** Python, existing model assets, geospatial raster processing, CLI tooling and Docker.

## Engineering decisions and limits

The supported entry point should make the workflow's prerequisites visible. Height estimation based on shadows needs suitable acquisition and solar information; missing metadata cannot be replaced by an arbitrary default without changing the meaning of the result.

A partial capability can still be useful. Producing valid masks when a height calculation is unsupported is different from pretending the complete workflow succeeded. The outputs and logs should explain that distinction.

Legacy environments also need care. A notebook that once ran on a particular machine is not a complete dependency specification. The container and installed-package checks help expose missing resources and version assumptions.

This public case study excludes checkpoints, private imagery and operational configurations. It makes no height-accuracy claim. Its transferable lesson is how to preserve a useful research workflow while making its execution contract, prerequisites and limitations explicit.

## Independent public-data demonstration

[Notebook 07: shipping geoai](../../notebooks/07-shipping-geoai.ipynb) demonstrates related methods using public observations and original code. It does not reproduce this private project or its operational results.
