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

    fixtures_dir = os.path.join("fixtures", "tables")
    filenames = sorted(f for f in os.listdir(fixtures_dir) if f.endswith(".xml"))

    all_passed = True
    for filename in filenames:
        filepath = os.path.join(fixtures_dir, filename)
        result = parse_table_xml(filepath)
        try:
            validate(instance=result, schema=schema)
            print(f"PASS: {filename} ({result['name']}) -- {len(result['fields'])} fields, {len(result['relations'])} relations")
        except ValidationError as e:
            all_passed = False
            print(f"FAIL: {filename}")
            print(f"  Path: {list(e.path)}")
            print(f"  Reason: {e.message}")

    if all_passed:
        print("\nAll fixtures validate against table_schema.json.")
    else:
        raise SystemExit("One or more fixtures failed schema validation -- see above.")


if __name__ == "__main__":
    main()