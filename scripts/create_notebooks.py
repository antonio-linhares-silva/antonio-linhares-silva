"""Maintainer notebook sources. Regeneration clears outputs; execute before publishing."""

import ast
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import nbformat as nbf

NOTEBOOKS = Path(__file__).resolve().parents[1] / "notebooks"
SETUP = """
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
from IPython import get_ipython
from geoai_portfolio.io import ensure_data, root, workspace

get_ipython().run_line_magic("matplotlib", "inline")
plt.rcParams.update({"figure.dpi": 110, "figure.figsize": (10, 4),
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.labelsize": 9,
                     "axes.titlesize": 11, "font.size": 10,
                     "savefig.bbox": "tight"})
pd.set_option("display.precision", 4)
"""


def md(source):
    return nbf.v4.new_markdown_cell(dedent(source).strip())


def code(source):
    source = dedent(source).strip()
    lines, imports, excluded = source.splitlines(), [], set()
    for node in ast.parse(source).body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.extend(lines[node.lineno - 1 : node.end_lineno])
            excluded.update(range(node.lineno - 1, node.end_lineno))
    content = imports + [""] + [line for index, line in enumerate(lines) if index not in excluded]
    return nbf.v4.new_code_cell("\n".join(content).strip())


def notebook(number, slug, title, introduction, cells):
    lead = md(
        f"# {number:02d} · {title}\n\n{introduction}\n\n"
        f"[Notebook index](README.md) · [Companion article](../docs/articles/{slug}.md) · "
        "[Data sources and licences](../docs/DATA_SOURCES.md)\n\n"
        "Run every cell from top to bottom in the locked Python 3.12 environment. "
        "The first run downloads the required public data pack and checks its SHA-256. "
        "Generated artifacts remain in the ignored `outputs/` directory."
    )
    document = nbf.v4.new_notebook(
        cells=[lead, code(SETUP), *cells],
        metadata={
            "kernelspec": {
                "display_name": "Python 3 (GeoAI)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.12"},
            "geoai": {"data_version": "public-data-v1", "independent_run_all": True},
        },
    )
    for index, cell in enumerate(document.cells):
        cell.id = f"nb{number:02d}-cell{index:02d}"
    nbf.write(document, NOTEBOOKS / f"{number:02d}-{slug}.ipynb")


