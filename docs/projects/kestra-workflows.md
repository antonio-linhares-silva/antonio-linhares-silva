# Kestra Geospatial Workflows

[Documentation index](../README.md) · [Recovery article](../articles/resumable-workflows.md)

**Project:** spotlite-kestra-workflows. **Role:** proposed workflow and queue contribution. **Status:** pull request under review as of 13 September 2026.

## Problem and project scope

Long geospatial batches need a reliable relationship between source discovery, processing, delivery and completion. Without durable progress, a later failure can cause previously completed inputs to be rediscovered and processed again.

The existing project provides an orchestration layer around geospatial processing components. My proposed contribution extends that context with queue and recovery behavior for canopy-related jobs.

## My contribution

The open pull request contains work on idempotent queues, source identity, completion records, reconciliation and explicit retry behavior. It also includes resource-awareness and monitoring-related work around the execution of processing containers.

This status is important: the contribution was not merged into the main branch when this documentation was prepared. The page describes implemented work submitted for review, rather than presenting the proposed behavior as the state of the main branch.

## Conceptual architecture

Discover source → identify task → coordinate execution → validate output → publish result → record completion → reconcile on later runs.

**Technologies:** Kestra, Python helpers, containerized geospatial processing and persisted workflow state.

## Engineering decisions and limits

A source filename is insufficient to prove that a result can be reused. Task identity should capture the input and result-affecting decisions, while completion should follow successful output validation.

Coordination also has a scope. A local sequential example and a queue coordinating external services have different failure modes. The public tutorial demonstrates only the former; it is not a reconstruction of the private queue implementation.

The collection omits workflow files, integration endpoints, storage identifiers, alert destinations, resource limits and internal benchmarks. It makes no claim of distributed exactly-once delivery.

The [batch recovery tutorial](../tutorials/resuming-a-batch.md) uses invented integer tasks to demonstrate interruption, verified skipping and invalidation. That small example lets readers inspect the underlying reasoning without access to private orchestration or company accounts.
