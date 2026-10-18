import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("agent_app", ROOT / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        app.DB = Path(self.temp.name) / "test.sqlite3"
        app.init_db()
        app.paused = False
        app.running.clear()

    def tearDown(self):
        self.temp.cleanup()

    def test_initial_state(self):
        self.assertEqual(app.setting("daily_task_limit"), "20")
        self.assertEqual(app.query("SELECT count(*) AS n FROM tasks")[0]["n"], 0)

    def test_roles_validated(self):
        with self.assertRaises(ValueError):
            app.new_task("unknown", "test goal")
        with self.assertRaises(ValueError):
            app.new_task("general", "x")

    def test_task_and_memory(self):
        task = app.new_task("research", "Test renewable energy sources")
        self.assertEqual(app.query("SELECT status FROM tasks WHERE id=?", (task,))[0]["status"], "queued")
        app.complete(task, "completed", "Conclusions with uncertainty.", input_tokens=12, output_tokens=20)
        self.assertEqual(app.query("SELECT count(*) AS n FROM memory")[0]["n"], 1)
        self.assertEqual(app.query("SELECT output_tokens FROM tasks WHERE id=?", (task,))[0]["output_tokens"], 20)

    def test_daily_cap(self):
        with app.connect() as con:
            con.execute("UPDATE settings SET value='1' WHERE key='daily_task_limit'")
        app.new_task("general", "First task")
        with self.assertRaisesRegex(ValueError, "limit"):
            app.new_task("general", "Second task")

    def test_missing_key_fails_honestly(self):
        task = app.new_task("general", "Summarize my plan")
        with patch.dict(os.environ, {}, clear=True):
            app.process(task)
        state = app.query("SELECT status,error FROM tasks WHERE id=?", (task,))[0]
        self.assertEqual(state["status"], "failed")
        self.assertIn("OPENAI_API_KEY", state["error"])
        self.assertEqual(app.query("SELECT count(*) AS n FROM memory")[0]["n"], 0)

    def test_model_stub_path(self):
        task = app.new_task("research", "Investigate grid storage")
        with patch.object(app, "model_request", return_value=("Answer with evidence", 30, 10)):
            app.process(task)
        self.assertEqual(app.query("SELECT status FROM tasks WHERE id=?", (task,))[0]["status"], "completed")
        self.assertEqual(app.query("SELECT content FROM memory")[0]["content"], "Answer with evidence")

    def test_pause_prevents_running(self):
        task = app.new_task("general", "Something useful")
        app.paused = True
        with patch.object(app, "model_request") as model:
            app.process(task)
            model.assert_not_called()
        self.assertEqual(app.query("SELECT status FROM tasks WHERE id=?", (task,))[0]["status"], "queued")


if __name__ == "__main__":
    unittest.main()
