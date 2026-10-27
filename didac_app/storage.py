from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import asdict, fields
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from didac_app.models import Lead


LEAD_FIELDS = [field.name for field in fields(Lead)]


class LeadStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.path)

    def init_db(self) -> None:
        columns = ", ".join(f"{field} TEXT" for field in LEAD_FIELDS if field != "id")
        with self.connect() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {columns}
                )
                """
            )
            existing_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(leads)").fetchall()
            }
            for field in LEAD_FIELDS:
                if field != "id" and field not in existing_columns:
                    conn.execute(f"ALTER TABLE leads ADD COLUMN {field} TEXT")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    url TEXT,
                    content_type TEXT,
                    local_path TEXT,
                    extracted_text TEXT,
                    FOREIGN KEY(lead_id) REFERENCES leads(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    from_number TEXT,
                    lead_id INTEGER,
                    feedback_type TEXT,
                    body TEXT,
                    media_id INTEGER,
                    sentiment TEXT,
                    action_required TEXT,
                    FOREIGN KEY(lead_id) REFERENCES leads(id),
                    FOREIGN KEY(media_id) REFERENCES media(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS inbound_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    from_number TEXT,
                    body TEXT,
                    num_media INTEGER,
                    media_urls TEXT,
                    status TEXT,
                    lead_ids TEXT,
                    error TEXT,
                    raw_payload TEXT
                )
                """
            )

    def create_lead(self, lead: Lead) -> Lead:
        data = asdict(lead)
        data.pop("id", None)
        columns = list(data.keys())
        placeholders = ", ".join("?" for _ in columns)
        with self.connect() as conn:
            cursor = conn.execute(
                f"INSERT INTO leads ({', '.join(columns)}) VALUES ({placeholders})",
                [data[column] for column in columns],
            )
            lead.id = cursor.lastrowid
        return lead

    def update_lead(self, lead: Lead) -> Lead:
        if not lead.id:
            return self.create_lead(lead)
        data = asdict(lead)
        data.pop("id", None)
        assignments = ", ".join(f"{column}=?" for column in data)
        with self.connect() as conn:
            conn.execute(
                f"UPDATE leads SET {assignments} WHERE id=?",
                [*data.values(), lead.id],
            )
        return lead

    def latest_lead_for_number(self, from_number: str) -> Lead | None:
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM leads WHERE from_number=? ORDER BY id DESC LIMIT 1",
                (from_number,),
            ).fetchone()
        return row_to_lead(row) if row else None

    def list_leads(self, where: str = "", params: tuple = ()) -> list[Lead]:
        query = "SELECT * FROM leads"
        if where:
            query += f" WHERE {where}"
        query += " ORDER BY id DESC"
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        return [row_to_lead(row) for row in rows]

    def count_by_priority(self) -> dict[str, int]:
        with self.connect() as conn:
            rows = conn.execute("SELECT priority, COUNT(*) FROM leads GROUP BY priority").fetchall()
        return {priority or "Unknown": count for priority, count in rows}

    def add_media(self, lead_id: int, url: str, content_type: str = "", local_path: str = "", extracted_text: str = "") -> None:
        with self.connect() as conn:
            cursor = conn.execute(
                "INSERT INTO media (lead_id, url, content_type, local_path, extracted_text) VALUES (?, ?, ?, ?, ?)",
                (lead_id, url, content_type, local_path, extracted_text),
            )
            return cursor.lastrowid

    def add_feedback(
        self,
        from_number: str,
        body: str,
        lead_id: int | None = None,
        feedback_type: str = "general",
        media_id: int | None = None,
        sentiment: str = "",
        action_required: str = "",
    ) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO feedback
                (from_number, lead_id, feedback_type, body, media_id, sentiment, action_required)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (from_number, lead_id, feedback_type, body, media_id, sentiment, action_required),
            )
            return cursor.lastrowid

    def list_feedback(self) -> list[sqlite3.Row]:
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute("SELECT * FROM feedback ORDER BY id DESC").fetchall()

    def list_media(self) -> list[sqlite3.Row]:
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute("SELECT * FROM media ORDER BY id DESC").fetchall()

    def get_media(self, media_id: int) -> sqlite3.Row | None:
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute("SELECT * FROM media WHERE id=?", (media_id,)).fetchone()

    def add_inbound_event(
        self,
        from_number: str,
        body: str,
        num_media: int,
        media_urls: list[str],
        raw_payload: dict,
        status: str = "received",
    ) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO inbound_events
                (from_number, body, num_media, media_urls, status, lead_ids, error, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    from_number,
                    body,
                    num_media,
                    json.dumps(media_urls),
                    status,
                    "",
                    "",
                    json.dumps(raw_payload, ensure_ascii=False),
                ),
            )
            return cursor.lastrowid

    def update_inbound_event(self, event_id: int | None, status: str, lead_ids: list[int] | None = None, error: str = "") -> None:
        if not event_id:
            return
        with self.connect() as conn:
            conn.execute(
                "UPDATE inbound_events SET status=?, lead_ids=?, error=? WHERE id=?",
                (status, ",".join(str(item) for item in lead_ids or []), error, event_id),
            )

    def list_inbound_events(self) -> list[sqlite3.Row]:
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute("SELECT * FROM inbound_events ORDER BY id DESC").fetchall()

    def export_excel(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        leads = list(reversed(self.list_leads()))
        wb = Workbook()
        ws = wb.active
        ws.title = "DIDAC Leads"
        headers = [field for field in LEAD_FIELDS if field != "raw_message"]
        ws.append(headers)
        for lead in leads:
            data = asdict(lead)
            ws.append([data.get(header, "") for header in headers])
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        header_fill = PatternFill("solid", fgColor="D9EAF7")
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = header_fill
        for column_cells in ws.columns:
            width = 12
            for cell in column_cells[:30]:
                if cell.value:
                    width = min(max(width, len(str(cell.value)) + 2), 55)
            ws.column_dimensions[get_column_letter(column_cells[0].column)].width = width
        wb.save(output_path)
        return output_path

    def export_report_excel(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb = Workbook()
        leads = list(reversed(self.list_leads()))
        ws = wb.active
        ws.title = "Leads"
        headers = [field for field in LEAD_FIELDS if field != "raw_message"]
        ws.append(headers)
        for lead in leads:
            data = asdict(lead)
            ws.append([data.get(header, "") for header in headers])
        feedback_ws = wb.create_sheet("Feedback")
        feedback_headers = ["id", "created_at", "from_number", "lead_id", "feedback_type", "body", "media_id", "sentiment", "action_required"]
        feedback_ws.append(feedback_headers)
        for row in reversed(self.list_feedback()):
            feedback_ws.append([row[header] for header in feedback_headers])
        media_ws = wb.create_sheet("Media")
        media_headers = ["id", "lead_id", "created_at", "url", "content_type", "local_path", "extracted_text"]
        media_ws.append(media_headers)
        for row in reversed(self.list_media()):
            media_ws.append([row[header] for header in media_headers])
        inbound_ws = wb.create_sheet("Inbound Events")
        inbound_headers = ["id", "created_at", "from_number", "body", "num_media", "media_urls", "status", "lead_ids", "error"]
        inbound_ws.append(inbound_headers)
        for row in reversed(self.list_inbound_events()):
            inbound_ws.append([row[header] for header in inbound_headers])
        for sheet in wb.worksheets:
            format_sheet(sheet)
        wb.save(output_path)
        return output_path

    def export_report_csv(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        headers = [field for field in LEAD_FIELDS if field != "raw_message"]
        leads = list(reversed(self.list_leads()))
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for lead in leads:
                data = asdict(lead)
                writer.writerow([data.get(header, "") for header in headers])
        return output_path


def format_sheet(ws) -> None:
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    header_fill = PatternFill("solid", fgColor="D9EAF7")
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
    for column_cells in ws.columns:
        width = 12
        for cell in column_cells[:30]:
            if cell.value:
                width = min(max(width, len(str(cell.value)) + 2), 60)
        ws.column_dimensions[get_column_letter(column_cells[0].column)].width = width


def row_to_lead(row) -> Lead:
    data = {field: (row[field] if row[field] is not None else "") for field in LEAD_FIELDS if field in row.keys()}
    data["id"] = row["id"]
    return Lead(**data)
