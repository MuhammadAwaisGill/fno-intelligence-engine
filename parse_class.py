"""
parse_class.py -- Step 5: regex-based CoC extraction + signature parsing.

VALIDATED against all 6 real class fixtures (see test_parse_class.py):
- classstr, formstr, formdatasourcestr CoC targets
- non-CoC negative cases
- multi-line signatures, doc-comment + attribute prefixes, next() vs
  queryRun.next() disambiguation

Deliberately NOT a full X++ parser (per project scope decision): bracket
matching is naive about string literals inside parens/brackets. This is
an accepted, documented limitation, not an oversight.
"""
import re
from lxml import etree

EXTENSION_OF_RE = re.compile(
    r"ExtensionOf\s*\(\s*(classstr|tablestr|formstr|formdatasourcestr)\s*\(\s*([^)]+)\s*\)\s*\)",
    re.IGNORECASE,
)

# Matches a bare `next methodName(` call -- deliberately does NOT match
# `next()` with no name, since that's table-cursor iteration (confirmed
# real collision: queryRun.next() appears constantly in while loops and
# must not be flagged as a CoC call).
NEXT_CALL_RE = re.compile(r"\bnext\s+(\w+)\s*\(")

# Doc comment lines (///) -- stripped before signature extraction so
# they don't get mistaken for part of the modifier/return-type prefix.
DOC_COMMENT_RE = re.compile(r"^[ \t]*///.*$", re.MULTILINE)

# X++ modifier keywords -- order-independent, since confirmed real
# fixtures vary ("display static X" vs "public static display X").
KNOWN_MODIFIERS = {
    "public", "private", "protected", "internal",
    "static", "final", "abstract", "display", "virtual",
    "server", "client", "delegate", "edit",
}

DEFAULT_SPLIT_RE = re.compile(r"(?<!=)=(?!=)")  # avoid splitting on == 


def get_method_name(method_el):
    """
    Tag-variance-safe method name lookup. Checks <Name> first, then <n>.
    NOTE: all 6 real fixtures tested so far use <Name>. The <n> fallback
    remains written defensively but UNCONFIRMED against real bytes --
    do not claim this branch is validated.
    """
    return method_el.findtext("Name") or method_el.findtext("n")


def parse_extension_of(declaration_text):
    """
    Look for [ExtensionOf(...)] in the class's <Declaration> CDATA block.
    Returns None for non-CoC classes -- confirmed real case: static
    helper classes have a Declaration with no ExtensionOf attribute at all.

    formdatasourcestr(Form, DataSource) takes two arguments -- confirmed
    real case (SalesEditLines_SalesParmTable_ApplicationSuite_Extension).
    Split into form_name / datasource_name instead of one fused string,
    since downstream SQL needs to query on datasource_name alone.
    """
    if not declaration_text:
        return None
    match = EXTENSION_OF_RE.search(declaration_text)
    if not match:
        return None

    kind = match.group(1).lower()  # normalize casing -- confirmed real fixtures vary
    raw_args = match.group(2).strip()

    result = {"target_kind": kind}

    if kind == "formdatasourcestr":
        parts = [p.strip() for p in raw_args.split(",")]
        if len(parts) == 2:
            result["form_name"] = parts[0]
            result["datasource_name"] = parts[1]
        else:
            result["target_name"] = raw_args
            result["parse_warning"] = (
                f"expected 2 comma-separated args for formdatasourcestr, got {len(parts)}: {raw_args!r}"
            )
    else:
        result["target_name"] = raw_args

    return result


def strip_doc_comments(text):
    return DOC_COMMENT_RE.sub("", text)


def strip_leading_attributes(text):
    """
    Removes one or more [Attribute(...)] blocks appearing before the
    signature. Manual bracket counting on [ / ] only -- ignores whatever
    is inside (parens, quotes, backslashes). Confirmed safe against the
    real [SysObsolete('...', false, 21\\04\\2020)] case, which has
    backslash-separated tokens that would confuse a naive regex.
    """
    i, n = 0, len(text)
    while True:
        while i < n and text[i] in " \t\r\n":
            i += 1
        if i < n and text[i] == "[":
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                if text[j] == "[":
                    depth += 1
                elif text[j] == "]":
                    depth -= 1
                j += 1
            i = j
        else:
            break
    return text[i:]


