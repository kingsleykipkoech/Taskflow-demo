import sys
import os
import calendar
import smtplib
import urllib.request
from datetime import date, datetime, timedelta
import connection as db


# ==============================================================================
# MODULE 1: REMINDERS & EMAIL NOTIFICATIONS (Felix)
# ==============================================================================

SENDER_EMAIL        = ""
SENDER_APP_PASSWORD = ""


class ReminderService:
    """Handles desktop notifications and email sending for TaskFlow."""
    @staticmethod
    def notify_desktop(title, message):
        if sys.platform != "win32":
            os.system(f'notify-send "{title}" "{message}"')

    @staticmethod
    def send_email(to_email, subject, body):
        load_email_config()
        if not SENDER_EMAIL or not SENDER_APP_PASSWORD:
            return
        try:
            full_message = f"From: {SENDER_EMAIL}\nTo: {to_email}\nSubject: {subject}\n\n{body}"
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, full_message)
            server.quit()
        except:
            pass


def load_email_config():
    global SENDER_EMAIL, SENDER_APP_PASSWORD
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".email_config")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    SENDER_EMAIL = lines[0].strip()
                    SENDER_APP_PASSWORD = lines[1].strip()
        except:
            pass


def configure_email():
    print("")
    print("  +-----------------------------------------+")
    print("  |       Configure Email Reminders         |")
    print("  +-----------------------------------------+")
    print("")
    email_input = input("  Enter your Gmail address (or Enter to disable): ").strip()
    if email_input == "":
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".email_config")
        if os.path.exists(config_path):
            os.remove(config_path)
        global SENDER_EMAIL, SENDER_APP_PASSWORD
        SENDER_EMAIL = ""
        SENDER_APP_PASSWORD = ""
        print("  Email reminders disabled.")
        return

    password_input = input("  Enter your App Password: ").strip()
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".email_config")
    with open(config_path, "w") as f:
        f.write(f"{email_input}\n{password_input}\n")

    load_email_config()
    print("  Email reminders configured successfully!")


def check_email_setup_on_startup():
    load_email_config()
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".email_config")
    if SENDER_EMAIL == "" and not os.path.exists(config_path):
        print("")
        print("  +-----------------------------------------+")
        print("  |   First-Time Setup: Email Reminders    |")
        print("  +-----------------------------------------+")
        answer = input("  Would you like to set up email reminders now? (y/n): ").strip().lower()
        if answer == "y" or answer == "yes":
            configure_email()
        else:
            with open(config_path, "w") as f:
                f.write("disabled\n")


def send_email(to_email, subject, body):
    ReminderService.send_email(to_email, subject, body)


def check_upcoming():
    today = str(date.today())
    tomorrow = str(date.today() + timedelta(days=1))
    current_time = datetime.now().strftime("%H:%M")
    events = db.get_events_on_dates(today, tomorrow)
    upcoming = []
    for event in events:
        event_date = event[2]
        event_time = format_time(event[3])
        status = event[4]

        if status == "done":
            continue
        if event_date == today and event_time != "ALL DAY" and event_time < current_time:
            continue
        upcoming.append(event)

    if len(upcoming) == 0:
        return

    print("")
    print("  -----------------------------------------")
    print("             Upcoming Reminders!           ")
    print("  -----------------------------------------")
    for event in upcoming:
        event_id = event[0]
        title = event[1]
        event_date = event[2]
        event_time = format_time(event[3])
        when = "TODAY" if event_date == today else "TOMORROW"
        print(f"   • {title} ({when} at {event_time})")

        message = f"{title} is happening {when} at {event_time}"
        ReminderService.notify_desktop("TaskFlow Reminder", message)

        owner_name = event[7] if len(event) > 7 and event[7] else "Planner"
        attendee_emails = db.get_attendee_emails(event_id)
        for one_email in attendee_emails:
            ReminderService.send_email(
                one_email,
                f"TaskFlow Reminder: {owner_name}'s Event '{title}'",
                f"Hi there!\n\nThis is an automated reminder from TaskFlow.\n\nYour teammate {owner_name} has an upcoming event:\nEvent: {title}\nWhen: {when}\nTime: {event_time}\n\nPlease reach out and remind {owner_name} so they don't forget\n\nBest regards"
            )
    print("  -----------------------------------------")


def send_reminders():
    check_upcoming()


# ==============================================================================
# MODULE 2: USER IDENTITY & ROLE AUTHENTICATION (Lilian)
# ==============================================================================

