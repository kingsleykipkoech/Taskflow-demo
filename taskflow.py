import sys
import os
import calendar
import smtplib
from datetime import date, timedelta
import connection as db

# To email reminders, put a Gmail address and its 16-character App Password here.
# Leave them empty and reminders will just show as desktop notifications.
SENDER_EMAIL        = ""
SENDER_APP_PASSWORD = ""


def is_valid_date(text):
    parts = text.split("-")
    if len(parts) != 3:
        return False
    year_part = parts[0]
    month_part = parts[1]
    day_part = parts[2]
    if not year_part.isdigit():
        return False
    if not month_part.isdigit():
        return False
    if not day_part.isdigit():
        return False
    if len(year_part) != 4:
        return False
    if int(month_part) < 1 or int(month_part) > 12:
        return False
    if int(day_part) < 1 or int(day_part) > 31:
        return False
    return True


def is_valid_time(text):
    parts = text.split(":")
    if len(parts) != 2:
        return False
    hour_part = parts[0]
    minute_part = parts[1]
    if not hour_part.isdigit():
        return False
    if not minute_part.isdigit():
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


def send_email(to_email, subject, body):
    if SENDER_EMAIL == "":
        return
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        full_message = "Subject: " + subject + "\n\n" + body
        server.sendmail(SENDER_EMAIL, to_email, full_message)
        server.quit()
    except:
        pass


def choose_category():
    all_categories = db.get_all_categories()
    print("")
    print("  +-----------------------------+")
    print("  |        Categories            |")
    print("  +-----------------------------+")
    number = 1
    for category in all_categories:
        category_name = category[1]
        print("  |  " + str(number) + ") " + category_name.ljust(23) + "|")
        number = number + 1
    print("  +-----------------------------+")
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
    title = input("  Event title: ").strip()
    while title == "":
        title = input("  Title cannot be empty. Event title: ").strip()
    date_input = input("  Date (YYYY-MM-DD): ").strip()
    while not is_valid_date(date_input):
        date_input = input("  Invalid. Date (YYYY-MM-DD): ").strip()
    time_input = input("  Time (HH:MM): ").strip()
    while not is_valid_time(time_input):
        time_input = input("  Invalid. Time (HH:MM): ").strip()
    details = input("  Details (optional): ").strip()
    category_id = choose_category()

    new_event_id = db.add_event(title, date_input, time_input, details, category_id)
    print("")
    print("  Event added successfully!")
    print("")
    emails_input = input("  Add participant emails (space separated), or Enter to skip: ").strip()
    if emails_input != "":
        for one_email in emails_input.split():
            db.add_attendee(new_event_id, one_email)
        print("  Participants added.")


def show_event_list():
    all_events = db.get_all_events()
    if len(all_events) == 0:
        print("  No events yet.")
        return

    today = str(date.today())
    print("  +-----+----------------------+------------+-------+----------------+---------+")
    print("  | ID  | Title                | Date       | Time  | Category       | Status  |")
    print("  +-----+----------------------+------------+-------+----------------+---------+")
    for event in all_events:
        event_id = str(event[0]).ljust(3)
        title = str(event[1])[:20].ljust(20)
        event_date = str(event[2]).ljust(10)
        event_time = str(event[3]).ljust(5)
        category_name = str(event[6])[:14].ljust(14)
        current_status = get_event_status(event[5], event[2], today).upper().ljust(7)
        print("  | " + event_id + " | " + title + " | " + event_date + " | " + event_time + " | " + category_name + " | " + current_status + " |")
        if event[4]:
            print("  |     |   -> " + str(event[4])[:65].ljust(73) + " |")
    print("  +-----+----------------------+------------+-------+----------------+---------+")


def show_calendar():
    today = date.today()
    year_month = "%04d-%02d" % (today.year, today.month)
    busy_days = db.get_busy_days(year_month)

    month_title = calendar.month_name[today.month] + " " + str(today.year)
    print("  +------------------------------+")
    print("  |  " + month_title.center(26) + "  |")
    print("  +------------------------------+")

    header = "  |  "
    for day_name in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
        header = header + day_name.ljust(4)
    header = header + "|"
    print(header)
    print("  |  " + "-" * 26 + "  |")

    for week in calendar.monthcalendar(today.year, today.month):
        line = "  |  "
        for day in week:
            if day == 0:
                cell = "    "
            elif day == today.day:
                cell = ("[" + str(day) + "]").ljust(4)
            elif day in busy_days:
                cell = (str(day) + "*").ljust(4)
            else:
                cell = str(day).ljust(4)
            line = line + cell
        line = line + "|"
        print(line)

    print("  +------------------------------+")
    print("  (* = has events)  [" + str(today.day) + "] = today")


def view_all():
    print("")
    show_calendar()
    print("")
    show_event_list()
    print("")


