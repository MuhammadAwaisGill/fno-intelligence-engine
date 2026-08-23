from lxml import etree
import os

xml_path = os.path.join("fixtures", "tables", "VendTrans.xml")

# Load and parse the XML document
tree = etree.parse(xml_path)
root = tree.getroot()

# 1. Extract Table Name
table_name = root.findtext("Name")
print(f"=== Table: {table_name} ===\n")

# 2. Extract Fields and Extended Data Types (EDTs)
print("--- Fields ---")
fields = root.xpath("./Fields/AxTableField")
for field in fields:
    field_name = field.findtext("Name")
    edt = field.findtext("ExtendedDataType") or "None"
    
    # Retrieve XMLSchema-instance type attribute (xsi:type)
    xsi_type = field.get("{http://www.w3.org/2001/XMLSchema-instance}type", "Unknown")
    
    print(f"Name: {field_name:<30} | Type: {xsi_type:<22} | EDT: {edt}")

# 3. Extract Relations
print("\n--- Relations ---")
relations = root.xpath("./Relations/AxTableRelation")
for relation in relations:
    rel_name = relation.findtext("Name")
    related_table = relation.findtext("RelatedTable")
    print(f"\nRelation: {rel_name} -> Related Table: {related_table}")
    
    # Extract field constraints
    constraints = relation.xpath("./Constraints/AxTableRelationConstraint")
    for constraint in constraints:
        c_type = constraint.get("{http://www.w3.org/2001/XMLSchema-instance}type", "Constraint")
        field = constraint.findtext("Field")
        related_field = constraint.findtext("RelatedField")
        print(f"  └─ [{c_type}] {field} == {related_field}")