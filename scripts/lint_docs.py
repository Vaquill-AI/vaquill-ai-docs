#!/usr/bin/env python3
"""Lint the docs. Exits non-zero and prints file:line for every violation.

Checks:
  1. Every page published in docs.json has a description of at most 140 characters.
  2. No em dash or en dash in any .mdx file, docs.json, llms.txt or README.md.
  3. No hard-wrapped prose (a sentence split across two lines).
  4. A short list of banned phrases in prose.

Pages that .mintignore hides are skipped. Snippets are always checked.
Run from anywhere: python3 scripts/lint_docs.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_DESCRIPTION = 140
DASHES = ("—", "–")  # em dash, en dash

BANNED = [
    "leverage",
    "leveraging",
    "seamless",
    "seamlessly",
    "cutting-edge",
    "state-of-the-art",
    "best-in-class",
    "game-changing",
    "revolutionary",
    "delve",
    "in order to",
    "legal AI suite",
]
BANNED_RE = re.compile(r"\b(" + "|".join(re.escape(b) for b in BANNED) + r")\b", re.I)

LIST_RE = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
STRUCTURAL_RE = re.compile(r"^\s*(#|\||<|>|```|~~~|---|import |export |\{/\*|\*\*\*|:::)")


def published_pages() -> list[str]:
    docs = json.loads((ROOT / "docs.json").read_text(encoding="utf-8"))
    pages: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, str):
            pages.append(node)
        elif isinstance(node, dict):
            if node.get("root"):
                pages.append(node["root"])
            for key in ("pages", "groups"):
                for child in node.get(key, []):
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    for tab in docs["navigation"]["tabs"]:
        walk(tab)
    return list(dict.fromkeys(pages))


def ignored_prefixes() -> list[str]:
    f = ROOT / ".mintignore"
    out = []
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


def is_ignored(rel: str, patterns: list[str]) -> bool:
    for p in patterns:
        if p.endswith("/") and rel.startswith(p):
            return True
        if rel == p:
            return True
    return False


def split_frontmatter(text: str) -> tuple[dict[str, tuple[str, int]], int]:
    """Return ({key: (value, line_no)}, first body line index, 0-based)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, 0
    fm: dict[str, tuple[str, int]] = {}
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return fm, i + 1
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", lines[i])
        if m:
            value = m.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fm[m.group(1)] = (value, i + 1)
    return fm, 0


def is_prose(line: str) -> bool:
    s = line.strip()
    return bool(s) and not STRUCTURAL_RE.match(line) and not LIST_RE.match(line)


def check_body(rel: str, lines: list[str], start: int, errors: list[str]) -> None:
    in_fence = False
    prev_prose = False
    prev_text = ""
    prev_no = 0
    for i in range(start, len(lines)):
        line = lines[i]
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            prev_prose = False
            continue
        if in_fence:
            continue
        is_list = bool(LIST_RE.match(line))
        indented_cont = bool(re.match(r"^\s{2,}\S", line)) and not is_list and not STRUCTURAL_RE.match(line)
        prose = is_prose(line) or indented_cont
        # Hard wrap: previous line is prose or list text that stops mid-sentence,
        # and this line carries on.
        if prev_prose and prose:
            last = prev_text.rstrip()[-1:]
            if last and (last.isalnum() or last in ",;-"):
                errors.append(f"{rel}:{prev_no}: hard-wrapped prose (sentence continues on the next line)")
        if is_prose(line) or is_list or indented_cont:
            prev_prose = True
            prev_text = line
            prev_no = i + 1
        else:
            prev_prose = False
        stripped = re.sub(r"`[^`]*`", "", line)
        if not STRUCTURAL_RE.match(line) or is_list:
            m = BANNED_RE.search(stripped)
            if m:
                errors.append(f"{rel}:{i + 1}: banned phrase '{m.group(1)}'")


def main() -> int:
    errors: list[str] = []
    patterns = ignored_prefixes()
    pages = published_pages()
    files: list[Path] = []
    published = set()
    for page in pages:
        f = ROOT / f"{page}.mdx"
        if not f.exists():
            errors.append(f"docs.json:1: page '{page}' is in the navigation but {page}.mdx does not exist")
            continue
        files.append(f)
        published.add(f)
    for f in sorted((ROOT / "snippets").glob("*.mdx")):
        if f not in published:
            files.append(f)
    for f in sorted(ROOT.rglob("*.mdx")):
        rel = f.relative_to(ROOT).as_posix()
        if f in files or is_ignored(rel, patterns) or rel.startswith((".", "node_modules")):
            continue
        files.append(f)

    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding="utf-8")
        lines = text.split("\n")
        fm, body_start = split_frontmatter(text)
        page = rel[:-4]
        if page in pages:
            if "description" not in fm or not fm["description"][0]:
                errors.append(f"{rel}:1: missing description")
            else:
                value, no = fm["description"]
                if len(value) > MAX_DESCRIPTION:
                    errors.append(f"{rel}:{no}: description is {len(value)} characters (max {MAX_DESCRIPTION})")
        for n, line in enumerate(lines, 1):
            if any(d in line for d in DASHES):
                errors.append(f"{rel}:{n}: em or en dash")
        check_body(rel, lines, body_start, errors)

    for name in ("docs.json", "llms.txt", "README.md"):
        f = ROOT / name
        if not f.exists():
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            if any(d in line for d in DASHES):
                errors.append(f"{name}:{n}: em or en dash")

    for e in errors:
        print(e)
    if errors:
        print(f"\n{len(errors)} violation(s).", file=sys.stderr)
        return 1
    print("docs lint: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
