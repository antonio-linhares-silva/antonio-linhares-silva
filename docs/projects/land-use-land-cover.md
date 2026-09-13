# Land Use Land Cover

[Documentation index](../README.md) · [Model artifact article](../articles/model-artifacts-mlflow.md)

**Role:** co-development of the landcover package. **Status:** private project with training, inference and model-management workflows.

## Problem and project scope

A land-cover workflow needs more than a classifier. Training data must have a consistent feature order, inference must process spatial data at an appropriate scale, and model artifacts must remain loadable in the environments that consume them.

The landcover package connects these stages through reusable Python components and command-line workflows. Its scope includes conventional classifiers, optical/SAR feature preparation, raster prediction, post-processing and temporal comparison.

## My contribution

My work includes inference and model-discovery improvements, model-loading integration, MLflow support, environment documentation and package maintenance. The implementation includes a PyFunc wrapper for cuML-oriented model use and compressed model artifacts.

The project is described as collaborative. Using scikit-learn, XGBoost, LightGBM or RAPIDS components is integration work; their algorithms remain the work of their respective authors and communities.

## Conceptual architecture

Prepared features → training and model selection → versioned model artifact → loading wrapper → batched raster prediction → georeferenced output. Feature order, validity and environment compatibility connect the stages.

**Technologies:** Python, scikit-learn ecosystem, optional GPU-oriented components, Rasterio/GDAL and MLflow.

## Engineering decisions and limits

Model identity and preprocessing identity need to travel together. Loading the intended model is not enough if the raster channels differ from the training schema. Post-processing also needs to preserve unsupported regions rather than converting missing data into a confident class.

The code has CPU/GPU-oriented interfaces, but that does not establish that every historical version imports or executes in every CPU-only environment. Compatibility should be tested for the particular package and model environment.

The repository is private. This page replaces the former public-code link with an account of the technical work. It exposes no trained artifacts, private data, internal class recipes or registry endpoints. The [local MLflow tutorial](../tutorials/local-mlflow-model.md) demonstrates packaging independently, using a tiny synthetic arithmetic model and local storage.
