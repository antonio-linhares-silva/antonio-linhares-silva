"""Pretrained detection boxes and cautious AHN surface-height summaries."""

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box

from .rasters import require_same_grid

DEEPFOREST_REVISION = "cc21436bc5d572dde8ff5f93c1e71a32f563cace"


def detect_boxes(rgb_path, device="cpu", score_threshold=0.5):
    import torch
    from deepforest import main
    from torchvision.ops import nms

    from .neural import device_name

    detector = main.deepforest()
    detector.load_model("weecology/deepforest-tree", revision=DEEPFOREST_REVISION)
    selected_device = device_name(device)
    detector.model.to(selected_device).eval()
    with rasterio.open(rgb_path) as source:
        image = source.read().astype("float32") / 255
        boxes, scores = [], []
        # Explicit tensor placement also supports CPU. DeepForest's single-image
        # convenience method in 2.1.0 creates CPU tensors even for a CUDA model.
        with torch.inference_mode():
            for row in range(0, source.height, 448):
                for col in range(0, source.width, 448):
                    chip = torch.from_numpy(image[:, row : row + 512, col : col + 512]).to(
                        selected_device
                    )
                    prediction = detector.model([chip])[0]
                    offset = torch.tensor([col, row, col, row], device=selected_device)
                    boxes.append((prediction["boxes"] + offset).cpu())
                    scores.append(prediction["scores"].cpu())
        boxes, scores = torch.cat(boxes), torch.cat(scores)
        selected = nms(boxes, scores, iou_threshold=0.15)
        selected = selected[scores[selected] >= score_threshold]
        predictions = pd.DataFrame(
            boxes[selected].numpy(), columns=["xmin", "ymin", "xmax", "ymax"]
        )
        predictions["score"] = scores[selected].numpy()
        predictions["label"] = "Tree"
        if predictions.empty:
            raise ValueError(
                "No detection boxes; inspect imagery and model domain before proceeding"
            )
        geometries = []
        for row in predictions.itertuples():
            left, top = source.transform * (row.xmin, row.ymin)
            right, bottom = source.transform * (row.xmax, row.ymax)
            geometries.append(box(left, bottom, right, top))
        result = gpd.GeoDataFrame(predictions, geometry=geometries, crs=source.crs)
        result["geometry_role"] = "predicted bounding box"
        result["model_revision"] = DEEPFOREST_REVISION
    return result.reset_index(drop=True)


def height_surface(dsm_path, dtm_path):
    with rasterio.open(dsm_path) as dsm, rasterio.open(dtm_path) as dtm:
        require_same_grid(dsm, dtm)
        values = dsm.read(1, masked=True) - dtm.read(1, masked=True)
        # Negative differences remain visible in the QA result; never silently clip.
        return values


def summarize_boxes(boxes, height, reference_path, min_valid=0.8):
    result = boxes.copy()
    with rasterio.open(reference_path) as source:
        if boxes.crs != source.crs:
            raise ValueError("Box and height raster CRS differ")
        if height.shape != (source.height, source.width):
            raise ValueError("Height shape does not match reference")
        summaries = []
        for geometry in boxes.geometry:
            inside = geometry_mask([geometry], height.shape, source.transform, invert=True)
            values = np.ma.masked_where(~inside, height)
            count = int(values.count())
            coverage = count / int(inside.sum()) if inside.any() else 0
            summaries.append(
                {
                    "valid_fraction": coverage,
                    "valid_pixels": count,
                    "surface_p95_m": float(np.percentile(values.compressed(), 95))
                    if count and coverage >= min_valid
                    else np.nan,
                    "height_status": "box surface statistic"
                    if coverage >= min_valid
                    else "insufficient coverage",
                }
            )
    for key in summaries[0] if summaries else []:
        result[key] = [row[key] for row in summaries]
    return result
