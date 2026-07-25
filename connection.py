import os
import sys
import mysql.connector
DB_HOST     = "mysql-321c1333-alustudent-a6c3.c.aivencloud.com"
DB_PORT     = 21755
DB_USER     = "avnadmin"
DB_PASSWORD = "AVNS_bI1GHgU3lywk6XbCIWa"
DB_NAME     = "defaultdb"
try:
    connection = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connection_timeout=5
    )
    cursor = connection.cursor(buffered=True)
except Exception as e:
    print("\n  [Database Error] Could not connect to the cloud database.")
    print("  Please check your internet connection and try again.\n")
    sys.exit(1)

def setup():                  #Read schema.sql and create the tables if they don't exist.
    folder = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(folder, "databse.sql")
    schema_file = open(schema_path)
    full_sql = schema_file.read()
    schema_file.close()
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
    connection.commit()
    cursor.execute("SELECT COUNT(*) FROM categories")
    count = cursor.fetchone()[0]
    if count == 0:
        default_categories = ["Classes", "Assignments", "Personal", "Others"]
        for category_name in default_categories:
            cursor.execute(
                "INSERT INTO categories (name) VALUES (%s)",
                (category_name,)
            )
        connection.commit()

    cursor.execute("SELECT COUNT(*) FROM members")
    m_count = cursor.fetchone()[0]
    if m_count == 0:
        default_members = ["Kingsley", "Felix", "Vanessa", "Rita", "Gabriel"]
        for member_name in default_members:
            cursor.execute(
                "INSERT INTO members (name) VALUES (%s)",
                (member_name,)
            )
        connection.commit()


# Member operations

def get_all_members():
    cursor.execute("SELECT id, name FROM members ORDER BY id")
    return cursor.fetchall()


def add_member(name):
    try:
        cursor.execute("INSERT INTO members (name) VALUES (%s)", (name,))
        connection.commit()
    except:
        pass


#  Category operations 

def get_all_categories(): #Return all categories as a list of (id, name) pairs.
    cursor.execute("SELECT id, name FROM categories ORDER BY id")
    return cursor.fetchall()


def get_category_id(name): #Return the id of a category by its name, or None if not found.
    """Return the id of a category by its name, or None if not found."""
    cursor.execute("SELECT id FROM categories WHERE name = %s", (name,))
    row = cursor.fetchone()
    if row is None:
        return None
    return row[0]


def add_category(name):
    """Add a new category."""
    cursor.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
    connection.commit()


# Event operations 

def add_event(title, event_date, event_time, details, category_id, created_by="Planner"): #Create a new event. Returns the new event's id.
    try:
        cursor.execute(
            "INSERT INTO events (title, event_date, event_time, details, status, category_id, created_by) "
            "VALUES (%s, %s, %s, %s, 'pending', %s, %s)",
            (title, event_date, event_time, details, category_id, created_by)
        )
        connection.commit()
    except Exception:
        connection.rollback()
        cursor.execute(
            "INSERT INTO events (title, event_date, event_time, details, status, category_id, created_by) "
            "VALUES (%s, %s, %s, %s, 'pending', %s, %s)",
            (title, event_date, event_time, details, category_id, created_by)
        )
        connection.commit()
    return cursor.lastrowid


def get_user_events(owner_name):
    if not owner_name or owner_name.lower() == "planner":
        return get_all_events()
    pattern = "%" + owner_name.lower() + "%"
    cursor.execute(
        "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
        "FROM events e "
        "LEFT JOIN categories c ON e.category_id = c.id "
        "WHERE LOWER(e.created_by) LIKE %s "
        "ORDER BY e.event_date, e.event_time",
        (pattern,)
    )
    return cursor.fetchall()


def get_all_events():
    """Return all events joined with their category name."""
    cursor.execute(
        "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
        "FROM events e "
        "LEFT JOIN categories c ON e.category_id = c.id "
        "ORDER BY e.event_date, e.event_time"
    )
    return cursor.fetchall()


def search_events(keyword):
    """Search events by title or details using a keyword."""
    pattern = "%" + keyword + "%"
    cursor.execute(
        "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
        "FROM events e "
        "LEFT JOIN categories c ON e.category_id = c.id "
        "WHERE LOWER(e.title) LIKE %s OR LOWER(e.details) LIKE %s "
        "ORDER BY e.event_date, e.event_time",
        (pattern, pattern)
    )
    return cursor.fetchall()


def get_event_title(event_id):
    """Return the title of a single event, or None if not found."""
    cursor.execute("SELECT title FROM events WHERE id = %s", (event_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return row[0]


def get_events_on_dates(date1, date2):
    """Return events happening on either of two dates (for reminders)."""
    cursor.execute(
        "SELECT id, title, event_date, event_time, status "
        "FROM events "
        "WHERE event_date = %s OR event_date = %s",
        (date1, date2)
    )
    return cursor.fetchall()


def mark_event_done(event_id):
    """Mark an event as done."""
    cursor.execute("UPDATE events SET status = 'done' WHERE id = %s", (event_id,))
    connection.commit()
    return cursor.rowcount


def delete_event(event_id):
    """Delete an event and its attendees."""
    cursor.execute("DELETE FROM attendees WHERE event_id = %s", (event_id,))
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    connection.commit()
    return cursor.rowcount



def add_attendee(event_id, email): #Add a person to be reminded about an event.
    cursor.execute("INSERT INTO attendees (event_id, email) VALUES (%s, %s)", (event_id, email))
    connection.commit()


def get_attendee_emails(event_id): #Return a list of email addresses for an event.
    cursor.execute("SELECT email FROM attendees WHERE event_id = %s", (event_id,))
    email_list = []
    for row in cursor.fetchall():
        email_list.append(row[0])
    return email_list



def get_all_owners():
    cursor.execute("SELECT DISTINCT created_by FROM events WHERE created_by IS NOT NULL AND created_by != '' ORDER BY created_by")
    owners = []
    for row in cursor.fetchall():
        owners.append(row[0])
    return owners


def get_events_by_owner(owner_name):
    pattern = "%" + owner_name.lower() + "%"
    cursor.execute(
        "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
        "FROM events e "
        "LEFT JOIN categories c ON e.category_id = c.id "
        "WHERE LOWER(e.created_by) LIKE %s "
        "ORDER BY e.event_date, e.event_time",
        (pattern,)
    )
    return cursor.fetchall()


def get_busy_days_by_owner(year_month_prefix, owner_name):
    pattern = "%" + owner_name.lower() + "%"
    cursor.execute(
        "SELECT event_date FROM events WHERE event_date LIKE %s AND LOWER(created_by) LIKE %s",
        (year_month_prefix + "-%", pattern)
    )
    day_numbers = []
    for row in cursor.fetchall():
        day_numbers.append(int(row[0][8:10]))
    return day_numbers


def get_busy_days(year_month_prefix):
    """Return a list of day numbers that have events in a given month.
    year_month_prefix should be like '2026-07'."""
    cursor.execute(
        "SELECT event_date FROM events WHERE event_date LIKE %s",
        (year_month_prefix + "-%",)
    )
    day_numbers = []
    for row in cursor.fetchall():
        # event_date looks like '2026-07-25', we want just the day (25)
        day_numbers.append(int(row[0][8:10]))
    return day_numbers
