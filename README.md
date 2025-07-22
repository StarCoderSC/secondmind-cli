# StarCoder's SecondMind SQL CLI Notepad

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/github/license/StarCoderSC/smartnotepad-cli)
![Build Status](https://github.com/StarCoderSC/smartnotepad-cli/actions/workflows/python-app.yml/badge.svg)

Welcome to **SecondMind SQL**, a simple, secure CLI notepad built with Python and SQLite. This project allows users to store and manage notes with support for tags, due dates, and user authentication.

## Features
- **User Authentication**: Register and login using username and password.
- **CRUD Operations**: Create, read, update, and delete notes.
- **Tagging and Due Dates**: Add tags to organize your notes and set due dates.
- **Export/Import**: Export notes to JSON and import from legacy text or JSON files.
- **SQLite Database**: Notes are stored in a local SQLite database for persistence.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/StarCoderSC/secondmind-sql.git

    Install dependencies:

        pip install -r requirements.txt

Initialize the database by running:

    python app.py

Usage

    Register a new user:
    When prompted, choose to register by entering a username and password.

    Create a new note:
    You can add a note with optional tags and a due date.

    View/Modify/Delete Notes:
    You can view all notes, search for specific notes by keyword or tag, and edit or delete them.

    Import and Export Notes:
    You can import legacy notes from a .txt or .json file, and export your notes as a JSON file for backup.