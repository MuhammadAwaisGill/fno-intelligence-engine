"""
parse.py -- Step 6: CLI wrapper.

Usage:
    python parse.py --model path\to\ModelFolder --out metadata.json

Walks a model directory, routes each XML file to the correct parser
based on its root tag (AxTable -> parse_table, AxClass -> parse_class),
and writes one combined JSON file.

ASSUMPTION (please confirm against your actual parse_table.py):
this expects a function `parse_table_xml(filepath) -> dict`. If your
real function/module name differs, update the import below.
"""
import argparse
import json
import os
import sys
from lxml import etree

from parse_class import parse_class_xml

try:
    from parse_table import parse_table_xml
except ImportError:
    parse_table_xml = None  # lets the CLI still run for class-only testing


def detect_object_type(filepath):
    """
    Peeks at the root XML tag to route to the right parser without a
    full double-parse. Returns 'table', 'class', None (not Part 1's
    scope -- e.g. AxForm, AxDataEntity), or ('error', message).
    """
    try:
        for _event, elem in etree.iterparse(filepath, events=("start",)):
            tag = elem.tag
            elem.clear()
            if tag == "AxTable":
                return "table"
            if tag == "AxClass":
                return "class"
            return None
    except etree.XMLSyntaxError as e:
        return ("error", str(e))


def find_xml_files(model_dir):
    """
    Recursive walk. Confirmed real edge cases this must survive (per
    project plan Step 6 notes): nested folders, non-XML files present.
    """
    xml_files = []
    for root, _dirs, files in os.walk(model_dir):
        for f in files:
            if f.lower().endswith(".xml"):
                xml_files.append(os.path.join(root, f))
    return xml_files


def process_model_directory(model_dir):
    results = {"tables": [], "classes": [], "skipped": [], "errors": []}

    for filepath in find_xml_files(model_dir):
        obj_type = detect_object_type(filepath)

        if isinstance(obj_type, tuple) and obj_type[0] == "error":
            results["errors"].append({"file": filepath, "reason": obj_type[1]})
            continue

        if obj_type == "table":
            if parse_table_xml is None:
                results["errors"].append({
                    "file": filepath,
                    "reason": "parse_table_xml not available -- check parse_table.py import",
                })
                continue
            try:
                results["tables"].append(parse_table_xml(filepath))
            except Exception as e:
                results["errors"].append({"file": filepath, "reason": str(e)})

        elif obj_type == "class":
            try:
                results["classes"].append(parse_class_xml(filepath))
            except Exception as e:
                results["errors"].append({"file": filepath, "reason": str(e)})

        else:
            # Not AxTable/AxClass -- expected, not an error. Model dirs
            # contain many other AOT object types outside Part 1's scope.
            results["skipped"].append(filepath)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Parse D365 F&O AxTable/AxClass XML into structured JSON."
    )
    parser.add_argument("--model", required=True, help="Path to the model directory to walk.")
    parser.add_argument("--out", required=True, help="Path to write the combined JSON output.")
    args = parser.parse_args()

    if not os.path.isdir(args.model):
        print(f"Error: model directory not found: {args.model}", file=sys.stderr)
        sys.exit(1)

    results = process_model_directory(args.model)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Parsed {len(results['tables'])} tables, {len(results['classes'])} classes.")
    print(f"Skipped {len(results['skipped'])} non-Part1 object files.")
    if results["errors"]:
        print(f"WARNING: {len(results['errors'])} files failed to parse:", file=sys.stderr)
        for err in results["errors"]:
            print(f"  {err['file']}: {err['reason']}", file=sys.stderr)

    print(f"Output written to {args.out}")


if __name__ == "__main__":
    main()