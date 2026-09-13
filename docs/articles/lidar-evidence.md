# Reconstructing Power Lines from LiDAR Evidence

[**Run the public-data notebook**](../../notebooks/10-lidar-evidence.ipynb) ? [Notebook setup](../../notebooks/README.md)

[Documentation index](../README.md) · [Powerline reconstruction](../projects/powerline-reconstruction.md)

A fitted curve can look convincing even when the point cloud provides little support for it. In reconstruction work, the quality of the presentation can therefore exceed the strength of the evidence. A useful pipeline must preserve the distinction between measured observations and generated geometry.

My powerline-reconstruction work includes an exploratory pipeline with input auditing, adaptive fitting, traceable outputs and packaging checks. This article describes general design principles. It does not distribute source point clouds, operational fitting parameters or infrastructure geometry.

## Establish what the input represents

LAS and LAZ data can carry coordinates, classifications and flags, but those fields still need interpretation. A classification code may follow a standard scheme or a dataset-specific mapping. Treating every numerical class value as universal can send the wrong points into reconstruction.

Units and spatial references are equally important. A geometric fit in arbitrary coordinate units is not automatically a fit in metres. Vertical references also affect relationships between ground, vegetation and conductor observations.

Input auditing should therefore precede model fitting. The audit can record what was declared, what was observed and which assumptions remain unresolved. It should preserve original point attributes so a later reviewer can inspect the source evidence.

~~~mermaid
flowchart LR
    A["Original observations"] --> B["Input and class audit"]
    B --> C["Supported candidate groups"]
    C --> D["Fit and inspect evidence"]
    D --> E["Accepted reconstruction"]
    D --> F["Unresolved or rejected"]
    A --> G["Preserved measured points"]
    E --> H["Clearly marked generated geometry"]
~~~

## Use local support rather than total density

A large point cloud does not necessarily contain strong conductor evidence. Most observations may belong to terrain or vegetation. Even within one scene, some spans can be well observed while others have sparse or ambiguous support.

A useful method evaluates the relevant evidence locally. The number and arrangement of candidate points, directional coherence and continuity can inform whether a fit is defensible. A route chosen only from the filename or total point count does not inspect that geometry.

Adaptive processing should not mean that sparse regions are always completed. It can mean selecting a more conservative method or retaining an unresolved result. The decision to refrain from generating a segment is an informative outcome when the evidence is inadequate.

## A fitted shape is a hypothesis

A catenary is a useful mathematical model for certain suspended-cable configurations. Whether a particular observed structure is adequately represented by that model depends on its support and the assumptions of the fit. The model family alone does not establish a correct association between points and cables.

Several candidate curves may explain part of the same point set. Nearby conductors, vegetation and crossing structures can create ambiguous associations. A reconstruction should retain enough diagnostics to distinguish a well-supported fit from one chosen primarily by a heuristic.

Residuals are useful but incomplete. A small residual on a small or selectively chosen subset does not establish support over the entire generated span. Coverage along the candidate geometry and rejected observations matter too.

## Preserve observations and label generated geometry

Generated samples should remain identifiable after export. Otherwise a downstream consumer may treat a reconstructed point as another measurement from the sensor. That can contaminate later analysis or make an apparently dense output look more strongly observed than it was.

The format needs to carry the distinction in machine-readable fields, not only in a color palette. LAS supports additional dimensions for per-point attributes, and laspy exposes that mechanism. The exact schema must remain compatible with the consumer. [laspy extra dimensions](https://laspy.readthedocs.io/en/latest/lessbasic.html)

Presentation still matters: conservative and exploratory views should communicate their different meanings. However, a viewer style should reinforce the recorded distinction, not be its only implementation. Exporting a file without its custom style should not erase the provenance of its points.

## Missing terrain remains missing information

Ground-relative vegetation heights require a suitable terrain reference. If no defensible terrain estimate is available, an unresolved height is preferable to silently using zero. Reconstruction of another structure may still proceed if its own input requirements are satisfied.

This separates independent capabilities. Failure to estimate terrain-relative vegetation height should not necessarily discard valid conductor observations. Conversely, successful cable fitting should not imply that all derived vegetation quantities are valid.

A quality record can explain which outputs are supported and which are absent. This is more useful than a single success flag for a pipeline that produces several different kinds of result.

## Validate the exported product independently

A processing function can preserve the right fields in memory while an export step loses them. Reading the product back with an independent path helps verify coordinates, attributes and generated-point markers.

Synthetic fixtures can test invariants such as retaining original observations and rejecting undeclared units. They can also exercise sparse support and deliberately ambiguous geometry. Those tests do not replace validation against surveyed reference data.

For exploratory reconstruction, a useful evaluation distinguishes where geometry was accepted, rejected or left unresolved. A score computed only on accepted easy cases can hide an important coverage limitation. The abstention pattern belongs in the interpretation of the result.

## Keep scope proportional to the evidence

The project is a bounded survey workflow rather than a claim of unlimited scale or universal reconstruction accuracy. Large inputs, incomplete classification and ambiguous support remain material constraints. Resource controls prevent runaway processing but do not create missing observations.

The portfolio contribution is the engineering around evidence-aware computation: explicit input interpretation, preservation of measured data, separation of generated products and independent readback. Those properties help another engineer judge the result without confusing geometric plausibility with measurement.

For related issues in derived metrics, continue with [tree crowns, height and distance](tree-crowns-height-distance.md).
