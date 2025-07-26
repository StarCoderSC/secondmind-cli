# StarCoder's SecondMind SQL CLI Notepad

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Last Commit](https://img.shields.io/github/last-commit/StarCoderSC/secondmind-cli)
![Repo Size](https://img.shields.io/github/repo-size/StarCoderSC/secondmind-cli)

[![Build Status](https://github.com/StarCoderSC/secondmind-cli/actions/workflows/python-app.yml/badge.svg)](https://github.com/StarCoderSC/secondmind-cli/actions)
[![Code Coverage](https://codecov.io/gh/StarCoderSC/secondmind-cli/main/graph/badge.svg)](https://codecov.io/gh/StarCoderSC/secondmind-cli)
[![Linting](https://img.shields.io/badge/linting-flake8-blue)](https://flake8.pycqa.org/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)


SecondMind SQL is a secure, colorful CLI notepad built in Python using SQLite.
It supports user authentication, note tagging, due-date reminders, import/export, and more.

---

## 🚀 Features

- 🧾 **SQLite-backed Note Storage**
- 🔐 **SHA256-based User Login/Register**
- 🏷️ **Tag Filtering**
- 📆 **Due Date Alerts**
- 📥 **Import from .txt / .json**
- 📤 **Export to .json**
- 🌈 **Rich-powered Colorful TUI**
- ✅ **CI via GitHub Actions + Test Coverage**

---

## 📦 Installation
1. **Clone this repo**
    ```bash
    git clone https://github.com/StarCoderSC/secondmind-cli.git
    cd secondmind-cli
    pip install -r requirements.txt
    python core.py  # Launches the CLI and initializes the database

🧑‍💻 Usage
🔐 Register/Login

You’ll be prompted in the terminal to register a username/password
(securely hashed with SHA256 and stored in users.txt).
📝 Note Operations

    Add notes with optional #tags and due dates (YYYY-MM-DD)

    View, update, or delete notes

    Filter notes by keyword or tag

📤 Export & 📥 Import

    Export all notes to JSON

    Import legacy notes from .txt or .json files

🗺️ Roadmap

AES Encryption support for notes

Tag autocomplete

    CLI installation via pip install secondmind

📄 License

This project is licensed under the MIT License.
See the LICENSE file or choosealicense.com/licenses/mit for full details.
🙌 Acknowledgements

    Built with 💻 Python, 💾 SQLite, and 🎨 Rich

    Auth powered by hashlib

    Tested with pytest, CI via GitHub Actions, and coverage powered by pytest-cov

📈 Contributions Welcome

Pull requests, issues, and suggestions are welcome!
If you find a bug or have an idea to improve SecondMind, don't hesitate to open an issue.

    Made with patience, perseverance, and Python – by StarCoder.
