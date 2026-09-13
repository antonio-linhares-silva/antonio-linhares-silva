# Forest Cut Classifier

[Documentation index](../README.md) · [Vegetation-change article](../articles/vegetation-change.md)

**Project:** spotlite-forest-cut-classifier. **Role:** workflow development, missing-value handling and delivery integration. **Status:** private geospatial package.

## Problem and project scope

A difference between vegetation observations needs to be connected to meaningful spatial units before it can support review. That involves masking, polygon-based analysis, aggregation and interpretable outputs, alongside the underlying raster calculation.

The project contains workflows for index differences, vegetation-intervention analysis and raster/vector delivery. Its historical implementations include several classification conventions, which must be interpreted in the context of their specific version.

## My contribution

My contributions include CLI and workflow implementation, polygon-oriented processing, missing-value handling, documentation, examples and integration with spatial publication tooling. I have worked on the connection between numerical outputs and the formats consumed downstream.

This page describes those engineering contributions. It does not claim that an index difference alone confirms a physical cutting event or that every historical rule is appropriate for every monitoring context.

## Conceptual architecture

Comparable observations → common valid support → declared difference calculation → polygon summaries → review-oriented classes and spatial exports.

**Technologies:** Python, raster/vector processing, command-line workflows, container delivery and GeoServer-related integration.

## Engineering decisions and limits

Missing information needs explicit semantics. A region with insufficient observations should not be interpreted as unchanged vegetation merely to obtain a complete table. Denominators used in percentage summaries also need to be stated.

Sensor and processing compatibility must be established before the difference is interpreted. Alignment, seasonal behavior and observation coverage are not details that can be repaired by choosing a more confident label afterward.

The public article uses an invented cell-count example to explain support and aggregation. It publishes no client geometry, decision thresholds or private validation results.

The project provides a useful case study in preserving meaning through a pipeline: numerical arrays become spatial products that may be viewed independently of the original computation. Clear validity states, documented fields and appropriately limited claims make those products more interpretable.
