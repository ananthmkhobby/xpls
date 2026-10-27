from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from didac_app.media import append_qr_details, media_storage_dir, sender_folder


def test_sender_folder_uses_whatsapp_number():
    assert sender_folder("whatsapp:+919845604740") == "919845604740"


def test_sender_folder_handles_unknown_values():
    assert sender_folder("") == "unknown_sender"


def test_media_storage_dir_uses_date_then_sender():
    received_at = datetime(2026, 10, 18, 9, 30, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert media_storage_dir(Path("data/didac_media"), "whatsapp:+919845604740", received_at) == Path(
        "data/didac_media/2026-10-18/919845604740"
    )


def test_append_qr_details_records_non_url_qr_value(monkeypatch):
    monkeypatch.setattr("didac_app.media.decode_qr_values", lambda local_path: ["EXB0987"])
    text = append_qr_details("/tmp/badge.jpg", "Name: Magesh")
    assert "Name: Magesh" in text
    assert "QR Page Text: EXB0987" in text
