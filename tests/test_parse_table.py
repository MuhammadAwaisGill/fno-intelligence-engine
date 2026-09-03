"""
tests/test_parse_table.py

Regression tests for parse_table.py.

Validation basis (be precise about this, don't overstate it):
- Aggregate field/relation counts (957 fields, 407 relations across 6
  real fixtures) confirmed to match the original Step 4 validation figures.
- A programmatic scan of all output found zero structural anomalies:
  no null constraint kinds, no missing field names, no missing xsi_types.
- The specific documented edge case (VendTrans.TransType = enum_type only,
  VendTrans.Correct = edt + enum_type both) confirmed present by name.

NOT yet done: manual line-by-line cross-check against raw table XML,
the way test_parse_class.py's fixtures were checked. If that level of
rigor is needed, it requires pasting the raw XML fixtures and repeating
the same process used for the class parser.
"""
import os
import pytest
from parse_table import parse_table_xml

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "tables")


def fixture_path(filename):
    return os.path.join(FIXTURES_DIR, filename)


# (filename, expected_name, expected_field_count, expected_relation_count)
TABLE_CASES = [
    ("InventTable.xml", "InventTable", 145, 66),
    ("PurchLine.xml", "PurchLine", 187, 78),
    ("PurchTable.xml", "PurchTable", 148, 62),
    ("SalesLine.xml", "SalesLine", 199, 80),
    ("SalesTable.xml", "SalesTable", 185, 81),
    ("VendTrans.xml", "VendTrans", 93, 40),
]


@pytest.mark.parametrize(
    "filename,expected_name,expected_field_count,expected_relation_count",
    TABLE_CASES,
    ids=[case[0] for case in TABLE_CASES],
)
def test_table_name_and_counts(filename, expected_name, expected_field_count, expected_relation_count):
    result = parse_table_xml(fixture_path(filename))
    assert result["name"] == expected_name
    assert len(result["fields"]) == expected_field_count
    assert len(result["relations"]) == expected_relation_count


@pytest.mark.parametrize(
    "filename,expected_name,expected_field_count,expected_relation_count",
    TABLE_CASES,
    ids=[case[0] for case in TABLE_CASES],
)
def test_no_structural_anomalies(filename, expected_name, expected_field_count, expected_relation_count):
    """
    Every field must have a name and an xsi_type. Every constraint must
    have a recognized 'kind' (column_join / target_value / source_value) --
    an unmapped xsi_type on a constraint would silently produce kind=None,
    which is the exact failure mode the 3-kind schema fix (Step 4) was
    written to catch. This test locks that fix in.
    """
    result = parse_table_xml(fixture_path(filename))

    for field in result["fields"]:
        assert field["name"] is not None, f"field with no name in {filename}"
        assert field["xsi_type"] is not None, f"field {field['name']} has no xsi_type in {filename}"

    for relation in result["relations"]:
        for constraint in relation["constraints"]:
            assert constraint["kind"] is not None, (
                f"unmapped constraint kind in relation {relation['name']} ({filename}) -- "
                f"a new AxTableRelationConstraint* xsi_type appeared that CONSTRAINT_KIND_MAP doesn't cover"
            )


def test_vendtrans_enum_only_field():
    """
    Confirmed real case: VendTrans.TransType has enum_type set with NO edt.
    Locks in that parse_field() reads edt and enum_type independently
    rather than treating them as one merged value.
    """
    result = parse_table_xml(fixture_path("VendTrans.xml"))
    trans_type = next(f for f in result["fields"] if f["name"] == "TransType")
    assert trans_type["xsi_type"] == "AxTableFieldEnum"
    assert trans_type["edt"] is None
    assert trans_type["enum_type"] == "LedgerTransType"


def test_vendtrans_edt_and_enum_both_field():
    """
    Confirmed real case: VendTrans.Correct has BOTH edt and enum_type set.
    Companion case to the enum-only test above -- together they prove
    parse_field() correctly distinguishes all combinations, not just one.
    """
    result = parse_table_xml(fixture_path("VendTrans.xml"))
    correct_field = next(f for f in result["fields"] if f["name"] == "Correct")
    assert correct_field["xsi_type"] == "AxTableFieldEnum"
    assert correct_field["edt"] == "Correct"
    assert correct_field["enum_type"] == "NoYes"


def test_total_fields_and_relations_across_all_fixtures():
    """
    Aggregate sanity check locking in the totals from the original
    Step 4 validation pass (957 fields, 407 relations across all 6
    real table fixtures combined).
    """
    total_fields = 0
    total_relations = 0
    for filename, _name, _fc, _rc in TABLE_CASES:
        result = parse_table_xml(fixture_path(filename))
        total_fields += len(result["fields"])
        total_relations += len(result["relations"])

    assert total_fields == 957
    assert total_relations == 407