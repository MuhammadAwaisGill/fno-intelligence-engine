"""
diagnose_constraints.py -- one-off diagnostic, not part of the pipeline.

validate.py found that 4 of 6 real table fixtures have at least one
AxTableRelationConstraint with NO <RelatedField> at all (not even a
ConstraintRelatedFixed with just no value -- genuinely no RelatedField
tag). This prints the raw XML of every such constraint so we can see
the real structure instead of guessing what it is.
"""
import os
from lxml import etree

XSI_NS = "{http://www.w3.org/2001/XMLSchema-instance}type"


def diagnose(filepath):
    tree = etree.parse(filepath)
    root = tree.getroot()

    for relation_el in root.findall("./Relations/AxTableRelation"):
        relation_name = relation_el.findtext("Name")
        for constraint_el in relation_el.findall("./Constraints/AxTableRelationConstraint"):
            related_field = constraint_el.findtext("RelatedField")
            if related_field is None:
                xsi_type = constraint_el.get(XSI_NS, "(no xsi:type attribute)")
                print(f"--- {os.path.basename(filepath)} | relation: {relation_name} | xsi:type: {xsi_type} ---")
                print(etree.tostring(constraint_el, pretty_print=True).decode())
                print()


if __name__ == "__main__":
    fixtures_dir = os.path.join("fixtures", "tables")
    for filename in sorted(os.listdir(fixtures_dir)):
        if filename.endswith(".xml"):
            diagnose(os.path.join(fixtures_dir, filename))