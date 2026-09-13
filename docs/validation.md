# Validation scope

[Documentation index](README.md)

Validation covers the original synthetic examples and ten independently executed public-data notebooks. The notebooks include actual public-data model evaluation with a declared spatial split; those results do not reproduce private project evaluations or establish operational readiness.

## Reproduce the checks

From the repository root with [uv installed](https://docs.astral.sh/uv/getting-started/installation/):

~~~text
uv sync --frozen
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen python scripts/check_docs.py
~~~

Python 3.12 and the dependency versions in `uv.lock` define the example environment. The automated workflow runs these checks on Windows and Ubuntu; its run status is the evidence for each platform, rather than an assumption of universal compatibility.

## Public-data execution

All ten notebooks were executed in fresh Python kernels on Windows, with saved tables and PNG figures. The ResNet18 fine-tune and DeepForest inference also completed on both CPU and an NVIDIA GeForce RTX 5080 Laptop GPU using PyTorch 2.14.0 + CUDA 13.0. A separate environment installed with the frozen `cpu` extra also executed both notebooks using PyTorch 2.14.0+cpu. Each ResNet run completed three epochs on the same 2,999-chip subset. [The execution record](notebook-validation.json) lists per-notebook duration, code-cell counts and visible figures. Durations exclude initial environment installation and use cached data/model downloads.

The wheel notebook builds and installs the package plus locked dependencies in a separate virtual environment outside the checkout, then checks the CLI raster against its reference. Docker execution is checked by the Ubuntu CI job. Check the [workflow status](https://github.com/antonio-linhares-silva/antonio-linhares-silva/actions/workflows/validate.yml) for platform and container evidence.

Public fixtures add source-checksum verification, actual Sentinel calibration/grid checks, raster recovery, and AHN coordinate/classification checks. The local suite now passes **33 tests**. The notebook checker requires ten executed notebooks, sequential execution counts, no error outputs, visible figures, valid local links and pinned data packs under 500 MB.

~~~text
uv run --frozen python scripts/check_notebooks.py
~~~

## What the tests check

| Area | Behavior under test |
| --- | --- |
| Raster processing | Whole-array equality, partial edge windows, valid zeros, missing pixels, all-invalid input, unchanged source, and preserved grid |
| Preprocessing | Disjoint regions, held-out perturbation isolation, constant features, and rejection of invalid training selections |
| Model packaging | Local logging and reload, independent-process loading outside the repository, and invalid input rejection |
| Batch recovery | Restart after failure, verified skipping, input and parameter invalidation, missing/damaged artifacts, orphan outputs, and stale completion |
| Atomic JSON writing | A serialization failure leaves the preceding complete document intact |
| Documentation | Relative links, heading anchors, page reachability, collection counts, and diagram presence |

The initial local run on Windows completed 21 tests. The raster fixture produces 5,536 valid pixels and 25 invalid pixels. The preprocessing fixture has 384 training pixels, 384 held-out pixels, and 192 excluded pixels. The reloaded arithmetic model predicts `[5.0, 7.0]` for its documented inputs. These are synthetic software checks, not operational benchmarks.

The documentation checker parses CommonMark and tables. It can export Mermaid sources for a separate browser-render check:

~~~text
uv run --frozen python scripts/check_docs.py --diagrams-json outputs/diagrams.json
~~~

Diagram presence is checked in CI; successful browser rendering is a separate publication check. All 10 diagrams rendered successfully in Chrome with Mermaid 11.12.2 before publication, and the 17 external documentation/profile links returned HTTP 200. These checks describe that publication run; external sites and GitHub's renderer can change. GitHub documents its [Mermaid rendering support](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams).

## Limits of the evidence

The whole-array raster reference is intentionally tiny. The original synthetic suite includes no peak-memory or independent COG conformance benchmark. The public notebooks add real CPU/GPU execution and spatially separated EuroSAT footprints, but do not measure process peak RSS or establish independence at every geographic or temporal scale.

The MLflow test uses the installed locked environment, even when its process is isolated from project imports. It does not cover arbitrary dependency versions or remote tracking infrastructure. Generated run IDs, timestamps, and package bytes can vary.

The batch example has one writer and local files. Its artifact and manifest updates are distinct replacements. It does not provide multi-writer coordination or guarantee durability through every filesystem or power failure.

Project case studies describe documented contributions at the time of writing. Conceptual articles and diagrams are general explanations, and the public examples were created independently. No private source artifacts or evaluation outputs are required to reproduce this collection.
