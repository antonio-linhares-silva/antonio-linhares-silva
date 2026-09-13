# Geospatial Annotation Tool

[Documentation index](../README.md) · [Shipping GeoAI](../articles/shipping-geoai.md)

**Project:** spotlite-annotation-tool. **Role:** workflow integration, refactoring and delivery tooling. **Status:** private package and CLI.

## Problem and project scope

Interactive segmentation can reduce the manual work of annotation, but processing geospatial imagery introduces additional requirements. A scene may need tiling, spatial metadata must survive the workflow, and predicted masks must be converted into usable vector outputs.

The project builds on external geospatial and segmentation libraries, including SAM-related tooling. It connects image preparation, prompted segmentation, optional shadow handling and polygon export.

## My contribution

My contributions include pipeline refactoring, CLI and logging improvements, testing infrastructure, shadow-mask integration, spatial export work and release automation. I have also worked on container packaging, version-based image tagging and materialization of required large-file assets.

These activities support the use of third-party segmentation models. They do not imply authorship of SAM or the external libraries that provide the model interfaces.

## Conceptual architecture

Input raster → tile preparation → prompted model execution → mask processing → polygon extraction → spatial output. Metadata and validity need to remain interpretable as representations change.

**Technologies:** Python, SAM/GeoAI ecosystem, Rasterio/GDAL, vector geometry libraries, Docker and GitHub Actions.

## Engineering decisions and limits

A prompt is part of the input contract rather than a guarantee of the intended object class. Shadow handling can also change geometry and should remain visible in the workflow description.

Packaging needs to account for native geospatial dependencies and any assets expected at runtime. A source checkout that works on one machine does not establish that its installed package or container contains the same resources.

The public case study focuses on integration and software delivery. It does not distribute annotated imagery, model weights, private prompts or application-specific settings. No segmentation-accuracy comparison is claimed.

The linked article explains how a notebook workflow becomes an explicit CLI and tested artifact. The independent tutorials provide smaller examples of spatial contracts and model packaging that readers can execute without access to this private project.
