from app.contact_extractor import categorize_email, extract_emails
from app.models import Page


def test_email_priority_prefers_direct_then_role_then_general():
    page = Page(
        url="https://ngo.testfixture/contact",
        title="Contact",
        text="info@ngo.testfixture partnerships@ngo.testfixture priya.shah@ngo.testfixture jobs@ngo.testfixture",
        html='<a href="mailto:contact@ngo.testfixture">Mail</a>',
    )
    emails = extract_emails([page])
    assert [item.email for item in emails[:3]] == [
        "priya.shah@ngo.testfixture",
        "partnerships@ngo.testfixture",
        "contact@ngo.testfixture",
    ]


def test_irrelevant_email_category():
    assert categorize_email("careers@example.org") == "irrelevant"


def test_example_domain_is_irrelevant():
    assert categorize_email("johnsmith@example.com") == "irrelevant"
