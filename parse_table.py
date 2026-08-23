"""
parse_table.py -- Step 4 work: generalized AxTable parser.

Design note (why this file exists instead of just extending parse_poc.py):
parse_poc.py proved raw extraction works. This turns that into a reusable
function whose OUTPUT SHAPE is dictated by schema/table_schema.json, not
by whatever felt convenient while exploring. That's the actual point of
doing schema-first: the parser now has a contract to satisfy, not just
"does it print something reasonable."
"""
from lxml import etree

XSI_NS = "{http://www.w3.org/2001/XMLSchema-instance}type"


def parse_field(field_el):
    """
    Extract one AxTableField into the schema's field shape.

    Why both edt and enum_type are read independently, not one-or-the-other:
    confirmed real case (VendTrans.TransType) has enum_type set with NO edt.
    Confirmed real case (VendTrans.Correct) has BOTH set. If this function
    only checked ExtendedDataType and fell back to EnumType as a single
    merged value, we could not tell those two cases apart later -- and
    Part 2's SQL schema needs to tell them apart to answer "what enum does
    this field use" reliably for every field, not just the ones with an EDT.
    """
    return {
        "name": field_el.findtext("Name"),
        "xsi_type": field_el.get(XSI_NS),
        "edt": field_el.findtext("ExtendedDataType"),  # None if absent -- valid per schema
        "enum_type": field_el.findtext("EnumType"),     # None if absent -- valid per schema
    }


def parse_constraint(constraint_el):
    """
    Extract one AxTableRelationConstraint, tagging it by its real xsi:type
    rather than assuming every constraint is a field-to-field join.

    Why: confirmed real case (VendTrans's DataArea relation) has a
    ConstraintRelatedFixed constraint (isVirtual_Extern) with NEITHER a
    <Field> NOR a <ValueStr> tag. If this function assumed every constraint
    has a Field, it would return None silently and look like a parse bug
    later instead of a documented, expected shape.
    """
    xsi_type = constraint_el.get(XSI_NS, "")
    kind = "fixed" if xsi_type == "AxTableRelationConstraintRelatedFixed" else "field"

    return {
        "kind": kind,
        "field": constraint_el.findtext("Field"),          # None is valid when kind == "fixed"
        "related_field": constraint_el.findtext("RelatedField"),
        "value": constraint_el.findtext("ValueStr"),        # None is valid -- not every fixed constraint has one
    }


def parse_relation(relation_el):
    return {
        "name": relation_el.findtext("Name"),
        "related_table": relation_el.findtext("RelatedTable"),
        "constraints": [
            parse_constraint(c)
            for c in relation_el.findall("./Constraints/AxTableRelationConstraint")
        ],
    }


def parse_table_xml(filepath):
    """
    Parse one AxTable XML file into the schema/table_schema.json shape.
    This is the Step 4 deliverable: a reusable function, not a one-off script.
    """
    tree = etree.parse(filepath)
    root = tree.getroot()

    return {
        "object_type": "table",
        "name": root.findtext("Name"),
        "fields": [parse_field(f) for f in root.findall("./Fields/AxTableField")],
        "relations": [parse_relation(r) for r in root.findall("./Relations/AxTableRelation")],
    }


if __name__ == "__main__":
    import json
    import os

    result = parse_table_xml(os.path.join("fixtures", "tables", "VendTrans.xml"))
    print(json.dumps(result, indent=2))
