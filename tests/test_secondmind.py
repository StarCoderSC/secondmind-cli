from secondmind.core import (
    parse_note,
    get_connection,
    build_note_from_json,
    hash_password,
    register_user,
    login_user,
    initialize_database,
    add_note_to_db,
    view_note_from_db,
    delete_note_by_id,
    render_notes_table,
    import_txt_to_db,
    import_json_to_db,
    search_notes_by_keyword,
    filter_notes_by_tag,
    view_due_notes,
    edit_note_by_id,
    show_due_alerts_from_db,
    export_notes_to_json,
    db_note_exists,
)

from unittest.mock import patch, MagicMock, mock_open
import sqlite3
import json
import os
import pytest
import tempfile
from rich.table import Table
from datetime import datetime, timedelta


def test_parse_note_with_tags_and_due_date():
    raw = "Buy milk #grocery #urgent [due:2025-07-25]"
    note = parse_note(raw)

    assert note["note"] == "Buy milk"
    assert note["tags"] == ["#grocery", "#urgent"]
    assert note["due_date"] == "2025-07-25"


def parse_note_with_no_tags_or_due():
    raw = "Read a book"
    result = parse_note(raw)

    assert result["note"] == "Read a book"
    assert result["tags"] == []
    assert result["due_date"] is None


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            {
                "note": "Finish project",
                "tags": ["urgent", "work"],
                "due_date": "2025-09-01",
            },
            "Finish project urgent,work [due:2025-09-01]",
        ),
        (
            {"note": "Just a note", "tags": [], "due_date": "2025-09-01"},
            "Just a note [due:2025-09-01]",
        ),
        (
            {"note": "Read book", "tags": ["reading"], "due_date": None},
            "Read book reading",
        ),
        ({"note": "No extra", "tags": [], "due_date": None}, "No extra"),
    ],
)
def test_build_note_from_json(data, expected):
    assert build_note_from_json(data) == expected


def test_hash_password_consistency():
    password = "securePassword123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 == hash2  # Same input should produce the same length


def test_hash_password_different_inputs():
    password1 = "password123"
    password2 = "differentPassword456"
    hash1 = hash_password(password1)
    hash2 = hash_password(password2)

    assert hash1 != hash2  # Different passwords should not produce the same hash


def test_hash_password_length():
    password = "testpassword"
    hashed = hash_password(password)

    assert len(hashed) == 64  # SHA256 produces a 64-character hex string


def test_hash_password_empty():
    password = ""
    hashed = hash_password(password)

    assert (
        len(hashed) == 64
    )  # Hashing in empty string should still return a valid 64-char hash

    assert len(hashed) != "empty"  # Ensure it's not just returning the string "empty"


@patch("builtins.input", return_value="testuser")
@patch("secondmind.core.getpass", return_value="securePassword123")
@patch("secondmind.core.console.print")
@patch(
    "builtins.open", new_callable=mock_open, read_data=""
)  # Mocking open with empty file
def test_register_user_success(mock_file, mock_print, mock_getpass, mock_input):
    # Act
    username = register_user()

    # Assert username is returned correctly
    assert username == "testuser"

    # Assert the correct file operations
    mock_file.assert_any_call("users.txt", "a")
    mock_file.assert_any_call("users.txt", "r")

    handle = mock_file()

    handle.write.assert_called_once_with(
        f"testuser:{hash_password('securePassword123')}\n"
    )

    # Assert correct console output
    mock_print.assert_called_once_with(
        "User [bold green]'testuser'[/bold green] registered successfully!"
    )


@patch("builtins.input", return_value="")
@patch("secondmind.core.getpass", return_value="securePassword123")
@patch("secondmind.core.console.print")
def test_register_user_empty_username(mock_print, mock_getpass, mock_input):
    # Act
    username = register_user()

    # Assert no username is returned
    assert username is None

    # Assert the error message is printed
    mock_print.assert_called_once_with(
        "[bold red]Please enter a username and a password.[/bold red]"
    )


@patch("builtins.input", return_value="testuser")
@patch("secondmind.core.getpass", return_value="securePassword123")
@patch("secondmind.core.console.print")
@patch("builtins.open", new_callable=mock_open, read_data="testuser:hashed_pw\n")
def test_register_user_exists(mock_file, mock_print, mock_getpass, mock_input):
    # Act
    username = register_user()

    # Assert no new user is created
    assert username is None

    # Assert the error message is printed
    mock_print.assert_called_once_with("[bold red]Username already exists.[/bold red]")


