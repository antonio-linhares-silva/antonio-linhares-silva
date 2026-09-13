"""Installed command-line interface; all inputs and outputs are explicit paths."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    raster = commands.add_parser("ndvi", help="Produce a masked NDVI COG in bounded windows")
    raster.add_argument("--scene", required=True, type=Path)
    raster.add_argument("--scl", required=True, type=Path)
    raster.add_argument("--output", required=True, type=Path)
    raster.add_argument("--window-size", type=int, default=128)
    model = commands.add_parser("predict", help="Predict using a local MLflow model and CSV table")
    model.add_argument("--model", required=True, type=Path)
    model.add_argument("--input", required=True, type=Path)
    model.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "ndvi":
        from .rasters import windowed_ndvi

        print(json.dumps(windowed_ndvi(args.scene, args.scl, args.output, args.window_size)))
    else:
        import pandas as pd

        from .artifacts import predict_table

        result = predict_table(args.model, pd.read_csv(args.input))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"prediction": result}).to_csv(args.output, index=False)
        print(json.dumps({"predictions": len(result)}))


if __name__ == "__main__":
    main()
