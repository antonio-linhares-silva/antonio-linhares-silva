"""Verified public downloads and portable experiment directories."""

import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def root() -> Path:
    """Find the checkout from a notebook or use an explicitly configured data root."""
    if os.environ.get("GEOAI_ROOT"):
        return Path(os.environ["GEOAI_ROOT"]).resolve()
    for parent in (Path.cwd(), *Path.cwd().parents):
        if (parent / "data" / "manifest.json").exists():
            return parent
    raise FileNotFoundError("Run inside the checkout or set GEOAI_ROOT to its directory.")


def sha256(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
        ) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def session() -> requests.Session:
    client = requests.Session()
    retry = Retry(total=4, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    client.mount("https://", HTTPAdapter(max_retries=retry))
    client.headers["User-Agent"] = "geoai-public-notebooks/2.0"
    return client


def download(url: str, path: Path, expected: str | None = None) -> Path:
    """Atomic download. Published packs always pass a pinned SHA-256."""
    path = Path(path)
    if path.exists() and (expected is None or sha256(path) == expected):
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    try:
        with session().get(url, stream=True, timeout=(30, 120)) as response:
            response.raise_for_status()
            with temporary.open("wb") as stream:
                for chunk in response.iter_content(2**20):
                    stream.write(chunk)
        if expected is not None and sha256(temporary) != expected:
            raise ValueError(f"Checksum mismatch: {path.name}")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def ensure_data(pack: str) -> Path:
    """Download a release pack once and validate every extracted member on reuse."""
    base = root()
    manifest = json.loads((base / "data" / "manifest.json").read_text())
    entry = manifest["packs"][pack]
    destination = base / "data" / "prepared" / pack
    valid = destination.exists() and all(
        (destination / name).is_file() and sha256(destination / name) == digest
        for name, digest in entry["files"].items()
    )
    if not valid:
        archive = download(entry["url"], base / "data" / "cache" / (pack + ".zip"), entry["sha256"])
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as bundle:
            if set(bundle.namelist()) != set(entry["files"]):
                raise ValueError("Unexpected archive members")
            for name in bundle.namelist():
                target = (destination / name).resolve()
                if not target.is_relative_to(destination.resolve()):
                    raise ValueError("Unsafe archive member")
                content = bundle.read(name)
                if hashlib.sha256(content).hexdigest() != entry["files"][name]:
                    raise ValueError(f"Invalid archive member: {name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
    return destination


def workspace(name: str) -> Path:
    destination = root() / "outputs" / "notebooks" / name
    destination.mkdir(parents=True, exist_ok=True)
    return destination
