from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

messages = []


@app.route("/")
def index():
    return render_template("index.html", messages=messages)


@app.route("/post", methods=["POST"])
def post():
    name = request.form.get("name", "").strip()[:20]
    content = request.form.get("content", "").strip()[:500]

    if name and content:
        messages.insert(0, {
            "name": name,
            "content": content,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)