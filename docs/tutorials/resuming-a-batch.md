# Resume a batch after an interruption

[Index](../README.md) · [Article](../articles/resumable-workflows.md) · [Source](../examples/resume_batch.py)

This tutorial makes restart behavior observable with three integer tasks. Each output is `value² × multiplier`. A manifest records completion, and the next run skips a task only when its identity and output both match expectations.

It is an original local demonstration with one writer. It is not a copy of a private orchestration workflow or an implementation of a distributed queue.

## Inject a failure

From the repository root, with [uv installed](https://docs.astral.sh/uv/getting-started/installation/), use a fresh output directory:

~~~text
uv sync --frozen
uv run --frozen python -m docs.examples.resume_batch --output-dir outputs/batch-demo --fail-at 1
~~~

The default inputs are 2, 3, and 4 with multiplier 2. Task zero completes; task one simulates a failure before writing its output. The command intentionally exits with status 1 and reports:

~~~json
{"executed": [0], "skipped": [], "failed": 1}
~~~

Run without the injected failure:

~~~text
uv run --frozen python -m docs.examples.resume_batch --output-dir outputs/batch-demo
~~~

The report is `{"executed": [1, 2], "skipped": [0], "failed": null}`. The three output values are 8, 18, and 32. Running that command once more reports no executed tasks and skips all three verified outputs.

Use a new directory to repeat the initial failure scenario. If task one has already completed with a valid output, it will be skipped before the failure injection can apply.

## Change a dependency

~~~text
uv run --frozen python -m docs.examples.resume_batch --output-dir outputs/batch-demo --multiplier 3
~~~

All tasks rerun because the multiplier forms part of their fingerprints. The results become 12, 27, and 48. Now change only the first input:

~~~text
uv run --frozen python -m docs.examples.resume_batch --output-dir outputs/batch-demo --multiplier 3 --values 7 3 4
~~~

Only task zero reruns, producing 147. A task fingerprint combines the algorithm version, input value, and multiplier. Task indices identify slots, while the fingerprint identifies the computation currently assigned to each slot.

## Follow the completion protocol

Before an attempt, stale completion for that task is removed. The worker writes the output through a temporary file and replaces the destination, then records completion in the manifest through the same atomic-write helper. Python documents the behavior and filesystem constraints of [os.replace](https://docs.python.org/3/library/os.html#os.replace).

Those two replacements are separate operations, not one transaction. A crash between them can leave an orphan output. The next run safely recomputes it. A matching manifest entry with a missing, malformed, or incorrect artifact also triggers recomputation. For this toy operation, the expected output is cheap to verify exactly; real workloads need an appropriate output contract.

Atomic replacement prevents a partially serialized JSON document from becoming the destination under ordinary process interruption. It is not a promise of durability through every storage or power failure, and it provides no multi-writer coordination.

## Test the recovery cases

~~~text
uv run --frozen pytest -q tests/test_examples.py -k "batch or json"
~~~

Tests cover failure and restart, repeated execution, changed inputs, changed parameters, missing and damaged artifacts, orphan outputs, stale completion, and failed JSON serialization.

The example has no parallel workers, locking, remote side effects, or claim of distributed exactly-once execution. Shortening the input list does not delete old output files; only outputs referenced by the current batch should be treated as current results. These limits keep the demonstration focused on a verifiable local restart contract.
