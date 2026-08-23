"""
validate.py -- proves parse_table.py's output actually satisfies
schema/table_schema.json, rather than just "looking right" when printed.

This is the mechanical version of Step 7 ("hand mentor the JSON, ask
what's wrong") -- except this catches STRUCTURAL violations automatically,
before a human ever needs to look at it. Mentor review still matters for
CORRECTNESS (is this the right EDT for this field); this script only
proves SHAPE (does the output match the contract we designed).
"""
import json
import os
from jsonschema import validate, ValidationError

from parse_table import parse_table_xml


def main():
    with open(os.path.join("schema", "table_schema.json")) as f:
        schema = json.load(f)

    result = parse_table_xml(os.path.join("fixtures", "tables", "VendTrans.xml"))

    try:
        validate(instance=result, schema=schema)
        print("PASS: parser output matches table_schema.json")
        print(f"  - {result['name']}: {len(result['fields'])} fields, {len(result['relations'])} relations")

        # Explicitly surface the two edge cases so they're visible in output,
        # not just silently "passing" without proof they were exercised.
        enum_only = [f for f in result["fields"] if f["edt"] is None and f["enum_type"]]
        mixed_relations = [
            r for r in result["relations"]
            if len({c["kind"] for c in r["constraints"]}) > 1
        ]
        print(f"  - fields with enum_type but no edt (edge case 1): {[f['name'] for f in enum_only]}")
        print(f"  - relations mixing field+fixed constraints (edge case 2): {[r['name'] for r in mixed_relations]}")

    except ValidationError as e:
        print("FAIL: parser output does NOT match schema")
        print(f"  Path: {list(e.path)}")
        print(f"  Reason: {e.message}")
        raise


if __name__ == "__main__":
    main()
