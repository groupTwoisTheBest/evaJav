from app.db import get_connection, init_db


def test_neon_connection_and_schema():
    init_db()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.feedback')")
            assert cur.fetchone()[0] == "feedback"
    finally:
        conn.close()
