# Managing Model Artifacts with MLflow

[**Run the public-data notebook**](../../notebooks/06-model-artifacts-mlflow.ipynb) ? [Notebook setup](../../notebooks/README.md)

[Documentation index](../README.md) · [Land Use Land Cover](../projects/land-use-land-cover.md) · [MLflow infrastructure](../projects/mlflow-infrastructure.md)

A checkpoint is only one part of a usable model. An inference workflow also needs its preprocessing assumptions, expected feature order, loading code and compatible environment. Losing any of those can make a stored artifact difficult to reproduce even when the weight file itself is intact.

My work includes MLflow integration in geospatial packages, model-loading support and infrastructure for experiment tracking. This article describes the responsibilities around those components, using a generic architecture rather than an internal service configuration.

## Package the execution contract

A useful model package answers what it accepts, what it returns and what must be loaded before prediction. For a multispectral model, that includes channel order and input representation. For a conventional classifier, it may include a wrapper that adapts array types and device behavior.

The loading boundary is a natural place to reject incompatible artifacts. A model that expects a feature schema should not accept a different schema solely because the input happens to contain the same number of columns.

MLflow's PythonModel interface provides hooks for loading contextual artifacts and performing prediction. The accompanying tutorial uses those hooks for a tiny arithmetic model whose coefficients live in a JSON artifact. [MLflow PythonModel guide](https://mlflow.org/docs/latest/ml/model/python_model/)

~~~mermaid
flowchart LR
    A["Run metadata"] --> B["Versioned model package"]
    C["Artifact files"] --> B
    D["Input contract and environment"] --> B
    B --> E["Resolve version"]
    E --> F["Verify or populate cache"]
    F --> G["Load and predict"]
~~~

## Distinguish metadata from artifacts

Experiment metadata describe runs, parameters and identities. Artifact storage holds the files that a run or model needs. These roles are connected, but restoring only one does not necessarily restore a usable experiment.

MLflow documents its backend store separately from its artifact store. A local SQLite database can hold tracking metadata while a local directory holds the tutorial's model files. [MLflow backend stores](https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/)

In a larger system, the same distinction helps frame backup and access requirements. Metadata need to preserve the references that explain the experiment. Artifact storage needs to preserve the bytes those references identify. Recovery should be tested by loading a model, not just by checking that a database starts.

The infrastructure projects also highlight a related separation: a compute instance can be temporary while experiment data remain persistent. That separation reduces the coupling between an interrupted machine lifecycle and the continued availability of model artifacts.

## Resolve a version before doing expensive work

A convenient alias can identify the model a caller wants to use. Its meaning may change later. Recording the resolved immutable version at the start of a run makes the result explainable after that change.

A cache should use a similarly precise identity. If it is keyed only by a friendly model name, one version can accidentally stand in for another. The cache entry should also have an integrity or completeness check so an interrupted download is not accepted as a finished model package.

The practical failure mode is subtle: an inference run appears reproducible because its configuration has not changed, but a mutable alias now resolves to different bytes. Recording both the requested alias and resolved version separates user intent from execution provenance.

## Environment compatibility is a tested property

Serializing an object does not erase its dependencies. A wrapper using GPU arrays may still import a GPU library during module loading, even if a command exposes a CPU option. Public documentation should describe tested environments rather than infer compatibility from the name of a flag.

This distinction matters for the LULC case study. The project contains CPU/GPU-oriented interfaces and environment definitions, but this portfolio does not claim that every package version imports or executes in every CPU-only environment. The public example is deliberately independent of that private dependency graph.

The same care applies to model serialization. A package should be loaded in a clean environment that resembles its intended consumer. A successful load inside the developer's existing process can conceal modules or files that were never included in the artifact.

## Make a smoke test small and meaningful

The [local MLflow tutorial](../tutorials/local-mlflow-model.md) stores a two-coefficient weighted sum. After loading the package, two rows must produce exactly the expected outputs. The calculation is deterministic and does not require training data or a GPU.

This example exercises artifact loading, input signature and prediction behavior. It does not establish any predictive accuracy, registry governance or server security. Keeping the model trivial helps isolate whether packaging is correct.

A useful additional check uses malformed input. The model should reject the wrong feature count or non-finite values with an understandable error. An exception deep inside a matrix multiplication may be technically correct, but it is a poor interface for a caller trying to diagnose a contract mismatch.

## Treat distribution as another boundary

A model can arrive through a registry, a file bundle or a container image. Each distribution path must preserve the same package identity and input contract. A cached file or container layer is not a substitute for documenting which model it contains.

Large-file storage adds another failure mode: a checkout may contain a pointer instead of the model bytes. Git LFS explicitly separates the small Git-tracked pointer from the large stored object. Loading the artifact during a build or smoke test can expose an incomplete materialization. [Git LFS](https://git-lfs.com/)

The resulting engineering story is about connecting model identity, environment and execution. Versioning is useful when it allows a reader to trace a prediction back to a specific package and reproduce the loading path. A collection of model filenames alone cannot provide that chain.