CURRENT_USER = "Planner"


def select_user_identity():
    global CURRENT_USER
    while True:
        all_members = db.get_all_members()
        print("")
        print("  +-----------------------------+")
        print("  |      Who are you?           |")
        print("  +-----------------------------+")
        number = 1
        for member in all_members:
            print(f"   {number}) {member[1]}")
            number += 1
        print(f"   {number}) + Edit / Manage Users")
        print("  -----------------------------")
        print("")
        choice = input("  Pick your name number: ").strip()
        while not choice.isdigit() or int(choice) < 1 or int(choice) > len(all_members) + 1:
            choice = input("  Invalid. Pick your name number: ").strip()

        if int(choice) == len(all_members) + 1:
            print("")
            print("  -----------------------------")
            print("  Edit / Manage Users Options:")
            print("  -----------------------------")
            print("   1) Add a new user")
            print("   2) Delete an existing user")
            print("  -----------------------------")
            sub_choice = input("  Pick 1 or 2: ").strip()

            if sub_choice == "1":
                new_name = input("  Enter new user name: ").strip()
                if new_name != "":
                    db.add_member(new_name)
                    CURRENT_USER = new_name
                    print(f"\n  Logged in as: {CURRENT_USER}")
                    break
                else:
                    CURRENT_USER = "Planner"
                    print(f"\n  Logged in as: {CURRENT_USER}")
                    break
            elif sub_choice == "2":
                if len(all_members) == 0:
                    print("  No users available to delete.")
                    continue
                print("")
                print("  Pick user number to delete:")
                del_num = 1
                for member in all_members:
                    print(f"   {del_num}) {member[1]}")
                    del_num += 1
                del_choice = input("  User number to delete: ").strip()
                if del_choice.isdigit() and 1 <= int(del_choice) <= len(all_members):
                    target_name = all_members[int(del_choice) - 1][1]
                    db.delete_member(target_name)
                    print(f"  User '{target_name}' deleted successfully.")
                else:
                    print("  Invalid selection.")
                continue
            else:
                print("  Invalid choice.")
                continue
        else:
            CURRENT_USER = all_members[int(choice) - 1][1]
            print(f"\n  Logged in as: {CURRENT_USER}")
            break


def pick_role():
    print("")
    print("  +-----------------------------------------+")
    print("  |                                         |")
    print("  |      Welcome to TaskFlow Planner        |")
    print("  |                                         |")
    print("  +-----------------------------------------+")
    print("")
    print("  Choose your role:")
    print("  " + "-" * 41)
    print("  1) Planner  -  full access")
    print("  2) Viewer   -  view and search only")
    print("  " + "-" * 41)
    print("")
    choice = input("  Enter 1 or 2: ").strip()
    while choice != "1" and choice != "2":
        choice = input("  Please enter 1 or 2: ").strip()
    if choice == "1":
        print("")
        print("  Logged in as Planner.")
        return "planner"
    else:
        print("")
        print("  Logged in as Viewer.")
        return "viewer"


# ==============================================================================
# MODULE 3: EVENT CREATION & CATEGORY MANAGEMENT (VANESSA)
# ==============================================================================

class Event:
    """Represents an Event object in TaskFlow (OOP Data Model)."""
    def __init__(self, event_id, title, event_date, event_time, details, status, category_name, owner_name="Planner"):
        self.id = event_id
        self.title = title
        self.event_date = event_date
        self.event_time = event_time
        self.details = details
        self.status = status
        self.category_name = category_name
        self.owner_name = owner_name

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        owner_name = row[7] if len(row) > 7 and row[7] else "Planner"
        return cls(row[0], row[1], row[2], row[3], row[4], row[5], row[6], owner_name)


def choose_category():
    all_categories = db.get_all_categories()
    print("")
    print("  Categories:")
    print("  -----------------------------")
    number = 1
    for category in all_categories:
        category_name = category[1]
        print(f"   {number}) {category_name}")
        number = number + 1
    print("  -----------------------------")
    print("")
    choice = input("  Pick a category number: ").strip()
    while not choice.isdigit() or int(choice) < 1 or int(choice) > len(all_categories):
        choice = input("  Invalid. Pick a category number: ").strip()
    chosen_category = all_categories[int(choice) - 1]
    return chosen_category[0]


