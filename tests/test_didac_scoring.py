from didac_app.config import DidacConfig
from didac_app.models import Lead
from didac_app.scoring import enrich_lead


def test_hot_csr_school_stem_lead_gets_owner_and_drafts():
    lead = Lead(
        org="XYZ Foundation",
        role="CSR Head",
        lead_type="CSR",
        interest="STEM lab for government schools",
        schools_count="20",
        timeline="Q1",
        phone="9876543210",
    )
    enriched = enrich_lead(lead, DidacConfig())
    assert enriched.priority == "Hot"
    assert enriched.owner == "Chethan"
    assert "DIDAC follow-up" in enriched.email_subject
    assert "Lab-in-Classroom" in enriched.email_draft
