# Fit preprocessing only on training regions

[Index](../README.md) · [Article](../articles/multispectral-experiments.md) · [Source](../examples/train_only.py)

This tutorial demonstrates a testable preprocessing boundary: changing held-out values must not change statistics fitted on training data. It does not train a predictive model or claim that a synthetic gap proves spatial independence.

## Run it

From the repository root, with [uv installed](https://docs.astral.sh/uv/getting-started/installation/):

~~~text
uv sync --frozen
uv run --frozen python -m docs.examples.train_only --output-dir outputs/train-only
~~~

The command writes `report.json` into the selected directory. The synthetic array has 24 rows, 40 columns, and three channels, generated with seed 42 and a column-dependent trend.

## Define the regions before fitting

The first 16 columns form the training region; the last 16 form the held-out region. Eight columns between them are excluded. There are 384 pixels in each selected region and 192 excluded pixels.

That gap makes the masks easy to inspect. Its width is illustrative: a real separation distance must reflect scene structure, acquisition footprint, overlapping chips, and the intended deployment geography. Nearby pixels can remain dependent despite a gap. A region split also cannot prevent leakage from a preprocessing operation that was fitted before the split.

`fit_statistics` receives the array and a Boolean training mask. It selects training pixels before computing the channel means and standard deviations. Empty or nonfinite training data raises an error. A constant channel receives a scale of one, keeping normalization defined without inventing variation.

Apply the resulting training statistics to other regions without refitting. This follows the train/test separation described in scikit-learn's [common pitfalls guidance](https://scikit-learn.org/stable/common_pitfalls.html).

## Perturb the held-out data

The example adds 10,000 to every held-out channel value and fits the statistics again using the same training mask. The fitted means and scales must remain exactly equal. Training values have not changed, so held-out perturbation has no legitimate route into that fit.

As a negative control, it also calculates a mean over the entire array before and after perturbation. That mean changes, showing that a globally fitted transform would depend on the held-out region. The negative control makes the check informative: the perturbation is large enough to expose an incorrectly shared fit.

## Read the report

Alongside fitted statistics, `report.json` records:

~~~json
{
  "train_pixels": 384,
  "test_pixels": 384,
  "excluded_pixels": 192,
  "gap_columns": 8,
  "train_test_overlap": 0,
  "held_out_perturbation_changes_fit": false,
  "global_mean_changes": true,
  "model_trained": false
}
~~~

The program also checks that normalized training channels have approximately zero mean. Rerunning the command regenerates its report in the selected output directory.

## Check the boundaries

~~~text
uv run --frozen pytest -q tests/test_examples.py -k "train or preprocessing or constant"
~~~

Tests cover disjoint masks, the excluded gap, held-out perturbation, constant channels, empty training selections, nonfinite training values, and incompatible masks. Nonfinite held-out values do not affect fitting because that operation does not read them; a subsequent inference step would need its own missing-data policy.

The result verifies isolation of this fitted transform. Real experiments still need grouped or spatial splits, independent model selection, label-quality checks, and metrics appropriate to their task. No accuracy, generalization, or production-readiness claim follows from this tutorial.