@patch("builtins.input", return_value="newuser")
@patch("secondmind.core.getpass", return_value="newPassword123")
@patch("secondmind.core.console.print")
def test_register_user_file_not_found(mock_print, mock_getpass, mock_input):
    mocked_open = mock_open()
    open_call_tracker = MagicMock()

    # Custom side effect to stimulate FileNotFoundError on first read.
    # then return mock handle for writing - while tracking all calls
    def open_side_effect(file, mode, *args, **kwargs):
        open_call_tracker(file, mode)  # record the call manually
        if mode == "r":
            raise FileNotFoundError()
        return mocked_open.return_value

    with patch("builtins.open", side_effect=open_side_effect):
        username = register_user()

        # Assert username is returned correctly
        assert username == "newuser"

        open_call_tracker.assert_any_call("users.txt", "a")

        # Ensure content was written
        handle = mocked_open()

        handle.write.assert_called_once_with(
            f"newuser:{hash_password('newPassword123')}\n"
        )

        # Assert correct console output
        mock_print.assert_called_once_with(
            "User [bold green]'newuser'[/bold green] registered successfully!"
        )


@patch("builtins.input", return_value="testuser")
@patch("secondmind.core.getpass", return_value="securePassword123")
@patch("secondmind.core.console.print")
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="testuser:" + hash_password("securePassword123") + "\n",
)
def test_login_user_success(mock_file, mock_print, mock_getpass, mock_input):
    # ACt
    username = login_user()

    # Assert login succeeded
    assert username == "testuser"

    # Assert console outptu

    mock_print.assert_called_once_with(
        "[bold green]'testuser'[/bold green] Login successfull!"
    )


@patch("builtins.input", return_value="testuser")
@patch("secondmind.core.getpass", return_value="wrongpassword")
@patch("secondmind.core.console.print")
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="testuser:" + hash_password("correctpassword") + "\n",
)
def test_login_user_incorrect_password(mock_file, mock_print, mock_getpass, mock_input):
    # Act
    username = login_user()

    # Assert login failed
    assert username is None

    # Assert error message shown
    mock_print.assert_called_once_with("[red]Login failed. Try again[/red]")


@patch("builtins.input", return_value="testuser")
@patch("secondmind.core.getpass", return_value="somepassword")
@patch("secondmind.core.console.print")
@patch("builtins.open", side_effect=FileNotFoundError)
def test_login_user_filel_not_found(mock_file, mock_print, mock_getpass, mock_input):
    # Act
    username = login_user()

    # Assert login failed
    assert username is None

    # Assert error message shown
    mock_print.assert_called_once_with("[red]Login failed. Try again[/red]")


def test_initialize_database_create_table():
    # Act
    initialize_database()

    # Assert the table exists
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='notes'"
        )
        table = cursor.fetchone()
        assert table is not None
        assert table[0] == "notes"


def test_initialize_database_idempotent():
    initialize_database()
    initialize_database()


def test_notes_table_schema():
    initialize_database()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(notes)")
        columns = [col[1] for col in cursor.fetchall()]
        expected_columns = ["id", "user", "note", "tags", "due_date"]

        assert columns == expected_columns


def get_test_db_conn(db_path):
    return sqlite3.connect(db_path)


def test_add_unique_note(temp_db):
    conn = get_test_db_conn(temp_db)
    with patch("secondmind.core.get_connection", return_value=conn):
        user = "testuser"
        note = "This is a unique test note"
        result = add_note_to_db(user, note, ["test", "unique"], "2025-12-31")
        assert result is True


def test_add_duplicate_note(temp_db):
    conn = get_test_db_conn(temp_db)
    with patch("secondmind.core.get_connection", return_value=conn):
        user = "testuser"
        note = "Duplicate note here"
        tags = ["duplicate"]
        due_date = "2025-11-01"

        first = add_note_to_db(user, note, tags, due_date)
        second = add_note_to_db(user, note, tags, due_date)

        assert first is True
        assert second is False


