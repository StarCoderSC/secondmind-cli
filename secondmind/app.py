import hashlib
from rich.console import Console
from datetime import datetime
from rich.panel import Panel
from rich import box
from rich.table import Table
import json
from rich.prompt import Prompt
import sqlite3
import os
from datetime import timedelta
from getpass import getpass

console = Console()


def get_connection():
    """Establish a connection to the SQLite database"""
    return sqlite3.connect("secondmind.db")


def parse_note(raw_note):
    """Parse a rae note string into its content, tags, and a due date"""
    note_part = raw_note
    tags = []
    due = None

    if "[due:" in raw_note:
        note_part, due_chunk = raw_note.rsplit("[due:", 1)
        due = due_chunk.rstrip("]").strip()

    tag_tokens = [word for word in note_part.strip().split() if word.startswith("#")]
    tags = tag_tokens
    clean_note = " ".join(
        [word for word in note_part.strip().split() if not word.startswith("#")]
    )

    return {"note": clean_note.strip(), "tags": tags, "due_date": due}


def build_note_from_json(data):
    """Construct a note string from a dictionary with note data."""
    note = data["note"]
    tags = ",".join(data["tags"]) if data["tags"] else ""
    due = f"[due:{data['due_date']}]" if data["due_date"] else ""

    return f"{note} {tags} {due}".strip()


def hash_password(password):
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user():
    """Register a new user and store thier credentials."""
    username = input("Choose a username: ").strip()
    password = getpass("Choose a password: ").strip()

    hashed_pw = hash_password(password)

    # Check if user already exist
    try:
        with open("users.txt", "r") as file:
            for line in file:
                if line.startswith(username + ":"):
                    console.print("[bold red]Username already exists.[/bold red]")
                    return None

    except FileNotFoundError:
        pass

    # Save new user
    with open("users.txt", "a") as file:
        file.write(f"{username}:{hashed_pw}\n")
    console.print(
        f"User [bold green]'{username}'[/bold green] registered successfully!"
    )
    return username


def login_user():
    """Authenticate a user against stored credentials."""
    username = input("Username: ").strip()
    password = getpass("Password: ").strip()
    hashed_pw = hash_password(password)

    try:
        with open("users.txt", "r") as file:
            for line in file:
                saved_user, saved_pw = line.strip().split(":")
                if saved_user == username and saved_pw == hashed_pw:
                    console.print(
                        f"[bold green]'{username}'[/bold green] Login successfull!"
                    )
                    return username

    except FileNotFoundError:
        pass

    console.print("[red]Login failed. Try again[/red]")
    return None


user = None


def initialize_database():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                note TEXT NOT NULL,
                tags TEXT,
                due_date TEXT
            )
        """
        )
        conn.commit()


initialize_database()


def render_notes_table(rows, header_style="bold green"):
    """Render a formatting table of notes in the console using Rich.

    Args:
        rows (list): List of tuples containing note data.

        header_style (str): Rich style for the header row.
    """

    table = Table(show_header=True, header_style=header_style)
    table.add_column("ID", style="dim")
    table.add_column("Note", style="cyan")
    table.add_column("Tags", style="yellow")
    table.add_column("Due Date", style="magenta")

    for row in rows:
        id_, note, tags, due = row
        table.add_row(str(id_), note, tags or "-", due or "-")

    console.print(table)


def add_note_to_db(user, note, tags, due_date):
    """
    Add a new note to the SQLite database after checking for duplicates.

    Args:
        user (str): Username associated with the note.
        note (str): The main note text.
        tag (list): List of tags (strings) for the note.
        due_date (str): Optional due date in YYYY-MM-DD format

    Returns:
        bool: True if note was added, False if it was a duplicate.
    """

    tag_string = ",".join(tags) if tags else None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM notes WHERE user = ? AND note = ? AND tags = ? AND due_date IS?
        """,
            (user, note, tag_string, due_date),
        )

        duplicate = cursor.fetchone()

        if duplicate:
            console.print(
                "[yellow]Note already exists with same content, tags, and due date. Skipping save.[/yellow]"
            )
            conn.close()
            return False

        cursor.execute(
            """
            INSERT INTO notes (user, note, tags, due_date)
            VALUES (?, ?, ?, ?)
        """,
            (user, note, tag_string, due_date),
        )

        conn.commit()
        conn.close()
        console.print("[green]Note added successfully.[/green]")
        return True


