# StarCoder's SecondMind SQL CLI Notepad

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/github/license/StarCoderSC/secondmind-cli)
![Build Status](https://github.com/StarCoderSC/secondmind-cli/actions/workflows/python-app.yml/badge.svg)
[![codecov](https://codecov.io/gh/StarCoderSC/secondmind-cli/main/graph/badge.svg)](https://codecov.io/gh/StarCoderSC/secondmind-cli)

Welcome to **SecondMind SQL**, a simple, secure CLI notepad built with Python and SQLite. This project allows users to store and manage notes with support for tags, due dates, and user authentication.

- 🧾 SQLite database storage
- 🏷️ Tag filtering
- 📆 Due date reminders
- 🔐 User login/register (SHA256-hashed)
- 📥 Import from TXT/JSON
- 📤 Export to JSON
- 🌈 Rich-powered colorful TUI
- ✅ GitHub Actions CI for code linting


## Features
- **User Authentication**: Register and login using username and password.
- **CRUD Operations**: Create, read, update, and delete notes.
- **Tagging and Due Dates**: Add tags to organize your notes and set due dates.
- **Export/Import**: Export notes to JSON and import from legacy text or JSON files.
- **SQLite Database**: Notes are stored in a local SQLite database for persistence.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/StarCoderSC/secondmind-cli.git

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

🔐 Auth System

    Stores credentials hashed using SHA256

    User login and registration via terminal

    Credentials saved to users.txt

📤 Export / 📥 Import

    Supports legacy .txt and .json imports

    JSON backup/export via CLI

🛠 Roadmap

Encryption support

Tag autocomplete

    Turn into installable CLI tool

📄 License

MIT License – See LICENSE file


---

## 📜 LICENSE (MIT)

```txt
MIT License

Copyright (c) 2025 StarCoder

Permission is hereby granted, free of charge, to any person obtaining a copy
...
(Use `https://choosealicense.com/licenses/mit/` for full version.)