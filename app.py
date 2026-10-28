import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for

app = Flask(__name__)

DATABASE = Path(__file__).parent / "guestbook.db"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()


@app.route("/")
def index():
    messages = get_db().execute(
        "SELECT name, content, created_at FROM messages ORDER BY id DESC"
    ).fetchall()
    return render_template("index.html", messages=messages)


@app.route("/post", methods=["POST"])
def post():
    name = request.form.get("name", "").strip()[:20]
    content = request.form.get("content", "").strip()[:500]

    if name and content:
        db = get_db()
        db.execute(
            "INSERT INTO messages (name, content, created_at) VALUES (?, ?, ?)",
            (name, content, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()

    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)