def find_matching_paren(text, open_index):
    """
    Manual depth counting from an opening '(' to its matching ')'.
    Confirmed necessary: naive non-greedy regex breaks on nested calls
    in default values, e.g.
    `= DateTimeUtil::getSystemDate(DateTimeUtil::getUserPreferredTimeZone())`.
    Does not understand string literals -- accepted limitation, consistent
    with the project's explicit decision not to build a full X++ parser.
    """
    depth, i, n = 0, open_index, len(text)
    while i < n:
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def split_top_level_commas(text):
    """Splits a parameter list on commas not nested inside parens."""
    parts, depth, current = [], 0, []
    for ch in text:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def parse_parameter(param_text):
    """
    Splits one parameter declaration into type/name/default.
    Typical form: 'Type _name' or 'Type _name = defaultExpr'.
    """
    parts = DEFAULT_SPLIT_RE.split(param_text, maxsplit=1)
    decl = parts[0].strip()
    default = parts[1].strip() if len(parts) > 1 else None

    tokens = decl.split()
    if len(tokens) < 2:
        return {
            "type": None,
            "name": decl if decl else None,
            "default": default,
            "parse_warning": f"could not split type/name from {param_text!r}",
        }

    name = tokens[-1]
    param_type = " ".join(tokens[:-1])
    result = {"type": param_type, "name": name}
    if default is not None:
        result["default"] = default
    return result


def parse_signature(method_name, source_text):
    """
    Extracts return type, modifiers, and parameters from a method's own
    <Source> text. Relies on each method having its own dedicated
    <Source> block -- so the first occurrence of "methodname(" after
    stripping comments/attributes is guaranteed to be the definition
    itself, not a self-reference (recursive calls occur inside the body,
    i.e. after the opening '{', which is after what we extract here).
    """
    if not method_name:
        return {
            "return_type": None, "modifiers": [], "parameters": [],
            "parse_warning": "method has no name -- cannot extract signature",
        }

    text = strip_doc_comments(source_text)
    text = strip_leading_attributes(text.lstrip())

    name_pattern = re.compile(r"\b" + re.escape(method_name) + r"\s*\(")
    match = name_pattern.search(text)
    if not match:
        return {
            "return_type": None, "modifiers": [], "parameters": [],
            "parse_warning": f"could not locate signature for method {method_name!r}",
        }

    prefix = text[: match.start()].strip()
    paren_open = match.end() - 1
    paren_close = find_matching_paren(text, paren_open)

    if paren_close == -1:
        params_text, parse_warning = "", "unbalanced parentheses in parameter list"
    else:
        params_text, parse_warning = text[paren_open + 1 : paren_close], None

    prefix_tokens = prefix.split()
    modifiers = [t for t in prefix_tokens if t in KNOWN_MODIFIERS]
    return_type_tokens = [t for t in prefix_tokens if t not in KNOWN_MODIFIERS]
    return_type = " ".join(return_type_tokens) if return_type_tokens else None

    parameters = [parse_parameter(p) for p in split_top_level_commas(params_text)]

    result = {"return_type": return_type, "modifiers": modifiers, "parameters": parameters}
    if parse_warning:
        result["parse_warning"] = parse_warning
    return result


def parse_method(method_el):
    name = get_method_name(method_el)
    source = method_el.findtext("Source") or ""
    calls_next = bool(NEXT_CALL_RE.search(source))

    result = {
        "name": name,
        "calls_next": calls_next,
        "is_new_method": not calls_next,  # ASSUMPTION -- untested against a real "forgot next()" bug
    }
    result.update(parse_signature(name, source))
    return result


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
        sys.exit(1)

    result = parse_class_xml(sys.argv[1])
    print(json.dumps(result, indent=2))