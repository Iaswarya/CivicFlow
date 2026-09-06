"""
Seeds a small STARTER set of illustrative compliance rules plus a demo admin/inspector
account, so the app is demoable immediately after setup.

IMPORTANT: These rules are ILLUSTRATIVE ONLY -- they check for the *presence and basic
format* of commonly-required label declarations (product name, net quantity, MRP,
manufacturer/packer/importer details, country of origin, consumer care, dates). They do
NOT encode actual Legal Metrology (Packaged Commodities) Rules, 2011 section numbers,
exact legal thresholds, or penalties, and must be reviewed/corrected by someone with the
legal text in hand before being used for anything beyond an SIH demo.

Run with:  python seed_rules.py   (after the database is reachable and migrated)
"""
from app.database.session import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models import models as m

Base.metadata.create_all(bind=engine)
db = SessionLocal()

STARTER_RULES = [
    dict(rule_name="Product name present", category="ALL", field_to_check="product_name",
         validation_type=m.ValidationType.REQUIRED_FIELD, severity=m.Severity.MEDIUM,
         description="Label should identify the product.",
         source_reference="Illustrative -- verify against LMR 2011 before production use."),
    dict(rule_name="Net quantity declared", category="ALL", field_to_check="net_quantity",
         validation_type=m.ValidationType.REQUIRED_FIELD, severity=m.Severity.HIGH,
         description="Net quantity (weight/volume/count) should be declared on the label.",
         source_reference="Illustrative -- verify against LMR 2011 before production use."),
    dict(rule_name="Net quantity format", category="ALL", field_to_check="net_quantity",
         validation_type=m.ValidationType.PATTERN_MATCH, expected_pattern=r"[0-9.,]+\s*(g|kg|ml|l|gm)",
         severity=m.Severity.MEDIUM, description="Net quantity should include a numeric value and a standard unit.",
         source_reference="Illustrative -- verify against LMR 2011 before production use."),
    dict(rule_name="MRP declared", category="ALL", field_to_check="mrp",
         validation_type=m.ValidationType.REQUIRED_FIELD, severity=m.Severity.HIGH,
         description="Maximum Retail Price should be declared on the label.",
         source_reference="Illustrative -- verify against LMR 2011 before production use."),
    dict(rule_name="Manufacturer/packer/importer identified", category="ALL", field_to_check="manufacturer",
         validation_type=m.ValidationType.REQUIRED_FIELD, severity=m.Severity.HIGH,
         description="The manufacturer, packer, or importer's name should be identifiable on the label.",
         source_reference="Illustrative -- verify against LMR 2011 before production use."),
    dict(rule_name="Address present", category="ALL", field_to_check="address",
         validation_type=m.ValidationType.REQUIRED_FIELD, severity=m.Severity.MEDIUM,
         description="A postal address for the manufacturer/packer/importer should be present.",
         source_reference="Illustrative -- verify against LMR 2011 before production use."),
    dict(rule_name="Country of origin declared", category="ALL", field_to_check="country_of_origin",
         validation_type=m.ValidationType.REQUIRED_FIELD, severity=m.Severity.LOW,
         description="Country of origin should be stated, particularly for imported goods.",
         source_reference="Illustrative -- verify against LMR 2011 before production use."),
    dict(rule_name="Consumer care details present", category="ALL", field_to_check="consumer_care_details",
         validation_type=m.ValidationType.REQUIRED_FIELD, severity=m.Severity.LOW,
         description="A consumer care contact (phone/email) should be provided.",
         source_reference="Illustrative -- verify against LMR 2011 before production use."),
    dict(rule_name="Manufacturing/expiry date legibility", category="Food", field_to_check="expiry_date",
         validation_type=m.ValidationType.MANUAL_VERIFICATION, severity=m.Severity.HIGH,
         description="Date declarations on food products should be manually cross-checked against the physical pack.",
         source_reference="Illustrative -- always requires human verification."),
    dict(rule_name="Batch number present", category="ALL", field_to_check="batch_number",
         validation_type=m.ValidationType.REQUIRED_FIELD, severity=m.Severity.LOW,
         description="A batch/lot number helps trace the product.",
         source_reference="Illustrative -- verify against LMR 2011 before production use."),
]


def run():
    created_rules = 0
    for rule_data in STARTER_RULES:
        exists = db.query(m.Rule).filter(
            m.Rule.rule_name == rule_data["rule_name"], m.Rule.category == rule_data["category"]
        ).first()
        if not exists:
            db.add(m.Rule(**rule_data))
            created_rules += 1
    db.commit()
    print(f"Seeded {created_rules} new rule(s) (skipped any that already existed).")

    demo_users = [
        ("admin@civicflow.demo", "Admin123!", "CivicFlow Admin", m.UserRole.ADMIN),
        ("inspector@civicflow.demo", "Inspector123!", "Demo Inspector", m.UserRole.INSPECTOR),
        ("consumer@civicflow.demo", "Consumer123!", "Demo Consumer", m.UserRole.CONSUMER),
    ]
    created_users = 0
    for email, password, name, role in demo_users:
        if not db.query(m.User).filter(m.User.email == email).first():
            db.add(m.User(full_name=name, email=email, hashed_password=hash_password(password), role=role))
            created_users += 1
    db.commit()
    print(f"Seeded {created_users} new demo user(s) (skipped any that already existed).")
    print("Demo credentials: admin@civicflow.demo / Admin123!  |  inspector@civicflow.demo / Inspector123!")


if __name__ == "__main__":
    run()
    db.close()