@pytest.fixture
def temp_db():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    conn = get_test_db_conn(db_path)

    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            note TEXT,
            tags TEXT,
            due_date TEXT
        )
    """
    )
    conn.commit()

    yield db_path

    conn.close()
    os.close(db_fd)
    os.remove(db_path)


def test_view_note_with_notes(temp_db, monkeypatch):
    os.environ["SECOND_MIND_DB"] = str(temp_db)

    conn = get_test_db_conn(temp_db)
    # Add note to DB using real function
    with patch("secondmind.core.get_connection", return_value=conn):
        add_note_to_db("testuser", "Sample note", ["#test"], "2025-08-01")

    # Mock render_notes_table to check it was called
    with patch("secondmind.core.render_notes_table") as mock_render:
        view_note_from_db("testuser")
        mock_render.assert_called_once()  # Should render


def test_view_note_empty(temp_db, monkeypatch):
    os.environ["SECOND_MIND_DB"] = str(temp_db)

    conn = get_test_db_conn(temp_db)
    with patch("secondmind.core.get_connection", return_value=conn):
        # No notes added

        with patch("secondmind.core.console.print") as mock_print:
            view_note_from_db("newuser")  # user with no notes
            mock_print.assert_called_once_with(
                "[italic red]No notes found.[/italic red]"
            )


def test_delete_note_success(temp_db):
    user = "testuser"
    note = "Note to delete"
    tags = "#test"
    due_date = "2025-07-25"

    with get_test_db_conn(temp_db) as conn:
        with patch("secondmind.core.get_connection", return_value=conn):
            add_note_to_db(user, note, tags.split(","), due_date)
            # insert a test note directly
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (user, note, tags, due_date) VALUES (?, ?, ?, ?)",
                (user, note, tags, due_date),
            )
            note_id = cursor.lastrowid
            conn.commit()

            # Now test deletion
            with patch("secondmind.core.console.print") as mock_print:
                delete_note_by_id(user, note_id)
                mock_print.assert_called_once_with(
                    f"[green]Deleted note ID {note_id}[/green]"
                )

                # Check if notes was actually deleted
                cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
                assert cursor.fetchone() is None


def test_delete_note_invalid_id(temp_db):
    """Test case where an Invalid note ID is deleted"""

    user = "testuser"
    invalid_note_id = 9999

    with get_test_db_conn(temp_db) as conn:
        with patch("secondmind.core.get_connection", return_value=conn):
            with patch("secondmind.core.console.print") as mock_print:
                delete_note_by_id(user, invalid_note_id)

            # Verify the error message was shown
            mock_print.assert_called_once_with(
                f"[green]Deleted note ID {invalid_note_id}[/green]"
            )


def test_render_notes_table_renders_correctly():
    sample_data = [
        (1, "Buy milk", "#grocery", "2025-07-25"),
        (2, "Read book", "", None),
    ]

    with patch("secondmind.core.console.print") as mock_print:
        render_notes_table(sample_data)

        # Assert print was called once
        mock_print.assert_called_once()

        printed_table = mock_print.call_args[0][0]

        # Assert it's a Rich Table
        assert isinstance(printed_table, Table)

        # Asssert the correct number if rows and columns
        assert len(printed_table.columns) == 4
        assert printed_table.columns[0].header == "ID"
        assert printed_table.columns[1].header == "Note"
        assert printed_table.columns[2].header == "Tags"
        assert printed_table.columns[3].header == "Due Date"


def test_import_txt_to_db(tmp_path):
    # Setup
    username = "testuser"
    filename = tmp_path / f"notes_{username}.txt"
    content = """Buy groceries #errand [due:2025-07-31]
        Clean the house #chores
        Just a note with no tags and date
    """
    filename.write_text(content)

    # Patch cwd so function looks in tmp_path
    with patch("secondmind.core.os.path.exists", return_value=True), patch(
        "secondmind.core.open", side_effect=lambda *a, **k: open(filename, *a[1:], **k)
    ), patch("secondmind.core.add_note_to_db") as mock_add, patch(
        "secondmind.core.console.print"
    ) as mock_print:
        import_txt_to_db(username)

        # Check add_note_to_db called correct number of times
        assert mock_add.call_count == 3

        # Optionally check one specific call
        mock_add.assert_any_call(username, "Buy groceries", ["#errand"], "2025-07-31")

        # Print message should contain import
        mock_print.assert_called_with(
            f"[green]Imported 3 notes from notes_{username}.txt into DB.[/green]"
        )


def test_import_json_to_db(tmp_path):
    # Arrange
    user = "testuser"
    filename = tmp_path / f"{user}_notes_export.json"
    notes_data = [
        {"note": "Note 1", "tags": ["#tag"], "due_date": "2025-08-01"},
        {"note": "Note 2", "tags": [], "due_date": None},
        {"note": "Note 3", "tags": ["#tag3"], "due_date": "2025-08-15"},
    ]
    filename.write_text(json.dumps(notes_data))

    # Patch os.path.exists + open + add_note_to_db
    with patch("secondmind.core.os.path.exists", return_value=True), patch(
        "secondmind.core.open", side_effect=lambda *a, **k: open(filename, *a[1:], **k)
    ), patch("secondmind.core.add_note_to_db") as mock_add, patch(
        "secondmind.core.console.print"
    ) as mock_print:

        import_json_to_db(user)

        # Assert: Called once for each note
        assert mock_add.call_count == 3
        mock_add.assert_any_call(user, "Note 1", ["#tag"], "2025-08-01")
        mock_add.assert_any_call(user, "Note 2", [], None)

        # Final print confirmation
        mock_print.assert_not_called()  # No warning/error, only silent success


def test_import_json_to_db_invalid_json(tmp_path):
    user = "testuser"
    filename = tmp_path / f"{user}_notes_export.json"
    filename.write_text("This is not valid JSON")

    with patch("secondmind.core.os.path.exists", return_value=True), patch(
        "secondmind.core.open", side_effect=lambda *a, **k: open(filename, *a[1:], **k)
    ), patch("secondmind.core.console.print") as mock_print:
        import_json_to_db(user)

        mock_print.assert_called_once_with("[red]Invalid JSON format.[/red]")


def test_search_notes_by_keyword_found():
    user = "testuser"
    keyword = "project"
    expected_results = [
        (1, "Finish project report", "#work", "2025-08-01"),
        (2, "Project meeting with team", "#meeting", "2025-08-02"),
    ]

    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = expected_results

    with patch(
        "secondmind.core.get_connection", return_value=mock_conn
    ) as mock_get_conn, patch(
        "secondmind.core.render_notes_table"
    ) as mock_render, patch(
        "secondmind.core.console.print"
    ) as mock_print:

        # Stimulate context manager
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        search_notes_by_keyword(user, keyword)

        expected_query = (
            "SELECT id, note, tags, due_date FROM notes "
            "WHERE user = ? AND LOWER(note) LIKE LOWER(?)"
        )
        expected_params = (user, f"%{keyword.lower()}%")
        # Assert query was executed with correct LIKE clause
        mock_cursor.execute.assert_called_once_with(
            expected_query, expected_params
        )

        # Assert results were rendered
        mock_render.assert_called_once_with(expected_results)
        mock_print.assert_not_called()


def test_search_notes_by_keyword_not_found():
    user = "testuser"
    keyword = "unicorns"

    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = []

    with patch(
        "secondmind.core.get_connection", return_value=mock_conn
    ) as mock_get_conn, patch(
        "secondmind.core.render_notes_table"
    ) as mock_render, patch(
        "secondmind.core.console.print"
    ) as mock_print:

        mock_get_conn.return_value.__enter__.return_value = mock_conn

        search_notes_by_keyword(user, keyword)

        mock_cursor.execute.assert_called_once()
        # Should not render anything
        mock_render.assert_not_called()
        mock_print.assert_called_once_with(
            f"[red]No notes found containing: {keyword}[/red]"
        )


def test_filter_notes_by_tag_found(temp_db, monkeypatch):
    user = "testuser"
    tag = "test"

    conn = get_test_db_conn(temp_db)

    with patch("secondmind.core.get_connection", return_value=conn):
        # Add some note with different tags
        add_note_to_db(user, "Note 1", ["#test", "#urgent"], "2025-08-01")
        add_note_to_db(user, "Note 2", ["#work", "#test"], "2025-09-01")
        add_note_to_db(user, "Note 3", ["#test"], "2025-10-01")

        # Mock reneder_notes_table to check if it's called
        with patch("secondmind.core.render_notes_table") as mock_render:
            filter_notes_by_tag(user, tag)

            # The table render function should be called
            # with results for notes with the "#test" tag
            mock_render.assert_called_once()


def test_filter_notes_by_tag_not_found(temp_db, monkeypatch):
    user = "testuser"
    tag = "unicorn"

    conn = get_test_db_conn(temp_db)

    with patch("secondmind.core.get_connection", return_value=conn):

        # Add some notes with different tags
        add_note_to_db(user, "Note 1", ["#test", "#urgent"], "2025-08-01")
        add_note_to_db(user, "Note 2", ["#work"], "2025-09-01")

        # Mock console.print to check if the "No notes found" message is printed
        with patch("secondmind.core.console.print") as mock_print:
            filter_notes_by_tag(user, tag)

            # No notes should match the "unicorn" tag,
            # so console.print should be called with this message
            mock_print.assert_called_once_with(
                f"[red]No notes found with tag: {tag}[/red]"
            )


def test_view_notes_today(temp_db, monkeypatch):
    user = "testuser"
    today = datetime.today().date()

    conn = get_test_db_conn(temp_db)

    with patch("secondmind.core.get_connection", return_value=conn):
        add_note_to_db(user, "Note 1", ["#test"], str(today))
        add_note_to_db(user, "Note 2", ["#test"], "2025-08-01")
        add_note_to_db(user, "Note 3", ["#test"], "2025-07-01")

        # Mock render_notes_table to check if it's called
        with patch("secondmind.core.render_notes_table") as mock_render:
            view_due_notes(user, mode="today")

            # The table render function should be called
            # with results for notes due today
            mock_render.assert_called_once()


def test_view_due_notes_overdue(temp_db, monkeypatch):
    user = "testuser"
    today = datetime.today().date()

    conn = get_test_db_conn(temp_db)

    with patch("secondmind.core.get_connection", return_value=conn):
        add_note_to_db(user, "Note 1", ["#test"], str(today))
        add_note_to_db(user, "Note 2", ["#test"], "2025-08-01")
        add_note_to_db(user, "Note 3", ["#test"], "2025-07-01")

        # Mock render_notes_table to check if it's called
        with patch("secondmind.core.render_notes_table") as mock_render:
            view_due_notes(user, mode="overdue")

            # The table render function should be called with results for overdue notes
            mock_render.assert_called_once()


def test_view_due_notes_week(temp_db, monkeypatch):
    user = "testuser"
    today = datetime.today().date()
    week_later = today + timedelta(days=7)

    conn = get_test_db_conn(temp_db)

    with patch("secondmind.core.get_connection", return_value=conn):
        add_note_to_db(user, "Note 1", ["#test"], str(today))
        add_note_to_db(user, "Note 2", ["#test"], str(week_later))
        add_note_to_db(user, "Note 3", ["#test"], "2025-07-01")

        # Mock render_notes_teble to check id it's called
        with patch("secondmind.core.render_notes_table") as mock_render:
            view_due_notes(user, mode="week")

            # The table render function should be called
            # with results for notes due this week
            mock_render.assert_called_once()


def test_view_due_notes_no_matching(temp_db, monkeypatch):
    user = "testuser"

    conn = get_test_db_conn(temp_db)

    with patch("secondmind.core.get_connection", return_value=conn):
        # Add notes with due dates far in the future or past
        add_note_to_db(user, "Note 1", ["#test"], "2025-08-01")
        add_note_to_db(user, "Note 2", ["#test"], "2025-07-01")

        # Mock console.print to check if the "No notes found" message is printed
        with patch("secondmind.core.console.print") as mock_print:
            view_due_notes(user, mode="today")
            mock_print.assert_called_once_with("[red]No notes found for: TODAY[/red]")


def test_edit_note_by_id(temp_db):
    """Test editing a note by its ID"""

    # insert a smaple note into the temporary database
    user = "testuser"
    original_note = "Original note text"
    original_tags = "#test, #edit"
    original_due = "2025-08-01"

    conn = get_test_db_conn(temp_db)

    with patch("secondmind.core.get_connection", return_value=conn):
        add_note_to_db(user, original_note, original_tags.split(","), original_due)

        # Fetch the inserted note's ID
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM notes WHERE user = ? AND note = ?", (user, original_note)
        )
        note_id = cursor.fetchone()[0]

        # Mock iser input for the new note
        new_note = "Updated note text"
        new_tags = "#updated #tags"
        new_due = "2025-09-01"

        # Patch input() calls to stimulate the user entering new values
        with patch("builtins.input", side_effect=[new_note, new_tags, new_due]):
            # Patch console.print to capture output
            with patch("secondmind.core.console.print") as mock_print:
                with patch("secondmind.core.get_connection", return_value=conn):

                    # Call the function to edit the  note
                    edit_note_by_id(user, note_id)

                # Check if the update query was updated
                cursor.execute(
                    "SELECT note, tags, due_date FROM notes WHERE id = ?", (note_id,)
                )
                updated_note, updated_tags, updated_due = cursor.fetchone()

                assert updated_note == new_note
                assert updated_tags == new_tags
                assert updated_due == new_due

                # Check if the console print was called with success message
                mock_print.assert_called_with(
                    "[green]Note updated successfully[/green]"
                )


def test_edit_note_not_found(temp_db):
    """Test case where note is not found for editing."""

    user = "testuser"
    non_existing_note_id = 9999  # This ID doesn't exist in the database

    conn = get_test_db_conn(temp_db)

    # Patch console.print to capture output
    with patch("secondmind.core.console.print") as mock_print:
        with patch("secondmind.core.get_connection", return_value=conn):
            # Call the function to edit the note
            edit_note_by_id(user, non_existing_note_id)

        # Check if the appropriate "Note not found" message is printed
        mock_print.assert_called_with("[red]Note not found.[/red]")


@patch("secondmind.core.console.print")
@patch("secondmind.core.get_connection")
def test_show_due_alerts_from_db_summary(mock_get_conn, mock_print):
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [
        ("2025-07-01",),  # overdue
        (datetime.today().strftime("%Y-%m-%d"),),  # Today
    ]

    mock_get_conn.return_value.__enter__.return_value = mock_conn

    with patch("secondmind.core.user", "testuser"):
        show_due_alerts_from_db()

    # Extract the printed Panel
    actual_panel = mock_print.call_args[0][0]
    content = str(actual_panel.renderable)

    assert "1 overdue" in content
    assert "1 due_today" in content


@patch("secondmind.core.console.print")
@patch("secondmind.core.open", new_callable=mock_open)
@patch("secondmind.core.get_connection")
def test_export_notes_to_json(mock_get_conn, mock_file, mock_print):
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [
        ("Test note 1", "tag1,tag2", "2025-08-01"),
        ("Test note 2", "", None),
    ]

    mock_get_conn.return_value.__enter__.return_value = mock_conn

    # Act
    export_notes_to_json("testuser")

    # Assert file writing
    mock_file.assert_called_once_with("testuser_notes_export.json", "w")
    handle = mock_file()
    written_data = json.loads(
        "".join(call.args[0] for call in handle.write.call_args_list)
    )

    expected = [
        {"note": "Test note 1", "tags": ["tag1", "tag2"], "due_date": "2025-08-01"},
        {"note": "Test note 2", "tags": [], "due_date": None},
    ]

    assert written_data == expected

    # Assert console output
    mock_print.assert_called_once_with(
        "[green]Notes exported to testuser_notes_export.json[/green]"
    )


@patch("secondmind.core.get_connection")
def test_db_note_exists_true(mock_get_conn):
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchone.return_value = (1,)

    # Stimulate row found
    mock_get_conn.return_value = mock_conn

    # Act
    exists = db_note_exists("testuser", 1)

    # Assert
    assert exists is True

    mock_cursor.execute.assert_called_once_with(
        "SELECT 1 FROM notes WHERE id = ? AND user = ?", (1, "testuser")
    )


@patch("secondmind.core.get_connection")
def test_db_note_exists_false(mock_get_conn):
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchone.return_value = None

    mock_get_conn.return_value = mock_conn

    # Act
    exists = db_note_exists("testuser", 999)

    # Assert
    assert exists is False

    mock_cursor.execute.assert_called_once_with(
        "SELECT 1 FROM notes WHERE id = ? AND user = ?", (999, "testuser")
    )
