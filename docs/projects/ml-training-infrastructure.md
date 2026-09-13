# ML Training Infrastructure

[Documentation index](../README.md) · [Model artifact article](../articles/model-artifacts-mlflow.md) · [Shipping GeoAI](../articles/shipping-geoai.md)

**Project:** mltrain-ovh-terraform. **Role:** infrastructure and bootstrap development. **Status:** private compute-environment project.

## Problem and project scope

Training environments combine GPU availability, system dependencies and large persistent datasets. Recreating those pieces manually makes recovery slow and leaves the configuration dependent on the machine's history.

The project describes cloud compute and attached storage through infrastructure as code, with bootstrap work for the runtime environment. Its scope includes handling the distinction between compute availability and persistence of training data.

## My contribution

My work includes the initial Terraform stack, training-environment configuration and startup/bootstrap scripts. These changes support rebuilding a usable environment without treating the compute instance as the only copy of the experiment's state.

The contribution is operational infrastructure. It does not establish performance advantages for a particular GPU, training method or model, and this page does not publish internal resource sizing.

## Conceptual architecture

Declared compute and storage → runtime bootstrap → verified training environment → experiment execution → persistent datasets and model artifacts.

**Technologies:** Terraform, cloud GPU infrastructure, Linux, NVIDIA/CUDA tooling and geospatial Python environments.

## Engineering decisions and limits

Compute and storage have different lifecycles. A capacity issue or instance replacement should not automatically imply loss of datasets and model artifacts. That separation must be reflected in infrastructure state and in recovery procedures.

Bootstrap success also needs a concrete meaning. Installing a package is different from confirming that the intended runtime can see the GPU and import its geospatial dependencies. A useful smoke test checks the environment that will execute the work.

Reproducibility remains bounded by driver, library and hardware compatibility. Infrastructure as code makes configuration visible; it does not remove those constraints or guarantee that a provider has capacity.

The public documentation excludes credentials, machine inventories, network details, costs and deployment commands. The linked articles discuss generic packaging and artifact-lifecycle principles that apply without exposing the private environment or encouraging readers to provision paid resources for the tutorials.
