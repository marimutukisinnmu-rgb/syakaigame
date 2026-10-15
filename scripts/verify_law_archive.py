#!/usr/bin/env python3
"""Validate an e-Gov-style law XML bulk archive.

Usage:
  python verify_law_archive.py all_xml.zip
  python verify_law_archive.py all_xml.zip --start-index 0 --end-index 3000

The index range is zero-based, end-exclusive, over XML archive paths sorted
lexicographically. Chunked runs can be merged by summing counts; archive-wide
metadata is reported on each run. Requires Python 3.11+ and lxml.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import io
import json
import os
import platform
import sys
import time
import zipfile
from pathlib import PurePosixPath
from datetime import datetime, timezone
from lxml import etree

COUNT_TAGS = (
    "Law", "LawNum", "LawTitle", "LawBody", "MainProvision",
    "SupplProvision", "Chapter", "Section", "Article", "ArticleTitle",
    "ArticleCaption", "Paragraph", "ParagraphSentence", "Item",
    "ItemSentence", "Subitem1", "Table", "Fig",
)
SOURCE_URL = "https://laws.e-gov.go.jp/bulkdownload?file_section=1&only_xml_flag=true"


def local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return str(tag)
    return tag.rsplit("}", 1)[-1]


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def xml_path_for_url(url: str) -> str:
    tail = url.split("/law/", 1)[1]
    law_id, revision = tail.split("/", 1)
    revision = revision.split("?", 1)[0].rstrip("/")
    basename = f"{law_id}_{revision}"
    return f"{basename}/{basename}.xml"


def main() -> int:
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("archive", help="Path to all_xml.zip")
    argp.add_argument("--start-index", type=int, default=0, help="First XML index (zero-based)")
    argp.add_argument("--end-index", type=int, default=None, help="End XML index (exclusive)")
    argp.add_argument("--skip-crc", action="store_true", help="Skip archive-wide ZIP CRC test")
    argp.add_argument("--output", help="Write JSON result to this path as well as stdout")
    args = argp.parse_args()
    if args.start_index < 0 or (args.end_index is not None and args.end_index < args.start_index):
        argp.error("invalid index range")

    started = time.time()
    archive_path = os.path.abspath(args.archive)
    result: dict[str, object] = {
        "archive": os.path.basename(archive_path),
        "archive_size_bytes": os.path.getsize(archive_path),
        "archive_sha256": sha256_file(archive_path),
        "inspection_time_utc": datetime.now(timezone.utc).isoformat(),
        "inspection_time_note": "検査実行環境の時計。取得日や法令データの基準時点を示すものではない。",
        "source_reference_url": SOURCE_URL,
        "source_provenance_note": "このURLはXML一括ダウンロードの公式参照先。ローカルアーカイブ個体の取得履歴は別途保存が必要。",
        "python_version": sys.version,
        "platform": platform.platform(),
        "lxml_version": ".".join(map(str, etree.LXML_VERSION)),
        "libxml2_version": ".".join(map(str, etree.LIBXML_VERSION)),
        "parse_method": "lxml.etree.fromstring per XML file; checks XML well-formedness only; no DTD/XSD schema validation",
    }

    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        xml_entries = sorted(
            [entry for entry in entries if not entry.is_dir() and PurePosixPath(entry.filename).suffix.lower() == ".xml"],
            key=lambda entry: entry.filename,
        )
        directories = [entry for entry in entries if entry.is_dir()]
        csv_entries = [entry for entry in entries if not entry.is_dir() and PurePosixPath(entry.filename).suffix.lower() == ".csv"]
        other_files = [entry.filename for entry in entries if not entry.is_dir() and PurePosixPath(entry.filename).suffix.lower() not in (".xml", ".csv")]
        csv_info = next((entry for entry in csv_entries if PurePosixPath(entry.filename).name == "all_law_list.csv"), None)
        if csv_info is None:
            raise SystemExit("all_law_list.csv was not found")
        csv_text = archive.read(csv_info).decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)
        xml_names = {entry.filename for entry in xml_entries}
        expected_paths: list[str] = []
        malformed_url_rows = 0
        for row in rows:
            try:
                expected_paths.append(xml_path_for_url(row["本文URL"]))
            except (KeyError, IndexError, ValueError):
                malformed_url_rows += 1
                expected_paths.append("")
        path_counts = collections.Counter(path for path in expected_paths if path)
        matched_rows = sum(1 for path in expected_paths if path and path in xml_names)
        missing_paths = sorted(set(path for path in expected_paths if path) - xml_names)
        extra_paths = sorted(xml_names - set(path for path in expected_paths if path))
        bad_zip_member = None if args.skip_crc else archive.testzip()

        result.update({
            "zip_entries_total": len(entries),
            "directory_entries": len(directories),
            "xml_file_count": len(xml_entries),
            "csv_file_count": len(csv_entries),
            "other_regular_files": other_files,
            "zip_crc_test": "skipped" if args.skip_crc else ("passed" if bad_zip_member is None else f"failed: {bad_zip_member}"),
            "csv_file": csv_info.filename,
            "csv_row_count": len(rows),
            "csv_column_count": len(reader.fieldnames or []),
            "csv_columns": reader.fieldnames or [],
            "csv_url_malformed_rows": malformed_url_rows,
            "csv_xml_matched_rows": matched_rows,
            "csv_xml_unique_expected_paths": len(path_counts),
            "csv_xml_duplicate_expected_paths": {path: count for path, count in path_counts.items() if count > 1},
            "csv_rows_without_xml": missing_paths,
            "xml_without_csv_row": extra_paths,
            "xml_uncompressed_bytes_total": sum(entry.file_size for entry in xml_entries),
            "largest_xml_bytes": max((entry.file_size for entry in xml_entries), default=0),
            "zip_entry_timestamp_min": min((entry.date_time for entry in entries), default=None),
            "zip_entry_timestamp_max": max((entry.date_time for entry in entries), default=None),
            "zip_entry_timestamp_timezone": "not encoded in ZIP DOS timestamps; do not infer a timezone",
            "xml_index_range_zero_based_end_exclusive": [args.start_index, min(args.end_index if args.end_index is not None else len(xml_entries), len(xml_entries))],
        })

        end = min(args.end_index if args.end_index is not None else len(xml_entries), len(xml_entries))
        if args.start_index > len(xml_entries):
            argp.error("start-index exceeds XML file count")
        selected_entries = xml_entries[args.start_index:end]
        tags = collections.Counter()
        root_names = collections.Counter()
        articles_missing_num = 0
        article_titles_not_under_article = 0
        article_title_other_parent = collections.Counter()
        unusual_title_examples = []
        broad_article_prefix_bytes = 0
        parse_errors = []

        for pos, entry in enumerate(selected_entries, args.start_index):
            try:
                data = archive.read(entry)
                broad_article_prefix_bytes += data.count(b"<Article")
                parser = etree.XMLParser(
                    resolve_entities=False,
                    no_network=True,
                    load_dtd=False,
                    huge_tree=True,
                    recover=False,
                )
                root = etree.fromstring(data, parser)
                root_name = local_name(root.tag)
                root_names[root_name] += 1
                tags[root_name] += 1
                for element in root.iterdescendants():
                    tag = local_name(element.tag)
                    if tag in COUNT_TAGS:
                        tags[tag] += 1
                    if tag == "Article" and element.get("Num") is None:
                        articles_missing_num += 1
                    elif tag == "ArticleTitle":
                        parent = element.getparent()
                        parent_name = local_name(parent.tag) if parent is not None else "<ROOT>"
                        if parent_name != "Article":
                            article_titles_not_under_article += 1
                            article_title_other_parent[parent_name] += 1
                            if len(unusual_title_examples) < 20:
                                unusual_title_examples.append({"file": entry.filename, "parent": parent_name})
            except Exception as exc:
                parse_errors.append({"file": entry.filename, "error": repr(exc)})
            if (pos - args.start_index + 1) % 1000 == 0:
                print(f"Parsed {pos - args.start_index + 1}/{len(selected_entries)} selected XML files", file=sys.stderr, flush=True)

    result.update({
        "xml_files_parsed_in_this_run": len(selected_entries),
        "xml_root_names_in_this_run": dict(root_names),
        "element_counts_in_this_run": {tag: tags[tag] for tag in COUNT_TAGS},
        "article_elements_missing_Num": articles_missing_num,
        "article_title_elements_not_directly_under_Article": article_titles_not_under_article,
        "article_title_other_parent_counts": dict(article_title_other_parent),
        "article_title_other_parent_examples": unusual_title_examples,
        "raw_byte_prefix_count_for_b_Article_in_this_run": broad_article_prefix_bytes,
        "xml_parse_error_count_in_this_run": len(parse_errors),
        "xml_parse_error_examples": parse_errors[:20],
        "elapsed_seconds": round(time.time() - started, 2),
    })
    failure_reasons = []
    if not args.skip_crc and bad_zip_member is not None:
        failure_reasons.append(f"ZIP CRC test failed: {bad_zip_member}")
    if malformed_url_rows:
        failure_reasons.append(f"Malformed CSV body URLs: {malformed_url_rows}")
    if any(count > 1 for count in path_counts.values()):
        failure_reasons.append("Duplicate XML paths derived from CSV body URLs")
    if matched_rows != len(rows):
        failure_reasons.append("Not every CSV row matched an XML file")
    if missing_paths:
        failure_reasons.append("CSV rows point to XML files missing from the ZIP")
    if extra_paths:
        failure_reasons.append("ZIP XML files without matching CSV rows")
    if other_files:
        failure_reasons.append("Unexpected regular files outside XML/CSV")
    if root_names != {"Law": len(selected_entries)}:
        failure_reasons.append("One or more selected XML roots were not Law, or parsing failed")
    if articles_missing_num:
        failure_reasons.append(f"Article elements missing Num: {articles_missing_num}")
    if parse_errors:
        failure_reasons.append(f"XML parse errors: {len(parse_errors)}")
    result["validation_passed_this_run"] = not failure_reasons
    result["validation_failure_reasons"] = failure_reasons

    output_text = json.dumps(result, ensure_ascii=False, indent=2)
    print(output_text)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as stream:
            stream.write(output_text + "\n")
    return 0 if not failure_reasons else 1


if __name__ == "__main__":
    raise SystemExit(main())
