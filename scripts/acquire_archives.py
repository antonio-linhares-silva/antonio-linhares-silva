"""Maintainer acquisition: full upstream archives, never included in Git."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from geoai_portfolio.io import download, sha256

SOURCES = {
    "EuroSATallBands.zip": (
        "https://huggingface.co/datasets/torchgeo/eurosat/resolve/"
        "1ce6f1bfb56db63fd91b6ecc466ea67f2509774c/EuroSATallBands.zip",
        "751f070f9bffa2eed48b24ca2dd0b02959280c08837e8c9a5532a67ba611df59",
    ),
    "C_39FN1.LAZ": (
        "https://basisdata.nl/hwh-ahn/ahn4/01_LAZ/C_39FN1.LAZ",
        "916757917f7ff2517c8d1e5f906377035b29e0c46f9c65fb5b3baf58bc5a9dfa",
    ),
    "M_39FN1.zip": (
        "https://basisdata.nl/hwh-ahn/ahn4/02a_DTM_0.5m/M_39FN1.zip",
        "16a5156bb237d43d1121fcfa6dda98f3f60e7dddc3637c2525f864b2e6ad7bb2",
    ),
    "R_39FN1.zip": (
        "https://basisdata.nl/hwh-ahn/ahn4/03a_DSM_0.5m/R_39FN1.zip",
        "f557aee220db5ef4f1f469b5c2402aab3998e288783fa304e6f9f5fa16a112d3",
    ),
}


def acquire(item):
    name, (url, digest) = item
    print(f"Downloading {name}", flush=True)
    path = download(url, Path("data/cache") / name, digest)
    print(f"Verified {name}: {sha256(path)} ({path.stat().st_size:,} bytes)", flush=True)


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(acquire, SOURCES.items()))
