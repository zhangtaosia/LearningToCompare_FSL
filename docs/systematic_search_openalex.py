"""Reproducible OpenAlex search for the systematic mapping review.

The script records the query-level hit counts and exports the first 200
relevance-ranked records for each pre-specified query. It does not make
inclusion decisions; those remain documented in the manuscript.
"""

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEARCH_DATE = "2026-07-17"
QUERIES = [
    ("Q01", '"high aspect ratio" "internal feature" metrology'),
    ("Q02", '"deep hole" geometrical measurement'),
    ("Q03", '"micro hole" tactile probe metrology'),
    ("Q04", '"fiber probe" small hole measurement'),
    ("Q05", '"inner surface" "structured light" measurement'),
    ("Q06", '"pipe inner wall" "3D measurement"'),
    ("Q07", '"measuring endoscope" 3D industrial'),
    ("Q08", 'borescope dimensional measurement'),
    ("Q09", '"confocal" "deep hole" measurement'),
    ("Q10", '"low coherence interferometry" bore measurement'),
    ("Q11", '"internal surface" laser triangulation metrology'),
    ("Q12", '"blade tip clearance" optical measurement'),
]

INTERNAL_TERMS = (
    "hole",
    "bore",
    "pipe",
    "tube",
    "inner",
    "internal",
    "cavity",
    "confined",
    "restricted",
    "clearance",
    "high aspect ratio",
)
MEASUREMENT_TERMS = (
    "measur",
    "metrolog",
    "probe",
    "profil",
    "three-dimensional",
    "3d",
    "inspection",
    "reconstruction",
    "sensor",
    "endoscope",
    "borescope",
    "interfer",
    "confocal",
    "structured light",
    "triangulation",
)
EXCLUSION_TERMS = (
    "colonoscopy",
    "gastrointestinal",
    "laparoscopic",
    "cancer",
    "tumor",
    "dental",
    "retinal",
    "brain",
    "cell",
)


def normalize_doi(value):
    if not value:
        return ""
    return value.lower().replace("https://doi.org/", "").strip()


def is_title_candidate(title):
    normalized = (title or "").lower()
    return (
        any(term in normalized for term in INTERNAL_TERMS)
        and any(term in normalized for term in MEASUREMENT_TERMS)
        and not any(term in normalized for term in EXCLUSION_TERMS)
    )


def fetch(query):
    params = urllib.parse.urlencode(
        {
            "search": query,
            "per-page": 200,
            "select": (
                "id,doi,title,publication_year,type,primary_location,"
                "authorships,cited_by_count"
            ),
            "mailto": "systematic-review@example.com",
        }
    )
    request = urllib.request.Request(
        f"https://api.openalex.org/works?{params}",
        headers={"User-Agent": "industrial-geometry-systematic-review/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main():
    records = {}
    query_rows = []
    for query_id, query in QUERIES:
        payload = fetch(query)
        results = payload.get("results", [])
        query_rows.append(
            {
                "query_id": query_id,
                "search_date": SEARCH_DATE,
                "query": query,
                "total_hits": payload.get("meta", {}).get("count", 0),
                "records_exported": len(results),
            }
        )
        for work in results:
            key = normalize_doi(work.get("doi")) or work.get("id", "")
            if not key:
                continue
            location = work.get("primary_location") or {}
            source = location.get("source") or {}
            authors = "; ".join(
                author.get("author", {}).get("display_name", "")
                for author in work.get("authorships", [])
            )
            if key not in records:
                records[key] = {
                    "record_key": key,
                    "doi": normalize_doi(work.get("doi")),
                    "openalex_id": work.get("id", ""),
                    "title": work.get("title", ""),
                    "authors": authors,
                    "year": work.get("publication_year", ""),
                    "type": work.get("type", ""),
                    "source": source.get("display_name", ""),
                    "cited_by_count": work.get("cited_by_count", 0),
                    "query_ids": query_id,
                    "title_screen_candidate": "yes"
                    if is_title_candidate(work.get("title", ""))
                    else "no",
                }
            else:
                query_ids = set(records[key]["query_ids"].split(";"))
                query_ids.add(query_id)
                records[key]["query_ids"] = ";".join(sorted(query_ids))
        time.sleep(0.15)

    with (ROOT / "systematic_search_log.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=query_rows[0].keys())
        writer.writeheader()
        writer.writerows(query_rows)

    fields = [
        "record_key",
        "doi",
        "openalex_id",
        "title",
        "authors",
        "year",
        "type",
        "source",
        "cited_by_count",
        "query_ids",
        "title_screen_candidate",
    ]
    with (ROOT / "systematic_search_records.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(records.values(), key=lambda row: row["record_key"]))

    summary = {
        "search_date": SEARCH_DATE,
        "queries": len(QUERIES),
        "records_exported_before_deduplication": sum(
            row["records_exported"] for row in query_rows
        ),
        "unique_records_after_deduplication": len(records),
        "title_screen_candidates": sum(
            row["title_screen_candidate"] == "yes" for row in records.values()
        ),
    }
    (ROOT / "systematic_search_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
