"""Example Render Cron Job: verifies both databases are reachable.

Run manually with `python scripts/check_connectivity.py`, or wire it up as
a Render Cron Job (a separate Render service of type "Cron Job", same repo,
start command `python scripts/check_connectivity.py`) to get an alert if
either database becomes unreachable. Use this as the template for any
future scheduled maintenance task (the original Worker had Cloudflare Cron
Triggers for this kind of thing; Render's Cron Jobs are the equivalent).
"""
import asyncio
import sys

from app.config import get_settings
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres


async def main() -> int:
    settings = get_settings()
    ok = True

    pg = SupabasePostgres(settings.supabase_db_url)
    try:
        await pg.connect()
        await pg.fetch_val("SELECT 1")
        print("[ok] Supabase Postgres reachable")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Supabase Postgres: {exc}")
        ok = False
    finally:
        await pg.close()

    d1 = D1Client(settings)
    try:
        result = await d1.query("SELECT 1 AS ok")
        print(f"[ok] D1 gateway reachable: {result.rows}")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] D1 gateway: {exc}")
        ok = False
    finally:
        await d1.aclose()

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
