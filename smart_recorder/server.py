"""
שרת המקליט החכם - ממשק דפדפן להקלטה, תמלול, סיכום ונקודות מפתח.

הפעלה:
    python -m smart_recorder.server          # ואז לפתוח http://localhost:5050
"""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import Flask, Response, abort, jsonify, request, send_file, send_from_directory
from werkzeug.utils import secure_filename

from .summarizer import Summarizer, SummaryError, summary_to_markdown
from .transcriber import Transcriber

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("SMART_RECORDER_DATA", BASE_DIR.parent / "data" / "smart_recorder"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_MB = int(os.environ.get("SMART_RECORDER_MAX_MB", "1024"))

app = Flask(__name__, static_folder=str(BASE_DIR / "static"), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

transcriber = Transcriber()
summarizer = Summarizer()
executor = ThreadPoolExecutor(max_workers=1)  # תמלול כבד - עבודה אחת בכל פעם
_lock = threading.Lock()


# ---------- אחסון עבודות ----------

def job_dir(job_id: str) -> Path:
    if not job_id.isalnum():
        abort(404)
    d = DATA_DIR / job_id
    if not d.is_dir():
        abort(404)
    return d


def load_job(job_id: str) -> dict:
    return json.loads((job_dir(job_id) / "job.json").read_text(encoding="utf-8"))


def save_job(job: dict) -> None:
    with _lock:
        path = DATA_DIR / job["id"] / "job.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)


def update_job(job: dict, **fields) -> None:
    job.update(fields)
    save_job(job)


# ---------- עיבוד ----------

def run_summary(job: dict) -> None:
    update_job(job, stage="summarizing", stage_label="מסכם ומחלץ נקודות מפתח...")
    try:
        summary = summarizer.summarize(
            job["transcript"]["timestamped_text"],
            output_language=job.get("summary_language") or job["transcript"]["language"],
            context=job.get("context", ""),
        )
        update_job(job, summary=summary, summary_error=None)
    except SummaryError as e:
        update_job(job, summary=None, summary_error=str(e))


def process_job(job_id: str) -> None:
    job = load_job(job_id)
    try:
        update_job(job, status="processing", stage="transcribing",
                   stage_label="מתמלל (טעינת המודל בפעם הראשונה עשויה לקחת זמן)...", progress=0)
        started = time.time()

        def on_progress(p):
            if p != job.get("progress"):
                update_job(job, progress=p, stage_label=f"מתמלל... {p}%")

        t = transcriber.transcribe(str(DATA_DIR / job_id / job["audio_file"]),
                                   language=job.get("language") or None, on_progress=on_progress)
        tdict = t.to_dict()
        tdict["timestamped_text"] = t.timestamped_text()
        update_job(job, transcript=tdict, transcribe_seconds=round(time.time() - started, 1))

        if job.get("summarize", True):
            run_summary(job)
        update_job(job, status="done", stage="done", stage_label="הושלם", progress=100)
    except Exception as e:  # noqa: BLE001 - מדווח למשתמש כל כשל
        update_job(job, status="error", stage="error", stage_label="שגיאה", error=str(e))


# ---------- נתיבים ----------

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/status")
def status():
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
                   or Path.home().joinpath(".config", "anthropic").exists())
    return jsonify(whisper_model=transcriber.model_size, claude_model=summarizer.model,
                   claude_configured=has_key, ffmpeg=bool(shutil.which("ffmpeg")))


@app.post("/api/jobs")
def create_job():
    f = request.files.get("audio")
    if not f or not f.filename:
        return jsonify(error="לא התקבל קובץ אודיו"), 400

    job_id = uuid.uuid4().hex[:12]
    d = DATA_DIR / job_id
    d.mkdir(parents=True)
    name = secure_filename(f.filename) or "recording.webm"
    ext = Path(name).suffix or ".webm"
    audio_file = f"audio{ext}"
    f.save(d / audio_file)

    job = {
        "id": job_id,
        "name": request.form.get("name") or Path(f.filename).stem or "הקלטה",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "audio_file": audio_file,
        "language": request.form.get("language", ""),
        "summary_language": request.form.get("summary_language", "he"),
        "context": request.form.get("context", "")[:2000],
        "summarize": request.form.get("summarize", "1") != "0",
        "status": "queued", "stage": "queued", "stage_label": "ממתין בתור...", "progress": 0,
        "transcript": None, "summary": None, "summary_error": None, "error": None,
    }
    save_job(job)
    executor.submit(process_job, job_id)
    return jsonify(job), 201


@app.get("/api/jobs")
def list_jobs():
    jobs = []
    for p in DATA_DIR.glob("*/job.json"):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        jobs.append({k: j.get(k) for k in ("id", "name", "created_at", "status")}
                    | {"title": (j.get("summary") or {}).get("title"),
                       "duration": (j.get("transcript") or {}).get("duration")})
    jobs.sort(key=lambda j: j["created_at"] or "", reverse=True)
    return jsonify(jobs)


@app.get("/api/jobs/<job_id>")
def get_job(job_id):
    return jsonify(load_job(job_id))


@app.delete("/api/jobs/<job_id>")
def delete_job(job_id):
    shutil.rmtree(job_dir(job_id))
    return jsonify(ok=True)


@app.post("/api/jobs/<job_id>/summarize")
def resummarize(job_id):
    job = load_job(job_id)
    if not job.get("transcript"):
        return jsonify(error="אין עדיין תמליל"), 400
    body = request.get_json(silent=True) or {}
    job["summary_language"] = body.get("summary_language", job.get("summary_language", "he"))
    job["context"] = body.get("context", job.get("context", ""))[:2000]
    update_job(job, status="processing", progress=100)

    def task():
        run_summary(job)
        update_job(job, status="done", stage="done", stage_label="הושלם")

    executor.submit(task)
    return jsonify(job), 202


@app.get("/api/jobs/<job_id>/audio")
def get_audio(job_id):
    job = load_job(job_id)
    return send_file(job_dir(job_id) / job["audio_file"], conditional=True)


@app.get("/api/jobs/<job_id>/export.<fmt>")
def export(job_id, fmt):
    job = load_job(job_id)
    t = job.get("transcript") or {}
    base = secure_filename(job.get("name", "recording")) or "recording"
    if fmt == "md":
        body = summary_to_markdown(job.get("summary") or {"title": job["name"]},
                                   t.get("timestamped_text"))
        mime = "text/markdown"
    elif fmt == "txt":
        body, mime = t.get("timestamped_text", ""), "text/plain"
    elif fmt == "srt":
        body, mime = to_srt(t.get("segments", [])), "application/x-subrip"
    elif fmt == "json":
        body, mime = json.dumps(job, ensure_ascii=False, indent=2), "application/json"
    else:
        abort(404)
    return Response(body, mimetype=f"{mime}; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{base}.{fmt}"'})


def to_srt(segments: list[dict]) -> str:
    def ts(sec: float) -> str:
        ms = int(round(sec * 1000))
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    return "\n".join(f"{i}\n{ts(s['start'])} --> {ts(s['end'])}\n{s['text']}\n"
                     for i, s in enumerate(segments, 1))


def lan_ip() -> str | None:
    """כתובת ה-IP של המחשב ברשת המקומית (לא נשלחת שום חבילה)."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return None


def main(argv=None):
    import argparse

    p = argparse.ArgumentParser(description="המקליט החכם - שרת")
    p.add_argument("--lan", action="store_true",
                   help="גישה גם מהטלפון: מאזין ברשת המקומית ב-HTTPS (נדרש להקלטה בדפדפן הטלפון)")
    p.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5050")))
    args = p.parse_args(argv)

    if args.lan:
        ip = lan_ip() or "<כתובת-המחשב>"
        print("🎙️  המקליט החכם פועל:")
        print(f"   💻 במחשב:  https://localhost:{args.port}")
        print(f"   📱 בטלפון: https://{ip}:{args.port}   (באותה רשת Wi-Fi)")
        print("   ⚠️  הדפדפן יציג אזהרת אבטחה (תעודה מקומית) - בחרו 'מתקדם' ← 'המשך לאתר'.")
        # תעודה זמנית בחתימה עצמית: דפדפני טלפון מאפשרים גישה למיקרופון רק ב-HTTPS
        app.run(host="0.0.0.0", port=args.port, threaded=True, ssl_context="adhoc")
    else:
        print(f"🎙️  המקליט החכם פועל: http://localhost:{args.port}")
        print("   📱 לגישה מהטלפון הפעילו עם --lan")
        app.run(host=os.environ.get("HOST", "127.0.0.1"), port=args.port, threaded=True)


if __name__ == "__main__":
    main()
