# Multispectral Feature and Permutation Importance

[Documentation index](../README.md) · [Experiment design article](../articles/multispectral-experiments.md)

**Project:** spotlite-feature-permutation-importance. **Role:** experiment-pipeline development. **Status:** private research and engineering workflow.

## Problem and project scope

Comparing feature subsets is difficult when preparation, normalization, model selection and evaluation vary between runs. A useful experiment pipeline must make those differences explicit before its numerical results can be interpreted.

The project supports multispectral feature preparation, segmentation experiments, permutation-based analysis and feature-subset comparisons. Its configuration and persisted metadata provide a common structure for those stages.

## My contribution

My work includes the reproducible pipeline, explicit training-region normalization, preservation of analytic feature values, validity handling and configuration-based run identities. The code checks relationships between feature schemas, normalization artifacts and the regions used for fitting.

The contribution is the experiment infrastructure and its data contracts. It does not imply invention of the segmentation architectures or establish that a specific private feature subset generalizes beyond its evaluation setting.

## Conceptual architecture

Declared imagery interpretation → analytic features → spatial regions → training-only preprocessing → candidate experiments → feature analysis → held-out evaluation and reports.

**Technologies:** Python, NumPy, Rasterio, PyTorch-based modeling and configuration-driven execution.

## Engineering decisions and limits

Normalizing the model input should not overwrite the analytic source. The two representations serve different purposes and should remain distinguishable during diagnosis.

A feature ranking belongs to a model and evaluation protocol. Correlated features, selection decisions and spatial dependence can all affect its interpretation. Reporting a ranked list without those conditions would overstate what the experiment established.

The public collection excludes private feature formulas, source imagery, labels, experiment budgets and benchmark results. It describes implemented controls without claiming that every possible experiment using the pipeline is scientifically valid.

The [train-only preprocessing tutorial](../tutorials/train-only-preprocessing.md) offers an independent demonstration of one narrow invariant: changing held-out pixels must not change the fitted training statistics. It deliberately trains no model and reports no predictive performance.

## Independent public-data demonstration

[Notebook 05: multispectral experiments](../../notebooks/05-multispectral-experiments.ipynb) demonstrates related methods using public observations and original code. It does not reproduce this private project or its operational results.
