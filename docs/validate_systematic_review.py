"""Consistency checks for the systematic review source and generated outputs."""

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANUSCRIPT = ROOT / "工业狭小空间几何测量方法研究进展.md"


def expand_citations(text):
    cited = set()
    for group in re.findall(r"\[([0-9,\-\s]+)\]", text):
        for item in group.split(","):
            item = item.strip()
            if "-" in item:
                start, end = (int(value) for value in item.split("-", 1))
                cited.update(range(start, end + 1))
            elif item:
                cited.add(int(item))
    return cited


def main():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    body, references = text.split("## 参考文献", 1)
    listed = [int(value) for value in re.findall(r"^\[(\d+)\]", references, re.M)]
    assert listed == list(range(1, 111)), "References must be sequential from 1 to 110"

    cited = expand_citations(body)
    unlisted = sorted(cited - set(listed))
    uncited = sorted(set(listed) - cited)
    assert not unlisted, f"Unlisted citations: {unlisted}"

    with (ROOT / "systematic_review_evidence_matrix.csv").open(
        encoding="utf-8-sig"
    ) as file:
        matrix = list(csv.DictReader(file))
    assert len(matrix) == 110
    assert sum(row["source_type"] == "primary_study" for row in matrix) == 92

    summary = json.loads((ROOT / "systematic_search_summary.json").read_text())
    assert summary["records_exported_before_deduplication"] == 1361
    assert summary["unique_records_after_deduplication"] == 1305
    assert summary["title_screen_candidates"] == 153

    print(
        {
            "references": len(listed),
            "cited_references": len(cited),
            "uncited_context_sources": uncited,
            "primary_studies": 92,
            "search_records": 1305,
            "title_candidates": 153,
        }
    )


if __name__ == "__main__":
    main()
