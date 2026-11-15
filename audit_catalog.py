import argparse
import csv
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app import FIELDS, _clean_row, _profile, _read_dataset, _review_rows

MAX_INPUT_BYTES = 100 * 1024 * 1024
MAX_ROWS = 100_000
OUTPUT_NAMES = ("audit.json", "summary.md", "clean.csv", "review.csv")


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stage_file(directory, name, write, *, encoding="utf-8"):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding=encoding, newline="", prefix=f".{name}.", suffix=".tmp",
            dir=directory, delete=False,
        ) as staged:
            temporary = Path(staged.name)
            write(staged)
        return temporary
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def audit_catalog(input_path, output_dir, *, force=False):
    source = Path(input_path).expanduser().resolve(strict=True)
    destination = Path(output_dir).expanduser().resolve()
    if not source.is_file():
        raise ValueError("input must be a regular CSV file")
    if source.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError(f"input exceeds {MAX_INPUT_BYTES // (1024 * 1024)} MiB")

    destination.mkdir(parents=True, exist_ok=True)
    targets = [destination / name for name in OUTPUT_NAMES]
    if source in targets:
        raise ValueError("input file cannot be one of the output files")
    existing = [target.name for target in targets if target.exists()]
    if existing and not force:
        raise FileExistsError(f"output already exists: {', '.join(existing)}; pass --force to replace")

    rows = _read_dataset(source, max_rows=MAX_ROWS)
    profile = _profile(rows)
    reviews = _review_rows(rows)
    issue_counts = {}
    for row in reviews:
        for code in row["issue_codes"]:
            issue_counts[code] = issue_counts.get(code, 0) + 1

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),  # noqa: UP017 - Python 3.10 compatibility
        "source_file": source.name,
        "source_sha256": _sha256(source),
        "records": profile["count"],
        "fields": profile["columns"],
        "completeness_percent": profile["quality"],
        "missing_cells": profile["missing_total"],
        "missing_by_field": profile["missing"],
        "duplicate_source_ids": profile["duplicate_ids"],
        "possible_duplicate_records": profile["possible_duplicates"],
        "flagged_records": len(reviews),
        "issue_counts": issue_counts,
        "release_year_range": [profile["year_min"], profile["year_max"]],
        "record_types": dict(profile["types"]),
    }

    staged = []
    try:
        def write_report(file):
            json.dump(report, file, indent=2, ensure_ascii=False)
            file.write("\n")

        staged.append(_stage_file(destination, OUTPUT_NAMES[0], write_report))

        def write_summary(file):
            file.write("# Catalog quality audit\n\n")
            file.write(f"Generated: {report['generated_at']} (UTC)\n\n")
            file.write("## At a glance\n\n")
            file.write(f"- Records: {report['records']:,}\n")
            file.write(f"- Completeness: {report['completeness_percent']:.1f}%\n")
            file.write(f"- Records needing review: {report['flagged_records']:,}\n")
            file.write(f"- Missing cells: {report['missing_cells']:,}\n")
            file.write(f"- Repeated source IDs: {report['duplicate_source_ids']:,}\n")
            file.write(f"- Possible duplicate records: {report['possible_duplicate_records']:,}\n\n")
            file.write("## Missing values by field\n\n")
            for field, count in report["missing_by_field"].items():
                file.write(f"- `{field}`: {count:,}\n")
            file.write("\n## Review reasons\n\n")
            if report["issue_counts"]:
                for issue, count in sorted(report["issue_counts"].items()):
                    file.write(f"- `{issue}`: {count:,}\n")
            else:
                file.write("No issues found.\n")
            file.write(f"\nSource SHA-256: `{report['source_sha256']}`\n")
            file.write("\nThis report contains aggregate metrics only; customer row values are not included.\n")

        staged.append(_stage_file(destination, OUTPUT_NAMES[1], write_summary))

        def write_clean(file):
            writer = csv.DictWriter(file, fieldnames=FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(_clean_row(row) for row in rows if (row.get("title") or "").strip())

        staged.append(_stage_file(destination, OUTPUT_NAMES[2], write_clean, encoding="utf-8-sig"))

        def write_review(file):
            writer = csv.DictWriter(file, fieldnames=(*FIELDS, "source_record", "review_flags"), extrasaction="ignore")
            writer.writeheader()
            for row in reviews:
                writer.writerow({**_clean_row(row), "source_record": row["source_record"], "review_flags": "; ".join(row["issues"])})

        staged.append(_stage_file(destination, OUTPUT_NAMES[3], write_review, encoding="utf-8-sig"))
        for temporary, target in zip(staged, targets):
            os.replace(temporary, target)
    finally:
        for temporary in staged:
            temporary.unlink(missing_ok=True)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit a media catalog locally without uploading its data.")
    parser.add_argument("--input", required=True, help="CSV with the documented catalog fields")
    parser.add_argument("--output-dir", required=True, help="folder for audit.json, summary.md, clean.csv and review.csv")
    parser.add_argument("--force", action="store_true", help="replace existing report files")
    args = parser.parse_args(argv)
    try:
        report = audit_catalog(args.input, args.output_dir, force=args.force)
    except (csv.Error, OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Audited {report['records']:,} rows; {report['flagged_records']:,} need review.")
    print(f"Reports saved locally to {Path(args.output_dir).expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
