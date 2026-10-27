from app.contact_extractor import normalize_phone


def test_normalizes_indian_mobile():
    assert normalize_phone("9876543210") == "+91 9876543210"


def test_normalizes_prefixed_indian_mobile():
    assert normalize_phone("+91-98765-43210") == "+91 9876543210"