def build():
    NOTEBOOKS.mkdir(exist_ok=True)
    notebook(
        1,
        "reusable-geoai-framework",
        "A dataset contract, a short fine-tune, and an honest test",
        "Adapt ImageNet-pretrained ResNet18 to ten EuroSAT classes. A shared dataset adapter "
        "also serves the classical experiments in notebook 05. CPU works; CUDA is recommended. "
        "This is a small spatial transfer demonstration, not a benchmark of the complete dataset.",
        [
            md("""
        ## Inspect the data before choosing a model

        The multispectral archive contains 13-band, 64 × 64 chips. We use original EuroSAT labels
        and TorchGeo's longitude-based train/validation/test lists, sample each class with seed 42,
        and exclude held-out footprints within 2 km of an earlier partition. The sampling manifest
        preserves filenames, original georeferencing, archive identity, and individual chip hashes.
        The effective distance is a design choice; it does not prove independence at every scale.
        """),
            code("""
        from geoai_portfolio.experiments import EuroSAT, report, group_bootstrap
        data = ensure_data("eurosat")
        out = workspace("01-framework")
        dataset = EuroSAT.load(data)
        display(pd.crosstab(dataset.samples["class"], dataset.samples.split))
        print("Image tensor:", dataset.images.shape, dataset.images.dtype)
        """),
            code("""
        import geopandas as gpd
        footprints = gpd.read_file(data/"footprints.gpkg")
        fig, ax = plt.subplots(figsize=(9, 5))
        for split, color in [("train", "#0072B2"), ("val", "#E69F00"), ("test", "#009E73")]:
            centers = footprints.loc[footprints.split.eq(split)].geometry.centroid
            ax.scatter(centers.x/1000, centers.y/1000, s=5, alpha=.6, color=color, label=split)
        ax.set(title="EuroSAT subset · geographical partitions", xlabel="Easting (EPSG:3035; km)",
               ylabel="Northing (km)", aspect="equal")
        ax.legend(title="Partition", markerscale=2)
        plt.show()
        """),
            md("""
        ## Keep the experiment interface explicit

        RGB band order is B04, B03, B02. Scaling by 10,000 retains EuroSAT's original DN convention;
        this is not the C1 L2A calibration used in the Sentinel notebooks. Mean and standard deviation
        are fitted on training chips only. A bilinear resize to 128 × 128 is a model input transform,
        not an increase in geographical resolution. Pretrained weights supply the backbone; the
        final layer starts with ten new outputs. Only layer4 and the classifier are updated.
        """),
            code("""
        import torch
        from geoai_portfolio.neural import (seed_everything, device_name, make_loaders,
                                            initialize_model, fine_tune, infer)
        seed_everything(42)
        device = device_name(os.environ.get("GEOAI_DEVICE", "auto"))
        loaders, preprocessing = make_loaders(dataset, batch_size=32)
        model = initialize_model()
        display(pd.DataFrame({"band": preprocessing["bands"], "training_mean": preprocessing["mean"],
                              "training_std": preprocessing["std"]}))
        print({"device": device, "torch": torch.__version__,
               "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
               "epochs": 3, "selection": "best validation macro-F1"})
        """),
            md("""
        ## Train briefly and select using validation

        Three epochs, AdamW (learning rate 0.0003, weight decay 0.001), batch size 32, seed 42.
        Frozen batch-normalization statistics avoid adapting the pretrained backbone statistics
        to tiny batches. There is no hyperparameter search on the test set. Timing describes this
        execution and hardware only; deterministic settings do not promise identical floats
        across different GPUs or dependency versions.
        """),
            code("""
        history = fine_tune(model, loaders, device=device, epochs=3)
        display(history)
        fig, axes = plt.subplots(1, 2, figsize=(10, 3))
        axes[0].plot(history.epoch, history.train_loss, "o-", color="#0072B2")
        axes[0].set(title="Training", xlabel="Epoch", ylabel="Cross-entropy")
        axes[1].plot(history.epoch, history.validation_macro_f1, "o-", color="#009E73")
        axes[1].set(title="Validation selection", xlabel="Epoch", ylabel="Macro-F1", ylim=(0, 1))
        plt.tight_layout(); plt.show()
        """),
            md("""
        ## Evaluate once on the held-out geography

        Macro-F1 weights the ten classes equally; support makes the sample size visible.
        Bootstrap intervals resample 100 km spatial groups, not individual correlated chips.
        These intervals describe this subset and grouping. They omit label uncertainty and
        cannot establish accuracy in Portugal or any private operational project.
        """),
            code("""
        probability, truth = infer(model, loaders["test"], device)
        predicted = probability.argmax(1)
        display(report(dataset, predicted))
        groups = dataset.samples.loc[dataset.mask("test"), "spatial_group"]
        display(group_bootstrap(truth, predicted, groups))
        from sklearn.metrics import ConfusionMatrixDisplay
        fig, ax = plt.subplots(figsize=(9, 8))
        ConfusionMatrixDisplay.from_predictions(truth, predicted, labels=range(10),
            display_labels=dataset.classes, normalize="true", ax=ax, cmap="Blues",
            xticks_rotation=70, values_format=".2f", colorbar=False)
        ax.set_title("Spatial test · row-normalized confusion matrix")
        plt.tight_layout(); plt.show()
        """),
            code("""
        test_images = dataset.images[dataset.mask("test")]
        errors = np.flatnonzero(predicted != truth)
        chosen = errors[:6] if len(errors) else np.arange(6)
        fig, axes = plt.subplots(2, 3, figsize=(10, 7))
        for ax, index in zip(axes.flat, chosen):
            rgb = np.clip(test_images[index, [3, 2, 1]].transpose(1, 2, 0)/3000, 0, 1)
            ax.imshow(rgb)
            ax.set_title(f"Label: {dataset.classes[truth[index]]}\\nPrediction: {dataset.classes[predicted[index]]}",
                         fontsize=9)
            ax.axis("off")
        fig.suptitle("Inspect errors · fixed RGB display stretch; each chip covers about 640 m")
        plt.tight_layout(); plt.show()
        torch.save(model.cpu().state_dict(), out/"resnet18-eurosat-state.pt")
        from geoai_portfolio.io import write_json, sha256
        write_json(out/"experiment.json", {"preprocessing": preprocessing, "seed": 42,
                   "weights": "ResNet18_Weights.IMAGENET1K_V1", "selected_epoch": int(
                       history.loc[history.validation_macro_f1.idxmax(), "epoch"]),
                   "data_sha256": sha256(data/"samples.csv"), "device": device})
        print("Saved local state dictionary and experiment metadata.")
        """),
            md("""
        ## Interpretation and next experiment

        Inspect which visually similar classes are confused before adding model complexity.
        The controlled comparison in [notebook 05](05-multispectral-experiments.ipynb) asks a
        different question: does a fixed classical model benefit from additional bands?
        ResNet's spatial image features and the forest's summary features are different
        representations, so their scores are not an isolated comparison of architectures.

        Sources: [EuroSAT authors](https://github.com/phelber/EuroSAT),
        [TorchGeo spatial splits](https://torchgeo.readthedocs.io/en/latest/_modules/torchgeo/datasets/eurosat.html),
        [torchvision ResNet18](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet18.html).
        """),
        ],
    )

    notebook(
        2,
        "memory-bounded-rasters",
        "NDVI in windows with a whole-array check",
        "Process an actual Sentinel-2 L2A crop while keeping array sizes independent of total "
        "scene size. Compare the output grid, mask, and values against a small reference.",
        [
            code("""
        import time
        import rasterio
        from geoai_portfolio.rasters import scene_ndvi, windowed_ndvi, map_array, grid
        data = ensure_data("satellite")
        out = workspace("02-rasters")
        provenance = json.loads((data/"provenance.json").read_text())
        display(pd.DataFrame([{k: row[k] for k in ["id", "datetime", "processing_baseline"]}
                              for row in provenance["sentinel"]]))
        with rasterio.open(data/"before.tif") as source:
            display(pd.DataFrame({"band": source.descriptions, "scale": source.scales,
                                  "offset": source.offsets}))
            print(grid(source))
        """),
            md("""
        ## Make valid pixels explicit

        The crop is 512 × 512 at 10 m in UTM zone 10N (EPSG:32610), north of Lake Almanor,
        California. Red and NIR are surface-reflectance bands from 12 August 2020, C1 L2A,
        processing baseline 05.00. Raw zero is nodata. Each band is calibrated once using its
        saved scale and offset. SCL classes 4, 5, 6, 7 are retained; cloud, cirrus, shadow,
        snow, defective and missing pixels are excluded. Class 7 is uncertain and needs visual
        inspection. Negative reflectance and near-zero denominators are also masked.
        """),
            code("""
        reference = scene_ndvi(data/"before.tif", data/"before-scl.tif")
        results = []
        for size in [64, 128, 256]:
            started = time.perf_counter()
            path = out/f"ndvi-{size}.tif"
            summary = windowed_ndvi(data/"before.tif", data/"before-scl.tif", path, size)
            with rasterio.open(path) as saved, rasterio.open(data/"before.tif") as source:
                actual = saved.read(1, masked=True)
                assert grid(saved) == grid(source)
                np.testing.assert_array_equal(actual.mask, reference.mask)
                np.testing.assert_allclose(actual.compressed(), reference.compressed(), atol=1e-6, rtol=0)
                assert saved.tags(ns="IMAGE_STRUCTURE").get("LAYOUT") == "COG"
            results.append({**summary, "seconds": time.perf_counter()-started,
                            "max_abs_difference": float(np.max(np.abs(actual-reference)))})
        display(pd.DataFrame(results))
        """),
            code("""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        with rasterio.open(data/"before.tif") as source:
            image = map_array(axes[0], reference, source, "12 Aug 2020 · NDVI", "YlGn", -1, 1)
            fig.colorbar(image, ax=axes[0], label="NDVI (unitless)", shrink=.75)
            mask = np.ma.getmaskarray(reference).astype("uint8")
            image = map_array(axes[1], mask, source, "Excluded pixels", "Greys", 0, 1)
            fig.colorbar(image, ax=axes[1], ticks=[0, 1], label="0 valid · 1 excluded", shrink=.75)
        fig.suptitle("Contains modified Copernicus Sentinel data (2020)", fontsize=10)
        plt.tight_layout(); plt.show()
        """),
            md("""
        ## What this proves

        All window sizes must produce the same numerical result and mask. Processing uses tiled
        scratch storage and then translates it to a COG; it never allocates a scene-sized result
        inside the windowed function. The whole-array reference is deliberately small and exists
        only for verification. `largest_input_pixels` is an array-size bound, not a measurement
        of process RSS: GDAL blocks, caches, compression and Python add memory costs. A COG layout
        tag and successful reopen are useful checks, not independent full conformance certification.

        [Rasterio windowed I/O](https://rasterio.readthedocs.io/en/stable/topics/windowed-rw.html)
        explains why actual network and disk reads also depend on the source block layout.
        """),
        ],
    )

    notebook(
        3,
        "resumable-workflows",
        "Recover a real raster batch after an interruption",
        "Use sixteen Sentinel-2 windows to demonstrate durable progress, verified skipping, "
        "corruption recovery, and invalidation when a result-affecting parameter changes.",
        [
            code("""
        import tempfile
        from geoai_portfolio.workflows import run_windows
        data = ensure_data("satellite")
        out = workspace("03-recovery")
        scene, scl = data/"before.tif", data/"before-scl.tif"
        """),
            md("""
        ## Define a task identity

        Each task records SHA-256 hashes of both input rasters, the algorithm version, the pixel
        window and an NDVI threshold. A completed task is reusable only if its output checksum
        still matches. The manifest is replaced atomically after the output is complete.
        This example has one writer and local storage; it is not a distributed queue.
        A temporary directory makes repeated Run All executions independent.
        """),
            code("""
        events = []
        with tempfile.TemporaryDirectory(prefix="batch-", dir=out) as temporary:
            batch = Path(temporary)
            first = run_windows(scene, scl, batch, fail_at=5)
            assert first["failed"] == 5 and len(first["executed"]) == 5
            events.append({"stage": "controlled failure", **first})
            second = run_windows(scene, scl, batch)
            assert second["skipped"] == list(range(5)) and second["failed"] is None
            events.append({"stage": "resume", **second})
            # Corrupt only an artifact created in this dedicated temporary directory.
            (batch/"window-002.json").write_text("damaged", encoding="utf-8")
            repaired = run_windows(scene, scl, batch)
            assert repaired["executed"] == [2]
            events.append({"stage": "repair damaged output", **repaired})
            changed = run_windows(scene, scl, batch, threshold=.6)
            assert len(changed["executed"]) == 16 and not changed["skipped"]
            events.append({"stage": "changed threshold", **changed})
            values = pd.DataFrame([json.loads(p.read_text()) for p in sorted(batch.glob("window-*.json"))])
        display(pd.DataFrame([{**row, "executed": len(row["executed"]), "skipped": len(row["skipped"])}
                              for row in events]))
        display(values[["window", "valid_pixels", "mean_ndvi", "above_threshold"]].head(8))
        """),
            code("""
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        labels = [row["stage"] for row in events]
        executed = [len(row["executed"]) for row in events]
        skipped = [len(row["skipped"]) for row in events]
        axes[0].barh(labels, executed, color="#0072B2", label="Executed")
        axes[0].barh(labels, skipped, left=executed, color="#009E73", label="Verified and skipped")
        axes[0].set(xlabel="Windows", title="Recovery ledger"); axes[0].legend(fontsize=8)
        axes[1].bar(values.window, values.above_threshold, color="#009E73")
        axes[1].set(title="Final batch · NDVI > 0.6", xlabel="Window ID (row-major)",
                    ylabel="Valid pixels above threshold")
        plt.tight_layout(); plt.show()
        """),
            md("""
        ## Interpret the execution evidence

        A saved completion flag alone is insufficient: the damaged task must run again.
        Changing 0.4 to 0.6 invalidates all sixteen tasks because their numerical outputs depend
        on that parameter. A source-file change has the same effect through its hash. A valid
        zero count remains a successful result; absence of an output never means zero vegetation.

        The threshold is an illustrative spectral cutoff, not a calibrated forest-area classifier.
        For durable multi-worker execution, extend the design with locks or transactional claims,
        atomic object publication, and explicit retry ownership before introducing concurrency.
        """),
        ],
    )

    notebook(
        4,
        "geospatial-data-contracts",
        "Find a misaligned raster before it enters analysis",
        "Combine Sentinel-2 spectral bands and ESA WorldCover 2021 to inspect grid contracts "
        "and demonstrate why continuous and categorical variables need different resampling.",
        [
            code("""
        import rasterio
        from rasterio.io import MemoryFile
        from affine import Affine
        from geoai_portfolio.rasters import grid, require_same_grid, align, map_array
        data = ensure_data("satellite")
        rows = []
        for name in ["before.tif", "swir20m.tif", "worldcover.tif"]:
            with rasterio.open(data/name) as source:
                rows.append({"file": name, "crs": str(source.crs), "shape": source.shape,
                             "resolution": source.res, "nodata": source.nodata,
                             "bands": source.descriptions})
        display(pd.DataFrame(rows))
        """),
            md("""
        ## Test an intentional contract violation

        Equal array shapes do not establish alignment. The following in-memory copy moves the
        affine origin by half a pixel, preserving the CRS and pixel count. The original public
        file remains unchanged. An early error is the desired result.
        """),
            code("""
        with rasterio.open(data/"before.tif") as source, MemoryFile() as memory:
            profile = source.profile.copy()
            profile["transform"] = source.transform @ Affine.translation(.5, 0)
            with memory.open(**profile) as shifted:
                shifted.write(source.read())
                try:
                    require_same_grid(source, shifted)
                except ValueError as error:
                    print("Expected contract rejection:", error)
                else:
                    raise AssertionError("Shifted grid was accepted")
        """),
            md("""
        ## Match resampling to the variable

        B12 is a continuous 20 m measurement, so bilinear interpolation can place it on the
        reference grid. Interpolation adds no independent 10 m information. WorldCover is a
        categorical 2021 v200 map in geographic coordinates: nearest neighbour preserves labels.
        Its classes are context for the contract example, not ground truth for EuroSAT or a
        validation of vegetation change. Even though its name includes “10m”, its angular grid
        is not identical to Sentinel's UTM grid at this latitude.
        """),
            code("""
        swir = align(data/"swir20m.tif", data/"before.tif", categorical=False)
        with rasterio.open(data/"swir20m.tif") as source:
            swir = swir*source.scales[0]+source.offsets[0]
        labels = align(data/"worldcover.tif", data/"before.tif", categorical=True)
        wrong = align(data/"worldcover.tif", data/"before.tif", categorical=False)
        with rasterio.open(data/"worldcover.tif") as source:
            source_labels = np.unique(source.read(1, masked=True).compressed())
        assert set(np.unique(labels.compressed())).issubset(set(source_labels))
        fractional = np.abs(wrong.compressed()-np.round(wrong.compressed())) > 1e-5
        display(pd.DataFrame({"check": ["Source classes", "Nearest output classes", "Fractional bilinear values"],
                              "value": [str(source_labels.tolist()),
                                        str(np.unique(labels.compressed()).tolist()), str(int(fractional.sum()))]}))
        """),
            code("""
        from matplotlib.colors import ListedColormap, BoundaryNorm
        from matplotlib.patches import Patch
        classes = {10: ("Tree cover", "#006400"), 20: ("Shrubland", "#ffbb22"),
                   30: ("Grassland", "#ffff4c"), 40: ("Cropland", "#f096ff"),
                   50: ("Built-up", "#fa0000"), 60: ("Bare/sparse", "#b4b4b4"),
                   70: ("Snow/ice", "#f0f0f0"), 80: ("Water", "#0064c8"),
                   90: ("Wetland", "#0096a0"), 95: ("Mangroves", "#00cf75"),
                   100: ("Moss/lichen", "#fae6a0")}
        encoded = np.ma.masked_all(labels.shape)
        for index, category in enumerate(classes):
            encoded[labels == category] = index
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        with rasterio.open(data/"before.tif") as reference:
            image = map_array(axes[0], swir, reference, "B12 · 20 m source → 10 m grid", "magma", 0, .5)
            fig.colorbar(image, ax=axes[0], label="Surface reflectance (unitless)", shrink=.7)
            map_array(axes[1], encoded, reference, "WorldCover 2021 · nearest neighbour",
                      ListedColormap([v[1] for v in classes.values()]), -.5, len(classes)-.5)
        axes[1].legend(handles=[Patch(facecolor=color, label=name) for value, (name, color) in classes.items()
                                if value in source_labels], loc="upper left", fontsize=7)
        fig.suptitle("Copernicus Sentinel data (2020) · ESA WorldCover consortium (2021), CC BY 4.0", fontsize=9)
        plt.tight_layout(); plt.show()
        """),
            md("""
        ## Contract carried downstream

        Record the CRS, affine transform, shape, band order, nodata meaning, units, source version
        and resampling choice together. Masking is part of the contract. A newly introduced
        fractional class code is evidence of an invalid processing choice, even if the plot
        looks smooth. [Rasterio reprojection](https://rasterio.readthedocs.io/en/stable/topics/reproject.html)
        and the [WorldCover product documentation](https://esa-worldcover.org/en/data-access)
        provide the source conventions used here.
        """),
        ],
    )

    notebook(
        5,
        "multispectral-experiments",
        "RGB versus thirteen bands under the same spatial split",
        "Compare fixed random forests using chip-level spectral summaries. Keep partitions, "
        "estimator settings and evaluation protocol constant, then inspect validation-set "
        "permutation importance without claiming causality.",
        [
            code("""
        from geoai_portfolio.experiments import EuroSAT, fit_forest, scores, report, group_bootstrap
        from sklearn.inspection import permutation_importance
        data = ensure_data("eurosat")
        dataset = EuroSAT.load(data)
        train, val, test = [dataset.mask(split) for split in ["train", "val", "test"]]
        truth = dataset.samples.loc[test, "label"].to_numpy()
        display(pd.crosstab(dataset.samples["class"], dataset.samples.split))
        """),
            md("""
        ## Control the comparison

        Each selected band contributes mean, standard deviation, and the 10th, 50th and 90th
        percentiles across a chip. Both models use 160 trees, minimum leaf size 2 and seed 42.
        StandardScaler is included to make fitted preprocessing auditable, although a forest
        does not require feature standardization. Only training rows reach `fit`.
        No WorldCover labels are mixed into this supervised experiment.
        """),
            code("""
        rgb_features = dataset.features(["B04", "B03", "B02"])
        ms_features = dataset.features(dataset.bands)
        models, comparisons = {}, []
        for name, features in [("RGB", rgb_features), ("13 bands", ms_features)]:
            model = fit_forest(dataset, features)
            models[name] = model
            predicted = model.predict(features.loc[test])
            comparisons.append({"features": name, "columns": features.shape[1], **scores(truth, predicted)})
        comparison = pd.DataFrame(comparisons).set_index("features")
        display(comparison)
        comparison[["accuracy", "macro_f1"]].plot.bar(color=["#0072B2", "#009E73"], rot=0, ylim=(0, 1))
        plt.title("Spatial test · fixed forest, changed band set"); plt.ylabel("Score"); plt.show()
        """),
            code("""
        # Perturb every held-out feature and refit only on the unchanged training rows.
        altered = ms_features.copy()
        altered.loc[~train] += 1000
        check_model = fit_forest(dataset, altered)
        np.testing.assert_array_equal(models["13 bands"][0].mean_, check_model[0].mean_)
        np.testing.assert_array_equal(models["13 bands"].predict(ms_features.loc[test]),
                                      check_model.predict(ms_features.loc[test]))
        print("Held-out perturbations did not change fitted statistics or predictions.")
        """),
            md("""
        ## Inspect which features the fitted model uses

        Permute validation columns, not test columns, and measure macro-F1 loss. Five repeats
        describe permutation variability. Correlated bands can substitute for one another,
        so low marginal importance is not proof that a band contains no useful information.
        This descriptive inspection does not trigger retraining or test-set model selection.
        """),
            code("""
        importance = permutation_importance(models["13 bands"], ms_features.loc[val],
            dataset.samples.loc[val, "label"], scoring="f1_macro", n_repeats=5, random_state=42, n_jobs=1)
        ranking = pd.DataFrame({"feature": ms_features.columns, "f1_drop": importance.importances_mean,
                                "repeat_std": importance.importances_std}).sort_values("f1_drop", ascending=False)
        display(ranking.head(12))
        top = ranking.head(12).sort_values("f1_drop")
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.barh(top.feature, top.f1_drop, xerr=top.repeat_std, color="#0072B2")
        ax.axvline(0, color="gray", linewidth=.8)
        ax.set(title="Validation permutation importance", xlabel="Macro-F1 decrease ± repeat SD")
        plt.tight_layout(); plt.show()
        """),
            code("""
        predicted = models["13 bands"].predict(ms_features.loc[test])
        display(report(dataset, predicted))
        display(group_bootstrap(truth, predicted, dataset.samples.loc[test, "spatial_group"]))
        """),
            md("""
        ## Limits and reproducibility

        This class-balanced subset changes the class frequencies relative to a real map.
        Accuracy therefore does not estimate area-weighted deployment accuracy. Longitude-based
        regions and a 2 km footprint exclusion improve the split, but acquisition dates and
        complete scene IDs are unavailable in the original chip metadata. That limits stronger
        claims about temporal independence. No result here reproduces a private benchmark.

        [scikit-learn permutation importance](https://scikit-learn.org/stable/modules/permutation_importance.html)
        discusses the dependence of importance on the fitted model and correlated inputs.
        """),
        ],
    )


