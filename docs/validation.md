# Validation scope

[Documentation index](README.md)

The public examples are small, deterministic demonstrations of software behavior. Validation covers their declared contracts and the navigation through this collection. It does not reproduce private project evaluations or establish model accuracy.

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

The whole-array raster reference is intentionally tiny. No peak-memory, GPU, throughput, or independent COG conformance benchmark is included. The synthetic region gap does not establish geographic independence for real imagery.

The MLflow test uses the installed locked environment, even when its process is isolated from project imports. It does not cover arbitrary dependency versions or remote tracking infrastructure. Generated run IDs, timestamps, and package bytes can vary.

The batch example has one writer and local files. Its artifact and manifest updates are distinct replacements. It does not provide multi-writer coordination or guarantee durability through every filesystem or power failure.

Project case studies describe documented contributions at the time of writing. Conceptual articles and diagrams are general explanations, and the public examples were created independently. No private source artifacts or evaluation outputs are required to reproduce this collection.