def add_event():
    print("")
    print("  +-----------------------------+")
    print("  |       Add New Event          |")
    print("  +-----------------------------+")
    print("")
    title = input("  Event title (or Enter to cancel): ").strip()
    if title == "" or title.lower() == "cancel":
        print("  Event creation cancelled.")
        return
    date_input = input("  Date (YYYY-MM-DD): ").strip()
    while not is_valid_date(date_input):
        date_input = input("  Invalid. Date (YYYY-MM-DD): ").strip()
    time_input = input("  Time (HH:MM or leave empty for All Day): ").strip()
    while not is_valid_time(time_input):
        time_input = input("  Invalid. Time (HH:MM or you can leave empty for All Day): ").strip()
    time_input = format_time(time_input)
    details = input("  Details (optional): ").strip()
    category_id = choose_category()

    new_event_id = db.add_event(title, date_input, time_input, details, category_id, CURRENT_USER)
    print("")
    print("  Event added successfully!")
    print("")
    emails_input = input("  Add a person/people to remind you: ").strip()
    if emails_input != "":
        for one_email in emails_input.split():
            db.add_attendee(new_event_id, one_email)
        print("  Emails added.")


def manage_categories():
    print("")
    all_categories = db.get_all_categories()
    print("  Current Categories:")
    print("  -----------------------------")
    for category in all_categories:
        print(f"   - {category[1]}")
    print("  -----------------------------")
    print("")
    name = input("  Enter new category name (or Enter to go back): ").strip()
    if name == "":
        return
    db.add_category(name)
    print(f"  Category '{name}' added!")


# ==============================================================================
# MODULE 4: DATA VALIDATION & STATUS ENGINE (Gabriel)
# ==============================================================================

def is_valid_date(text):
    parts = text.split("-")
    if len(parts) != 3:
        return False
    year_part = parts[0]
    month_part = parts[1]
    day_part = parts[2]
    if not year_part.isdigit() or not month_part.isdigit() or not day_part.isdigit():
        return False
    if len(year_part) != 4:
        return False
    if int(month_part) < 1 or int(month_part) > 12:
        return False
    if int(day_part) < 1 or int(day_part) > 31:
        return False
    return True


def format_time(text):
    cleaned = text.strip().lower()
    if cleaned in ["all", "all day", "allday", "all-day", ""]:
        return "ALL DAY"
    parts = cleaned.split(":")
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        return "%02d:%02d" % (int(parts[0]), int(parts[1]))
    return text


def is_valid_time(text):
    cleaned = text.strip().lower()
    if cleaned in ["all", "all day", "allday", "all-day", ""]:
        return True
    parts = cleaned.split(":")
    if len(parts) != 2:
        return False
    hour_part = parts[0]
    minute_part = parts[1]
    if not hour_part.isdigit() or not minute_part.isdigit():
        return False
    if int(hour_part) < 0 or int(hour_part) > 23:
        return False
    if int(minute_part) < 0 or int(minute_part) > 59:
        return False
    return True


def get_event_status(saved_status, event_date, today):
    if saved_status == "done":
        return "done"
    if event_date < today:
        return "due"
    if event_date == today:
        return "ongoing"
    return "pending"


# ==============================================================================
# MODULE 5: CALENDAR DISPLAY & TABLE RENDERER (Rita)
# ==============================================================================

def show_event_list():
    raw_events = db.get_user_events(CURRENT_USER)
    if len(raw_events) == 0:
        print(f"  No events yet for {CURRENT_USER}.")
        return

    today = str(date.today())
    print("  -------------------------------------------------------------------------")
    print("  ID | Title | Date | Time | Category | Status | Owner")
    print("  -------------------------------------------------------------------------")
    for row in raw_events:
        ev = Event.from_row(row)
        formatted_time = format_time(ev.event_time)
        current_status = get_event_status(ev.status, ev.event_date, today).upper()
        print(f"  #{ev.id} | {ev.title} | {ev.event_date} {formatted_time} | {ev.category_name} | {current_status} | Owner: {ev.owner_name}")
        if ev.details:
            print(f"      details: {ev.details}")
    print("  -------------------------------------------------------------------------")


def show_calendar():
    today = date.today()
    month_title = f"{calendar.month_name[today.month]} {today.year}"
    print("  +-----------------------------------+")
    print(f"  |  {month_title.center(31)}  |")
    print("  +-----------------------------------+")
    print("  |   Mo  Tu  We  Th  Fr  Sa  Su      |")
    print("  |  -------------------------------  |")

    for week in calendar.monthcalendar(today.year, today.month):
        line = "  |  "
        for day in week:
            if day == 0:
                cell = "    "
            elif day == today.day:
                cell = f" [{day}]" if day < 10 else f"[{day}]"
            else:
                cell = f"   {day}" if day < 10 else f"  {day}"
            line += cell
        line = line.ljust(37) + "|"
        print(line)

    print("  +-----------------------------------+")


