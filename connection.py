import os
import sys
import mysql.connector

DB_HOST     = "mysql-321c1333-alustudent-a6c3.c.aivencloud.com"
DB_PORT     = 21755
DB_USER     = "avnadmin"
DB_PASSWORD = "AVNS_bI1GHgU3lywk6XbCIWa"
DB_NAME     = "defaultdb"


def get_connection():
    try:
        return mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connection_timeout=5
        )
    except Exception:
        print("\n  [Database Error] Could not connect to the cloud database.")
        print("  Please check your internet connection and try again.\n")
        sys.exit(1)


def setup():
    db = get_connection()
    cursor = db.cursor(buffered=True)
    folder = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(folder, "databse.sql")
    if os.path.exists(schema_path):
        with open(schema_path) as schema_file:
            full_sql = schema_file.read()
        for statement in full_sql.split(";"):
            cleaned = statement.strip()
            lines = [l for l in cleaned.splitlines() if not l.strip().startswith("--")]
            clean_stmt = "\n".join(lines).strip()
            if clean_stmt != "" and clean_stmt.upper().startswith("CREATE"):
                cursor.execute(clean_stmt)
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS members (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50) UNIQUE)")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE events MODIFY COLUMN event_time VARCHAR(20)")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN created_by VARCHAR(50) DEFAULT 'Planner'")
    except:
        pass
    db.commit()

    cursor.execute("SELECT COUNT(*) FROM categories")
    count = cursor.fetchone()[0]
    if count == 0:
        default_categories = ["Classes", "Assignments", "Personal", "Others"]
        for category_name in default_categories:
            cursor.execute("INSERT INTO categories (name) VALUES (%s)", (category_name,))
        db.commit()

    cursor.execute("SELECT COUNT(*) FROM members")
    m_count = cursor.fetchone()[0]
    if m_count == 0:
        default_members = ["Kingsley", "Felix", "Vanessa", "Rita", "Gabriel"]
        for member_name in default_members:
            cursor.execute("INSERT INTO members (name) VALUES (%s)", (member_name,))
        db.commit()

    cursor.close()
    db.close()


def get_all_members():
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT id, name FROM members ORDER BY id")
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return rows


def add_member(name):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    try:
        cursor.execute("INSERT INTO members (name) VALUES (%s)", (name,))
        db.commit()
    except:
        pass
    cursor.close()
    db.close()


def delete_member(name):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("DELETE FROM members WHERE name = %s", (name,))
    db.commit()
    count = cursor.rowcount
    cursor.close()
    db.close()
    return count


def get_all_categories():
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT id, name FROM categories ORDER BY id")
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return rows


def get_category_id(name):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT id FROM categories WHERE name = %s", (name,))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row[0] if row else None


def add_category(name):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
    db.commit()
    cursor.close()
    db.close()


def add_event(title, event_date, event_time, details, category_id, created_by="Planner"):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    try:
        cursor.execute(
            "INSERT INTO events (title, event_date, event_time, details, status, category_id, created_by) "
            "VALUES (%s, %s, %s, %s, 'pending', %s, %s)",
            (title, event_date, event_time, details, category_id, created_by)
        )
        db.commit()
    except Exception:
        db.rollback()
        cursor.execute(
            "INSERT INTO events (title, event_date, event_time, details, status, category_id, created_by) "
            "VALUES (%s, %s, %s, %s, 'pending', %s, %s)",
            (title, event_date, event_time, details, category_id, created_by)
        )
        db.commit()
    new_id = cursor.lastrowid
    cursor.close()
    db.close()
    return new_id


def get_user_events(owner_name):
    if not owner_name or owner_name.lower() == "planner":
        return get_all_events()
    db = get_connection()
    cursor = db.cursor(buffered=True)
    pattern = "%" + owner_name.lower() + "%"
    cursor.execute(
        "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
        "FROM events e "
        "LEFT JOIN categories c ON e.category_id = c.id "
        "WHERE LOWER(e.created_by) LIKE %s "
        "ORDER BY e.event_date, e.event_time",
        (pattern,)
    )
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return rows


def get_all_events():
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute(
        "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
        "FROM events e "
        "LEFT JOIN categories c ON e.category_id = c.id "
        "ORDER BY e.event_date, e.event_time"
    )
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return rows


def search_events(keyword):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    pattern = "%" + keyword + "%"
    cursor.execute(
        "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
        "FROM events e "
        "LEFT JOIN categories c ON e.category_id = c.id "
        "WHERE LOWER(e.title) LIKE %s OR LOWER(e.details) LIKE %s "
        "ORDER BY e.event_date, e.event_time",
        (pattern, pattern)
    )
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return rows


def get_event_title(event_id):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT title FROM events WHERE id = %s", (event_id,))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row[0] if row else None


def get_events_on_dates(date1, date2):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute(
        "SELECT id, title, event_date, event_time, status, created_by "
        "FROM events "
        "WHERE event_date = %s OR event_date = %s",
        (date1, date2)
    )
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return rows


def mark_event_done(event_id):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("UPDATE events SET status = 'done' WHERE id = %s", (event_id,))
    db.commit()
    count = cursor.rowcount
    cursor.close()
    db.close()
    return count


def delete_event(event_id):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("DELETE FROM attendees WHERE event_id = %s", (event_id,))
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    db.commit()
    count = cursor.rowcount
    cursor.close()
    db.close()
    return count


def add_attendee(event_id, email):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("INSERT INTO attendees (event_id, email) VALUES (%s, %s)", (event_id, email))
    db.commit()
    cursor.close()
    db.close()


def get_attendee_emails(event_id):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT email FROM attendees WHERE event_id = %s", (event_id,))
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return [row[0] for row in rows]


def get_all_owners():
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT DISTINCT created_by FROM events WHERE created_by IS NOT NULL AND created_by != '' ORDER BY created_by")
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return [row[0] for row in rows]


def get_events_by_owner(owner_name):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    pattern = "%" + owner_name.lower() + "%"
    cursor.execute(
        "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
        "FROM events e "
        "LEFT JOIN categories c ON e.category_id = c.id "
        "WHERE LOWER(e.created_by) LIKE %s "
        "ORDER BY e.event_date, e.event_time",
        (pattern,)
    )
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return rows


def get_busy_days_by_owner(year_month_prefix, owner_name):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    pattern = "%" + owner_name.lower() + "%"
    cursor.execute(
        "SELECT event_date FROM events WHERE event_date LIKE %s AND LOWER(created_by) LIKE %s",
        (year_month_prefix + "-%", pattern)
    )
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return [int(row[0][8:10]) for row in rows]


def get_busy_days(year_month_prefix):
    db = get_connection()
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT event_date FROM events WHERE event_date LIKE %s", (year_month_prefix + "-%",))
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return [int(row[0][8:10]) for row in rows]
