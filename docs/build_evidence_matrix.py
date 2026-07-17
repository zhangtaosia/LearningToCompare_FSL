"""Build the review's auditable source matrix from the numbered references."""

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANUSCRIPT = ROOT / "工业狭小空间几何测量方法研究进展.md"
OUTPUT = ROOT / "systematic_review_evidence_matrix.csv"


def source_type(number):
    if number in {1, 2, 3, 4, 5, 104, 106}:
        return "review"
    if number in {43, 44, 45, 46}:
        return "review_method"
    if number in {36, 37, 40, 41, 42, 47, 48}:
        return "metrology_guide_or_standard"
    return "primary_study"


def evidence_family(number):
    if number in set(range(6, 17)) | set(range(49, 68)):
        return "tactile_probe"
    if number in set(range(17, 25)) | set(range(68, 75)):
        return "passive_endoscopic_vision"
    if number in set(range(25, 36)) | set(range(75, 99)):
        return "active_optical_probe"
    if number in {38, 39} | set(range(99, 108)):
        return "industrial_application"
    if number in {108, 109, 110}:
        return "pose_calibration_traceability"
    if source_type(number) == "review":
        return "secondary_evidence"
    return "review_method_or_standard"


def main():
    references = []
    for line in MANUSCRIPT.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\[(\d+)\]\s+(.+)$", line.strip())
        if not match:
            continue
        number = int(match.group(1))
        citation = match.group(2)
        doi_match = re.search(r"DOI:\s*([^\s.]+(?:\.[^\s.]+)*)\.?$", citation, re.I)
        references.append(
            {
                "reference_id": number,
                "source_type": source_type(number),
                "evidence_family": evidence_family(number),
                "included_in_primary_synthesis": (
                    "yes" if source_type(number) == "primary_study" else "no"
                ),
                "doi": doi_match.group(1).rstrip(".") if doi_match else "",
                "citation": citation,
            }
        )

    expected = list(range(1, 111))
    actual = [row["reference_id"] for row in references]
    if actual != expected:
        raise ValueError(f"Reference sequence mismatch: {actual}")

    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=references[0].keys(), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(references)

    counts = {}
    for row in references:
        counts[row["source_type"]] = counts.get(row["source_type"], 0) + 1
    print(counts)


if __name__ == "__main__":
    main()
