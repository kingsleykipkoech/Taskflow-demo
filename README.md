# TaskFlow Planner

**Group 23 — ALU, Introduction to Python Programming and Databases**

TaskFlow Planner is a command-line (CLI) event scheduling application written in
Python. It stores all of its data in a **MySQL database hosted online on Aiven**,
so information is saved permanently and can be shared across the group. The app
helps people keep track of their events, deadlines, and meetings — and it can
**remind the people close to you** about an upcoming activity, so you never miss it.

---

## The problem we are solving

People forget deadlines and events because they keep them in their heads or on
paper. Phone calendars exist, but they do not give a weekly overview, they do not
clearly show what is overdue, and they cannot easily remind *other people* on your
behalf. TaskFlow Planner fills those gaps with a simple, menu-driven tool.

---

## Features

### 1. Add an event  *(Create)*
Add a new activity with a **title, date, time, details, and a category**. The event
is saved straight into the MySQL database. *Why:* this is the heart of the app —
everything else works with the events you add.

### 2. View all events  *(Read)*
See every event in a clean list, ordered by date, each showing its live status.
*Why:* a single place to see everything coming up.

### 3. Search events  *(Read)*
Type a keyword and instantly find matching events by title or details.
*Why:* quickly locate one event without scrolling through the whole list.

### 4. Mark an event as done  *(Update)*
Tick off an event once it is completed.
*Why:* keeps your list clean and separates finished work from pending work.

### 5. Delete an event  *(Delete)*
Remove an event you no longer need (its participants are removed too).
*Why:* keeps the data tidy and correct.

### 6. Smart status (pending / ongoing / due / done)
The app **works out each event's status automatically** by comparing its date to
today: not yet reached = *pending*, happening today = *ongoing*, past and not done =
*due*, completed = *done*. *Why:* the status is always correct without us having to
update the database every day.

### 7. Month calendar (grid) view
Displays a real month grid in the terminal and **marks the days that have events**
with a star. *Why:* a visual overview that makes the app feel like a real calendar.

### 8. Import events from a calendar file (.ics)
Load events from a standard `.ics` calendar file (the same format phones and Google
Calendar use), adding them all at once. *Why:* saves typing and connects TaskFlow to
calendars people already use.

### 9. ⭐ Reminder notifications to the people close to you  *(facilitator's suggestion)*
This is the feature our facilitator asked us to add. When you create an event, you
can attach **participants — the people close to you** (friends, group members,
family) by their email. When the activity is coming up (today or tomorrow), TaskFlow
**sends a reminder notification by email to all of them**, not just you — so they can
remind you too. *Why:* reminders are more reliable when the people around you also
know about your upcoming activity. This runs both from the menu ("Send reminders now")
and automatically each day using a small scheduled job.

---

## How the data flows

```
You (terminal) → taskflow.py (menus) → database.py (runs SQL)
      → MySQL connector → Aiven MySQL (cloud storage) → results come back → printed
```

`taskflow.py` is the **application** (what the user sees). `database.py` is the
**database component** (all the SQL). `schema.sql` documents the table design.

---

## Database structure (3 tables)

- **categories** ( id, name ) — Classes, Assignments, Personal, Others
- **events** ( id, title, event_date, event_time, details, status, category_id )
- **attendees** ( id, event_id, email ) — the people close to you who get reminded

---

## Project files

```
Taskflow/
├── taskflow.py     # the application: menus, roles, user interaction
├── database.py     # the database component: connection + all SQL functions
├── schema.sql      # the table design, written in plain SQL (documentation/setup)
├── sample.ics      # a test calendar file for the import feature
└── README.md       # this file
```

---

## How to run

1. Install the connector: `pip install mysql-connector-python`
   (on newer Ubuntu use `pip install --break-system-packages mysql-connector-python`)
2. Put your Aiven database details in `database.py`.
3. Run it: `python3 taskflow.py`
4. (Optional, to email people) put a Gmail address + App Password at the top of `taskflow.py`.

---

## Running reminders in the background (optional)

The reminder check runs with:

```
python3 taskflow.py --check
```

This does not open the menu. It looks for events happening today or tomorrow,
pops a desktop notification for you, and emails the people you added.

To make it run **automatically** in the background, schedule that command with
**cron** (a built-in Linux tool). Note: cron is set up on each person's own
computer and is *not* part of this repo, so every user who wants automatic
reminders adds it once on their machine:

```
# open your schedule
crontab -e

# add this line to run the check every 30 minutes
# (the DISPLAY and DBUS_SESSION_BUS_ADDRESS parts let the notification show up)
*/30 * * * * DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus python3 /full/path/to/taskflow.py --check
```

Replace `/full/path/to/taskflow.py` with the real path on that computer.

---

## Team — Group 23

- Kingsley Kipkoech
- Felix Mwaniki
- Vanessa Kampiire
- Rita Akariza
- Lilian Kamikazi
- Gabriel Agaba
