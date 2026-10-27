from app.models import Page
from app.program_extractor import extract_program_research


def test_extracts_named_programmes_and_fit_reason_from_page_html():
    html = """
    <html><body>
      <h2>School Rejuvenation Programme</h2>
      <p>We work with government schools to improve classroom learning, teacher support, and student outcomes.</p>
      <h2>Giving Every Dream a Chance</h2>
      <p>This initiative supports children through education and school readiness.</p>
    </body></html>
    """
    page = Page(
        url="https://example.org/education",
        title="Education",
        text="School Rejuvenation Programme. We work with government schools to improve classroom learning.",
        html=html,
    )
    research = extract_program_research([page], "Akshaya Patra")
    assert "School Rejuvenation Programme" in research.named_programme
    assert "government schools" in research.what_they_do.lower()
    assert "School Rejuvenation Programme" in research.custom_appreciation
    assert "separate lab room" in research.why_xperimentor_fits
