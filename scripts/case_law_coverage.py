#!/usr/bin/env python3
"""Write the court tables in api-guide/coverage/case-law.mdx.

With live counts (free endpoint, needs a key):
    VAQUILL_API_KEY=vq_key_... python3 scripts/case_law_coverage.py

Court codes only, from the backend court registry:
    python3 scripts/case_law_coverage.py --registry <folder>

Counts under 1,000 print as Yes: the docs show large totals only. Larger counts are rounded
down, because one decision can be held as more than one record.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "api-guide" / "coverage" / "case-law.mdx"
BEGIN, END = "{/* BEGIN court-tables */}", "{/* END court-tables */}"
URL = "https://api.vaquill.ai/api/v1/us/courts?include=coverage&limit=100&offset={}"
SMALL = 1000

STATES = """AL Alabama|AK Alaska|AZ Arizona|AR Arkansas|CA California|CO Colorado|CT Connecticut|DE Delaware
DC District of Columbia|FL Florida|GA Georgia|HI Hawaii|ID Idaho|IL Illinois|IN Indiana|IA Iowa|KS Kansas
KY Kentucky|LA Louisiana|ME Maine|MD Maryland|MA Massachusetts|MI Michigan|MN Minnesota|MS Mississippi
MO Missouri|MT Montana|NE Nebraska|NV Nevada|NH New Hampshire|NJ New Jersey|NM New Mexico|NY New York
NC North Carolina|ND North Dakota|OH Ohio|OK Oklahoma|OR Oregon|PA Pennsylvania|RI Rhode Island
SC South Carolina|SD South Dakota|TN Tennessee|TX Texas|UT Utah|VT Vermont|VA Virginia|WA Washington
WV West Virginia|WI Wisconsin|WY Wyoming|AS American Samoa|GU Guam|MP Northern Mariana Islands
PR Puerto Rico|VI US Virgin Islands"""

FEDERAL = """SCOTUS Supreme Court|CA1 First Circuit|CA2 Second Circuit|CA3 Third Circuit|CA4 Fourth Circuit
CA5 Fifth Circuit|CA6 Sixth Circuit|CA7 Seventh Circuit|CA8 Eighth Circuit|CA9 Ninth Circuit
CA10 Tenth Circuit|CA11 Eleventh Circuit|CADC D.C. Circuit|CAFC Federal Circuit
TAX Tax Court|USCFC Court of Federal Claims|CIT Court of International Trade
CAVC Court of Appeals for Veterans Claims|JPML Panel on Multidistrict Litigation"""

# The last court of appeal for criminal cases, served with level=appellate.
ALSO_TOP = {"US_OK_CRIMINAL_APPEALS"}
# Served with level=appellate, but not appeals courts.
NOT_APPEALS = {
    "US_DE_CHANCERY", "US_MA_DISTRICT", "US_TX_PANEL_ON_MULTIDISTRICT_LITIGATION",
    "US_CT_SUPERIOR", "US_DE_SUPERIOR", "US_GU_SUPERIOR", "US_MA_SUPERIOR",
    "US_NC_SUPERIOR", "US_RI_SUPERIOR", "US_VT_SUPERIOR",
}

# label, system, levels, the filter a reader passes
GROUPS = (
    ("US Supreme Court", "federal", ("supreme",), "system=federal&level=supreme"),
    ("Federal courts of appeals", "federal", ("appellate",), "system=federal&level=appellate"),
    ("Federal district courts", "federal", ("trial",), "system=federal&level=trial"),
    ("Bankruptcy courts", "federal", ("bankruptcy",), "system=federal&level=bankruptcy"),
    ("Bankruptcy appellate panels", "federal", ("bankruptcy_appellate",), "system=federal&level=bankruptcy_appellate"),
    ("Federal specialty courts", "federal", ("special",), "system=federal&level=special"),
    ("Federal agencies", "federal", ("agency",), "system=federal&level=agency"),
    ("US Attorney General", "federal", ("attorney_general",), "system=federal&level=attorney_general"),
    ("State high courts", "state", ("supreme",), "system=state&level=supreme"),
    ("State appeals courts", "state", ("appellate",), "system=state&level=appellate"),
    ("State trial courts", "state", ("trial",), "system=state&level=trial"),
    ("State special courts", "state", ("special",), "system=state&level=special"),
    ("State agencies", "state", ("agency",), "system=state&level=agency"),
    ("State attorneys general", "state", ("attorney_general",), "system=state&level=attorney_general"),
    ("Territorial courts", "territorial", None, "system=territorial"),
    ("Tribal courts", "tribal", None, "system=tribal"),
    ("Military courts", "military", None, "system=military"),
)


def pairs(block: str) -> list[list[str]]:
    return [item.split(" ", 1) for item in block.replace("\n", "|").split("|")]


def from_registry(folder: Path) -> list[dict]:
    changes: dict[str, dict[str, str]] = {}
    with open(folder / "court_overrides.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            changes.setdefault(r["source_court"], {})[r["field"]] = r["value"]
    courts = []
    for name in ("courts.csv", "courts_own.csv"):
        with open(folder / name, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                r.update(changes.get(r["source_court"], {}))
                if r.get("exclude") == "true":
                    continue
                courts.append({
                    "courtId": r["court_id"], "system": r["system"], "level": r["level"],
                    "stateCode": r["state_code"], "isActive": r["is_active"] == "true", "endDate": r.get("end_date") or None,
                    "citationString": r["citation_string"], "coverage": None,
                })
    return courts


def from_api(key: str) -> list[dict]:
    courts: list[dict] = []
    while True:
        req = urllib.request.Request(
            URL.format(len(courts)),
            headers={"Authorization": f"Bearer {key}", "User-Agent": "vaquill-docs-coverage"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                page = json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise SystemExit(f"GET /us/courts answered {e.code}") from None
            time.sleep(int(e.headers.get("Retry-After") or 60))
            continue
        courts += page["results"]
        if not page["hasMore"]:
            return courts
        if not page["results"]:
            raise SystemExit("hasMore is true on an empty page")


def rounded(n: int) -> str:
    if n < SMALL:
        return "Yes"
    if n >= 1_000_000:
        return f"{n // 100_000 / 10:.1f}M+"
    step = 1_000 if n >= 10_000 else 100
    return f"{n // step * step:,}+"


def held(courts: list[dict]) -> list[str]:
    cov = [c["coverage"] for c in courts if c.get("coverage") and c["coverage"]["decisions"]]
    if not cov:
        return ["-", "-"]
    n = sum(c["decisions"] for c in cov)
    return [rounded(n), max(c["newestDecisionDate"] or "-" for c in cov)]


def table(head: list[str], rows: list[list[str]], counts: bool, at: int | None = None) -> list[str]:
    at = len(head) if at is None else at
    rule = ["---"] * len(head)
    if counts:
        head = head[:at] + ["Case records", "Newest decision"] + head[at:]
        rule = rule[:at] + ["---:", "---"] + rule[at:]
    return ["| " + " | ".join(head) + " |", "|" + "|".join(rule) + "|"] + ["| " + " | ".join(r) + " |" for r in rows]


def render(courts: list[dict]) -> str:
    counts = any(c.get("coverage") for c in courts)
    by_id = {c["courtId"]: c for c in courts}

    def extra(group: list[dict]) -> list[str]:
        return held(group) if counts else []

    def codes(group: list[dict]) -> str:
        return ", ".join(f"`{i}`" for i in sorted(c["courtId"] for c in group)) or "-"

    out = ["## Types of court", "", "Pass the filter to `GET /us/courts` to list the courts of that type."]
    out += ["A few state trial courts have `level=appellate`, such as the Connecticut Superior Court.", ""]
    rows = []
    for label, system, levels, query in GROUPS:
        group = [c for c in courts if c["system"] == system and (levels is None or c["level"] in levels)]
        rows.append([label, f"`{query}`", *extra(group)])
    out += table(["Court type", "Filter"], rows, counts)

    out += ["", "## Federal courts", ""]
    rows = []
    for code, label in pairs(FEDERAL):
        c = by_id[f"US_FED_{code}"]
        rows.append([label, f"`{c['courtId']}`", c.get("citationString") or "-", *extra([c])])
    out += table(["Court", "`courtId`", "Abbreviation"], rows, counts)

    out += ["", "## States and territories", "", "Main appeals courts sitting today."]
    out += ["For every court, call `GET /us/courts?state=CA` with the state you need. The list includes federal courts in that state.", ""]
    if counts:
        out += ["Records and dates cover every state court and body in that jurisdiction.", ""]
    rows = []
    for code, label in pairs(STATES):
        mine = [c for c in courts if c.get("stateCode") == code and c["system"] in ("state", "territorial")]
        # isActive is also true for some abolished courts, so check the end date too.
        live = [c for c in mine if c["isActive"] and not c.get("endDate")]
        top = [c for c in live if c["level"] == "supreme" or c["courtId"] in ALSO_TOP]
        lower = [c for c in live if c["level"] == "appellate" and c["courtId"] not in ALSO_TOP | NOT_APPEALS]
        rows.append([label, f"`{code}`", *extra(mine), codes(top), codes(lower)])
    out += table(["Jurisdiction", "`state`", "Highest court", "Appeals courts"], rows, counts, at=2)
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry", type=Path, help="loader folder of the court registry (no counts)")
    args = ap.parse_args()
    if args.registry:
        courts = from_registry(args.registry)
    else:
        key = os.environ.get("VAQUILL_API_KEY")
        if not key:
            print("Set VAQUILL_API_KEY, or pass --registry.", file=sys.stderr)
            return 2
        courts = from_api(key)
    body = render(courts)
    text, n = re.subn(
        f"{re.escape(BEGIN)}.*?{re.escape(END)}",
        lambda _: f"{BEGIN}\n\n{body}\n\n{END}",
        PAGE.read_text(encoding="utf-8"),
        flags=re.S,
    )
    if n != 1:
        print(f"expected one court-tables block in {PAGE}", file=sys.stderr)
        return 1
    PAGE.write_text(text, encoding="utf-8")
    print(f"wrote {PAGE} from {len(courts)} courts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
