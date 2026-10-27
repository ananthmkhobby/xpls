from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from didac_app.config import load_config
from didac_app.storage import LeadStore


def main() -> None:
    parser = argparse.ArgumentParser(description="DIDAC WhatsApp lead app utilities")
    parser.add_argument("command", choices=["export", "summary", "reset-sample"])
    parser.add_argument("--output", default="outputs/didac/didac_leads.xlsx")
    args = parser.parse_args()

    config = load_config()
    store = LeadStore(config.database_path)
    if args.command == "export":
        path = store.export_report_excel(Path(args.output))
        print(path)
    elif args.command == "summary":
        leads = store.list_leads()
        print(f"Total leads: {len(leads)}")
        for priority, count in store.count_by_priority().items():
            print(f"{priority}: {count}")
    elif args.command == "reset-sample":
        with sqlite3.connect(config.database_path) as conn:
            conn.execute("DELETE FROM feedback")
            conn.execute("DELETE FROM media")
            conn.execute("DELETE FROM leads")
        print(f"Cleared leads from {config.database_path}")


if __name__ == "__main__":
    main()
