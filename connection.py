import os
import mysql.connector
DB_HOST     = "mysql-321c1333-alustudent-a6c3.c.aivencloud.com"
DB_PORT     = 21755
DB_USER     = "avnadmin"
DB_PASSWORD = "AVNS_bI1GHgU3lywk6XbCIWa"
DB_NAME     = "defaultdb"
connection = mysql.connector.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = connection.cursor(buffered=True)

def setup():                  #Read schema.sql and create the tables if they don't exist.
    folder = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(folder, "schema.sql")
    schema_file = open(schema_path)
    full_sql = schema_file.read()
    schema_file.close()
    for statement in full_sql.split(";"):
        cleaned = statement.strip()
        if cleaned != "" and cleaned.startswith("CREATE"):
            cursor.execute(cleaned)
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

def add_event(title, event_date, event_time, details, category_id): #Create a new event. Returns the new event's id.
    cursor.execute(
        "INSERT INTO events (title, event_date, event_time, details, status, category_id) "
        "VALUES (%s, %s, %s, %s, 'pending', %s)",
        (title, event_date, event_time, details, category_id)
    )
    connection.commit()
    return cursor.lastrowid


def get_all_events():
    """Return all events joined with their category name."""
    cursor.execute(
        "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name "
        "FROM events e "
        "LEFT JOIN categories c ON e.category_id = c.id "
        "ORDER BY e.event_date, e.event_time"
    )
    return cursor.fetchall()


def search_events(keyword):
    """Search events by title or details using a keyword."""
    pattern = "%" + keyword + "%"
    cursor.execute(
        "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name "
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
