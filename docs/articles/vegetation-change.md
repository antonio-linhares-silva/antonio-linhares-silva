# Interpreting Vegetation Change

[**Run the public-data notebook**](../../notebooks/09-vegetation-change.ipynb) ? [Notebook setup](../../notebooks/README.md)

[Documentation index](../README.md) · [Forest cut classifier](../projects/forest-cut-classifier.md) · [Canopy delineation](../projects/canopy-delineation.md)

Subtracting two rasters produces a difference. Interpreting that difference as vegetation change requires more evidence. Acquisition conditions, coverage, alignment and preprocessing can all change the measurements without corresponding to the event a user wants to detect.

My work includes vegetation-change processing, handling of missing values and integration of review-oriented outputs. This article discusses the reasoning around those workflows. It does not publish internal decision thresholds, client areas or measured detection performance.

## Comparability precedes subtraction

The two observations should have documented sensor and product meaning, compatible spatial support and understood scaling. Matching a product label is not enough if processing conventions changed between acquisitions.

Spatial alignment is another separate requirement. A shifted canopy boundary can create a ring of apparent loss and gain even when the tree remains unchanged. Checking array dimensions and CRS labels does not detect every registration problem.

For a public teaching example, comparability can be established by constructing both observations on the same synthetic grid. A real application must establish it from metadata and appropriate checks. The convenience of a subtraction operator does not remove that responsibility.

~~~mermaid
flowchart LR
    A["Observation at time one"] --> C["Check comparability"]
    B["Observation at time two"] --> C
    C --> D["Common valid support"]
    D --> E["Compute change evidence"]
    E --> F["Review candidates"]
    F --> G["Confirm with suitable evidence"]
~~~

## Coverage defines where a comparison exists

A pixel observed at only one date cannot support an ordinary two-date difference. A common valid mask is therefore part of the comparison. The mask should account for missing measurements and other exclusions relevant to the chosen products.

Invalid observations should not be converted into a no-change class. That conversion reduces the apparent amount of missing information and can bias area summaries. Similarly, an unobserved crown should not be classified as removed solely because it has no match in the second observation.

A useful output distinguishes stable observations, change candidates and insufficient evidence. The distinction is a data contract for downstream users. A binary layer may be convenient for display, but the underlying uncertainty should not disappear.

## Sign and denominator belong in the explanation

For a difference between two indices, the sign depends on the order of subtraction. A report should state that order. Otherwise a negative value can be described as loss in one stage and gain in another.

Area percentages also need an explicit denominator. A fraction of the entire area and a fraction of the commonly observed area answer different questions. If clouds or missing coverage exclude part of a polygon, silently changing the denominator can make two reports difficult to compare.

In an invented region of 100 cells, suppose only 60 are observed at both dates and 12 show the chosen difference. That is 20 percent of the common observed support and 12 percent of the complete region. Neither number alone describes the unobserved 40 cells.

## Separate a signal from an explanation

A vegetation-index decrease can be consistent with several causes. Seasonal behavior, illumination, atmospheric effects and physical disturbance can all contribute. The index is evidence about the observation, not a complete causal explanation.

The same restraint applies to object matching. A crown can split into several polygons, merge with a neighbor or fail to be detected. A missing one-to-one match does not prove removal. Matching rules should retain unresolved cases rather than forcing every object into a confident event class.

This is why review-oriented labels are useful. They communicate that the pipeline has identified a candidate for inspection. A confirmed operational event requires evidence appropriate to the application and should remain distinguishable from the automated candidate.

## Validation needs an independent reference

A known synthetic modification can test sign conventions, masks and aggregation. It cannot establish performance on real vegetation. A real accuracy assessment needs reference information collected and interpreted independently of the prediction being assessed.

The reference should cover unchanged areas as well as candidate changes. Inspecting only conspicuous detections makes it difficult to estimate missed events or false alarms across the wider area. Temporal agreement also matters: the reference must describe the period being compared.

Evaluation should reflect the intended output unit. Pixel differences, event polygons and matched tree objects have different error structures. An aggregate area statistic cannot replace object-level review when the operational question concerns individual trees.

## Preserve information through export

The output format should carry enough context to interpret each result: observation dates, validity state and the meaning of the change field. A derived layer that loses those attributes becomes easier to misread when separated from its original report.

Post-processing deserves the same scrutiny as the initial difference. Filling holes, smoothing boundaries or assigning a default class can change coverage and area. A visually cleaner result is not necessarily a more faithful comparison.

In the forest-cut project, the portfolio emphasizes contributions to workflow integration and missing-value handling. It does not assume that every historic classification convention is a universally appropriate interpretation of missing data. The scientific meaning of a particular output must be checked against its implementation and intended use.

## Make the supported claim explicit

A practical workflow can say that it computed a declared difference over common valid support and generated review candidates under a documented method. A stronger claim about confirmed cutting, pruning or recovery requires stronger evidence.

That distinction does not reduce the value of automation. It makes the output easier to combine with field observations, human review and other sources. The useful engineering result is a comparison whose support and uncertainty remain visible after processing.

For the spatial assumptions underlying this discussion, see [geospatial data contracts](geospatial-data-contracts.md). For the project context, see the [forest-cut case study](../projects/forest-cut-classifier.md).
