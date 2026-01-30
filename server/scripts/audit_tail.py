from __future__ import annotations

import os
import sqlite3

DB = (os.getenv("LTC_DB_PATH") or "./data/app.db").strip()

def main() -> None:
    if not os.path.exists(DB):
        print(f"DB nicht gefunden: {DB}")
        return

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            SELECT created_at, action, result, reason_code
            FROM auth_audit
            ORDER BY created_at DESC
            LIMIT 20;
            """
        )
        rows = cur.fetchall()
        if not rows:
            print("Keine Audit-Events gefunden.")
            return

        print(f"Letzte {len(rows)} Audit-Events (ohne PII):")
        for r in rows:
            ca = r["created_at"]
            action = r["action"]
            result = r["result"]
            reason = r["reason_code"] or "-"
            print(f"- {ca}  {action}  {result}  reason={reason}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