def view_all():
    print("")
    show_calendar()
    print("")
    show_event_list()
    print("")


def view_member_calendar():
    print("")
    owners = db.get_all_owners()
    if len(owners) == 0:
        print("  No members have added events yet.")
        return

    print("  -----------------------------")
    print("  Users with Calendars:")
    print("  -----------------------------")
    number = 1
    for owner_name in owners:
        print(f"   {number}) {owner_name}")
        number += 1
    print("  -----------------------------")
    print("")

    choice = input("  Pick a user number (or Enter for all): ").strip()
    if choice == "":
        view_all()
        return

    if choice.isdigit() and 1 <= int(choice) <= len(owners):
        member_name = owners[int(choice) - 1]
    else:
        member_name = choice

    raw_events = db.get_events_by_owner(member_name)
    if len(raw_events) == 0:
        print(f"  No events found for owner '{member_name}'.")
        return

    today = date.today()
    month_title = f"{calendar.month_name[today.month]} {today.year} - {member_name.capitalize()}"
    print("  +-----------------------------------+")
    print(f"  |  {month_title.center(31)}  |")
    print("  +-----------------------------------+")
    print("  |   Mo  Tu  We  Th  Fr  Sa  Su      |")
    print("  |  -------------------------------  |")

    for week in calendar.monthcalendar(today.year, today.month):
        line = "  |  "
        for day in week:
            if day == 0:
                cell = "    "
            elif day == today.day:
                cell = f" [{day}]" if day < 10 else f"[{day}]"
            else:
                cell = f"   {day}" if day < 10 else f"  {day}"
            line += cell
        line = line.ljust(37) + "|"
        print(line)

    print("  +-----------------------------------+")
    print("")

    today_str = str(date.today())
    print("  -------------------------------------------------------------------------")
    print("  ID | Title | Date | Time | Category | Status | Owner")
    print("  -------------------------------------------------------------------------")
    for row in raw_events:
        ev = Event.from_row(row)
        formatted_time = format_time(ev.event_time)
        current_status = get_event_status(ev.status, ev.event_date, today_str).upper()
        print(f"  #{ev.id} | {ev.title} | {ev.event_date} {formatted_time} | {ev.category_name} | {current_status} | Owner: {ev.owner_name}")
        if ev.details:
            print(f"      details: {ev.details}")
    print("  -------------------------------------------------------------------------")
    print("")


# ==============================================================================
# MODULE 6: SEARCH, EDIT, DELETE & ICS IMPORTS (Kingsley)
# ==============================================================================

def search_events():
    print("")
    keyword = input("  Search keyword: ").strip().lower()
    raw_results = db.search_events(keyword)
    if len(raw_results) == 0:
        print("  No matching events.")
        return

    today = str(date.today())
    print("")
    print("  Search results:")
    print("  -------------------------------------------------------------------------")
    for row in raw_results:
        ev = Event.from_row(row)
        formatted_time = format_time(ev.event_time)
        current_status = get_event_status(ev.status, ev.event_date, today).upper()
        print(f"  #{ev.id} | {ev.title} | {ev.event_date} {formatted_time} | {ev.category_name} | {current_status} | Owner: {ev.owner_name}")
    print("  -------------------------------------------------------------------------")
    print("")


def edit_event():
    print("")
    show_event_list()
    print("")
    event_id = input("  Enter event id to edit: ").strip()
    if not event_id.isdigit():
        print("  Invalid id.")
        return
    title = db.get_event_title(event_id)
    if title is None:
        print("  No event with that id.")
        return

    print("")
    print(f"  Editing: {title}")
    print("  -----------------------------------")
    print("  1) Mark as done")
    print("  2) Add participants (people to remind you)")
    print("  -----------------------------------")
    choice = input("  Pick 1 or 2: ").strip()

    if choice == "1":
        db.mark_event_done(event_id)
        print("  Marked done.")
    elif choice == "2":
        emails_input = input("  Enter participant emails (space separated): ").strip()
        if emails_input == "":
            print("  No emails entered.")
            return
        for one_email in emails_input.split():
            db.add_attendee(event_id, one_email)
        print(f"  Participants added to: {title}")
    else:
        print("  Nothing changed.")


