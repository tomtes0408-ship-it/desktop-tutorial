"""
שכבת מסד נתונים - Database Layer
ניהול מסד הנתונים SQLite עבור העוזר האישי
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from .config import DATABASE_PATH, DATETIME_FORMAT


class DatabaseManager:
    """
    מנהל מסד נתונים - Database Manager
    אחראי על כל הפעולות מול מסד הנתונים
    """

    def __init__(self, db_path: Optional[Path] = None):
        """אתחול מנהל מסד הנתונים"""
        self.db_path = db_path or DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def get_connection(self):
        """מחזיר חיבור למסד הנתונים עם ניהול אוטומטי"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self):
        """יצירת טבלאות מסד הנתונים"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # טבלת קטגוריות - Categories Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    name_he TEXT NOT NULL,
                    color TEXT DEFAULT 'blue',
                    icon TEXT DEFAULT '📁',
                    created_at TEXT NOT NULL
                )
            """)

            # טבלת משימות - Tasks Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    category_id INTEGER,
                    priority INTEGER DEFAULT 3,
                    status TEXT DEFAULT 'pending',
                    due_date TEXT,
                    due_time TEXT,
                    estimated_duration INTEGER,
                    actual_duration INTEGER,
                    parent_task_id INTEGER,
                    course_name TEXT,
                    tags TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
                )
            """)

            # טבלת הגשות/מטלות - Assignments Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    course_name TEXT NOT NULL,
                    assignment_type TEXT NOT NULL,
                    weight REAL,
                    submission_link TEXT,
                    grade REAL,
                    feedback TEXT,
                    submitted_at TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)

            # טבלת תזכורות - Reminders Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    title TEXT NOT NULL,
                    message TEXT,
                    remind_at TEXT NOT NULL,
                    repeat_type TEXT,
                    repeat_interval INTEGER,
                    is_active INTEGER DEFAULT 1,
                    is_triggered INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)

            # טבלת סשנים של לימוד - Study Sessions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    course_name TEXT,
                    topic TEXT,
                    planned_start TEXT NOT NULL,
                    planned_end TEXT NOT NULL,
                    actual_start TEXT,
                    actual_end TEXT,
                    status TEXT DEFAULT 'planned',
                    notes TEXT,
                    productivity_rating INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)

            # טבלת קורסים - Courses Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    code TEXT,
                    lecturer TEXT,
                    credits REAL,
                    color TEXT DEFAULT 'blue',
                    semester TEXT,
                    year INTEGER,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # טבלת לוח שנה שבועי - Weekly Schedule Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weekly_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER,
                    day_of_week INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    room TEXT,
                    schedule_type TEXT DEFAULT 'lecture',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (course_id) REFERENCES courses(id)
                )
            """)

            # טבלת יומן פעילות - Activity Log Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER,
                    description TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # טבלת הגדרות משתמש - User Settings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # יצירת אינדקסים לביצועים
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_sessions_planned_start ON study_sessions(planned_start)")

            # הוספת קטגוריות ברירת מחדל
            self._insert_default_categories(cursor)

    def _insert_default_categories(self, cursor):
        """הוספת קטגוריות ברירת מחדל"""
        default_categories = [
            ("homework", "שיעורי בית", "orange", "📝"),
            ("exam", "מבחנים", "red", "📋"),
            ("project", "פרויקטים", "purple", "🎯"),
            ("reading", "קריאה", "green", "📚"),
            ("submission", "הגשות", "yellow", "📤"),
            ("meeting", "פגישות", "blue", "👥"),
            ("personal", "אישי", "gray", "👤"),
            ("study", "לימודים", "cyan", "📖"),
        ]

        now = datetime.now().strftime(DATETIME_FORMAT)
        for name, name_he, color, icon in default_categories:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (name, name_he, color, icon, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, name_he, color, icon, now))

    # ========== פעולות משימות - Task Operations ==========

    def create_task(self, task_data: Dict[str, Any]) -> int:
        """יצירת משימה חדשה"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (
                    title, description, category_id, priority, status,
                    due_date, due_time, estimated_duration, parent_task_id,
                    course_name, tags, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data.get('title'),
                task_data.get('description'),
                task_data.get('category_id'),
                task_data.get('priority', 3),
                task_data.get('status', 'pending'),
                task_data.get('due_date'),
                task_data.get('due_time'),
                task_data.get('estimated_duration'),
                task_data.get('parent_task_id'),
                task_data.get('course_name'),
                task_data.get('tags'),
                task_data.get('notes'),
                now,
                now
            ))
            task_id = cursor.lastrowid
            self._log_activity(cursor, 'create', 'task', task_id, f"נוצרה משימה: {task_data.get('title')}")
            return task_id

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """קבלת משימה לפי מזהה"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.*, c.name_he as category_name
                FROM tasks t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.id = ?
            """, (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """קבלת כל המשימות עם אפשרות סינון"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT t.*, c.name_he as category_name
                FROM tasks t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE 1=1
            """
            params = []

            if filters:
                if filters.get('status'):
                    query += " AND t.status = ?"
                    params.append(filters['status'])
                if filters.get('category_id'):
                    query += " AND t.category_id = ?"
                    params.append(filters['category_id'])
                if filters.get('priority'):
                    query += " AND t.priority = ?"
                    params.append(filters['priority'])
                if filters.get('due_date_from'):
                    query += " AND t.due_date >= ?"
                    params.append(filters['due_date_from'])
                if filters.get('due_date_to'):
                    query += " AND t.due_date <= ?"
                    params.append(filters['due_date_to'])
                if filters.get('course_name'):
                    query += " AND t.course_name = ?"
                    params.append(filters['course_name'])
                if filters.get('parent_task_id'):
                    query += " AND t.parent_task_id = ?"
                    params.append(filters['parent_task_id'])
                if filters.get('exclude_completed'):
                    query += " AND t.status != 'completed'"

            query += " ORDER BY t.priority ASC, t.due_date ASC NULLS LAST"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_task(self, task_id: int, task_data: Dict[str, Any]) -> bool:
        """עדכון משימה"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # בניית שאילתת עדכון דינמית
            updates = []
            params = []
            for key, value in task_data.items():
                if key not in ['id', 'created_at']:
                    updates.append(f"{key} = ?")
                    params.append(value)

            if not updates:
                return False

            updates.append("updated_at = ?")
            params.append(now)
            params.append(task_id)

            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            self._log_activity(cursor, 'update', 'task', task_id, f"עודכנה משימה #{task_id}")
            return cursor.rowcount > 0

    def complete_task(self, task_id: int) -> bool:
        """סימון משימה כהושלמה"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks
                SET status = 'completed', completed_at = ?, updated_at = ?
                WHERE id = ?
            """, (now, now, task_id))
            self._log_activity(cursor, 'complete', 'task', task_id, f"הושלמה משימה #{task_id}")
            return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """מחיקת משימה"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # מחיקת תזכורות קשורות
            cursor.execute("DELETE FROM reminders WHERE task_id = ?", (task_id,))
            # מחיקת משימות בת
            cursor.execute("DELETE FROM tasks WHERE parent_task_id = ?", (task_id,))
            # מחיקת המשימה
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self._log_activity(cursor, 'delete', 'task', task_id, f"נמחקה משימה #{task_id}")
            return cursor.rowcount > 0

    def get_subtasks(self, parent_task_id: int) -> List[Dict[str, Any]]:
        """קבלת תתי-משימות של משימה"""
        return self.get_all_tasks({'parent_task_id': parent_task_id})

    # ========== פעולות תזכורות - Reminder Operations ==========

    def create_reminder(self, reminder_data: Dict[str, Any]) -> int:
        """יצירת תזכורת חדשה"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reminders (
                    task_id, title, message, remind_at,
                    repeat_type, repeat_interval, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reminder_data.get('task_id'),
                reminder_data.get('title'),
                reminder_data.get('message'),
                reminder_data.get('remind_at'),
                reminder_data.get('repeat_type'),
                reminder_data.get('repeat_interval'),
                reminder_data.get('is_active', 1),
                now
            ))
            return cursor.lastrowid

    def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """קבלת תזכורות שממתינות להפעלה"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, t.title as task_title
                FROM reminders r
                LEFT JOIN tasks t ON r.task_id = t.id
                WHERE r.is_active = 1 AND r.is_triggered = 0 AND r.remind_at <= ?
                ORDER BY r.remind_at ASC
            """, (now,))
            return [dict(row) for row in cursor.fetchall()]

    def get_upcoming_reminders(self, hours: int = 24) -> List[Dict[str, Any]]:
        """קבלת תזכורות קרובות"""
        now = datetime.now()
        future = (now + timedelta(hours=hours)).strftime(DATETIME_FORMAT)
        now_str = now.strftime(DATETIME_FORMAT)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, t.title as task_title
                FROM reminders r
                LEFT JOIN tasks t ON r.task_id = t.id
                WHERE r.is_active = 1 AND r.remind_at BETWEEN ? AND ?
                ORDER BY r.remind_at ASC
            """, (now_str, future))
            return [dict(row) for row in cursor.fetchall()]

    def mark_reminder_triggered(self, reminder_id: int) -> bool:
        """סימון תזכורת כהופעלה"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reminders SET is_triggered = 1 WHERE id = ?
            """, (reminder_id,))
            return cursor.rowcount > 0

    def delete_reminder(self, reminder_id: int) -> bool:
        """מחיקת תזכורת"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            return cursor.rowcount > 0

    # ========== פעולות הגשות - Assignment Operations ==========

    def create_assignment(self, assignment_data: Dict[str, Any]) -> int:
        """יצירת הגשה חדשה"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO assignments (
                    task_id, course_name, assignment_type, weight,
                    submission_link, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                assignment_data.get('task_id'),
                assignment_data.get('course_name'),
                assignment_data.get('assignment_type'),
                assignment_data.get('weight'),
                assignment_data.get('submission_link'),
                now
            ))
            return cursor.lastrowid

    def get_assignments(self, course_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """קבלת כל ההגשות"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if course_name:
                cursor.execute("""
                    SELECT a.*, t.title, t.due_date, t.status
                    FROM assignments a
                    JOIN tasks t ON a.task_id = t.id
                    WHERE a.course_name = ?
                    ORDER BY t.due_date ASC
                """, (course_name,))
            else:
                cursor.execute("""
                    SELECT a.*, t.title, t.due_date, t.status
                    FROM assignments a
                    JOIN tasks t ON a.task_id = t.id
                    ORDER BY t.due_date ASC
                """)
            return [dict(row) for row in cursor.fetchall()]

    def update_assignment_grade(self, assignment_id: int, grade: float, feedback: str = None) -> bool:
        """עדכון ציון להגשה"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE assignments SET grade = ?, feedback = ? WHERE id = ?
            """, (grade, feedback, assignment_id))
            return cursor.rowcount > 0

    # ========== פעולות סשני לימוד - Study Session Operations ==========

    def create_study_session(self, session_data: Dict[str, Any]) -> int:
        """יצירת סשן לימוד חדש"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO study_sessions (
                    task_id, course_name, topic, planned_start, planned_end,
                    status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_data.get('task_id'),
                session_data.get('course_name'),
                session_data.get('topic'),
                session_data.get('planned_start'),
                session_data.get('planned_end'),
                session_data.get('status', 'planned'),
                session_data.get('notes'),
                now
            ))
            return cursor.lastrowid

    def get_study_sessions(self, date_from: str = None, date_to: str = None) -> List[Dict[str, Any]]:
        """קבלת סשני לימוד"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM study_sessions WHERE 1=1"
            params = []

            if date_from:
                query += " AND planned_start >= ?"
                params.append(date_from)
            if date_to:
                query += " AND planned_start <= ?"
                params.append(date_to)

            query += " ORDER BY planned_start ASC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def start_study_session(self, session_id: int) -> bool:
        """התחלת סשן לימוד"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE study_sessions
                SET actual_start = ?, status = 'in_progress'
                WHERE id = ?
            """, (now, session_id))
            return cursor.rowcount > 0

    def end_study_session(self, session_id: int, productivity_rating: int = None) -> bool:
        """סיום סשן לימוד"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE study_sessions
                SET actual_end = ?, status = 'completed', productivity_rating = ?
                WHERE id = ?
            """, (now, productivity_rating, session_id))
            return cursor.rowcount > 0

    # ========== פעולות קורסים - Course Operations ==========

    def create_course(self, course_data: Dict[str, Any]) -> int:
        """יצירת קורס חדש"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO courses (
                    name, code, lecturer, credits, color,
                    semester, year, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                course_data.get('name'),
                course_data.get('code'),
                course_data.get('lecturer'),
                course_data.get('credits'),
                course_data.get('color', 'blue'),
                course_data.get('semester'),
                course_data.get('year'),
                course_data.get('notes'),
                now
            ))
            return cursor.lastrowid

    def get_courses(self) -> List[Dict[str, Any]]:
        """קבלת כל הקורסים"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM courses ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]

    def get_course(self, course_id: int) -> Optional[Dict[str, Any]]:
        """קבלת קורס לפי מזהה"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ========== פעולות קטגוריות - Category Operations ==========

    def get_categories(self) -> List[Dict[str, Any]]:
        """קבלת כל הקטגוריות"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories ORDER BY name_he")
            return [dict(row) for row in cursor.fetchall()]

    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """קבלת קטגוריה לפי שם"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE name = ? OR name_he = ?", (name, name))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ========== פעולות הגדרות - Settings Operations ==========

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """קבלת הגדרה"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else default

    def set_setting(self, key: str, value: str) -> bool:
        """שמירת הגדרה"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, now))
            return True

    # ========== פעולות סטטיסטיקה - Statistics Operations ==========

    def get_task_statistics(self) -> Dict[str, Any]:
        """קבלת סטטיסטיקות משימות"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # סה"כ משימות
            cursor.execute("SELECT COUNT(*) as total FROM tasks")
            total = cursor.fetchone()['total']

            # לפי סטטוס
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM tasks
                GROUP BY status
            """)
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}

            # לפי עדיפות
            cursor.execute("""
                SELECT priority, COUNT(*) as count
                FROM tasks
                WHERE status != 'completed'
                GROUP BY priority
            """)
            by_priority = {row['priority']: row['count'] for row in cursor.fetchall()}

            # משימות שהושלמו השבוע
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM tasks
                WHERE status = 'completed'
                AND completed_at >= date('now', '-7 days')
            """)
            completed_this_week = cursor.fetchone()['count']

            # משימות באיחור
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM tasks
                WHERE status NOT IN ('completed', 'cancelled')
                AND due_date < date('now')
            """)
            overdue = cursor.fetchone()['count']

            return {
                'total': total,
                'by_status': by_status,
                'by_priority': by_priority,
                'completed_this_week': completed_this_week,
                'overdue': overdue
            }

    def get_upcoming_deadlines(self, days: int = 7) -> List[Dict[str, Any]]:
        """קבלת דדליינים קרובים"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.*, c.name_he as category_name
                FROM tasks t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.status NOT IN ('completed', 'cancelled')
                AND t.due_date IS NOT NULL
                AND t.due_date <= date('now', '+' || ? || ' days')
                ORDER BY t.due_date ASC, t.priority ASC
            """, (days,))
            return [dict(row) for row in cursor.fetchall()]

    # ========== פעולות יומן - Activity Log Operations ==========

    def _log_activity(self, cursor, action_type: str, entity_type: str,
                      entity_id: int, description: str):
        """רישום פעילות ביומן"""
        now = datetime.now().strftime(DATETIME_FORMAT)
        cursor.execute("""
            INSERT INTO activity_log (action_type, entity_type, entity_id, description, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (action_type, entity_type, entity_id, description, now))

    def get_activity_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """קבלת יומן פעילות"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM activity_log
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]


# יבוא timedelta לשימוש בפונקציות
from datetime import timedelta
