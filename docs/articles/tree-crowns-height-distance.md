# From Tree Crowns to Height and Distance

[Documentation index](../README.md) · [Tree height estimation](../projects/tree-height-estimation.md) · [Tree distance to conductors](../projects/tree-distance-conductor.md)

A crown polygon, a canopy-height raster and a conductor geometry describe different aspects of the same scene. Combining them can produce useful per-tree attributes, but a join is not enough: coordinate systems, height meanings and spatial support must agree.

My work includes integrating crown delineation and canopy-height inference, enriching tree polygons and calculating distances to conductor geometries. This article explains the conceptual boundaries of that integration. It contains no asset locations, operational clearance thresholds or engineering certification claims.

## Begin with what each observation means

A crown polygon is usually a horizontal footprint inferred from imagery. A canopy-height model estimates a height-related quantity on a raster grid. A conductor layer might represent a two-dimensional line, a three-dimensional curve or sampled observations. Those representations support different calculations.

The first useful product is therefore a description of the inputs. Which coordinate system applies horizontally? Are heights relative to terrain or referenced to a vertical datum? What is the acquisition date? Which areas have valid support?

These questions should be answered before assigning a distance field. A numerical result can look precise while combining incompatible meanings. More decimal places do not compensate for uncertainty in the geometry or height estimate.

~~~mermaid
flowchart LR
    A["Crown footprints"] --> C["Validate spatial compatibility"]
    B["Height raster and validity"] --> C
    C --> D["Sample supported crown pixels"]
    D --> E["Enriched tree attributes"]
    F["Declared conductor representation"] --> G["Distance calculation"]
    E --> G
    G --> H["Results with limitations"]
~~~

## Sampling is a modeling choice

Attaching a height to a polygon requires deciding which pixels contribute and which statistic to report. A maximum, median and upper percentile answer different questions. The choice should be visible in the field name or documentation.

A maximum can be sensitive to isolated artifacts. A median represents the central distribution of included pixels and may not describe the highest part of a tree. A robust high percentile has another interpretation and still needs sufficient valid support. There is no universally correct statistic independent of the intended use.

Boundary handling also matters. A small crown can contain few pixel centers while intersecting many pixel footprints. Different inclusion rules can change the sample. The calculation should record its rule and distinguish a crown with no supported pixels from a crown whose estimated height is zero.

The generic raster/vector relationship is part of the [data-contract article](geospatial-data-contracts.md). In these integrations, it becomes an explicit dependency of every downstream attribute.

## Horizontal distance and spatial distance differ

A distance between a polygon footprint and a projected line is a horizontal geometric quantity. A three-dimensional distance needs a representation of height on both sides. A single crown-height statistic does not fully reconstruct the surface of the tree.

Consider an invented example: two crowns share the same footprint but have different heights. Their horizontal distance to a line is identical. A three-dimensional distance might differ, depending on how the crowns and conductor are represented. The representation is therefore part of the answer.

Likewise, the distance to the nearest sampled conductor point is not automatically the distance to a continuous conductor curve. Sampling density and curve reconstruction affect the interpretation. A report should identify whether its target was a point collection, line segment or fitted geometry.

This article intentionally avoids presenting a simple formula as a complete infrastructure assessment. The spatial computation can provide a feature for review while leaving operational decisions to a separately validated process.

## Height references must be compatible

An above-ground height and an absolute elevation cannot be combined directly. They require a compatible terrain reference and documented units. Two datasets that both use metres can still have different vertical reference systems.

When the reference is undocumented, retaining an unresolved result is more honest than silently inserting a zero offset. A missing terrain observation should not turn into a ground elevation of zero just to complete the arithmetic.

The same caution applies when acquisitions are separated in time. A geometrically compatible dataset may describe a different state of the canopy or asset. Compatibility has spatial, temporal and semantic dimensions.

## Preserve the reasons behind missing results

An empty field can have several causes: no raster coverage, no valid pixels, incompatible metadata or no nearby target under the chosen search rule. Collapsing all of them into zero makes the dataset easier to consume superficially and harder to interpret correctly.

A compact quality status helps distinguish these cases. It need not expose internal diagnostics. It should give the consumer enough information to decide whether a result is supported, unresolved or excluded.

Preserving the original crown identity is equally useful. An enriched dataset should allow a reviewer to trace an attribute back to the corresponding footprint. Reordering or regenerating identifiers during each stage can make that comparison unnecessarily difficult.

## Validate integration separately from model accuracy

Synthetic geometries can verify unit conversion, sampling behavior and geometric calculations. A flat height surface, a crown outside coverage and a known point-to-segment arrangement provide independent expectations for the integration layer.

Those checks do not validate the height model against real trees. That requires suitable reference observations, compatible acquisition conditions and an evaluation protocol. Keeping the two forms of validation separate makes both results easier to understand.

The project pages therefore describe integration contributions and their limits. They do not claim a universal measurement accuracy or that a computed distance certifies safety. The engineering goal is to produce traceable attributes whose meanings remain intact from inputs through export.
