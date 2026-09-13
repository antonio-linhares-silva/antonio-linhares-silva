"""Validate executed notebook structure, outputs, links, and public-data manifest."""

import ast
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import nbformat
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]


def main():
    paths = sorted((ROOT / "notebooks").glob("*.ipynb"))
    assert len(paths) == 10, "Expected ten notebooks"
    outputs = 0
    for path in paths:
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        assert notebook.metadata.get("geoai", {}).get("executed"), path.name
        code_cells = [c for c in notebook.cells if c.cell_type == "code"]
        assert [c.execution_count for c in code_cells] == list(range(1, len(code_cells) + 1)), (
            path.name
        )
        figures = 0
        for cell in notebook.cells:
            if cell.cell_type == "code":
                ast.parse(cell.source)
                for output in cell.outputs:
                    assert output.output_type != "error", path.name
                    figures += "image/png" in output.get("data", {})
                    text = str(output.get("text", "")) + str(
                        output.get("data", {}).get("text/plain", "")
                    )
                    assert not re.search(
                        r"C:\\\\?Users\\|/home/[^/]+/|gh[pousr]_[A-Za-z0-9]{20,}", text
                    ), path.name
            else:
                for token in MarkdownIt().parse(cell.source):
                    for child in token.children or []:
                        if child.type != "link_open":
                            continue
                        link = urlsplit(child.attrGet("href"))
                        if not link.scheme and link.path:
                            target = (path.parent / unquote(link.path)).resolve()
                            assert target.is_relative_to(ROOT) and target.is_file(), (
                                path.name,
                                link.path,
                            )
        assert figures >= 1, f"No visible figure: {path.name}"
        outputs += figures
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    assert set(manifest["packs"]) == {"satellite", "eurosat", "ahn"}
    assert sum(entry["bytes"] for entry in manifest["packs"].values()) < 500_000_000
    for entry in manifest["packs"].values():
        assert re.fullmatch("[0-9a-f]{64}", entry["sha256"])
        assert entry["url"].startswith("https://github.com/antonio-linhares-silva/")
    print(
        json.dumps(
            {
                "executed_notebooks": len(paths),
                "png_outputs": outputs,
                "data_packs": 3,
                "local_links": "valid",
            }
        )
    )


if __name__ == "__main__":
    main()
