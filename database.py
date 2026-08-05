import sqlite3
from datetime import datetime
from contextlib import contextmanager

from config import DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS owners (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                phone TEXT,
                agreed INTEGER DEFAULT 0,
                agreed_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dachas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                region TEXT,
                district TEXT,
                location TEXT,
                price_per_night INTEGER NOT NULL,
                contact_phone TEXT,
                photo_file_id TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dacha_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                check_in TEXT,
                check_out TEXT,
                nights INTEGER DEFAULT 1,
                total_price INTEGER DEFAULT 0,
                commission_amount INTEGER DEFAULT 0,
                commission_status TEXT DEFAULT 'unpaid',
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                FOREIGN KEY (dacha_id) REFERENCES dachas (id)
            )
        """)


# ---------- Owners ----------

def get_owner(user_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM owners WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def upsert_owner(user_id, full_name, phone, agreed=1):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO owners (user_id, full_name, phone, agreed, agreed_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 full_name=excluded.full_name,
                 phone=excluded.phone,
                 agreed=excluded.agreed,
                 agreed_at=excluded.agreed_at""",
            (user_id, full_name, phone, agreed, datetime.now().isoformat()),
        )


def owner_has_agreed(user_id):
    owner = get_owner(user_id)
    return bool(owner and owner["agreed"])


# ---------- Dachas ----------

def add_dacha(owner_id, name, description, region, district, location, price_per_night, contact_phone, photo_file_id):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO dachas
               (owner_id, name, description, region, district, location, price_per_night, contact_phone, photo_file_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (owner_id, name, description, region, district, location, price_per_night,
             contact_phone, photo_file_id, datetime.now().isoformat()),
        )
        return cur.lastrowid


def get_active_dachas():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM dachas WHERE is_active = 1 ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def get_dachas_by_district(region, district):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM dachas WHERE is_active = 1 AND region = ? AND district = ? ORDER BY id DESC",
            (region, district),
        ).fetchall()
        return [dict(r) for r in rows]


def get_dacha(dacha_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM dachas WHERE id = ?", (dacha_id,)).fetchone()
        return dict(row) if row else None


def get_dachas_by_owner(owner_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM dachas WHERE owner_id = ? ORDER BY id DESC", (owner_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def deactivate_dacha(dacha_id):
    with get_conn() as conn:
        conn.execute("UPDATE dachas SET is_active = 0 WHERE id = ?", (dacha_id,))


# ---------- Bookings ----------

def create_booking(dacha_id, user_id, username, full_name, phone, check_in, check_out, nights, total_price, commission_amount):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO bookings
               (dacha_id, user_id, username, full_name, phone, check_in, check_out,
                nights, total_price, commission_amount, commission_status, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'unpaid', 'pending', ?)""",
            (dacha_id, user_id, username, full_name, phone, check_in, check_out,
             nights, total_price, commission_amount, datetime.now().isoformat()),
        )
        return cur.lastrowid


def get_booking(booking_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        return dict(row) if row else None


def update_booking_status(booking_id, status):
    with get_conn() as conn:
        conn.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))


def update_commission_status(booking_id, status):
    with get_conn() as conn:
        conn.execute("UPDATE bookings SET commission_status = ? WHERE id = ?", (status, booking_id))


def get_user_bookings(user_id):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT bookings.*, dachas.name as dacha_name
               FROM bookings JOIN dachas ON bookings.dacha_id = dachas.id
               WHERE bookings.user_id = ? ORDER BY bookings.id DESC""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_pending_bookings():
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT bookings.*, dachas.name as dacha_name
               FROM bookings JOIN dachas ON bookings.dacha_id = dachas.id
               WHERE bookings.status = 'pending' ORDER BY bookings.id ASC"""
        ).fetchall()
        return [dict(r) for r in rows]


def get_unpaid_commissions_for_owner(owner_id):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT bookings.*, dachas.name as dacha_name
               FROM bookings JOIN dachas ON bookings.dacha_id = dachas.id
               WHERE dachas.owner_id = ? AND bookings.status = 'approved'
                 AND bookings.commission_status != 'paid'
               ORDER BY bookings.id ASC""",
            (owner_id,),
        ).fetchall()
        return [dict(r) for r in rows]
