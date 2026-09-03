import json
import os
from parse_table import parse_table_xml

fixtures_dir = os.path.join("fixtures", "tables")

for filename in sorted(os.listdir(fixtures_dir)):
    if not filename.endswith(".xml"):
        continue
    filepath = os.path.join(fixtures_dir, filename)
    print(f"===== {filename} =====")
    print(json.dumps(parse_table_xml(filepath), indent=2))