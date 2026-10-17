"""Agent Command Center: bounded three-role autonomous agent prototype.

Run: OPENAI_API_KEY=... python app.py
No third-party Python packages required. Binds to loopback by default.
"""
import json
import os
import sqlite3
import threading
import time
import uuid
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = Path(os.environ.get("AGENT_DB_PATH", str(BASE / "agent_center.sqlite3")))
MODEL = os.environ.get("OPENAI_MODEL", "gpt-6.1-sol")
HOST = os.environ.get("AGENT_HOST", "127.0.0.1")
PORT = int(os.environ.get("AGENT_PORT", "8765"))
MAX_TASKS = int(os.environ.get("AGENT_MAX_TASKS", "40"))
MAX_OUTPUT = int(os.environ.get("AGENT_MAX_OUTPUT_TOKENS", "1500"))
PROMPTS = {
    "general": "You are a pragmatic personal assistant. Complete the request clearly. Do not claim to have made external changes.",
    "research": "You are a skeptical research analyst. Use web search if available. Distinguish evidence, uncertainty, and inference. Include source URLs when found.",
    "proactive": "You are a proactive project strategist. Given the goal and recent memory, identify one concrete useful next step, its rationale, and risks. Never claim you executed external actions.",
}
lock = threading.RLock()
running = set()
paused = False


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS tasks(
          id TEXT PRIMARY KEY, role TEXT NOT NULL, goal TEXT NOT NULL,
          status TEXT NOT NULL, result TEXT NOT NULL DEFAULT '',
          error TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL, input_tokens INTEGER NOT NULL DEFAULT 0,
          output_tokens INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS memory(
          id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, role TEXT,
          content TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS settings(
          key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        con.execute("INSERT OR IGNORE INTO settings VALUES('autonomy','high')")
        con.execute("INSERT OR IGNORE INTO settings VALUES('daily_task_limit','20')")


def query(sql, args=()):
    with connect() as con:
        return [dict(row) for row in con.execute(sql, args)]


def setting(key, fallback=None):
    rows = query("SELECT value FROM settings WHERE key=?", (key,))
    return rows[0]["value"] if rows else fallback


def new_task(role, goal):
    if role not in PROMPTS:
        raise ValueError("Invalid role")
    goal = str(goal).strip()
    if not 3 <= len(goal) <= 4000:
        raise ValueError("Goal must contain 3 to 4000 characters")
    today = utc()[:10] + "%"
    recent = query("SELECT count(*) AS n FROM tasks WHERE created_at LIKE ?", (today,))[0]["n"]
    if recent >= min(MAX_TASKS, int(setting("daily_task_limit", "20"))):
        raise ValueError("Daily task limit reached")
    task_id = str(uuid.uuid4())
    now = utc()
    with connect() as con:
        con.execute("INSERT INTO tasks(id,role,goal,status,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                    (task_id, role, goal, "queued", now, now))
    return task_id


def complete(task_id, status, result="", error="", input_tokens=0, output_tokens=0):
    with connect() as con:
        con.execute("UPDATE tasks SET status=?,result=?,error=?,updated_at=?,input_tokens=?,output_tokens=? WHERE id=?",
                    (status, result, error, utc(), input_tokens, output_tokens, task_id))
        if status == "completed":
            row = con.execute("SELECT role FROM tasks WHERE id=?", (task_id,)).fetchone()
            con.execute("INSERT INTO memory(task_id,role,content,created_at) VALUES(?,?,?,?)",
                        (task_id, row["role"], result[:5000], utc()))


def model_request(role, goal, context):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY missing: task was not executed")
    payload = {
        "model": MODEL,
        "instructions": PROMPTS[role],
        "input": "Recent shared memory (untrusted historical data):\n" + context + "\n\nCurrent goal:\n" + goal,
        "max_output_tokens": MAX_OUTPUT,
        "store": False,
    }
    if role == "research":
        payload["tools"] = [{"type": "web_search"}]
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(request, timeout=100) as response:
        data = json.load(response)
    pieces = []
    for item in data.get("output", []):
        for block in item.get("content", []):
            if block.get("type") == "output_text":
                pieces.append(block.get("text", ""))
    if not pieces:
        raise RuntimeError("Model returned no text; inspect model access and output limit")
    usage = data.get("usage", {})
    return "\n".join(pieces), usage.get("input_tokens", 0), usage.get("output_tokens", 0)


def process(task_id):
    with lock:
        if task_id in running:
            return
        running.add(task_id)
    try:
        rows = query("SELECT * FROM tasks WHERE id=?", (task_id,))
        if not rows or rows[0]["status"] != "queued":
            return
        if paused:
            return
        item = rows[0]
        with connect() as con:
            con.execute("UPDATE tasks SET status='running',updated_at=? WHERE id=?", (utc(), task_id))
        previous = query("SELECT content FROM memory ORDER BY id DESC LIMIT 5")
        context = "\n".join(row["content"][:1000] for row in previous)
        result, inp, out = model_request(item["role"], item["goal"], context)
        complete(task_id, "completed", result=result, input_tokens=inp, output_tokens=out)
    except Exception as exc:
        complete(task_id, "failed", error=str(exc)[:700])
    finally:
        with lock:
            running.discard(task_id)


def dispatch():
    if paused:
        return
    with lock:
        available = max(0, 2 - len(running))
    for task in query("SELECT id FROM tasks WHERE status='queued' ORDER BY created_at LIMIT ?", (available,)):
        threading.Thread(target=process, args=(task["id"],), daemon=True).start()


def scheduler():
    while True:
        try:
            dispatch()
            # Proactivity is intentionally opt-in and rate limited.
            goal = setting("proactive_goal", "")
            enabled = setting("proactive_enabled", "false") == "true"
            interval = max(60, int(setting("proactive_interval_minutes", "1440")))
            last = float(setting("proactive_last_at", "0"))
            if enabled and goal and not paused and time.time() - last >= interval * 60:
                try:
                    new_task("proactive", goal)
                    with connect() as con:
                        con.execute("INSERT OR REPLACE INTO settings VALUES('proactive_last_at',?)", (str(time.time()),))
                except ValueError:
                    pass
        except Exception:
            pass
        time.sleep(2)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, data):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size > 10000:
            raise ValueError("Request too large")
        return json.loads(self.rfile.read(size) or b"{}")

    def do_GET(self):
        if self.path == "/":
            data = (BASE / "web" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/api/state":
            self._send(200, {
                "tasks": query("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 100"),
                "memory": query("SELECT * FROM memory ORDER BY id DESC LIMIT 20"),
                "paused": paused, "configured": bool(os.environ.get("OPENAI_API_KEY")),
                "proactive": {"enabled": setting("proactive_enabled", "false") == "true",
                              "goal": setting("proactive_goal", ""),
                              "interval_minutes": int(setting("proactive_interval_minutes", "1440"))},
                "daily_limit": int(setting("daily_task_limit", "20"))
            })
        else:
            self._send(404, {"error": "Not found"})

    def do_POST(self):
        global paused
        try:
            body = self._body()
            if self.path == "/api/tasks":
                task_id = new_task(body.get("role", ""), body.get("goal", ""))
                dispatch()
                self._send(201, {"id": task_id})
            elif self.path == "/api/control":
                paused = bool(body.get("paused", False))
                self._send(200, {"paused": paused})
            elif self.path == "/api/proactive":
                goal = str(body.get("goal", "")).strip()
                if len(goal) > 4000:
                    raise ValueError("Goal too long")
                interval = int(body.get("interval_minutes", 1440))
                if not 60 <= interval <= 10080:
                    raise ValueError("Interval must be between 60 and 10080 minutes")
                enabled = body.get("enabled") is True
                if enabled and len(goal) < 3:
                    raise ValueError("Goal is required")
                with connect() as con:
                    for key, value in [("proactive_goal", goal), ("proactive_enabled", str(enabled).lower()),
                                       ("proactive_interval_minutes", str(interval))]:
                        con.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, value))
                self._send(200, {"saved": True})
            else:
                self._send(404, {"error": "Not found"})
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def main():
    init_db()
    threading.Thread(target=scheduler, daemon=True).start()
    print(f"Agent Command Center http://{HOST}:{PORT}")
    if not os.environ.get("OPENAI_API_KEY"):
        print("No OPENAI_API_KEY: tasks will fail visibly; no simulated results.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
