from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "你好，这是 James 的留言板！"


if __name__ == "__main__":
    app.run(debug=True)