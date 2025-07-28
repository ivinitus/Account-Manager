import datetime
import random
import time

from flask import Blueprint, jsonify, request

from .database import db_pool
from .utils import cache, CACHE_TIMEOUT, normalize_output, is_cache_valid

accounts_bp = Blueprint("accounts", __name__)


@accounts_bp.route("/import_accounts", methods=["POST"])
def import_accounts():
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Expected a list of account objects"}), 400

    if not data:
        return jsonify({"error": "Empty data provided"}), 400

    inserted = 0
    skipped = 0

    with db_pool.get_connection() as conn:
        cursor = conn.cursor()

        customer_ids = [acc["customerId"] for acc in data]
        placeholders = ",".join(["?" for _ in customer_ids])
        cursor.execute(
            f"SELECT customer_id FROM accounts WHERE customer_id IN ({placeholders})",
            customer_ids,
        )
        existing_ids = {row["customer_id"] for row in cursor.fetchall()}

        new_accounts = []
        for acc in data:
            if acc["customerId"] in existing_ids:
                skipped += 1
                continue

            new_accounts.append(
                (
                    acc["customerId"],
                    acc["email"],
                    acc["password"],
                    acc["marketplace"],
                    acc["type"],
                    acc["date"],
                )
            )
            inserted += 1

        if new_accounts:
            cursor.executemany(
                """
                INSERT INTO accounts (customer_id, email, password, marketplace, type, date)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                new_accounts,
            )

        conn.commit()

    return jsonify(
        {"status": "success", "inserted": inserted, "skipped": skipped, "total_received": len(data)}
    )


@accounts_bp.route("/accounts")
def get_accounts():
    marketplace = request.args.get("marketplace", "").lower()
    account_type = request.args.get("type", "").lower()

    if not marketplace or not account_type:
        return jsonify({"error": "Missing 'marketplace' or 'type' parameter"}), 400

    with db_pool.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM accounts 
            WHERE LOWER(marketplace) = ? AND LOWER(type) = ?
        """,
            (marketplace, account_type),
        )
        accounts = cursor.fetchall()

        if accounts:
            accounts_list = [dict(acc) for acc in accounts]
            acc_dict = random.choice(accounts_list)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if acc_dict["type"].lower() == "rnb":
                cursor.execute(
                    """UPDATE accounts SET type = ?, date = ? WHERE customer_id = ?""",
                    ("member", now, acc_dict["customer_id"]),
                )
                acc_dict["type"] = "member"
                acc_dict["date"] = now

            cursor.execute("DELETE FROM last_used")
            cursor.execute(
                """
                INSERT INTO last_used (customer_id, email, password, marketplace, type, date)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    acc_dict["customer_id"],
                    acc_dict["email"],
                    acc_dict["password"],
                    acc_dict["marketplace"],
                    acc_dict["type"],
                    acc_dict["date"],
                ),
            )

            cache["last_used"] = normalize_output(acc_dict)
            cache["last_used_timestamp"] = time.time()

            conn.commit()
            return jsonify([normalize_output(acc_dict)])

    return jsonify([])


@accounts_bp.route("/last_used_account")
def last_used():
    if is_cache_valid():
        return jsonify(cache["last_used"])

    with db_pool.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM last_used ORDER BY id DESC LIMIT 1")
        acc = cursor.fetchone()
        if not acc:
            return jsonify({"error": "No account used yet"}), 404

        result = normalize_output(dict(acc))
        cache["last_used"] = result
        cache["last_used_timestamp"] = time.time()
        return jsonify(result)


@accounts_bp.route("/update_account_type", methods=["POST"])
def update_account_type():
    data = request.get_json()
    customer_id = data.get("customer_id")
    new_type = data.get("new_type")

    if not customer_id or not new_type:
        return jsonify({"error": "Missing 'customer_id' or 'new_type'"}), 400

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with db_pool.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE accounts SET type = ?, date = ? WHERE customer_id = ?""",
            (new_type.lower(), now, customer_id),
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Account not found"}), 404

        if cache["last_used"] and cache["last_used"].get("Customer ID") == customer_id:
            cache["last_used"] = None
            cache["last_used_timestamp"] = 0

        conn.commit()

    return jsonify({"status": "success", "message": f"Account {customer_id} updated"})


@accounts_bp.route("/health")
def health():
    return jsonify({"status": "ok"})