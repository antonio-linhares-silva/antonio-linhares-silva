# Processing Large Rasters Within a Memory Budget

[**Run the public-data notebook**](../../notebooks/02-memory-bounded-rasters.ipynb) ? [Notebook setup](../../notebooks/README.md)

[Documentation index](../README.md) · [Canopy delineation](../projects/canopy-delineation.md) · [Canopy height](../projects/canopy-height.md)

A pipeline can process every tile successfully and still fail when it assembles the final raster. Tiling the model input solves only one part of the memory problem. Preprocessing, prediction queues, merge buffers and vectorization can each become the largest allocation in the run.

My canopy-processing work includes changes to memory-bounded merging and recovery of interrupted inference. The general lesson is to budget the complete execution path. This article uses invented examples and does not publish operational settings or private performance measurements.

## Estimate the arrays you actually hold

For a dense array, the basic storage estimate is width × height × bands × bytes per value. A hypothetical 12,000 by 12,000 image with four float32 bands needs about 2.15 GiB for that array alone. Keeping an input, normalized copy and output simultaneously can multiply the working set before library caches or model activations are considered.

The calculation is an accounting aid, not a peak-memory prediction. Views can share storage; conversions can create copies; compression buffers can be temporary. The useful question is which arrays coexist at a particular stage. Reviewing lifetimes often reveals a larger saving than reducing a single array's precision.

~~~mermaid
flowchart LR
    A["Read bounded window"] --> B["Prepare channels"]
    B --> C["Predict bounded batch"]
    C --> D["Write intermediate result"]
    D --> E["Merge bounded output region"]
    E --> F["Validate final grid and mask"]
~~~

Memory also belongs to the host. A worker that independently budgets most of the available RAM is reasonable in isolation and dangerous when several workers do the same thing. Concurrency and per-worker allocations must be considered together.

## Windows bound arithmetic, blocks shape I/O

Reading a window limits the requested array. Storage blocks still determine what must be fetched and decoded underneath. Aligning access patterns with block structure can avoid repeatedly reading the same compressed data. Rasterio documents this difference between logical windows and physical blocks. [Rasterio windowed reading and writing](https://rasterio.readthedocs.io/en/stable/topics/windowed-rw.html)

A pointwise operation can process disjoint windows directly. A neighborhood operation needs surrounding context. Convolutional inference, local filtering and some polygonization steps therefore need a halo or overlap policy. Without one, a perfectly valid sequence of array operations can produce seams at tile boundaries.

Overlap has a cost: more pixels are processed than appear in the final image. That cost should be evaluated alongside the quality of the boundary result. A larger tile is not automatically better; it may reduce overlap overhead while creating a memory peak that limits concurrency.

## Treat merging as an algorithm

A merge should specify which contributions reach each output pixel and how overlapping contributions are combined. It also needs a validity rule. An uncovered cell should not become a confident background prediction because an accumulator was initialized to zero.

For a weighted average, a conceptual implementation tracks a weighted sum and a support sum. The output is defined only where support is positive. This is a general teaching pattern; the weighting function and model-specific interpretation require their own validation.

The memory advantage comes from processing an output slab or block at a time, gathering only intersecting contributions, writing the result and releasing the working buffers. A spatial index over tile extents can reduce unnecessary scanning. The correct optimization target is the largest simultaneously live set, including temporary reductions.

Deterministic traversal matters when floating-point reductions are involved. Equivalent inputs can produce tiny numerical differences under different accumulation orders. Tests should distinguish tolerable numerical variation from changes in mask, coverage or class decisions.

## GPU memory and host memory are different budgets

GPU batching controls model execution, while CPU staging and final output processing can remain host-bound. Moving a batch to the GPU may briefly retain both host and device copies. Prefetching can improve utilization while increasing the number of live batches.

The PyTorch CUDA documentation distinguishes memory occupied by tensors from memory managed by its caching allocator. These signals answer different questions and should not be treated as interchangeable measurements. [PyTorch CUDA memory management](https://docs.pytorch.org/docs/stable/notes/cuda.html#memory-management)

An adaptive batch size is useful only if failure is handled deliberately. A retry should reduce the relevant workload and retain an unambiguous record of which outputs are complete. Repeating a failed allocation without changing the workload is unlikely to improve the next attempt.

## Verify equivalence before celebrating savings

A smaller peak is valuable when the intended output is preserved. A comparison should include dimensions, transform, CRS, valid-data coverage and representative numerical values. For categorical products, the label domain and boundary behavior also matter.

The [windowed raster tutorial](../tutorials/windowed-raster-processing.md) uses a tiny fixture where a whole-array calculation is affordable. It compares that oracle with windowed arithmetic and independently reads back the output. This checks the spatial and numerical contract, not the throughput of a real inference system.

Tests should include dimensions that do not divide evenly by the window size. Otherwise, a loop can pass every ordinary tile and still truncate the bottom or right edge. Empty windows, invalid-only scenes and valid zero-valued results expose a different class of silent errors.

## Keep performance claims attached to conditions

Runtime depends on more than array size: storage layout, compression, CPU availability, GPU model, caching and concurrency all contribute. A useful report identifies the workload and compares equivalent outputs. A single successful run does not establish a universal memory ceiling.

The transferable contribution is a method for controlling allocation and testing recovery. It is not a claim that a particular budget is suitable for every sensor, model or machine. The companion article on [resumable workflows](resumable-workflows.md) explains how persisted state helps recover when a long-running stage still fails.
