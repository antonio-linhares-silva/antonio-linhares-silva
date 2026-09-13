# Resumable Geospatial Workflows

[Documentation index](../README.md) · [Kestra workflows](../projects/kestra-workflows.md) · [Canopy delineation](../projects/canopy-delineation.md)

When a long batch fails near the end, restarting from the beginning wastes time and can create duplicate products. Skipping every output that already exists has the opposite problem: partial or obsolete results can be mistaken for completed work. Resuming correctly requires evidence about both the computation and its output.

My work includes recovery in canopy inference and a proposed Kestra contribution for idempotent batch queues. The Kestra contribution was still in an open pull request when this collection was prepared on 13 September 2026. It is described as work under review, without implying integration into the main branch.

## Define the unit of completion

The first decision is what a task means. It might be one scene, one tile or one model applied to one source. If a batch produces both a height raster and crown polygons, completion of one product should not silently imply completion of the other.

Task identity needs enough information to distinguish results that could differ. A source fingerprint, algorithm version and result-affecting configuration are natural ingredients. A pathname alone is weak evidence because a file can be replaced without changing its name.

Execution settings deserve separate treatment. Increasing a logging level should not invalidate a correct result. Changing selected bands should. A worker count might or might not affect numerical output, depending on the algorithm. The decision belongs to the computation's contract rather than a universal list of ignored settings.

~~~mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> Running
    Running --> Validating
    Running --> Failed
    Validating --> Completed
    Validating --> Failed
    Failed --> Pending: explicit retry
    Completed --> Pending: changed input or invalid output
~~~

## Completion follows validation

The safe sequence is to produce an output, check it, publish it to its intended location and then record completion. A process exit code is useful evidence but cannot replace an output check. A successful command may still have produced an empty file or a raster with the wrong grid.

For a local result, validation can inspect dimensions, expected fields, validity masks and a content checksum. For a remote delivery, it must also account for the acknowledgment from the destination. The public example stops at local files; it does not simulate a cloud provider's consistency or retry behavior.

There is usually a gap between publishing an artifact and recording completion. A crash in that gap should lead to reconciliation or safe recomputation. It should not require assuming that the two writes were a transaction when they were not.

## Atomic replacement has a limited job

Writing a small manifest to a temporary file and replacing the old document reduces the chance of observing a half-written JSON file. The temporary file should live on the same filesystem as the destination. Python documents replacement semantics and the possibility of failures across filesystems. [Python file replacement](https://docs.python.org/3/library/os.html#os.replace)

That mechanism does not turn several files into one transaction. It also does not solve concurrent writers, remote uploads or every power-loss scenario. The tutorial therefore explicitly supports one writer per output directory. A production queue with concurrent consumers needs additional coordination.

This distinction helps keep an example honest. A short local demonstration can explain ordering and recovery very well. Calling it a distributed exactly-once system would promise properties it has never implemented.

## Reconciliation makes state useful

Persisted state should be checked against the artifacts it describes. Suppose a task has a completion record but its output is missing. A resume operation should schedule the task again. If the output is present but its contents are corrupt, the same principle applies.

Conversely, an artifact can exist without a completion record after an interrupted write sequence. A reconciler can verify and adopt it, or a simpler workflow can recompute it safely. Both are reasonable designs when their costs and semantics are explicit.

The [batch recovery tutorial](../tutorials/resuming-a-batch.md) chooses recomputation for that case. It also invalidates results after input or multiplier changes. It does not use a filename as proof that an earlier computation is still relevant.

## Retry policy should preserve diagnosis

Not every failure is transient. Retrying an unavailable download can make sense; repeatedly submitting an invalid CRS or missing band cannot fix the input. Error categories should guide what happens next.

A useful failure record tells an operator which stage failed and whether prior outputs are reusable. It should avoid exposing credentials or sensitive command arguments. When a pipeline has multiple stages, the recovery boundary should be visible rather than hidden in an exception handler.

Unlimited retries can turn a small failure into a resource problem. A bounded attempt policy, clear terminal state and deliberate manual retry path are easier to operate. Backoff and rate limiting become relevant when an external service is involved, but they are outside the local teaching example.

## Test crashes as ordinary scenarios

The most useful recovery tests are about transitions: failure before output, failure after output, missing completed output, corrupt output and changed input. A test that only reruns a successful batch establishes very little about interrupted execution.

The public example deliberately fails before its second result is written. On the next invocation, the verified first result is skipped and the remaining work completes. A subsequent parameter change invalidates all affected tasks. The expected executed and skipped indices are documented and tested.

For a real spatial pipeline, the same reasoning must extend to the scientific state: source grid, mask, model artifact and processing configuration. Durable progress is valuable when it preserves meaning as well as computation. A fast restart that reuses incompatible results is a correctness failure, even if it appears operationally convenient.
