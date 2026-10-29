import sqlite3
from datetime import datetime
from pathlib import Path

from flask import (Flask, abort, g, redirect, render_template, request,
                   session, url_for)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile("config.py")
app.config.update(SESSION_COOKIE_SAMESITE="Lax")
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")

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


@app.errorhandler(429)
def too_many_requests(e):
    return render_template("429.html"), 429


@app.route("/")
def index():
    messages = get_db().execute(
        "SELECT id, name, content, created_at FROM messages ORDER BY id DESC"
    ).fetchall()
    return render_template("index.html", messages=messages)


@app.route("/post", methods=["POST"])
@limiter.limit("5 per minute; 30 per day")
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


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
def login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if check_password_hash(app.config["ADMIN_PASSWORD_HASH"], password):
            session.clear()
            session["admin"] = True
            return redirect(url_for("index"))
        error = "密码错误"
    return render_template("login.html", error=error)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/delete/<int:message_id>", methods=["POST"])
def delete(message_id):
    if not session.get("admin"):
        abort(403)
    db = get_db()
    db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    db.commit()
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)