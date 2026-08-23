"""
parse_class.py -- Step 5 work: regex-based CoC extraction.

NOT YET VALIDATED against a full real class file (see class_schema.json
header note). Built from confirmed grep facts only. Designed to run
the instant a real file is pasted -- structure should not need to
change, but every regex here should be treated as a hypothesis until
tested against real bytes, per the project's own Step 5 risk note:
"this is where 'looks right' and 'is right' diverge most easily."
"""
import re
from lxml import etree

# Matches [ExtensionOf(classstr(SalesInvoiceDP))] or formStr(...) or
# formdatasourcestr(A, B) etc. -- case-insensitive because confirmed
# real fixtures use both "classstr" and "classStr" casing.
EXTENSION_OF_RE = re.compile(
    r"ExtensionOf\s*\(\s*(classstr|tablestr|formstr|formdatasourcestr)\s*\(\s*([^)]+)\s*\)\s*\)",
    re.IGNORECASE,
)

# Matches a bare `next methodName(` call inside a method body.
# Deliberately does NOT match `next()` with no name (that's a table-level
# super()-style call in a different context, not what CoC next() looks like).
NEXT_CALL_RE = re.compile(r"\bnext\s+(\w+)\s*\(")


def get_method_name(method_el):
    """
    Tag-variance-safe method name lookup. Checks <Name> first, then <n>.
    Why: unresolved conflict in our own notes about which fixture uses
    which tag -- this function is written so it doesn't matter which one
    is right, it just checks both instead of guessing.
    """
    return method_el.findtext("Name") or method_el.findtext("n")


def parse_extension_of(declaration_text):
    """
    Look for [ExtensionOf(...)] in the class's <Declaration> CDATA block.
    Returns None for non-CoC classes -- confirmed real case: static
    helper classes have a Declaration with no ExtensionOf attribute at all.
    """
    if not declaration_text:
        return None
    match = EXTENSION_OF_RE.search(declaration_text)
    if not match:
        return None
    return {
        "target_kind": match.group(1),
        "target_name": match.group(2).strip(),
    }


def parse_method(method_el):
    source = method_el.findtext("Source") or ""
    calls_next = bool(NEXT_CALL_RE.search(source))
    return {
        "name": get_method_name(method_el),
        "calls_next": calls_next,
        "is_new_method": not calls_next,  # ASSUMPTION -- see schema note, not yet confirmed
    }


def parse_class_xml(filepath):
    tree = etree.parse(filepath)
    root = tree.getroot()

    declaration = root.findtext("./SourceCode/Declaration")
    methods_el = root.findall("./SourceCode/Methods/Method")

    return {
        "object_type": "class",
        "name": root.findtext("Name") or root.findtext("n"),
        "extension_of": parse_extension_of(declaration),
        "methods": [parse_method(m) for m in methods_el],
    }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 parse_class.py <path_to_class_xml>")
        print("Not run yet -- waiting on a real class file to test against.")
        sys.exit(1)

    result = parse_class_xml(sys.argv[1])
    print(json.dumps(result, indent=2))
