# MLflow Infrastructure

[Documentation index](../README.md) · [Model artifact article](../articles/model-artifacts-mlflow.md)

**Project:** mlflow-ovh-terraform. **Role:** infrastructure implementation and persistence fixes. **Status:** private infrastructure-as-code project.

## Problem and project scope

Model tracking needs persistent metadata and artifact storage beyond the lifetime of an interactive session. A repeatable deployment also needs to describe how the service starts and how its storage is attached.

The project uses Terraform and cloud bootstrap configuration to provision an MLflow-oriented environment. This public page describes component responsibilities, without exposing network topology, credentials, service addresses or resource identifiers.

## My contribution

My work includes the infrastructure implementation and fixes to storage-mount persistence across reboots. The focus is on connecting provisioned resources with a service that can continue to find its data after a machine lifecycle event.

These contributions concern infrastructure and operation. They do not imply that provisioning alone establishes availability targets, backup completeness or the scientific validity of models stored in the service.

## Conceptual architecture

Declared infrastructure → provisioned compute and persistent storage → service bootstrap → experiment metadata and model artifacts → package consumers.

**Technologies:** Terraform, OVH/OpenStack-related providers, Linux service management, MLflow and object storage.

## Engineering decisions and limits

A storage volume being present does not mean that the intended filesystem is mounted when the service starts. Startup ordering and persistence configuration are therefore part of the service's data contract.

Metadata and model artifacts also have different storage roles. A recovery exercise should establish that a model can be loaded, rather than merely checking that an endpoint responds.

The public collection uses a local SQLite database and local files in its MLflow tutorial. That example demonstrates the separation of responsibilities without reproducing the cloud deployment or requiring a paid account.

This case study makes no uptime, security-certification or disaster-recovery guarantee. It omits operational topology, account settings and deployment commands. The relevant portfolio evidence is the use of declarative infrastructure, explicit persistent storage and reproducible service setup to support model-management workflows.
