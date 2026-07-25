import os
import sys
import mysql.connector

DB_HOST     = "mysql-321c1333-alustudent-a6c3.c.aivencloud.com"
DB_PORT     = 21755
DB_USER     = "avnadmin"
DB_PASSWORD = "AVNS_bI1GHgU3lywk6XbCIWa"
DB_NAME     = "defaultdb"


class DatabaseManager:
    """Encapsulates MySQL database connections and CRUD queries for TaskFlow."""
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connection_timeout=5
            )
            self.cursor = self.connection.cursor(buffered=True)
        except Exception as e:
            print("\n  [Database Error] Could not connect to the cloud database.")
            print("  Please check your internet connection and try again.\n")
            sys.exit(1)

    def setup(self):
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
                self.cursor.execute(clean_stmt)
        try:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS members (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50) UNIQUE)")
        except:
            pass
        try:
            self.cursor.execute("ALTER TABLE events MODIFY COLUMN event_time VARCHAR(20)")
        except:
            pass
        try:
            self.cursor.execute("ALTER TABLE events ADD COLUMN created_by VARCHAR(50) DEFAULT 'Planner'")
        except:
            pass
        self.connection.commit()

        self.cursor.execute("SELECT COUNT(*) FROM categories")
        count = self.cursor.fetchone()[0]
        if count == 0:
            default_categories = ["Classes", "Assignments", "Personal", "Others"]
            for category_name in default_categories:
                self.cursor.execute(
                    "INSERT INTO categories (name) VALUES (%s)",
                    (category_name,)
                )
            self.connection.commit()

        self.cursor.execute("SELECT COUNT(*) FROM members")
        m_count = self.cursor.fetchone()[0]
        if m_count == 0:
            default_members = ["Kingsley", "Felix", "Vanessa", "Rita", "Gabriel"]
            for member_name in default_members:
                self.cursor.execute(
                    "INSERT INTO members (name) VALUES (%s)",
                    (member_name,)
                )
            self.connection.commit()

    def get_all_members(self):
        self.cursor.execute("SELECT id, name FROM members ORDER BY id")
        return self.cursor.fetchall()

    def add_member(self, name):
        try:
            self.cursor.execute("INSERT INTO members (name) VALUES (%s)", (name,))
            self.connection.commit()
        except:
            pass

    def get_all_categories(self):
        self.cursor.execute("SELECT id, name FROM categories ORDER BY id")
        return self.cursor.fetchall()

    def get_category_id(self, name):
        self.cursor.execute("SELECT id FROM categories WHERE name = %s", (name,))
        row = self.cursor.fetchone()
        if row is None:
            return None
        return row[0]

    def add_category(self, name):
        self.cursor.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
        self.connection.commit()

    def add_event(self, title, event_date, event_time, details, category_id, created_by="Planner"):
        try:
            self.cursor.execute(
                "INSERT INTO events (title, event_date, event_time, details, status, category_id, created_by) "
                "VALUES (%s, %s, %s, %s, 'pending', %s, %s)",
                (title, event_date, event_time, details, category_id, created_by)
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            self.cursor.execute(
                "INSERT INTO events (title, event_date, event_time, details, status, category_id, created_by) "
                "VALUES (%s, %s, %s, %s, 'pending', %s, %s)",
                (title, event_date, event_time, details, category_id, created_by)
            )
            self.connection.commit()
        return self.cursor.lastrowid

    def get_user_events(self, owner_name):
        if not owner_name or owner_name.lower() == "planner":
            return self.get_all_events()
        pattern = "%" + owner_name.lower() + "%"
        self.cursor.execute(
            "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
            "FROM events e "
            "LEFT JOIN categories c ON e.category_id = c.id "
            "WHERE LOWER(e.created_by) LIKE %s "
            "ORDER BY e.event_date, e.event_time",
            (pattern,)
        )
        return self.cursor.fetchall()

    def get_all_events(self):
        self.cursor.execute(
            "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
            "FROM events e "
            "LEFT JOIN categories c ON e.category_id = c.id "
            "ORDER BY e.event_date, e.event_time"
        )
        return self.cursor.fetchall()

    def search_events(self, keyword):
        pattern = "%" + keyword + "%"
        self.cursor.execute(
            "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
            "FROM events e "
            "LEFT JOIN categories c ON e.category_id = c.id "
            "WHERE LOWER(e.title) LIKE %s OR LOWER(e.details) LIKE %s "
            "ORDER BY e.event_date, e.event_time",
            (pattern, pattern)
        )
        return self.cursor.fetchall()

    def get_event_title(self, event_id):
        self.cursor.execute("SELECT title FROM events WHERE id = %s", (event_id,))
        row = self.cursor.fetchone()
        if row is None:
            return None
        return row[0]

    def get_events_on_dates(self, date1, date2):
        self.cursor.execute(
            "SELECT id, title, event_date, event_time, status "
            "FROM events "
            "WHERE event_date = %s OR event_date = %s",
            (date1, date2)
        )
        return self.cursor.fetchall()

    def mark_event_done(self, event_id):
        self.cursor.execute("UPDATE events SET status = 'done' WHERE id = %s", (event_id,))
        self.connection.commit()
        return self.cursor.rowcount

    def delete_event(self, event_id):
        self.cursor.execute("DELETE FROM attendees WHERE event_id = %s", (event_id,))
        self.cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
        self.connection.commit()
        return self.cursor.rowcount

    def add_attendee(self, event_id, email):
        self.cursor.execute("INSERT INTO attendees (event_id, email) VALUES (%s, %s)", (event_id, email))
        self.connection.commit()

    def get_attendee_emails(self, event_id):
        self.cursor.execute("SELECT email FROM attendees WHERE event_id = %s", (event_id,))
        email_list = []
        for row in self.cursor.fetchall():
            email_list.append(row[0])
        return email_list

    def get_all_owners(self):
        self.cursor.execute("SELECT DISTINCT created_by FROM events WHERE created_by IS NOT NULL AND created_by != '' ORDER BY created_by")
        owners = []
        for row in self.cursor.fetchall():
            owners.append(row[0])
        return owners

    def get_events_by_owner(self, owner_name):
        pattern = "%" + owner_name.lower() + "%"
        self.cursor.execute(
            "SELECT e.id, e.title, e.event_date, e.event_time, e.details, e.status, c.name, e.created_by "
            "FROM events e "
            "LEFT JOIN categories c ON e.category_id = c.id "
            "WHERE LOWER(e.created_by) LIKE %s "
            "ORDER BY e.event_date, e.event_time",
            (pattern,)
        )
        return self.cursor.fetchall()

    def get_busy_days_by_owner(self, year_month_prefix, owner_name):
        pattern = "%" + owner_name.lower() + "%"
        self.cursor.execute(
            "SELECT event_date FROM events WHERE event_date LIKE %s AND LOWER(created_by) LIKE %s",
            (year_month_prefix + "-%", pattern)
        )
        day_numbers = []
        for row in self.cursor.fetchall():
            day_numbers.append(int(row[0][8:10]))
        return day_numbers

    def get_busy_days(self, year_month_prefix):
        self.cursor.execute(
            "SELECT event_date FROM events WHERE event_date LIKE %s",
            (year_month_prefix + "-%",)
        )
        day_numbers = []
        for row in self.cursor.fetchall():
            day_numbers.append(int(row[0][8:10]))
        return day_numbers


# Instance of DatabaseManager for import access
db_instance = DatabaseManager()

setup                 = db_instance.setup
get_all_members       = db_instance.get_all_members
add_member            = db_instance.add_member
get_all_categories    = db_instance.get_all_categories
get_category_id       = db_instance.get_category_id
add_category          = db_instance.add_category
add_event             = db_instance.add_event
get_user_events       = db_instance.get_user_events
get_all_events        = db_instance.get_all_events
search_events         = db_instance.search_events
get_event_title       = db_instance.get_event_title
get_events_on_dates   = db_instance.get_events_on_dates
mark_event_done       = db_instance.mark_event_done
delete_event          = db_instance.delete_event
add_attendee          = db_instance.add_attendee
get_attendee_emails   = db_instance.get_attendee_emails
get_all_owners        = db_instance.get_all_owners
get_events_by_owner   = db_instance.get_events_by_owner
get_busy_days_by_owner = db_instance.get_busy_days_by_owner
get_busy_days         = db_instance.get_busy_days
