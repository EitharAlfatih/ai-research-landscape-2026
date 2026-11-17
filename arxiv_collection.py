"""Collect arXiv metadata without cleaning or silently excluding records."""

from calendar import monthrange
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


def build_url(categories, start_date, end_date, max_results=20, start=0):
    """Return a query URL. Dates use YYYYMMDDHHMM in UTC, inclusive."""
    if not categories:
        raise ValueError("Provide at least one category.")
    for date in (start_date, end_date):
        if len(date) != 12 or not date.isdigit():
            raise ValueError("Dates must use YYYYMMDDHHMM.")
        datetime.strptime(date, "%Y%m%d%H%M")
    if start_date > end_date:
        raise ValueError("The start date must not follow the end date.")
    if not isinstance(max_results, int) or max_results < 1:
        raise ValueError("max_results must be a positive integer.")
    if not isinstance(start, int) or start < 0:
        raise ValueError("start must be a nonnegative integer.")

    category_query = " OR ".join(f"cat:{category}" for category in categories)
    parameters = {
        "search_query": (
            f"({category_query}) AND submittedDate:[{start_date} TO {end_date}]"
        ),
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "ascending",
    }
    return "https://export.arxiv.org/api/query?" + urlencode(parameters)


def fetch_xml(url, timeout=90):
    """Make one HTTPS request and return bytes; network errors propagate.

    Callers should allow at least three seconds between API requests.
    """
    request = Request(
        url,
        headers={"User-Agent": "ai-research-landscape-2026/0.1 (research sample)"},
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def parse_feed(xml):
    """Return records and the API's total match count, without cleaning text.

    Missing fields become empty strings/lists for inspection. An empty feed
    returns no records; malformed XML, non-Atom feeds, and API errors raise.
    The total count can exceed this page's length, or be None if not supplied.
    """
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
        "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    }
    root = ET.fromstring(xml)
    if root.tag != "{" + ns["atom"] + "}feed":
        raise ValueError("Expected an Atom feed from arXiv.")

    records = []
    for entry in root.findall("atom:entry", ns):
        entry_id = entry.findtext("atom:id", default="", namespaces=ns)
        if entry_id.startswith(("http://arxiv.org/api/errors", "https://arxiv.org/api/errors")):
            raise RuntimeError(entry.findtext("atom:summary", default="arXiv API error", namespaces=ns))
        primary = entry.find("arxiv:primary_category", ns)
        records.append({
            "arxiv_id": entry_id.rsplit("/abs/", 1)[-1],
            "title": entry.findtext("atom:title", default="", namespaces=ns),
            "abstract": entry.findtext("atom:summary", default="", namespaces=ns),
            "submitted_at": entry.findtext("atom:published", default="", namespaces=ns),
            "updated_at": entry.findtext("atom:updated", default="", namespaces=ns),
            "primary_category": primary.get("term", "") if primary is not None else "",
            "categories": [item.get("term", "") for item in entry.findall("atom:category", ns)],
            "authors": [item.findtext("atom:name", default="", namespaces=ns) for item in entry.findall("atom:author", ns)],
        })

    total = root.findtext("opensearch:totalResults", namespaces=ns)
    return {"records": records, "total_results": int(total) if total is not None else None}


def month_ranges(first_month, last_month):
    """Return inclusive UTC query bounds for months specified as YYYY-MM."""
    first = datetime.strptime(first_month, "%Y-%m")
    last = datetime.strptime(last_month, "%Y-%m")
    if first > last:
        raise ValueError("The first month must not follow the last month.")
    ranges = []
    current = first
    while current <= last:
        final_day = monthrange(current.year, current.month)[1]
        end = current.replace(day=final_day, hour=23, minute=59)
        ranges.append((current.strftime("%Y%m%d%H%M"), end.strftime("%Y%m%d%H%M")))
        current = (end + timedelta(minutes=1)).replace(hour=0, minute=0)
    return ranges


def validate_records(records, categories, start_date, end_date):
    """Count problems without changing records. A duplicate ignores v1/v2 suffixes."""
    lower = datetime.strptime(start_date, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
    upper = datetime.strptime(end_date, "%Y%m%d%H%M").replace(tzinfo=timezone.utc) + timedelta(minutes=1)
    checks = dict.fromkeys([
        "records", "missing_ids", "duplicate_ids", "invalid_submission_dates",
        "outside_date_range", "without_requested_category", "blank_titles", "blank_abstracts",
    ], 0)
    seen = set()
    for record in records:
        checks["records"] += 1
        base_id = re.sub(r"v\d+$", "", record["arxiv_id"])
        if not base_id.strip():
            checks["missing_ids"] += 1
        elif base_id in seen:
            checks["duplicate_ids"] += 1
        seen.add(base_id)
        try:
            submitted = datetime.fromisoformat(record["submitted_at"].replace("Z", "+00:00"))
            if submitted.tzinfo is None:
                raise ValueError("A submission date needs a timezone.")
            if not lower <= submitted < upper:
                checks["outside_date_range"] += 1
        except ValueError:
            checks["invalid_submission_dates"] += 1
        if not set(categories).intersection(record["categories"]):
            checks["without_requested_category"] += 1
        checks["blank_titles"] += int(not record["title"].strip())
        checks["blank_abstracts"] += int(not record["abstract"].strip())
    return checks


def collect_month(categories, start_date, end_date, output_dir, page_size=500):
    """Collect one date window and return its saved manifest.

    Completed windows are reused after checking settings and the data hash.
    An interrupted window is downloaded again; completed windows are kept.
    A manifest is written last, so a data file alone is not a completion marker.
    No automatic retries: a failed request stops collection visibly.
    """
    # Validate settings before creating files or contacting the API.
    build_url(categories, start_date, end_date, max_results=page_size)
    if page_size > 2000:
        raise ValueError("Use at most 2000 records per page.")
    output_dir = Path(output_dir)
    stem = f"{start_date}_{end_date}"
    data_path = output_dir / f"{stem}.jsonl"
    manifest_path = output_dir / f"{stem}.manifest.json"
    settings = {"categories": list(categories), "start_date": start_date, "end_date": end_date}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("settings") != settings or manifest.get("status") != "complete":
            raise RuntimeError(f"Saved settings do not match: {manifest_path}. Use a separate output folder.")
        if not data_path.exists() or hashlib.sha256(data_path.read_bytes()).hexdigest() != manifest.get("sha256"):
            raise RuntimeError(f"Saved data is missing or changed: {data_path}. Inspect it before continuing.")
        print(f"Reusing {stem}: {manifest['retrieved_count']:,} records", flush=True)
        return manifest

    records = []
    expected_total = None
    requests = []
    started_at = datetime.now(timezone.utc).isoformat()
    while expected_total is None or len(records) < expected_total:
        offset = len(records)
        url = build_url(categories, start_date, end_date, page_size, start=offset)
        time.sleep(3)
        feed = parse_feed(fetch_xml(url))
        requests.append({"url": url, "retrieved_at": datetime.now(timezone.utc).isoformat()})
        total = feed["total_results"]
        if total is None or total < 0:
            raise RuntimeError(f"No valid API total for {stem} at offset {offset}.")
        if total > 30000:
            raise RuntimeError(f"{stem} has {total} matches; split it into smaller date windows.")
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise RuntimeError(f"API total changed during {stem}; rerun this window.")
        page = feed["records"]
        if not page and len(records) < expected_total:
            raise RuntimeError(f"Incomplete download for {stem}: {len(records)} of {expected_total} records.")
        records.extend(page)
        if len(records) > expected_total:
            raise RuntimeError(f"API returned more records than reported for {stem}.")
        print(f"{stem}: {len(records):,}/{expected_total:,}", flush=True)

    checks = validate_records(records, categories, start_date, end_date)
    fatal_checks = ["missing_ids", "duplicate_ids", "invalid_submission_dates", "outside_date_range", "without_requested_category"]
    if any(checks[key] for key in fatal_checks):
        raise RuntimeError(f"Collection validation failed for {stem}: {checks}. No completed checkpoint saved.")
    # Blank text remains in the data and is reported for the cleaning step.
    payload = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records).encode("utf-8")
    manifest = {
        "status": "complete", "settings": settings, "page_size": page_size,
        "api_total": expected_total, "retrieved_count": len(records),
        "started_at": started_at, "completed_at": datetime.now(timezone.utc).isoformat(),
        "requests": requests, "validation": checks,
        "data_file": data_path.name, "sha256": hashlib.sha256(payload).hexdigest(),
        "collector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary_data = data_path.with_suffix(".jsonl.part")
    temporary_data.write_bytes(payload)
    temporary_data.replace(data_path)
    temporary_manifest = manifest_path.with_suffix(".json.part")
    temporary_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(manifest_path)
    return manifest
