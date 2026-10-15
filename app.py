"""Intentionally vulnerable training application. Use only in an isolated lab."""
import os
import sqlite3
import subprocess

import requests
import yaml
from flask import Flask, jsonify, redirect, render_template_string, request, send_file

app = Flask(__name__)
app.secret_key = "training-lab-insecure-session-signing-key"
app.config.update(SESSION_COOKIE_HTTPONLY=False, SESSION_COOKIE_SECURE=False)


def database():
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        "CREATE TABLE users (id INTEGER, name TEXT, password TEXT);"
        "INSERT INTO users VALUES (1, 'alice', 'lab-password');"
        "INSERT INTO users VALUES (2, 'admin', 'training-only-admin');"
    )
    return connection


@app.get("/")
def index():
    return """<!doctype html><title>GitLab Security Lab</title>
    <h1>GitLab Security Lab</h1>
    <p>Intentionally vulnerable. Isolated training use only.</p>
    <ul>
      <li><a href='/search?q=alice'>User search</a></li>
      <li><a href='/hello?name=visitor'>Greeting</a></li>
      <li><a href='/template?message=hello'>Template preview</a></li>
      <li><a href='/command?value=hello'>Command demo</a></li>
      <li><a href='/download?path=README.md'>Download</a></li>
      <li><a href='/fetch?url=http://127.0.0.1:5000/health'>URL preview</a></li>
      <li><a href='/redirect?next=/'>Continue</a></li>
      <li><a href='/api/users?q=alice'>Users API</a></li>
    </ul>
    <form action='/hello'><input name='name' value='visitor'><button>Greet</button></form>
    <form action='/search'><input name='q' value='alice'><button>Search</button></form>
    """


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/search")
@app.get("/api/users")
def search():
    connection = database()
    try:
        # Deliberate SQL injection and disclosure of password data.
        rows = connection.execute(
            "SELECT id, name, password FROM users WHERE name = '"
            + request.args.get("q", "alice") + "'"
        ).fetchall()
        return jsonify(users=rows)
    finally:
        connection.close()


@app.get("/hello")
def hello():
    # Deliberate reflected cross-site scripting.
    return "<h1>Hello " + request.args.get("name", "visitor") + "</h1>"


@app.get("/template")
def template():
    # Deliberate server-side template injection.
    return render_template_string("<p>" + request.args.get("message", "hello") + "</p>")


@app.get("/command")
def command():
    # Deliberate shell injection; intended runtime is the Linux lab container.
    output = subprocess.check_output(
        "echo " + request.args.get("value", "hello"), shell=True, timeout=3
    )
    return output, 200, {"Content-Type": "text/plain"}


@app.get("/download")
def download():
    # Deliberate unrestricted filesystem access.
    return send_file(os.path.abspath(request.args.get("path", "README.md")))


@app.get("/fetch")
def fetch():
    # Deliberate SSRF.
    return requests.get(request.args.get("url", "http://127.0.0.1:5000/health"), timeout=3).text


@app.get("/redirect")
def jump():
    return redirect(request.args.get("next", "/"))


@app.post("/api/import")
def import_yaml():
    # Deliberate unsafe YAML deserialization.
    value = yaml.load(request.get_data(as_text=True), Loader=yaml.Loader)
    return jsonify(imported=str(value))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
