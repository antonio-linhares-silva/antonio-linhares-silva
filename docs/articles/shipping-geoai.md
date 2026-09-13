# Shipping GeoAI: From Notebooks to Containers

[Documentation index](../README.md) · [Annotation tool](../projects/annotation-tool.md) · [Legacy canopy workflow](../projects/canopy-shadow-legacy.md)

A notebook can explain an experiment well while still being difficult for another person to operate. Hidden state, absolute paths and manually installed libraries become problems when the same workflow must run on a new machine or recover from a failure.

My contributions across annotation, shadow processing and legacy canopy workflows include packaging, command-line interfaces, tests and container delivery. I have also contributed documentation and packaging support to collaborative InSAR work. Those contributions should not be confused with authorship of every underlying model or scientific method.

## Extract the execution contract

Before reorganizing files, identify what the workflow consumes and produces. A command needs a finite set of inputs, documented outputs and meaningful failures. An operator should not need to inspect a notebook cell to discover that a checkpoint must be copied to an unrelated directory.

The extraction process also reveals hidden dependencies between steps. A variable created during an earlier interactive session may be doing real work that the visible notebook no longer explains. Restarting the kernel and running from the beginning is a useful diagnostic before turning the sequence into a script.

The first executable version can stay small. A focused command with explicit paths and a clear output directory is more useful than introducing a large service before the underlying workflow has a stable boundary.

~~~mermaid
flowchart LR
    A["Exploratory notebook"] --> B["Explicit inputs and outputs"]
    B --> C["Importable processing code"]
    C --> D["CLI and focused tests"]
    D --> E["Installed package"]
    E --> F["Container smoke test"]
~~~

## Keep the interface separate from the computation

A CLI should translate user input into a well-defined processing call. Argument parsing, progress messages and exit codes belong at that boundary. Core functions should remain callable by tests or another package without reproducing the command-line environment.

This separation makes error handling clearer. A function can explain that required spatial metadata are missing; the CLI can turn that error into an actionable message and unsuccessful exit. Catching every exception and continuing would make an incomplete output look successful.

A useful command also states what happens on rerun. Does it reject an existing destination, create a new run directory or resume verified stages? Leaving this implicit encourages callers to invent their own cleanup procedure, which can destroy the very artifacts needed for diagnosis.

## Native dependencies need deliberate packaging

Geospatial Python environments often combine Python packages with native libraries. GDAL and PROJ compatibility can therefore depend on how the environment was assembled. A Python version pin alone does not document the full runtime.

A container offers a way to package that runtime, but its existence is not proof of portability. The image still needs to be built, installed and exercised through the same command that a user will run. Testing imports is useful; processing a tiny synthetic fixture checks more of the contract.

Docker documents the trade-off between mutable image tags and digest-pinned base images, as well as the importance of controlling build context and dependencies. These are useful foundations for reproducible packaging, with an explicit process for refreshing the pinned inputs. [Docker build guidance](https://docs.docker.com/build/building/best-practices/)

## Check assets inside the delivered package

A source checkout can contain files that are absent from the installed package. Configuration templates, model definitions and other runtime resources need explicit inclusion. Running tests from the repository root can accidentally hide those omissions.

A clean installation test should run outside that root. The same principle applies to a container: inspect the filesystem and load the required artifact inside the built image rather than relying on a developer's mounted directory.

Large model assets need particular care because a text pointer can occupy the expected filename. A file-existence test passes, while the actual model loader fails. The meaningful test asks whether the delivered artifact can be interpreted by its intended loader.

This portfolio's MLflow tutorial uses a self-contained model source file and a tiny coefficient artifact. A separate-process test loads the package from outside the repository, making the package boundary observable without distributing private checkpoints.

## Choose tests that represent operational failures

An end-to-end test on a small fixture can verify the command, output format and spatial metadata. Focused tests can then isolate invalid inputs, empty masks and path handling. Both are useful; a large collection of tests that only mirrors helper implementations is less convincing.

Package tests should distinguish optional features. A CPU-only installation should not be declared supported merely because a parser accepts a CPU flag. Imports and a representative execution need to succeed in that actual environment.

Release automation should build on those checks. A version label, container tag and package version should refer to the same intended release. Otherwise a reported bug can be difficult to reproduce because the visible identifiers disagree.

## Document operations as part of the interface

An operator needs to know which outputs are authoritative, which files are temporary and which records explain a failed run. Logging should preserve useful stage information without dumping sensitive arguments or credentials.

Troubleshooting is most effective when organized around symptoms. A missing checkpoint, incompatible native library and empty spatial overlap are different problems. Giving all three the same suggestion to reinstall dependencies hides useful diagnosis.

The public project pages describe the engineering scope without reproducing internal installation instructions. The standalone tutorials have their own small environment and explicit expected results. This allows a reader to evaluate the principles without gaining access to company infrastructure.

## A release claim needs a boundary

Passing a smoke test establishes behavior for that fixture and environment. It does not certify model accuracy, every deployment platform or every input product. A useful release record states the tested boundary and known limitations.

The work of turning research into usable software is largely about making these boundaries visible. Explicit contracts, installable resources and representative tests let another engineer reason about a workflow before committing a large dataset or a long compute job to it.