def search_events():
    print("")
    keyword = input("  Search keyword: ").strip().lower()
    results = db.search_events(keyword)
    if len(results) == 0:
        print("  No matching events.")
        return

    today = str(date.today())
    print("")
    print("  Search results:")
    print("  " + "-" * 60)
    for event in results:
        event_id = str(event[0])
        title = event[1]
        event_date = event[2]
        event_time = event[3]
        category_name = event[6]
        current_status = get_event_status(event[5], event_date, today).upper()
        print("  #" + event_id + "  " + title + "  |  " + event_date + " " + event_time + "  |  " + category_name + "  |  " + current_status)
    print("  " + "-" * 60)
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
    print("  Editing: " + title)
    print("  " + "-" * 35)
    print("  1) Mark as done")
    print("  2) Add participants (people to remind you)")
    print("  " + "-" * 35)
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
        print("  Participants added to: " + title)
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
    filename = input("  Enter .ics filename: ").strip()
    if not os.path.exists(filename):
        print("  File not found.")
        return

    ics_file = open(filename)
    all_lines = ics_file.readlines()
    ics_file.close()

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

    print("  Imported " + str(imported_count) + " event(s).")


def manage_categories():
    print("")
    all_categories = db.get_all_categories()
    print("  +-----------------------------+")
    print("  |     Current Categories       |")
    print("  +-----------------------------+")
    for category in all_categories:
        print("  |  - " + category[1].ljust(23) + "|")
    print("  +-----------------------------+")
    print("")
    name = input("  Enter new category name (or Enter to go back): ").strip()
    if name == "":
        return
    db.add_category(name)
    print("  Category '" + name + "' added!")


def check_upcoming():
    today = str(date.today())
    tomorrow = str(date.today() + timedelta(days=1))
    events = db.get_events_on_dates(today, tomorrow)
    upcoming = []
    for event in events:
        if event[4] != "done":
            upcoming.append(event)

    if len(upcoming) == 0:
        return

    print("")
    print("  +-----------------------------------------+")
    print("  |           Upcoming Reminders!            |")
    print("  +-----------------------------------------+")
    for event in upcoming:
        event_id = event[0]
        title = event[1]
        event_date = event[2]
        event_time = event[3]
        if event_date == today:
            when = "TODAY"
        else:
            when = "TOMORROW"
        print("  |  " + (title + " - " + when + " at " + event_time).ljust(37) + "|")

        # Send desktop notification
        message = title + " is happening " + when + " at " + event_time
        os.system('notify-send "TaskFlow Reminder" "' + message + '"')

        # Email attendees silently
        attendee_emails = db.get_attendee_emails(event_id)
        for one_email in attendee_emails:
            send_email(
                one_email,
                "Reminder: " + title,
                "Hi, this is a friendly reminder that '" + title +
                "' is happening " + when + " at " + event_time +
                ". Please remind your friend!"
            )
    print("  +-----------------------------------------+")


def send_reminders():
    today = str(date.today())
    tomorrow = str(date.today() + timedelta(days=1))
    events = db.get_events_on_dates(today, tomorrow)
    for event in events:
        if event[4] == "done":
            continue
        event_id = event[0]
        title = event[1]
        event_date = event[2]
        event_time = event[3]
        if event_date == today:
            when = "TODAY"
        else:
            when = "TOMORROW"
        message = title + " is happening " + when + " at " + event_time
        os.system('notify-send "TaskFlow Reminder" "' + message + '"')
        attendee_emails = db.get_attendee_emails(event_id)
        for one_email in attendee_emails:
            send_email(
                one_email,
                "Reminder: " + title,
                "Hi, this is a friendly reminder that '" + title +
                "' is happening " + when + " at " + event_time +
                ". Please remind your friend!"
            )


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


def planner_menu():
    while True:
        print("")
        print("  +-----------------------------------------+")
        print("  |      TaskFlow Planner  [Planner]        |")
        print("  +-----------------------------------------+")
        print("  |                                         |")
        print("  |  1) Add event                           |")
        print("  |  2) View all events and calendar        |")
        print("  |  3) Search events                       |")
        print("  |  4) Edit event                          |")
        print("  |  5) Delete event                        |")
        print("  |  6) Import events from .ics file        |")
        print("  |  7) Manage categories                   |")
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
            search_events()
        elif choice == "4":
            edit_event()
        elif choice == "5":
            delete_event()
        elif choice == "6":
            import_ics()
        elif choice == "7":
            manage_categories()
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
        print("  |  2) Search events                       |")
        print("  |  0) Exit                                |")
        print("  |                                         |")
        print("  +-----------------------------------------+")
        print("")
        choice = input("  Choose: ").strip()
        if choice == "1":
            view_all()
        elif choice == "2":
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
        role = pick_role()
        check_upcoming()
        if role == "planner":
            planner_menu()
        else:
            viewer_menu()
