from app.sales_automation import build_lead_automation


def test_sales_automation_scores_and_segments_stem_csr_lead():
    lead = build_lead_automation({
        "NGO Name": "Good STEM Foundation",
        "Role in the deal": "CSR Partner; Implementation Partner",
        "Evidence / relevance": "Found education/STEM signals: stem, school education, teacher training.",
        "Email": "partner@goodstem.org",
        "Key person": "Asha Rao",
        "LinkedIn URL": "https://linkedin.com/company/goodstem",
        "verification_status": "VERIFIED",
    })
    assert lead.lead_fit_score >= 80
    assert lead.lead_priority == "A - outreach now"
    assert lead.recommended_channel == "Email + LinkedIn"
    assert "STEM" in lead.likely_pitch_angle
    assert lead.email_subject.startswith("Partnership Opportunity:")
    assert "I'm Chethan" in lead.suggested_first_email
    assert "What we bring:" in lead.suggested_first_email
    assert "100+ government schools" in lead.suggested_first_email
    assert "Corporate Partnerships or Programmes team" in lead.suggested_first_email


def test_sales_email_uses_named_programme_research():
    lead = build_lead_automation({
        "NGO Name": "Akshaya Patra Foundation",
        "Role in the deal": "CSR Partner",
        "Named programme": "School Rejuvenation Programme; Giving Every Dream a Chance",
        "What they do": "School Rejuvenation Programme: works with government schools to improve classroom learning environments.",
        "Custom appreciation": "We were glad to see your Beyond Meals work, particularly the School Rejuvenation Programme.",
        "Why Xperimentor fits": "Xperimentor can add a hands-on science and math layer to the schools already being served.",
        "Email": "partnerships@example-foundation.org",
        "verification_status": "VERIFIED",
    })
    assert "School Rejuvenation Programme" in lead.suggested_first_email
    assert "Beyond Meals" in lead.suggested_first_email
    assert "hands-on science and math layer" in lead.suggested_first_email


def test_sales_email_uses_curated_fallback_when_site_blocks():
    lead = build_lead_automation({
        "NGO Name": "The Akshaya Patra Foundation",
        "Website": "https://www.akshayapatra.org",
        "Email": "shridhar.venkat@akshayapatra.org",
        "verification_status": "REVIEW_REQUIRED",
    })
    assert "Beyond Meals" in lead.suggested_first_email
    assert "School Rejuvenation Programme" in lead.suggested_first_email
    assert "Giving Every Dream a Chance" in lead.suggested_first_email


def test_sales_automation_routes_no_contact_to_manual_research():
    lead = build_lead_automation({
        "NGO Name": "Unknown Trust",
        "Evidence / relevance": "Limited public evidence of school programs.",
        "errors": "NO_EMAIL_FOUND; NO_PHONE_FOUND",
    })
    assert lead.recommended_channel == "Manual research"
    assert lead.lead_priority in {"C - nurture", "D - manual review"}
