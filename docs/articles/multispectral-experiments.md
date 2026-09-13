# Reproducible Multispectral Experiments

[Documentation index](../README.md) · [Feature importance project](../projects/feature-importance.md) · [GAIA](../projects/gaia.md)

An experiment is reproducible when another run can reconstruct what was compared and why the comparison is meaningful. A seed and a model name are useful, but they do not identify the source imagery, feature order, training region, normalization or selection procedure.

My multispectral feature-selection work includes explicit feature preparation, train-region normalization and configuration-based experiment identities. The discussion here explains general design principles. It does not publish private feature recipes, training configurations, benchmark results or claims of superior accuracy.

## Define the generalization question first

Predicting another pixel in a familiar scene is different from predicting a new scene or region. A validation split should correspond to the intended question. Otherwise the metric can be numerically correct while answering something the reader did not intend to ask.

Spatial proximity complicates splitting because neighboring observations can share texture, illumination and acquisition conditions. Assigning individual pixels at random can place closely related observations on both sides of a split. Spatial blocks, scenes or regions provide more explicit units of separation.

The block size and gap should be justified for the data and intended use. A fixed gap copied from a tutorial is not evidence of independence. The synthetic example in this collection demonstrates isolation of preprocessing; it does not estimate a real spatial correlation range.

~~~mermaid
flowchart LR
    A["Define regions"] --> B["Prepare features with provenance"]
    B --> C["Fit preprocessing on train"]
    C --> D["Train candidate models"]
    D --> E["Select using validation"]
    E --> F["Evaluate on held-out test"]
~~~

## Fit preprocessing inside the training boundary

A scaler, percentile transform or learned imputer is part of the fitted procedure. Computing it on the entire image before splitting allows held-out observations to influence the representation used for training. The influence can exist even when test labels are never inspected.

The scikit-learn guidance on leakage explains the separation between fitting transformations on training data and applying those fitted transformations to held-out data. [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)

The [train-only tutorial](../tutorials/train-only-preprocessing.md) makes this observable. It changes every test-region value by a large amount and verifies that the stored training means and scales are identical. A deliberately global calculation changes, showing that the test can detect a boundary violation.

This is a contract check, not an accuracy experiment. No predictive model is trained. That narrow scope makes the example easy to inspect and avoids confusing an engineering assertion with a statement about a real dataset.

## Keep feature identity stable

Multispectral inputs often include physical bands and derived features. The array's channel count is insufficient to identify them. Two arrays can contain the same features in different orders and produce different predictions from an unchanged model.

A feature schema should carry names and order, with any source scaling documented. The normalization artifact should be tied to that schema and to its training region. If a channel changes meaning, an old scaler should not continue to load merely because its vector length still matches.

Separating analytic values from a model's normalized view helps preserve this distinction. The same physical feature source can support different experiments without repeatedly overwriting the original measurements. This also makes diagnostics easier: unexpected model input can be compared with the underlying analytic data.

## Feature selection is another fitted decision

Permutation importance measures the effect of disrupting a feature for a particular model and evaluation setting. It does not establish a causal relationship. Correlated features can substitute for one another, so low individual importance does not necessarily mean that a group carries little information. [scikit-learn permutation importance](https://scikit-learn.org/stable/modules/permutation_importance.html)

Selecting a feature subset based on a final test set makes that set part of model development. A comparison should reserve independent evaluation after selection, or use a suitable nested procedure when the experiment calls for it.

Repeating the permutation can expose instability in the ranking. A useful report shows that uncertainty and the evaluation unit, rather than presenting a single ordering as a universal property of the sensor. Feature rankings can change with model family, region and target definition.

## Separate repeatability from comparability

A run can be perfectly repeatable and still be an unfair comparison. Two candidates need compatible training budgets, split definitions and evaluation rules. A changed mask can make a score improve simply by removing difficult observations.

Useful run metadata identify data versions, split membership, feature schema, normalization, configuration and software environment. These records should support answering a concrete question: what changed between the runs?

An experiment identity should include result-affecting decisions. It should not change because a log directory moved. Conversely, a cache should not be reused after the training region or feature order changes. The identity boundary is an engineering expression of the scientific comparison.

## Report outcomes at the strength of the evidence

Segmentation metrics, object metrics and area summaries answer different questions. A pixel-level score can conceal systematic object fragmentation; an aggregate score can conceal a weak region. The evaluation unit and known failure patterns should accompany any numerical result.

Multiple regions or folds help characterize variability, but they do not automatically make an uncertainty interval valid. The resampling unit must reflect dependence. A large collection of adjacent pixels is not equivalent to the same number of independent scenes.

This portfolio describes implemented experiment infrastructure and general evaluation principles. It deliberately leaves private results out. The strongest public demonstration is a reader who can run a small example, observe the isolation checks and understand exactly which claim those checks support.