def view_note_from_db(user):
    """Retrieve and display all notes belonging to a specific user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, note, tags, due_date FROM notes WHERE user = ?", (user,)
        )
        rows = cursor.fetchall()

    if rows:
        render_notes_table(rows)
    else:
        console.print("[italic red]No notes found.[/italic red]")


def delete_note_by_id(user, note_id):
    """
    Delete a specific note by ID for a given user.

    Args:
        user (str): Username.
        note_id (int): ID of the note to be deleted.
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ? AND user = ?", (note_id, user))

        conn.commit()
        console.print(f"[green]Deleted note ID {note_id}[/green]")


def import_txt_to_db(user):
    """
    Import legacy plain text notes from a user-specific .txt file into the database.

    Expected file format: `notes_<username>.txt`
    Each line represents a note and may contain tags or a due date.
    """

    notes_file = f"notes_{user}.txt"
    if not os.path.exists(notes_file):
        console.print("[yellow]No legacy .txt notes found.[/yellow]")
        return

    imported = 0
    with open(notes_file, "r") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            tags = [word for word in line.split() if word.startswith("#")]
            note_part = " ".join(
                [
                    w
                    for w in line.split()
                    if not w.startswith("#") and not w.startswith("[due:")
                ]
            )
            due_date = None
            if "[due:" in line:
                try:
                    due_date = line.split("[due:")[1].split("]")[0]
                except:
                    pass

            add_note_to_db(user, note_part.strip(), tags, due_date)
            imported += 1

    console.print(
        f"[green]Imported {imported} notes from {notes_file} into DB.[/green]"
    )


