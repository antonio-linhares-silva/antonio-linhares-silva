# Geospatial Data Contracts: Grids, Bands and NoData

[Documentation index](../README.md) · [Land Use Land Cover](../projects/land-use-land-cover.md) · [GAIA](../projects/gaia.md)

Two arrays can have identical shapes and still describe different places. They can also describe the same place while using different band orders, units or validity conventions. A geospatial pipeline needs a data contract that carries these meanings through every transformation.

Work on classification, segmentation and raster export has made these boundary conditions especially important in my projects. A model can run successfully on a malformed input and produce a plausible-looking raster. The absence of an exception is therefore a weak correctness signal.

## A grid is more than a CRS

The coordinate reference system identifies how coordinates are interpreted. The transform, dimensions and pixel convention determine where the raster cells lie. Matching CRS labels alone does not establish pixel alignment.

For example, imagine two invented rasters with the same resolution and dimensions. Move one origin by half a pixel and their corresponding array positions no longer represent the same footprint. Direct subtraction would compare different locations even though the arrays broadcast perfectly.

An explicit reference grid gives each downstream stage a target: CRS, transform, width and height. Reprojection should map observations onto that grid rather than merely editing metadata. Rasterio's reprojection API makes the source and destination spatial definitions explicit. [Rasterio reprojection documentation](https://rasterio.readthedocs.io/en/stable/topics/reproject.html)

~~~mermaid
flowchart LR
    A["Source values and metadata"] --> B{"Contract satisfied?"}
    B -->|yes| C["Declared processing"]
    B -->|no| D["Explain mismatch"]
    C --> E["Output values and metadata"]
    E --> F["Independent readback"]
~~~

## Band positions need meanings

The fourth band is not universally near-infrared. A file can contain an alpha band, a quality mask or a sensor-specific measurement. A model expecting a particular channel order needs a mapping that is checked before inference.

A useful band contract records names, order, units and any scaling or offset. It also identifies the provenance of the interpretation. An explicit override may be necessary for an unusual product, but it should be recorded rather than quietly becoming a new default.

Display imagery and analytic imagery deserve different treatment. A visually attractive contrast stretch changes numerical relationships. Feeding that image into a workflow that assumes physical measurements creates a semantic mismatch, even when the file retains its original spatial reference.

The practical interface is a small declaration that accompanies the data. An engineer reviewing a prediction should be able to answer which physical or derived quantity entered each channel. That answer should not depend on remembering a filename convention.

## Validity is independent of the value zero

A zero value can be a legitimate observation or class identifier. Missing observations need a separate representation. Treating every zero as invalid discards valid data; treating every invalid cell as class zero creates unsupported predictions.

Rasterio exposes masks whose nonzero values identify valid pixels. NumPy masked arrays use the opposite sense for their boolean mask: True identifies masked elements. Crossing that boundary without an explicit conversion is an easy source of inverted validity. [Rasterio mask documentation](https://rasterio.readthedocs.io/en/stable/topics/masks.html)

For a derived index, input validity is necessary but may not be sufficient. The arithmetic can have an undefined denominator. The tutorial includes both an invalid calculation from otherwise usable zero measurements and a valid index value of zero from equal positive bands. These cases must remain distinguishable.

For a model output, validity may mean the input had enough support for inference. That is different from a model being uncertain about the class. A confidence value cannot restore a measurement where no usable source observation existed.

## Transformations should state what they change

Reprojection changes sampling. A cast changes numerical representation. Normalization changes the values presented to a model. Polygonization changes how a raster region is represented geometrically. Each deserves an explicit declaration of preserved and changed properties.

Resampling also depends on meaning. A categorical class raster and a continuous height raster do not have the same interpolation requirements. Choosing an algorithm because it produces a smooth-looking result can create values that have no interpretation in the source vocabulary.

A useful transformation record includes the source identity, output grid, band selection, validity policy and method. It need not contain every temporary pathname. The purpose is to explain the result, not to reproduce an operator's entire machine configuration.

This record becomes particularly valuable during debugging. If an output shifts unexpectedly, a declared target transform narrows the investigation. Without it, the reviewer must reconstruct spatial intent from several unrelated files.

## Test the boundary with independent expectations

Small fixtures are useful because their expected behavior can be calculated directly. An invented raster can contain an invalid corner, a valid zero, a distinctive border and dimensions that leave partial windows. Each feature probes a different failure mode.

The [windowed processing example](../tutorials/windowed-raster-processing.md) reads the finished file back and checks its CRS, transform, dimensions, mask and values. Reopening matters because a writer can produce an in-memory array correctly while persisting incorrect metadata.

The same idea applies to vector results. Check geometry types, units, attribute meanings and missing-value representation after reading the delivery format. A field silently truncated by an interchange format can break a downstream contract without changing the geometry.

## Contracts expose unresolved assumptions

Sometimes the available metadata are insufficient. An unknown CRS or undocumented height reference should remain an unresolved input issue. Guessing may make a command run, but it transfers an invisible assumption into every downstream result.

A contract is useful when it makes that uncertainty visible early. It should give the caller enough information to repair the input or choose a documented transformation. It should not invent geographic meaning to satisfy a type check.

This is also why data validation and scientific validation are separate. A correctly georeferenced output can still be an inaccurate model prediction. Passing the contract establishes that the pipeline preserved declared meaning; it does not establish that the model generalizes to a new region.
