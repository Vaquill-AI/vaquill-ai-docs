#!/usr/bin/env python3
"""Rewrite the "Which jurisdictions name which levels" table in api-guide/concepts/hierarchy.mdx.

    python3 scripts/container_names_table.py <census.json>

`census.json` is the output of the backend repository's container-name census
(`python -m scripts.us_corpus.statutes.container_names.census --live --json-out <file>`), which reads
the breadcrumb of every state statute section. The table is DERIVED: edit the census or this script,
never the rows. The text between the two `census:` markers is replaced; nothing else in the page is touched.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / "api-guide" / "concepts" / "hierarchy.mdx"
START, END = "{/* census:start */}", "{/* census:end */}"

NAMES = {
    "ak": "Alaska", "al": "Alabama", "ar": "Arkansas", "as": "American Samoa", "az": "Arizona",
    "ca": "California", "co": "Colorado", "ct": "Connecticut", "dc": "District of Columbia",
    "de": "Delaware", "fl": "Florida", "ga": "Georgia", "gu": "Guam", "hi": "Hawaii", "ia": "Iowa",
    "id": "Idaho", "il": "Illinois", "in": "Indiana", "ks": "Kansas", "ky": "Kentucky",
    "la": "Louisiana", "ma": "Massachusetts", "md": "Maryland", "me": "Maine", "mi": "Michigan",
    "mn": "Minnesota", "mo": "Missouri", "mp": "Northern Mariana Islands", "ms": "Mississippi",
    "mt": "Montana", "nc": "North Carolina", "nd": "North Dakota", "ne": "Nebraska",
    "nh": "New Hampshire", "nj": "New Jersey", "nm": "New Mexico", "nv": "Nevada", "ny": "New York",
    "oh": "Ohio", "ok": "Oklahoma", "or": "Oregon", "pa": "Pennsylvania", "pr": "Puerto Rico",
    "ri": "Rhode Island", "sc": "South Carolina", "sd": "South Dakota", "tn": "Tennessee",
    "tx": "Texas", "ut": "Utah", "va": "Virginia", "vi": "U.S. Virgin Islands", "vt": "Vermont",
    "wa": "Washington", "wi": "Wisconsin", "wv": "West Virginia", "wy": "Wyoming",
}
ORDER = ["title", "subtitle", "division", "part", "subpart", "chapter", "subchapter", "article",
         "subarticle", "act"]
#: Crumbs that are not containers: a printing marker after the section, or a state's own catch-all.
SKIP = {"version", "code", "section", "other", "container"}


def share(r: dict) -> str:
    n, k = r["containers"], r["containers_named"]
    if k == n:
        return "all"
    if k == 0:
        return "none"
    return f"{k:,} of {n:,}"


def row(code: str, data: dict) -> str:
    levels = {k: v for k, v in data["levels"].items() if k not in SKIP}
    if not levels:
        return f"| {NAMES.get(code, code)} | no container level above its sections | |"
    ordered = sorted(levels, key=lambda lv: (ORDER.index(lv) if lv in ORDER else 99, lv))
    recorded = ", ".join(ordered)
    gaps = [f"{lv}: {share(levels[lv])}" for lv in ordered if levels[lv]["containers_named"] < levels[lv]["containers"]]
    return f"| {NAMES.get(code, code)} | {recorded} | {'; '.join(gaps) if gaps else 'every level named'} |"


def render(census: dict) -> str:
    lines = [
        START,
        f"Measured {census['date']} across every state statute section.",
        "A container counts as named when any of its sections carries its heading in `breadcrumb`, or in `chapterName` or `articleName`.",
        "The second column lists the levels the jurisdiction records above its sections.",
        "The third lists each level that is not fully named, with how many of its containers carry a heading.",
        "",
        "| Jurisdiction | Levels recorded | Levels not fully named |",
        "|---|---|---|",
    ]
    for code in sorted(NAMES, key=lambda c: NAMES[c]):
        if code in census["states"]:
            lines.append(row(code, census["states"][code]))
        else:
            lines.append(f"| {NAMES[code]} | | not in this reading |")
    lines += ["", END]
    return "\n".join(lines)


def main() -> int:
    census = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    text = PAGE.read_text(encoding="utf-8")
    if START not in text:
        text = text.replace("{{CENSUS_TABLE}}", f"{START}\n{END}")
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    PAGE.write_text(head + render(census) + tail, encoding="utf-8")
    print(f"wrote {PAGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
