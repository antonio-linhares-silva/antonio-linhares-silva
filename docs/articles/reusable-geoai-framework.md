# Designing a Reusable GeoAI Framework

[**Run the public-data notebook**](../../notebooks/01-reusable-geoai-framework.ipynb) ? [Notebook setup](../../notebooks/README.md)

[Documentation index](../README.md) · [GAIA project](../projects/gaia.md) · [Land Use Land Cover](../projects/land-use-land-cover.md)

A reusable GeoAI framework earns its value when a second task can reuse the engineering without inheriting the first task's assumptions. A tree-crown detector and a land-cover classifier may both read satellite imagery, yet they disagree about labels, output shapes, batching and evaluation. Treating those differences as configuration alone usually moves complexity into invisible conventions.

My experience co-developing GAIA and Land Use Land Cover has involved this boundary between shared infrastructure and task-specific behavior. This article explains the engineering questions behind that work. The diagram is a conceptual teaching model, not a representation of an internal deployment.

## Start with the boundary of a sample

A dataset adapter should make a sample understandable without knowing the original folder layout. The important questions include which bands are present, how invalid pixels are represented, which split owns the sample, and what spatial metadata must accompany it. An array is only part of that answer.

For segmentation, the target may be a class value for every valid pixel. For detection, it may be a variable-length collection of objects. Super-resolution adds a relationship between two grids. A framework can share discovery and metadata handling while keeping these target contracts separate. The alternative is a universal sample object with so many optional fields that incorrect combinations become easy to construct.

~~~mermaid
flowchart LR
    A["Dataset adapter"] --> B["Sample and metadata"]
    B --> C["Task-specific preprocessing"]
    C --> D["Model adapter"]
    D --> E["Task-specific result"]
    E --> F["Evaluation or spatial export"]
    G["Resolved configuration"] --> A
    G --> C
    G --> D
~~~

The practical benefit of this separation is local reasoning. A change to a dataset's band mapping should not require editing the evaluator. A change to model architecture should not silently replace the output grid. Each boundary has something concrete to validate.

## Share mechanisms, preserve semantics

Logging, run directories, checkpoint discovery and configuration loading are useful shared mechanisms. Label meanings, geometric conventions and evaluation units belong to the task. This distinction reduces duplicated infrastructure without pretending that every model has the same interface.

In a hypothetical framework, a segmentation adapter could return probabilities plus a validity mask, while a detection adapter returns objects in image coordinates. Both can report the source grid and task identity. Spatial export then performs the appropriate conversion rather than guessing from an array's dimensions.

PyTorch distinguishes dataset access from the mechanisms that load and batch samples. That is a useful existing boundary to build on, instead of replacing the entire data-loading stack with framework-specific machinery. [PyTorch data loading documentation](https://docs.pytorch.org/docs/stable/data.html)

Another useful distinction is between a configurable capability and a supported combination. Listing two models and two datasets does not establish that every pairing has compatible bands, targets or losses. A small explicit compatibility check is easier to explain than allowing a mismatched run to fail after expensive preparation.

## Configuration is an input to execution

A configuration file records intent. The executed configuration also includes resolved paths, selected defaults and command-line overrides. When these are different, a reviewer needs the resolved version to understand what actually happened.

Consider an invented experiment that asks for four bands but points to a three-band sample. A good failure happens while validating the sample contract. Padding the missing channel with zeros would create a new scientific assumption. Unless that is a deliberate, documented transformation, it should not be an accidental convenience.

Configuration validation should therefore check relationships, not just field types. The number of normalization values must match the selected channels. The label vocabulary must agree with the model output. A spatial export needs a reference grid. These checks turn implicit coupling into readable errors.

The size of a configuration also matters. Exposing every internal parameter produces a large compatibility surface. A smaller set of meaningful choices, accompanied by a record of resolved behavior, is often more maintainable than a configuration file that mirrors every function signature.

## Extension points need small examples

A framework is easier to extend when adding a dataset or model requires a short, task-focused adapter. A useful example contains one invented sample and an explicit expected result. It should exercise the same interface as a real adapter without downloading a large dataset or requiring access to private assets.

The corresponding test should ask whether the adapter fulfills the contract. Does the segmentation target match the image extent? Does a detection result carry the correct coordinate convention? Does a super-resolution pair describe its scale relationship? Testing only that a class can be instantiated misses the behavior that downstream code depends on.

I also find it useful to distinguish framework tests from model tests. A deterministic dummy model can verify batching, metadata propagation and export. That does not measure a learned model's accuracy, but it can isolate an infrastructure regression that would otherwise look like a modeling problem.

## Recognize the cost of generality

Every shared abstraction adds a maintenance obligation. If two workflows differ only superficially, sharing a helper is straightforward. If they have different failure handling, spatial assumptions and output semantics, forcing them through one pipeline can make both harder to understand.

A practical review question is whether a new task uses the abstraction naturally or spends most of its adapter disabling inherited behavior. Frequent exceptions suggest the boundary is too broad. Splitting the abstraction can be a simplification even if it increases the number of classes.

GAIA is presented here as a prototype for applied experimentation. Its breadth does not establish that every configuration is equally mature or independently validated. The useful portfolio evidence is the work on reusable components, task integration and explicit interfaces. Production readiness remains a separate claim requiring task-specific validation and operating evidence.

Continue with [geospatial data contracts](geospatial-data-contracts.md) for the invariants that these interfaces must carry.
