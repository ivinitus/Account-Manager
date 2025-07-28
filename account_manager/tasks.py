import datetime
import threading
import time
from typing import List

from .database import db_pool


def auto_demote_members() -> None:
    """Demote newly created member accounts to '3 days old' after 3 days."""
    while True:
        try:
            with db_pool.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.datetime.now()
                three_days_ago = now - datetime.timedelta(days=3)

                cursor.execute(
                    """
                    UPDATE accounts
                    SET type = ?, date = ?
                    WHERE type = 'member'
                      AND datetime(date) <= datetime(?)
                """,
                    (
                        "3 days old",
                        now.strftime("%Y-%m-%d %H:%M:%S"),
                        three_days_ago.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
                updated = cursor.rowcount
                if updated:
                    print(f"Auto-demoted {updated} members -> '3 days old'")

                conn.commit()
        except Exception as exc:
            print(f"[tasks.auto_demote_members] {exc}")

        for _ in range(60):
            time.sleep(60)
            if not threading.current_thread().daemon:
                return


def cleanup_old_accounts() -> None:
    """cleanup old accounts on a rolling schedule."""
    while True:
        try:
            with db_pool.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.datetime.now()

                # Promote '3 days old' -> 'former' after 30 days
                thirty_days_ago = now - datetime.timedelta(days=30)
                cursor.execute(
                    """
                    UPDATE accounts
                    SET type = ?, date = ?
                    WHERE type = '3 days old'
                      AND datetime(date) <= datetime(?)
                """,
                    (
                        "former",
                        now.strftime("%Y-%m-%d %H:%M:%S"),
                        thirty_days_ago.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
                promoted = cursor.rowcount

                # Remove 'former' after 120 days
                one_twenty_ago = now - datetime.timedelta(days=120)
                cursor.execute(
                    """
                    DELETE FROM accounts
                    WHERE type = 'former'
                      AND datetime(date) <= datetime(?)
                """,
                    (one_twenty_ago.strftime("%Y-%m-%d %H:%M:%S"),),
                )
                deleted = cursor.rowcount

                if promoted or deleted:
                    print(
                        f"Cleanup stats: +{promoted} promoted to 'former', -{deleted} deleted"
                    )

                conn.commit()
        except Exception as exc:
            print(f"[tasks.cleanup_old_accounts] {exc}")

        # Run every 6 hours (sleep 10 min x36)
        for _ in range(36):
            time.sleep(600)
            if not threading.current_thread().daemon:
                return


def start_background_tasks() -> List[threading.Thread]:
    """Spawn daemon threads that run the background maintenance tasks."""
    demote = threading.Thread(target=auto_demote_members, daemon=True)
    cleanup = threading.Thread(target=cleanup_old_accounts, daemon=True)

    demote.start()
    cleanup.start()

    return [demote, cleanup]