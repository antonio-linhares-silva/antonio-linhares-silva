"""Stream AHN4 once to inventory classes and retain only observed conductor points."""

from collections import Counter
from pathlib import Path

import laspy
import numpy as np

from geoai_portfolio.io import write_json


def inspect():
    counts = Counter()
    wires = []
    context = []
    with laspy.open("data/cache/C_39FN1.LAZ") as source:
        print(
            source.header,
            source.header.mins,
            source.header.maxs,
            source.header.parse_crs(),
            flush=True,
        )
        for i, points in enumerate(source.chunk_iterator(2_000_000)):
            classes, frequency = np.unique(points.classification, return_counts=True)
            counts.update(dict(zip(classes.tolist(), frequency.tolist())))
            mask = np.isin(points.classification, [13, 14])
            if mask.any():
                wires.append(
                    np.column_stack(
                        [
                            np.asarray(points.x)[mask],
                            np.asarray(points.y)[mask],
                            np.asarray(points.z)[mask],
                            np.asarray(points.classification)[mask],
                            points.gps_time[mask],
                        ]
                    )
                )
            indices = np.arange(0, len(points), 2000)
            context.append(
                np.column_stack(
                    [
                        np.asarray(points.x)[indices],
                        np.asarray(points.y)[indices],
                        np.asarray(points.z)[indices],
                        np.asarray(points.classification)[indices],
                    ]
                )
            )
            if i % 25 == 0:
                print(i, counts, flush=True)
        Path("outputs/source-discovery").mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            "outputs/source-discovery/ahn-scan.npz",
            wires=np.concatenate(wires),
            context=np.concatenate(context),
        )
        write_json(
            Path("outputs/source-discovery/ahn-scan.json"),
            {
                "counts": counts,
                "crs_wkt": str(source.header.parse_crs()),
                "bounds_min": source.header.mins.tolist(),
                "bounds_max": source.header.maxs.tolist(),
                "point_count": source.header.point_count,
                "gps_time_type": str(source.header.global_encoding.gps_time_type),
            },
        )
    print("Complete", counts, flush=True)


if __name__ == "__main__":
    inspect()
