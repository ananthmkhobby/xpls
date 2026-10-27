from didac_app.parser import parse_message, parse_qualification_note, parse_voice_style_note


def test_parse_structured_new_lead_message():
    kind, lead = parse_message(
        """New lead
Name: Ramesh
Org: XYZ Foundation
Role: CSR Head
City: Delhi
Interest: STEM lab for govt schools
Budget: 20 schools
Timeline: Q1""",
        "whatsapp:+919999999999",
    )
    assert kind == "lead"
    assert lead.name == "Ramesh"
    assert lead.org == "XYZ Foundation"
    assert lead.role == "CSR Head"
    assert lead.interest == "STEM lab for govt schools"
    assert lead.timeline == "Q1"


def test_parse_card_form_fields():
    kind, lead = parse_message(
        """New lead
First Name: Jane
Last Name: Doe
Designation: Principal
Email: jane@school.edu
Phone: +91 9876543210
Org: Springfield High School
Organisation Type: School
Curriculum: CBSE, State Board
Medium of Instruction: English, Kannada
State: Karnataka
City: Bengaluru
District: Bengaluru Urban
Pincode: 560001
Website: https://springfield.edu
Google Maps URL: https://maps.google.com/example
UDISE Code: 29040100101
Parent Organisation ID: org_cuid""",
        "whatsapp:+919999999999",
    )
    assert kind == "lead"
    assert lead.first_name == "Jane"
    assert lead.last_name == "Doe"
    assert lead.name == "Jane Doe"
    assert lead.designation == "Principal"
    assert lead.organisation_type == "School"
    assert "CBSE" in lead.curriculum
    assert lead.medium_of_instruction == "English, Kannada"
    assert lead.pincode == "560001"
    assert lead.udise_code == "29040100101"


def test_parse_voice_style_note():
    lead = parse_voice_style_note(
        "Met Priya from ABC Foundation. They work with 40 government schools in Karnataka. Interested in science labs, wants proposal next week."
    )
    assert lead.name == "Priya"
    assert lead.org == "ABC Foundation"
    assert lead.schools_count == "40"
    assert "Proposal requested" in lead.interest
    assert "STEM lab / science kits" in lead.interest
    assert lead.timeline == "Next week"


def test_parse_qualification_note_for_role_and_interest():
    lead = parse_qualification_note(
        "I am a distributor from Karnataka interested in STREAM and science kits for 25 schools. Need demo next week."
    )
    assert lead.lead_type == "Distributor"
    assert lead.organisation_type == "Distributor"
    assert "STREAM" in lead.interest
    assert "STEM lab / science kits" in lead.interest
    assert lead.schools_count == "25"
    assert lead.timeline == "Next week"
    assert lead.city == "Karnataka"
