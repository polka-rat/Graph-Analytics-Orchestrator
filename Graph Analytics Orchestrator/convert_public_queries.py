"""Convert the public-query workbook into runner and evaluation JSON files."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from openpyxl import load_workbook


def _value(answer_type, raw_value):
    text = str(raw_value).strip()
    if answer_type == "number":
        number = float(text)
        return int(number) if number.is_integer() else number
    if answer_type == "boolean":
        return text.lower() == "true"
    if answer_type in {"node_list", "path"}:
        separator = "→" if "→" in text else ","
        return [part.strip() for part in text.split(separator)]
    return text


def convert(workbook_path: Path, queries_path: Path, expected_path: Path) -> int:
    """Convert valid rows from the workbook and return their count."""
    temporary_path = None
    try:
        workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    except PermissionError:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as file:
            temporary_path = Path(file.name)
        shutil.copyfile(workbook_path, temporary_path)
        workbook = load_workbook(temporary_path, read_only=True, data_only=True)
    if "Queries" not in workbook.sheetnames:
        raise ValueError("Workbook must contain a 'Queries' sheet.")

    rows = list(workbook["Queries"].values)
    if not rows:
        raise ValueError("The 'Queries' sheet is empty.")

    headers = rows[0]
    records = [dict(zip(headers, row)) for row in rows[1:] if row[0]]
    queries = []
    expected = []

    for record in records:
        query_id = record["Query ID"]
        question = record["Question"]
        status = record["Expected status"]
        answer_type = record["Answer type"]

        queries.append({"query_id": query_id, "query": question})
        if status == "answered":
            answer = {
                "type": answer_type,
                "value": _value(answer_type, record["Expected answer"]),
            }
            if answer_type == "node_list" and "Ranked" in str(record["Notes"]):
                answer["ordered"] = True
        else:
            answer = {"type": "text", "value": ""}
        expected.append({
            "query_id": query_id,
            "status": status,
            "answer": answer,
        })

    queries_path.write_text(
        json.dumps(queries, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    expected_path.write_text(
        json.dumps(expected, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if temporary_path:
        temporary_path.unlink(missing_ok=True)
    return len(queries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--xlsx",
        default="Public Query Set.xlsx",
        help="Public query workbook path.",
    )
    parser.add_argument(
        "--queries-out",
        default="public_queries.json",
        help="Runner query JSON output path.",
    )
    parser.add_argument(
        "--expected-out",
        default="public_expected.json",
        help="Expected answer JSON output path.",
    )
    args = parser.parse_args()

    count = convert(
        Path(args.xlsx),
        Path(args.queries_out),
        Path(args.expected_out),
    )
    print(f"Converted {count} public queries.")
    print(f"Queries: {Path(args.queries_out).resolve()}")
    print(f"Expected answers: {Path(args.expected_out).resolve()}")


if __name__ == "__main__":
    main()