def build_remaining():
    notebook(
        6,
        "model-artifacts-mlflow",
        "A model artifact another process can load",
        "Train a public EuroSAT forest, log it locally with MLflow, include its feature "
        "schema and environment, and reproduce predictions in a fresh Python process.",
        [
            code("""
        from geoai_portfolio.experiments import EuroSAT, fit_forest, scores
        from geoai_portfolio.artifacts import log_forest, predict_table, reload_in_fresh_process
        from geoai_portfolio.io import sha256
        data = ensure_data("eurosat")
        out = workspace("06-artifacts")
        dataset = EuroSAT.load(data)
        features = dataset.features(dataset.bands)
        train, test = dataset.mask("train"), dataset.mask("test")
        model = fit_forest(dataset, features)
        display(pd.DataFrame({"partition": ["train", "test"], "chips": [train.sum(), test.sum()],
                              "features": [features.shape[1], features.shape[1]]}))
        """),
            md("""
        ## Package the prediction contract

        The saved scikit-learn pipeline includes training-fitted preprocessing. MLflow stores
        a signature, an input example, and pinned Python requirements. A separate JSON schema
        records column names and order, units, band definitions and dataset identity. The local
        SQLite tracking store and artifact directory require no remote service or credentials.
        Load only model packages you trust: the scikit-learn flavor uses Python serialization.
        """),
            code("""
        package = log_forest(model, features.loc[train], dataset.samples.loc[train, "label"], out,
                             {"bands": dataset.bands, "data_version": "public-data-v1",
                              "samples_sha256": sha256(data/"samples.csv"), "seed": 42})
        files = pd.DataFrame([{"file": p.relative_to(package).as_posix(), "bytes": p.stat().st_size}
                               for p in sorted(package.rglob("*")) if p.is_file()])
        display(files)
        schema = json.loads((package/"feature_schema.json").read_text())
        display(pd.DataFrame({"feature": schema["columns"][:10],
                              "dtype": [schema["dtypes"][c] for c in schema["columns"][:10]]}))
        """),
            md("""
        ## Reload outside the checkout

        A subprocess starts with Python's isolated flag and a temporary working directory. It
        imports MLflow and pandas directly, reads the saved CSV, and loads the model without
        importing this repository. This verifies artifact independence from notebook state.
        The next notebook also verifies installation in a separate environment.
        """),
            code("""
        example = features.loc[test].iloc[:40]
        expected = model.predict(example)
        local = predict_table(package, example)
        external = reload_in_fresh_process(package, example)
        np.testing.assert_array_equal(expected, local)
        np.testing.assert_array_equal(expected, external)
        display(pd.DataFrame({"original": expected, "loaded": local, "fresh_process": external}).head(12))
        try:
            predict_table(package, example[example.columns[::-1]])
        except ValueError as error:
            print("Expected schema rejection:", error)
        else:
            raise AssertionError("Reordered features were accepted")
        """),
            code("""
        held_out = features.loc[test]
        predicted = predict_table(package, held_out)
        display(pd.DataFrame([scores(dataset.samples.loc[test, "label"], predicted)]))
        from sklearn.metrics import ConfusionMatrixDisplay
        fig, ax = plt.subplots(figsize=(9, 8))
        ConfusionMatrixDisplay.from_predictions(dataset.samples.loc[test, "label"], predicted,
            display_labels=dataset.classes, normalize="true", xticks_rotation=70, ax=ax,
            cmap="Blues", values_format=".2f", colorbar=False)
        ax.set_title("Reloaded artifact · spatial test predictions")
        plt.tight_layout(); plt.show()
        """),
            md("""
        ## What travels with the artifact

        Correct weights with the wrong feature order can produce plausible but wrong results.
        The explicit schema prevents that failure at the application boundary. Artifact reload
        does not prove robustness to arbitrary dependency changes; it reproduces predictions in
        the declared environment. Run IDs and serialization bytes may vary between executions.
        Public subset scores describe this experiment only.

        [MLflow model signatures](https://mlflow.org/docs/latest/ml/model/signatures/)
        document model input and output contracts.
        """),
        ],
    )

    notebook(
        7,
        "shipping-geoai",
        "Build a wheel and run it outside the repository",
        "Turn the raster workflow into an installed command-line tool, then verify its "
        "result from a fresh environment. This notebook needs uv and internet for installation.",
        [
            code("""
        from geoai_portfolio.shipping import verify_wheel
        data = ensure_data("satellite")
        out = workspace("07-shipping")
        checkout = root()
        display(pd.DataFrame({"interface": ["Python", "CLI", "Container"],
                              "entry": ["geoai_portfolio.rasters.windowed_ndvi",
                                        "geoai-portfolio ndvi", "Dockerfile; Ubuntu CI smoke check"]}))
        """),
            md("""
        ## Build, install, and execute a concrete artifact

        The verification function builds the wheel using the pinned build backend, exports the
        frozen base dependency lock, creates a separate virtual environment outside the checkout,
        and installs the wheel plus those dependencies. It then invokes the installed CLI with
        explicit input paths and a fresh working directory. The isolated interpreter does not
        use a source-tree `PYTHONPATH`. Installation can take several minutes on an empty cache.
        """),
            code("""
        result = verify_wheel(checkout, data, out)
        display(pd.DataFrame([result]))
        assert result["array_matches_reference"]
        """),
            code("""
        import rasterio
        from geoai_portfolio.rasters import map_array, scene_ndvi
        with rasterio.open(out/"installed-ndvi.tif") as source:
            saved = source.read(1, masked=True)
            reference = scene_ndvi(data/"before.tif", data/"before-scl.tif")
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            image = map_array(axes[0], saved, source, "Installed CLI · NDVI", "YlGn", -1, 1)
            fig.colorbar(image, ax=axes[0], label="NDVI (unitless)", shrink=.75)
            difference = saved-reference
            image = map_array(axes[1], difference, source, "CLI minus reference", "RdBu", -.001, .001)
            fig.colorbar(image, ax=axes[1], label="NDVI difference", shrink=.75)
        fig.suptitle("Contains modified Copernicus Sentinel data (2020)", fontsize=10)
        plt.tight_layout(); plt.show()
        """),
            md("""
        ## Container boundary

        The repository's [Dockerfile](../Dockerfile) uses the same package and frozen dependency
        lock. The [validation workflow](../.github/workflows/validate.yml) builds it on Ubuntu
        and executes the CLI against a tiny public fixture with network access disabled during
        inference. Local Run All does not require Docker. Consult the workflow result for
        evidence of the container check; the notebook's wheel result alone does not establish it.

        The output checksum identifies this concrete artifact, while array equality verifies
        the scientific result. Wheel bytes can differ with build metadata even when predictions
        agree. Neither wheel installation nor a container makes unspecified data conventions safe.
        """),
        ],
    )

    notebook(
        8,
        "tree-crowns-height-distance",
        "Tree detection boxes meet public height surfaces",
        "Run pretrained DeepForest inference on a public 2022 Dutch orthophoto, attach "
        "AHN4 surface-height statistics, and export the results in a GeoPackage. CPU is "
        "supported; CUDA is recommended. There are no reference crown labels in this crop.",
        [
            code("""
        import rasterio
        from geoai_portfolio.trees import detect_boxes, height_surface, summarize_boxes, DEEPFOREST_REVISION
        from geoai_portfolio.neural import device_name
        from geoai_portfolio.rasters import map_array
        data = ensure_data("ahn")
        out = workspace("08-trees")
        provenance = json.loads((data/"provenance.json").read_text())
        display(pd.DataFrame({"property": ["LiDAR UTC interval", "Orthophoto", "Horizontal CRS", "Height datum"],
                              "value": [str(provenance["gps_utc_ranges"]["trees"]),
                                        "2022 leaf-on; exact flight date unavailable", "EPSG:28992; metres",
                                        "NAP, EPSG:5709; metres"]}))
        """),
            md("""
        ## State the temporal and geometric limits first

        The AHN4 observations in this Ede crop date to 12 February 2022. The 0.25 m RGB mosaic
        is leaf-on 2022; it is not simultaneous. DTM and DSM use the same original AHN4 TOP tile
        and 0.5 m weighted-IDW products. Both heights refer to NAP, so no vertical-datum
        conversion is performed. The original LAS lacked a CRS record: the crop explicitly
        assigns the provider-documented compound CRS, without moving coordinates.

        DeepForest's public model was developed using other sites. Domain shift, season,
        resolution and shadows can affect detections here. Boxes are not segmented crown
        boundaries, and DSM minus DTM also contains buildings and other elevated objects.
        """),
            code("""
        device = device_name(os.environ.get("GEOAI_DEVICE", "auto"))
        boxes = detect_boxes(data/"trees-rgb.tif", device=device, score_threshold=.5)
        height = height_surface(data/"trees-dsm.tif", data/"trees-dtm.tif")
        summary = summarize_boxes(boxes, height, data/"trees-dtm.tif", min_valid=.8)
        print({"device": device, "model_revision": DEEPFOREST_REVISION, "detections": len(boxes),
               "valid_height_fraction": height.count()/height.size,
               "negative_height_pixels": int((height < 0).sum())})
        display(summary[["label", "score", "valid_fraction", "valid_pixels", "surface_p95_m"]].head(12))
        """),
            md("""
        ## Inspect the map before interpreting a height

        Inference uses 512-pixel windows with 64-pixel overlap; global NMS uses IoU 0.15.
        The score threshold is 0.5. Scores are model outputs, not calibrated probabilities of
        correctness. The 95th percentile summarizes valid 0.5 m surface pixels whose centres
        lie inside each predicted box; coverage below 80% suppresses the height value. Negative
        differences are reported, not silently clipped or replaced by zero.
        """),
            code("""
        fig, axes = plt.subplots(1, 2, figsize=(13, 6))
        with rasterio.open(data/"trees-rgb.tif") as source:
            rgb = source.read().transpose(1, 2, 0)
            map_array(axes[0], rgb, source, "2022 orthophoto · predicted boxes")
            boxes.boundary.plot(ax=axes[0], color="#00ffff", linewidth=.8)
        with rasterio.open(data/"trees-dtm.tif") as source:
            image = map_array(axes[1], height, source, "AHN4 · DSM − DTM", "viridis", 0, 35)
            boxes.boundary.plot(ax=axes[1], color="white", linewidth=.6)
            fig.colorbar(image, ax=axes[1], label="Surface height above ground (m)", shrink=.75)
        from matplotlib.lines import Line2D
        axes[0].legend(handles=[Line2D([0], [0], color="#00ffff", label="Predicted bounding box")], fontsize=8)
        fig.suptitle("Beeldmateriaal Nederland (2022), CC BY 4.0 · AHN4, CC0", fontsize=10)
        plt.tight_layout(); plt.show()
        """),
            code("""
        from scipy.spatial import cKDTree
        centers = np.column_stack([summary.geometry.centroid.x, summary.geometry.centroid.y])
        if len(centers) > 1:
            summary["nearest_box_center_m"] = cKDTree(centers).query(centers, k=2)[0][:, 1]
        else:
            summary["nearest_box_center_m"] = np.nan
        summary["height_datum"] = "NAP EPSG:5709"
        summary["height_role"] = "P95 surface inside detection box; not validated tree height"
        summary.to_file(out/"tree-boxes.gpkg", layer="detections", driver="GPKG")
        fig, axes = plt.subplots(1, 2, figsize=(10, 3))
        axes[0].hist(summary.surface_p95_m.dropna(), bins=10, color="#009E73")
        axes[0].set(title="Detected-box surface statistics", xlabel="P95 height (m)", ylabel="Boxes")
        axes[1].scatter(summary.score, summary.surface_p95_m, color="#0072B2")
        axes[1].set(title="Score does not validate height", xlabel="Detection score", ylabel="P95 height (m)")
        plt.tight_layout(); plt.show()
        display(summary[["surface_p95_m", "nearest_box_center_m", "valid_fraction"]].describe())
        print("Exported tree-boxes.gpkg with predicted geometry and explicit height provenance.")
        """),
            md("""
        ## What is still unknown

        Field measurements or suitable same-season reference crowns are needed to validate
        detection precision, recall and tree-height error. Nearest box-centre distance is a
        two-dimensional geometric descriptor, not stem spacing or an infrastructure clearance.
        The exported layer carries these distinctions so they survive beyond the notebook.

        Sources: [DeepForest public model](https://huggingface.co/weecology/deepforest-tree),
        [AHN products and vertical reference](https://www.ahn.nl/dataroom),
        [Beeldmateriaal licences and acquisition seasons](https://www.beeldmateriaal.nl/dataroom).
        """),
        ],
    )

    notebook(
        9,
        "vegetation-change",
        "A spectral change indicator with explicit confounders",
        "Compare same-tile Sentinel-2A C1 L2A observations from August 2020 and August 2021 "
        "near Lake Almanor. Show common valid coverage and threshold sensitivity instead "
        "of presenting a spectral difference as confirmed forest loss.",
        [
            code("""
        import rasterio
        from geoai_portfolio.rasters import scene_ndvi, reflectance, require_same_grid, map_array
        data = ensure_data("satellite")
        provenance = json.loads((data/"provenance.json").read_text())
        display(pd.DataFrame([{key: scene[key] for key in ["id", "datetime", "processing_baseline",
                                                          "sun_elevation", "scene_cloud_percent"]}
                              for scene in provenance["sentinel"]]))
        """),
            md("""
        ## Establish comparability before differencing

        Both observations are Sentinel-2A, tile T10TFK, C1 L2A, processing baseline 05.00,
        using the same UTM grid and native red/NIR 10 m bands. Saved metadata specifies scale
        0.0001 and offset −0.1 for both reprocessed dates. Acquisition year alone would not
        tell us the offset. SCL masks and physically invalid index inputs are applied per date,
        then intersected. The acquisitions are 12 August 2020 and 27 August 2021: the 15-day
        seasonal difference, atmosphere/smoke, illumination and water status remain confounders.
        Scene-wide cloud percentage does not guarantee a clear local crop.
        """),
            code("""
        before = scene_ndvi(data/"before.tif", data/"before-scl.tif")
        after = scene_ndvi(data/"after.tif", data/"after-scl.tif")
        with rasterio.open(data/"before.tif") as a, rasterio.open(data/"after.tif") as b:
            require_same_grid(a, b)
            pixel_area = abs(a.transform.a*a.transform.e-a.transform.b*a.transform.d)
        common_mask = np.ma.getmaskarray(before) | np.ma.getmaskarray(after)
        before_common = np.ma.array(before.data, mask=common_mask)
        after_common = np.ma.array(after.data, mask=common_mask)
        delta = after_common-before_common
        display(pd.DataFrame({"coverage": ["before valid", "after valid", "common valid", "excluded union"],
                              "pixels": [before.count(), after.count(), delta.count(), common_mask.sum()]}))
        """),
            code("""
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        with rasterio.open(data/"before.tif") as source:
            for ax, values, title in zip(axes[:2], [before_common, after_common],
                                         ["12 Aug 2020 · common support", "27 Aug 2021 · common support"]):
                image = map_array(ax, values, source, title, "YlGn", -1, 1)
                fig.colorbar(image, ax=ax, label="NDVI", shrink=.65)
            image = map_array(axes[2], delta, source, "After − before", "BrBG", -1, 1)
            fig.colorbar(image, ax=axes[2], label="ΔNDVI (unitless)", shrink=.65)
        fig.suptitle("Contains modified Copernicus Sentinel data (2020, 2021) · white = excluded", fontsize=10)
        plt.tight_layout(); plt.show()
        """),
            md("""
        ## Inspect RGB and threshold sensitivity

        Use the same reflectance-to-display stretch on both dates. The candidate area below
        uses ΔNDVI thresholds −0.2, −0.3 and −0.4 and requires initial NDVI above 0.4.
        The hectare totals are mapped indicator area on common valid support. They are not
        error-adjusted forest-loss estimates, and there is no reference sample for accuracy.
        """),
            code("""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        for ax, name, title in zip(axes, ["before", "after"], ["12 Aug 2020", "27 Aug 2021"]):
            with rasterio.open(data/f"{name}.tif") as source:
                rgb = np.stack([reflectance(source, band).filled(0) for band in [1, 2, 3]], axis=-1)
                map_array(ax, np.clip(rgb/.3, 0, 1), source, title)
        fig.suptitle("RGB · shared 0–0.3 reflectance stretch · contains Copernicus Sentinel data", fontsize=10)
        plt.tight_layout(); plt.show()
        sensitivity = pd.DataFrame([{"delta_threshold": threshold,
                    "candidate_ha": float(((delta < threshold) & (before_common > .4)).sum())*pixel_area/10000,
                    "common_valid_ha": delta.count()*pixel_area/10000} for threshold in [-.2, -.3, -.4]])
        display(sensitivity)
        fig, axes = plt.subplots(1, 2, figsize=(10, 3))
        axes[0].hist(delta.compressed(), bins=60, color="#0072B2")
        axes[0].set(xlabel="ΔNDVI", ylabel="Valid pixels", title="Difference distribution")
        axes[1].bar(sensitivity.delta_threshold.astype(str), sensitivity.candidate_ha, color="#A6611A")
        axes[1].set(xlabel="ΔNDVI threshold", ylabel="Candidate area (ha)", title="Decision sensitivity")
        plt.tight_layout(); plt.show()
        """),
            md("""
        ## Supported interpretation

        Large negative differences indicate reduced greenness on comparable valid pixels.
        Attribution to fire, clearing, drought or phenology needs independent event evidence,
        more observations, and reference sampling. Excluded pixels remain unknown. WorldCover
        is not used to turn the indicator into a validated loss label. A longer same-season
        time series and a stratified independent reference sample would be the next steps.
        """),
        ],
    )

    notebook(
        10,
        "lidar-evidence",
        "Keep observed conductors separate from a fitted curve",
        "Audit a public AHN4 point-cloud crop, select one observed conductor segment, "
        "fit an exploratory catenary, inspect withheld along-track blocks, and export "
        "measured points and generated geometry in distinct GeoPackage layers.",
        [
            code("""
        import laspy
        import geopandas as gpd
        from geoai_portfolio.lidar import coordinates, fit_catenary
        data = ensure_data("ahn")
        out = workspace("10-lidar")
        cloud = laspy.read(data/"corridor.laz")
        xyz = coordinates(cloud)
        original_xyz = xyz.copy()
        classes, counts = np.unique(cloud.classification, return_counts=True)
        names = {1: "Unclassified", 2: "Ground", 6: "Building", 9: "Water", 14: "Wire conductor"}
        display(pd.DataFrame({"class": classes, "meaning": [names.get(int(c), f"Provider code {c}")
                                                            for c in classes], "observations": counts}))
        provenance = json.loads((data/"provenance.json").read_text())
        print({"compound_crs": provenance["compound_crs"], "units": "metres",
               "UTC_range": provenance["gps_utc_ranges"]["corridor"],
               "CRS_assignment": provenance["crs_action"]})
        """),
            md("""
        ## Inspect evidence and select a bounded segment

        Coordinates and classifications are retained from the source. Class 1 is unclassified,
        not an automatic vegetation label. The overview thins points for display only; selection
        and fitting use all relevant observations. Class 14 supplies conductor candidates.
        We inspect a known straight corridor and choose northing 446100–446330 m with Z above
        30.5 m NAP, then separate parallel traces by their lateral position. This is an explicit
        case-specific selection, not a general network-reconstruction algorithm.
        """),
            code("""
        wire_mask = np.asarray(cloud.classification) == 14
        wires = xyz[wire_mask]
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        context = xyz[::100]
        axes[0].scatter(context[:, 0], context[:, 1], c="#cccccc", s=1, label="Context (display subsample)")
        axes[0].scatter(wires[:, 0], wires[:, 1], c="#D55E00", s=2, label="Observed class 14")
        axes[0].set(title="AHN4 · EPSG:28992", xlabel="Easting (m)", ylabel="Northing (m)", aspect="equal")
        axes[0].ticklabel_format(useOffset=False); axes[0].legend(fontsize=7)
        axes[1].scatter(wires[:, 1], wires[:, 2], s=3, color="#0072B2")
        axes[1].axvspan(446100, 446330, color="#E69F00", alpha=.15, label="Selected along-track interval")
        axes[1].set(title="Observed conductor profiles", xlabel="Northing (m)", ylabel="Height (m NAP)")
        axes[1].ticklabel_format(useOffset=False); axes[1].legend(fontsize=7)
        fig.suptitle("AHN4, CC0 · observed 12 Feb 2022", fontsize=10)
        plt.tight_layout(); plt.show()
        """),
            code("""
        from sklearn.cluster import DBSCAN
        candidate = wires[(wires[:, 1] > 446100) & (wires[:, 1] < 446330) & (wires[:, 2] > 30.5)]
        center = candidate[:, :2].mean(0)
        direction = np.linalg.svd(candidate[:, :2]-center, full_matrices=False)[2][0]
        lateral = (candidate[:, :2]-center) @ np.array([-direction[1], direction[0]])
        clusters = DBSCAN(eps=.4, min_samples=5).fit_predict(lateral[:, None])
        available = sorted(set(clusters)-{-1})
        if not available:
            raise ValueError("No supported lateral trace")
        chosen = max(available, key=lambda label: int((clusters == label).sum()))
        observed = candidate[clusters == chosen].copy()
        # Hold out every fifth 20-m northing block before fitting.
        block = np.floor((observed[:, 1]-446100)/20).astype(int)
        held_out = block % 5 == 2
        fit = fit_catenary(observed[~held_out])
        a, s0, z0 = fit["parameters"]
        s_test = (observed[held_out, :2]-fit["origin"]) @ fit["axis"]
        z_test = a*(np.cosh((s_test-s0)/a)-1)+z0
        test_residual = observed[held_out, 2]-z_test
        display(pd.DataFrame({"partition": ["fit", "withheld along-track blocks"],
                              "points": [(~held_out).sum(), held_out.sum()],
                              "vertical_RMSE_m": [fit["rmse_m"], np.sqrt(np.mean(test_residual**2))]}))
        print("Fitted parameters [a, s0, z0]:", np.round(fit["parameters"], 3))
        """),
            md("""
        ## A small residual does not establish operational accuracy

        The fitted equation is `z = a(cosh((s − s0)/a) − 1) + z0`, with a PCA horizontal axis.
        Robust least squares uses a 0.25 m residual scale and bounded parameters. Withheld
        along-track blocks test local interpolation on this acquisition. They do not measure
        absolute survey error, generalisation to other spans, or conductor movement under
        different load, wind or temperature. No independent control points or complete vertical
        accuracy budget are available, so these data do not support a clearance decision.
        """),
            code("""
        generated = fit["generated"]
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        axes[0].scatter(observed[~held_out, 1], observed[~held_out, 2], s=10, color="#0072B2", label="Fit observations")
        axes[0].scatter(observed[held_out, 1], observed[held_out, 2], s=20, marker="x", color="#D55E00", label="Withheld blocks")
        axes[0].plot(generated[:, 1], generated[:, 2], color="#009E73", label="Generated catenary")
        axes[0].set(xlabel="Northing (EPSG:28992; m)", ylabel="Height (m NAP)", title="Observation versus model")
        axes[0].ticklabel_format(useOffset=False); axes[0].legend(fontsize=8)
        axes[1].scatter(s_test, test_residual, color="#D55E00", s=15)
        axes[1].axhline(0, color="gray", linewidth=.8)
        axes[1].set(xlabel="Along-track distance from fit origin (m)", ylabel="Observed − fitted Z (m)",
                    title="Withheld-block residuals")
        plt.tight_layout(); plt.show()
        """),
            code("""
        from shapely.geometry import Point, LineString
        evidence = gpd.GeoDataFrame({"source_row": np.flatnonzero(wire_mask),
                                    "classification": 14, "evidence": "observed", "height_datum": "NAP EPSG:5709"},
                                   geometry=[Point(row) for row in wires], crs=28992)
        modeled = gpd.GeoDataFrame({"evidence": ["generated catenary"], "extrapolation": [False],
                                   "height_datum": ["NAP EPSG:5709"], "n_fit_points": [int((~held_out).sum())]},
                                  geometry=[LineString(generated)], crs=28992)
        evidence.to_file(out/"conductor-evidence.gpkg", layer="observed_conductors", driver="GPKG")
        modeled.to_file(out/"conductor-evidence.gpkg", layer="generated_curve", driver="GPKG")
        np.testing.assert_array_equal(xyz, original_xyz)
        from geoai_portfolio.io import write_json, sha256
        write_json(out/"fit-provenance.json", {"source_sha256": sha256(data/"corridor.laz"),
                   "selection": {"northing_m": [446100, 446330], "minimum_z_NAP_m": 30.5,
                                 "lateral_DBSCAN_eps_m": .4, "min_samples": 5},
                   "parameters": fit["parameters"].tolist(), "source_coordinates_unchanged": True,
                   "fit_rmse_m": fit["rmse_m"], "withheld_rmse_m": float(np.sqrt(np.mean(test_residual**2)))})
        display(pd.DataFrame({"layer": ["observed_conductors", "generated_curve"],
                              "features": [len(evidence), len(modeled)],
                              "role": ["Original measured XYZ", "Fitted geometry within observed support"]}))
        """),
            md("""
        ## Transferable engineering decision

        Preserve measured records and expose assumptions with generated geometry. A smooth
        curve is useful for inspection, but it must not erase gaps or become a substitute for
        observations without qualification. Separate layers, source-row identity, CRS, vertical
        reference, fitting parameters and residuals allow another reader to audit that distinction.

        [AHN source conventions](https://www.ahn.nl/dataroom) and
        [laspy documentation](https://laspy.readthedocs.io/en/latest/) describe the data interfaces.
        """),
        ],
    )


def generate():
    build()
    build_remaining()
    subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(NOTEBOOKS), "--fix", "--select", "I,F"],
        check=True,
    )
    subprocess.run([sys.executable, "-m", "ruff", "format", str(NOTEBOOKS)], check=True)
    subprocess.run([sys.executable, "-m", "ruff", "check", str(NOTEBOOKS)], check=True)


if __name__ == "__main__":
    generate()