def delete_event():
    print("")
    show_event_list()
    print("")
    event_id = input("  Enter event id to delete: ").strip()
    if not event_id.isdigit():
        print("  Invalid id.")
        return
    deleted_count = db.delete_event(event_id)
    if deleted_count == 0:
        print("  No event with that id.")
    else:
        print("  Deleted.")


def import_ics():
    print("")
    source = input("  Enter .ics absolute filename or web URL link: ").strip()
    if source == "":
        return

    all_lines = []
    if source.startswith("http://") or source.startswith("https://"):
        try:
            req = urllib.request.Request(source, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
                all_lines = content.splitlines()
        except Exception:
            print("  Could not download calendar from web URL link.")
            return
    else:
        if not os.path.exists(source):
            print("  File not found.")
            return
        try:
            with open(source, encoding='utf-8') as ics_file:
                all_lines = ics_file.readlines()
        except Exception:
            print("  Could not read file.")
            return

    others_category_id = db.get_category_id("Others")
    title = ""
    event_date = ""
    event_time = "00:00"
    imported_count = 0

    for raw_line in all_lines:
        line = raw_line.strip()

        if line.startswith("SUMMARY:"):
            title = line[8:]

        elif line.startswith("DTSTART"):
            value = line.split(":")[-1]
            date_part = value[0:8]
            if len(date_part) == 8 and date_part.isdigit():
                event_date = date_part[0:4] + "-" + date_part[4:6] + "-" + date_part[6:8]
            if "T" in value:
                time_part = value.split("T")[1]
                if len(time_part) >= 4 and time_part[0:4].isdigit():
                    event_time = time_part[0:2] + ":" + time_part[2:4]

        elif line.startswith("END:VEVENT"):
            if title != "" and event_date != "":
                db.add_event(title, event_date, event_time, "Imported from calendar", others_category_id)
                imported_count = imported_count + 1
            title = ""
            event_date = ""
            event_time = "00:00"

    print(f"  Imported {imported_count} event(s).")


# ==============================================================================
# CLI MENUS & APPLICATION ENTRY POINT (Felix)
# ==============================================================================

def planner_menu():
    while True:
        print("")
        print("  +-----------------------------------------+")
        print("  |      TaskFlow Planner  [Planner]        |")
        print("  +-----------------------------------------+")
        print("  |                                         |")
        print("  |  1) Add event                           |")
        print("  |  2) View all events and calendar        |")
        print("  |  3) View calendar by user               |")
        print("  |  4) Search events                       |")
        print("  |  5) Edit event                          |")
        print("  |  6) Delete event                        |")
        print("  |  7) Import events from .ics file        |")
        print("  |  8) Manage categories                   |")
        print("  |  9) Configure email reminders           |")
        print("  |  0) Exit                                |")
        print("  |                                         |")
        print("  +-----------------------------------------+")
        print("")
        choice = input("  Choose: ").strip()
        if choice == "1":
            add_event()
        elif choice == "2":
            view_all()
        elif choice == "3":
            view_member_calendar()
        elif choice == "4":
            search_events()
        elif choice == "5":
            edit_event()
        elif choice == "6":
            delete_event()
        elif choice == "7":
            import_ics()
        elif choice == "8":
            manage_categories()
        elif choice == "9":
            configure_email()
        elif choice == "0":
            print("  Goodbye!")
            break
        else:
            print("  Invalid choice.")


def viewer_menu():
    while True:
        print("")
        print("  +-----------------------------------------+")
        print("  |      TaskFlow Planner  [Viewer]         |")
        print("  +-----------------------------------------+")
        print("  |                                         |")
        print("  |  1) View all events and calendar        |")
        print("  |  2) View calendar by user               |")
        print("  |  3) Search events                       |")
        print("  |  0) Exit                                |")
        print("  |                                         |")
        print("  +-----------------------------------------+")
        print("")
        choice = input("  Choose: ").strip()
        if choice == "1":
            view_all()
        elif choice == "2":
            view_member_calendar()
        elif choice == "3":
            search_events()
        elif choice == "0":
            print("  Goodbye!")
            break
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    db.setup()
    if "--check" in sys.argv:
        send_reminders()
    else:
        check_email_setup_on_startup()
        role = pick_role()
        select_user_identity()
        check_upcoming()
        if role == "planner":
            planner_menu()
        else:
            viewer_menu()
