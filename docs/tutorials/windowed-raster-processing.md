# Windowed raster processing with a COG output

[Index](../README.md) · [Article](../articles/memory-bounded-rasters.md) · [Source](../examples/raster_windows.py)

This example computes a normalized difference from a synthetic two-band image, using windows for the processing step. It checks the result against a small whole-array reference and reopens the output to verify its spatial metadata and mask.

## Run it

From the repository root, with [uv installed](https://docs.astral.sh/uv/getting-started/installation/):

~~~text
uv sync --frozen
uv run --frozen python -m docs.examples.raster_windows --output-dir outputs/raster
~~~

The fixture contains 67 rows, 83 columns, and red/NIR-like floating-point channels generated with seed 42. Its projected grid is fictional and does not describe a surveyed location. The dimensions deliberately leave partial windows at the image edges.

## Follow the processing

`create_source` writes a tiled GeoTIFF with a declared CRS, transform, and NoData value. It introduces missing pixels, one undefined zero-denominator pixel, and one valid pixel whose normalized difference is zero.

`process_windows` reads bounded windows and computes `(nir - red) / (nir + red)`. A pixel is valid only when both source bands are valid and finite and the denominator is nonzero. Valid zero values remain valid; missing data uses a separate NoData sentinel.

Each result window is written into a temporary raster with the source grid. After all windows finish, the GDAL COG driver creates the final output. The temporary processing file is removed. Rasterio documents both [windowed reading and writing](https://rasterio.readthedocs.io/en/stable/topics/windowed-rw.html) and the distinction between [valid-data masks and pixel values](https://rasterio.readthedocs.io/en/stable/topics/masks.html).

The normalized difference is pointwise, so it needs no overlap or halo. A neighborhood filter or neural model would need its own boundary policy. The synthetic input generation and reference comparison intentionally load the small fixture into memory; the tutorial demonstrates bounded processing, not an end-to-end benchmark on a large dataset.

## Inspect the result

The command creates `synthetic-source.tif`, `synthetic-index.tif`, and `report.json` in the selected output directory. The report includes:

~~~json
{
  "shape": [67, 83],
  "valid_pixels": 5536,
  "invalid_pixels": 25,
  "whole_array_equal": true,
  "grid_preserved": true,
  "cog_layout": true
}
~~~

The shape and counts are deterministic. The valid zero at row 11, column 11 is preserved. Equality against the reference checks the edge windows as well as the central area. The output retains the source CRS, transform, and dimensions.

The COG driver and `LAYOUT=COG` readback support the layout claim for this fixture. This is not an independent, exhaustive COG conformance test. See the [GDAL COG driver documentation](https://gdal.org/en/stable/drivers/raster/cog.html) for layout options and limitations.

## Change the window size

~~~text
uv run --frozen python -m docs.examples.raster_windows --output-dir outputs/raster-small-windows --window-size 7
~~~

The numerical result should remain unchanged. The tests also cover a window larger than the raster, an entirely invalid image, an undefined ratio, and rejection of a source path reused as the destination.

Use a dedicated output directory: rerunning the command regenerates the example's own named files. To run its checks:

~~~text
uv run --frozen pytest -q tests/test_examples.py -k "raster or index"
~~~

This example establishes numerical and spatial behavior for a small synthetic case. It makes no claim about ecological interpretation, model accuracy, GPU memory, or processing throughput.