def import_json_to_db(user):
    """
    Import notes from a JSON file into the database for the specified user.

    Expected file format: `<username>_notes_export.json`
    Each JSON object must have 'note', 'tags', and 'due_date'.
    """

    json_file = f"{user}_notes_export.json"
    if not os.path.exists(json_file):
        console.print("[yellow]No exported JSON found to import.[/yellow]")
        return

    with open(json_file, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON format.[/red]")
            return

    imported = 0
    for item in data:
        note = item.get("note", "")
        tags = item.get("tags", [])
        due = item.get("due_date", None)
        if note:
            add_note_to_db(user, note, tags, due)
            imported += 1


def search_notes_by_keyword(user, keyword):
    """
    Search and display notes containing a given keyword for a specific user.

    Args:
        user (str): Username.
        keyword (str): Keyword to search within note content.
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT id, note, tags, due_date FROM notes WHERE user = ? AND LOWER(note) LIKE LOWER(?)"
        cursor.execute(query, (user, f"%{keyword.lower()}%"))
        results = cursor.fetchall()

    if results:
        render_notes_table(results)
    else:
        console.print(f"[red]No notes found containing: {keyword}[/red]")


def filter_notes_by_tag(user, tag):
    """
    Display notes that contain a specific tag.

    Args:
        user (str): Username.
        tag (str): Tag to filter by (without the #).
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        query = (
            "SELECT id, note, tags, due_date FROM notes WHERE user = ? AND tags LIKE ?"
        )
        cursor.execute(query, (user, f"%{tag}%"))
        results = cursor.fetchall()

    if results:
        render_notes_table(results, header_style="bold yellow")
    else:
        console.print(f"[red]No notes found with tag: {tag}[/red]")


def view_due_notes(user, mode="today"):
    """
    Filter and display notes based on due date criteria.

    Args:
        user (str): Username.
        mode (str): One of "today", "overdue", or "week".
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, note, tags, due_date FROM notes WHERE user = ?", (user,)
        )
        results = cursor.fetchall()

    today = datetime.today().date()
    week_later = today + timedelta(days=7)
    filtered = []

    for row in results:
        id_, note, tags, due = row
        if not due:
            continue
        try:
            due_date = datetime.strptime(due, "%Y-%m-%d").date()
            if mode == "today" and due_date == today:
                filtered.append(row)
            elif mode == "overdue" and due_date < today:
                filtered.append(row)
            elif mode == "week" and today <= due_date <= week_later:
                filtered.append(row)
        except ValueError:
            continue

    if filtered:
        render_notes_table(filtered, header_style="bold magenta")
    else:
        console.print(f"[red]No notes found for: {mode.upper()}[/red]")


def edit_note_by_id(user, note_id):
    """
    Edit the contents, tags, or due date of a specific note.

    Args:
        user (str): Username.
        note_id (int): ID of the note to be edited.
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT note, tags, due_date FROM notes WHERE id = ? AND user = ?",
            (note_id, user),
        )
        row = cursor.fetchone()

        if not row:
            console.print("[red]Note not found.[/red]")
            return

        old_note, old_tags, old_due = row
        console.print(
            Panel.fit(
                f"Current Note:\n[cyan]{old_note}[/cyan]\nTags:[yellow]{old_tags or '-'}[/yellow]\nDue:[magenta]{old_due or '-'}[/magenta]"
            )
        )

        new_note = input("New note (leave blank to keep current):").strip()
        new_tags = input(
            "New tags (comma-separated, leave blank to keep current): "
        ).strip()
        new_due = input(
            "New due date (YYYY-MM-DD, leave blank to keep current): "
        ).strip()

        final_note = new_note if new_note else old_note

        tag_list = [f"#{tags.strip()}" for tags in new_tags.split(",") if tags.strip()]
        final_tags = " ".join(tag_list) if tag_list else (old_tags or "")
        final_due = new_due if new_due else old_due

        cursor.execute(
            """
            UPDATE notes
            Set note = ?, tags = ?, due_date = ?
            WHERE id = ? AND user = ?
        """,
            (final_note, final_tags, final_due, note_id, user),
        )
        conn.commit()

        console.print("[green]Note updated successfully[/green]")


def show_due_alerts_from_db():
    """Display summary of overdue and today's due notes as alerts after login."""

    today = datetime.today().date()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT due_date FROM notes WHERE user = ? AND due_date IS NOT NULL
        """,
            (user,),
        )
        results = cursor.fetchall()

    overdue = 0
    due_today = 0

    for (due,) in results:
        try:
            due_date = datetime.strptime(due, "%Y-%m-%d").date()
            if due_date < today:
                overdue += 1
            elif due_date == today:
                due_today += 1
        except ValueError:
            continue  # Skip malformed data

    if overdue or due_today:
        console.print(
            Panel.fit(
                f"[bold red]{overdue} overdue[/bold red] | [bold yellow]{due_today} due_today[/bold yellow]",
                title="[bold green]Reminders[/bold green]",
                border_style="bright_red",
            )
        )
    else:
        console.print("[green]No due tasks today. All clear [/green]")


def export_notes_to_json(user):
    """
    Export all of a user's notes into a JSON file for backup.

    File is named `<username>_notes_export.json`.
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT note, tags, due_date FROM notes WHERE user = ?", (user,))
        notes = cursor.fetchall()

    data = []
    for note, tags, due in notes:
        data.append(
            {"note": note, "tags": tags.split(",") if tags else [], "due_date": due}
        )

    with open(f"{user}_notes_export.json", "w") as f:
        json.dump(data, f, indent=4)

    console.print(f"[green]Notes exported to {user}_notes_export.json[/green]")


def db_note_exists(user, note_id):
    """
    Check whether a note with a given ID exists for the user.

    Args:
        user (str): Username.
        note_id (int): Note ID to check.

    Returns:
        bool: True if note exists, False otherwise.
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM notes WHERE id = ? AND user = ?", (note_id, user))

    result = cursor.fetchone()

    conn.close()
    return result is not None


def main():
    """Main entry point for the application.

    Handle user login/registration and menu-driven navigation for all note operation
    such as creating, viewing, editing, deleting, importing, and exporting notes.
    """
    global user

    user = None

    console.print(
        "[bold cyan]Welcome to StarCodersecondMind Secure Notepad[/bold cyan]"
    )

    while user is None:
        console.print(
            Panel.fit(
                """
[1] Login
[2] Register
[3] Exit
        """,
                title="[bold green]Login Menu[/bold green]",
                border_style="bright_magenta",
                box=box.ROUNDED,
            )
        )

        auth_choice = Prompt.ask("Choose an option", choices=["1", "2", "3"])

        if auth_choice == "1":
            user = login_user()
        elif auth_choice == "2":
            user = register_user()
        elif auth_choice == "3":
            if (
                Prompt.ask("Are you sure you want to exit?", choices=["yes", "no"])
                == "yes"
            ):
                console.print("[green]Goodbye![/green]")
                exit()
        else:
            console.print("[red]Invalid choice.[/red]")

    show_due_alerts_from_db()

    while True:
        console.print(
            Panel.fit(
                "[bold cyan]Welcome to StarCoderSecondMind CLI[/bold cyan]🚀\n\n"
                "[bold yellow]1.[/bold yellow]✍ Write a note\n"
                "[bold yellow]2.[/bold yellow]📖 View Saved notes\n"
                "[bold yellow]3:[/bold yellow]Edit a note\n"
                "[bold yellow]4.[/bold yellow]Delete a note from db\n"
                "[bold yellow]5.[/bold yellow]Search notes by keyword\n"
                "[bold yellow]6.[/bold yellow]Filter notes by tag\n"
                "[bold yellow]7.[/bold yellow]View due today\n"
                "[bold yellow]8.[/bold yellow]View overdue notes\n"
                "[bold yellow]9.[/bold yellow]View notes due this week\n"
                "[bold yellow]10.[/bold yellow]Import legacy notes from .txt\n"
                "[bold yellow]11.[/bold yellow]Import legacy notes from .json\n"
                "[bold yellow]12.[/bold yellow]export_notes_to_json\n"
                "[bold yellow]13.[/bold yellow]❌ Exit",
                title="[bold green]Main Menu[/bold green]",
                border_style="bright_magenta",
                box=box.ROUNDED,
            )
        )
        choice = Prompt.ask(
            "Please enter your choice",
            choices=[
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
                "13",
            ],
        )

        if choice == "1":
            your_note = input("Enter your note: ").strip()

            if not your_note:
                console.print("[red]Note can't be empty![/red]")
                continue

            # Check for overlay long notes
            if len(your_note) > 500:
                console.print(
                    "[red]Note too long (max 500 characters). Please shorten it.[/red]"
                )
                continue

            your_tags = input(
                "Add tags (comma-separated, e.g., todo,idea) or press 'Enter' to skip: "
            ).strip()
            due_input = input("Add due date (YYYY-MM-DD) or leave blank: ").strip()

            tag_list = [
                f"#{tag.strip()}" for tag in your_tags.split(",") if tag.strip()
            ]

            due_date = None
            if due_input:
                try:
                    due_date = datetime.strptime(due_input, "%Y-%m-%d").strftime(
                        "%Y-%m-%d"
                    )
                except ValueError:
                    console.print("[red]Invalid date format. Skipping due date.[/red]")

            console.print(
                Panel.fit(
                    f"Note:\n[cyan]{your_note}[/cyan]\nTags:[yellow]{tag_list or '-'}[/yellow]\nDue:[magenta]{due_date or '-'}[/magenta]"
                )
            )
            if Prompt.ask("Save this note?", choices=["yes", "no"]) == "yes":
                add_note_to_db(user, your_note, tag_list, due_date)
                console.print("[bold green]Note saved to DB.[/bold green]")
            else:
                console.print("[bold yellow]Note not saved...[/bold yellow]")

        elif choice == "2":
            view_note_from_db(user)

        elif choice == "3":
            try:
                view_note_from_db(user)
                note_id = int(input("Enter note ID to edit: "))

                edit_note_by_id(user, note_id)
            except ValueError:
                console.print("[red]Invalid ID entered[/red]")

        elif choice == "4":
            view_note_from_db(user)
            while True:
                user_input = Prompt.ask(
                    "Enter note ID to delete (or type 'cancel' to abort): "
                ).strip()
                if user_input.lower() == "cancel":
                    console.print("[yellow]Delete Cancelled.[/yellow]")
                    break

                if user_input.isdigit():
                    note_id = int(user_input)
                    if db_note_exists(user, note_id):
                        delete_note_by_id(user, note_id)
                        break
                    else:
                        console.print(f"[red]Not with ID {note_id} not found[/red]")
                        continue
                else:
                    console.print(
                        "[red]Invalid ID entered. Please enter a number or type 'cancel[/red]"
                    )

        elif choice == "5":
            keyword = input("Keyword to search:").strip()
            search_notes_by_keyword(user, keyword)

        elif choice == "6":
            tag = input("Tag to filter (without #):").strip()
            filter_notes_by_tag(user, tag)

        elif choice == "7":
            view_due_notes(user, "today")

        elif choice == "8":
            view_due_notes(user, "overdue")

        elif choice == "9":
            view_due_notes(user, "week")

        elif choice == "10":
            import_txt_to_db(user)

        elif choice == "11":
            import_json_to_db(user)

        elif choice == "12":
            export_notes_to_json(user)

        elif choice == "13":
            if (
                Prompt.ask("Are you sure you want to exit?", choices=["yes", "no"])
                == "yes"
            ):
                console.print("[bold green]Goodbye, StarCoder![/bold green]")
                exit()

        else:
            console.print("[bold red]Invalid choice, please try again![/bold red]")


if __name__ == "__main__":
    main()
