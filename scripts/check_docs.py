"""Validate Markdown navigation and export diagrams for an optional render check."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
PARSER = MarkdownIt("commonmark").enable("table")


def inspect_markdown(path: Path) -> tuple[set[str], list[str], list[dict[str, str]]]:
    """Extract GitHub-style heading anchors, links, and Mermaid sources."""
    tokens = PARSER.parse(path.read_text(encoding="utf-8"))
    anchors: set[str] = set()
    occurrences: Counter[str] = Counter()
    links: list[str] = []
    diagrams: list[dict[str, str]] = []
    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            children = tokens[index + 1].children or []
            title = "".join(
                child.content
                for child in children
                if child.type
                in {
                    "text",
                    "code_inline",
                    "emoji",
                    "html_inline",
                }
            )
            slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
            suffix = f"-{occurrences[slug]}" if occurrences[slug] else ""
            anchors.add(slug + suffix)
            occurrences[slug] += 1
        if token.type == "fence" and token.info.strip() == "mermaid":
            diagrams.append({"path": path.relative_to(ROOT).as_posix(), "source": token.content})
        for child in token.children or []:
            if child.type == "link_open":
                links.append(child.attrGet("href") or "")
            elif child.type == "image":
                links.append(child.attrGet("src") or "")
    return anchors, links, diagrams


def main() -> None:
    """Check local targets, fragments, collection counts, and reachability."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagrams-json", type=Path)
    args = parser.parse_args()
    paths = [
        ROOT / "README.md",
        ROOT / "notebooks" / "README.md",
        *sorted((ROOT / "docs").rglob("*.md")),
    ]
    documents = {path: inspect_markdown(path) for path in paths}
    errors: list[str] = []
    edges: dict[Path, set[Path]] = {path: set() for path in paths}
    external: set[str] = set()
    diagrams = []
    for path, (_, links, page_diagrams) in documents.items():
        diagrams.extend(page_diagrams)
        for href in links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                if url.scheme not in {"https", "mailto"}:
                    errors.append(f"{path.relative_to(ROOT)}: unexpected URL scheme in {href}")
                external.add(href)
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.is_relative_to(ROOT) or not target.is_file():
                errors.append(f"{path.relative_to(ROOT)}: missing/escaping target {href}")
                continue
            if target in documents:
                edges[path].add(target)
                if url.fragment and unquote(url.fragment) not in documents[target][0]:
                    errors.append(f"{path.relative_to(ROOT)}: missing anchor {href}")
        content = path.read_text(encoding="utf-8")
        if "\ufffd" in content or re.search(r"\b(?:TODO|FIXME|TBD)\b", content):
            errors.append(f"{path.relative_to(ROOT)}: unfinished or invalid text")
    expected = {"articles": 10, "tutorials": 4, "projects": 15}
    counts = {name: len(list((ROOT / "docs" / name).glob("*.md"))) for name in expected}
    if counts != expected:
        errors.append(f"Collection counts differ: {counts}; expected {expected}")
    if len(diagrams) != 10:
        errors.append(f"Expected 10 Mermaid diagrams, found {len(diagrams)}")
    for path in (ROOT / "docs" / "articles").glob("*.md"):
        if len(documents[path][2]) != 1:
            errors.append(f"{path.relative_to(ROOT)}: expected one conceptual diagram")
    seen: set[Path] = set()
    pending = [ROOT / "README.md"]
    while pending:
        current = pending.pop()
        if current not in seen:
            seen.add(current)
            pending.extend(edges[current] - seen)
    errors.extend(f"Unreachable page: {path.relative_to(ROOT)}" for path in set(paths) - seen)
    if errors:
        raise SystemExit("\n".join(errors))
    if args.diagrams_json:
        args.diagrams_json.parent.mkdir(parents=True, exist_ok=True)
        args.diagrams_json.write_text(json.dumps(diagrams, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "markdown_pages": len(paths),
                **counts,
                "mermaid_diagrams": len(diagrams),
                "external_urls": len(external),
                "local_links": "valid",
                "all_pages_reachable": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
