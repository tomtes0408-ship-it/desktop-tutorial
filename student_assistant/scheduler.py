"""
מנהל תזכורות ותזמון - Scheduler Manager
ניהול תזכורות, התראות ותזמון אוטומטי
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Callable
import json

from .database import DatabaseManager
from .models import Task, Reminder
from .config import (
    MESSAGES, DATE_FORMAT, DATETIME_FORMAT, TIME_FORMAT,
    REMINDER_DEFAULTS, WEEKDAYS_HE
)


class SchedulerManager:
    """
    מנהל תזכורות - Scheduler Manager
    אחראי על תזכורות, התראות ותזמון
    """

    def __init__(self, db: Optional[DatabaseManager] = None):
        """אתחול המתזמן"""
        self.db = db or DatabaseManager()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._running = False
        self._notification_callback: Optional[Callable] = None
        self._check_interval = 60  # בדיקה כל דקה

    # ========== ניהול תזכורות - Reminder Management ==========

    def create_reminder(
        self,
        title: str,
        remind_at: str,
        message: str = None,
        task_id: int = None,
        repeat_type: str = None,
        repeat_interval: int = None
    ) -> Tuple[bool, str, Optional[Reminder]]:
        """
        יצירת תזכורת חדשה

        Args:
            title: כותרת התזכורת
            remind_at: זמן תזכורת (DD/MM/YYYY HH:MM)
            message: הודעה
            task_id: מזהה משימה מקושרת
            repeat_type: סוג חזרה (daily, weekly, monthly)
            repeat_interval: מרווח חזרה

        Returns:
            (success, message, reminder)
        """
        # ולידציית זמן
        try:
            remind_dt = datetime.strptime(remind_at, DATETIME_FORMAT)
        except ValueError:
            return False, MESSAGES['invalid_date'] + " " + MESSAGES['invalid_time'], None

        # בדיקה שהזמן בעתיד
        if remind_dt <= datetime.now():
            return False, "❌ זמן התזכורת חייב להיות בעתיד", None

        reminder_data = {
            'title': title,
            'message': message,
            'remind_at': remind_at,
            'task_id': task_id,
            'repeat_type': repeat_type,
            'repeat_interval': repeat_interval,
            'is_active': 1
        }

        try:
            reminder_id = self.db.create_reminder(reminder_data)
            return True, MESSAGES['reminder_set'], Reminder(
                id=reminder_id,
                **reminder_data
            )
        except Exception as e:
            return False, f"❌ שגיאה ביצירת תזכורת: {str(e)}", None

    def create_task_reminder(
        self,
        task_id: int,
        remind_before_minutes: int = 60
    ) -> Tuple[bool, str, Optional[Reminder]]:
        """
        יצירת תזכורת למשימה

        Args:
            task_id: מזהה המשימה
            remind_before_minutes: דקות לפני הדדליין

        Returns:
            (success, message, reminder)
        """
        task_data = self.db.get_task(task_id)
        if not task_data:
            return False, MESSAGES['task_not_found'], None

        task = Task.from_dict(task_data)

        if not task.due_date:
            return False, "❌ למשימה זו אין תאריך יעד", None

        # חישוב זמן תזכורת
        try:
            if task.due_time:
                due_str = f"{task.due_date} {task.due_time}"
            else:
                due_str = f"{task.due_date} 09:00"

            due_dt = datetime.strptime(due_str, DATETIME_FORMAT)
            remind_dt = due_dt - timedelta(minutes=remind_before_minutes)

            if remind_dt <= datetime.now():
                return False, "❌ זמן התזכורת כבר עבר", None

            return self.create_reminder(
                title=f"תזכורת: {task.title}",
                remind_at=remind_dt.strftime(DATETIME_FORMAT),
                message=f"נותרו {remind_before_minutes} דקות לדדליין",
                task_id=task_id
            )
        except ValueError:
            return False, "❌ שגיאה בחישוב זמן תזכורת", None

    def create_deadline_reminders(
        self,
        task_id: int,
        days_before: List[int] = None
    ) -> Tuple[bool, str, List[Reminder]]:
        """
        יצירת תזכורות דדליין למשימה

        Args:
            task_id: מזהה המשימה
            days_before: רשימת ימים לפני הדדליין

        Returns:
            (success, message, reminders)
        """
        if days_before is None:
            days_before = REMINDER_DEFAULTS['deadline_warning_days']

        task_data = self.db.get_task(task_id)
        if not task_data:
            return False, MESSAGES['task_not_found'], []

        task = Task.from_dict(task_data)

        if not task.due_date:
            return False, "❌ למשימה זו אין תאריך יעד", []

        reminders = []
        try:
            due_dt = datetime.strptime(task.due_date, DATE_FORMAT)

            for days in days_before:
                remind_dt = due_dt - timedelta(days=days)

                # דילוג אם התאריך כבר עבר
                if remind_dt.date() < datetime.now().date():
                    continue

                # הגדרת שעת תזכורת
                remind_dt = remind_dt.replace(hour=9, minute=0)

                if remind_dt <= datetime.now():
                    continue

                # יצירת הודעה מתאימה
                if days == 0:
                    message = f"היום הדדליין של '{task.title}'!"
                    title = f"🚨 דדליין היום: {task.title}"
                elif days == 1:
                    message = f"מחר הדדליין של '{task.title}'!"
                    title = f"⚠️ דדליין מחר: {task.title}"
                else:
                    message = f"נותרו {days} ימים לדדליין של '{task.title}'"
                    title = f"📅 תזכורת דדליין: {task.title}"

                success, msg, reminder = self.create_reminder(
                    title=title,
                    remind_at=remind_dt.strftime(DATETIME_FORMAT),
                    message=message,
                    task_id=task_id
                )

                if success and reminder:
                    reminders.append(reminder)

            if reminders:
                return True, f"✅ נוצרו {len(reminders)} תזכורות דדליין", reminders
            else:
                return False, "❌ לא נוצרו תזכורות (ייתכן שהתאריכים כבר עברו)", []

        except ValueError:
            return False, "❌ שגיאה בפורמט תאריך", []

    def get_pending_reminders(self) -> List[Reminder]:
        """קבלת תזכורות שממתינות להפעלה"""
        reminders_data = self.db.get_pending_reminders()
        return [Reminder.from_dict(r) for r in reminders_data]

    def get_upcoming_reminders(self, hours: int = 24) -> List[Reminder]:
        """קבלת תזכורות קרובות"""
        reminders_data = self.db.get_upcoming_reminders(hours)
        return [Reminder.from_dict(r) for r in reminders_data]

    def delete_reminder(self, reminder_id: int) -> Tuple[bool, str]:
        """מחיקת תזכורת"""
        try:
            self.db.delete_reminder(reminder_id)
            return True, "✅ תזכורת נמחקה"
        except Exception as e:
            return False, f"❌ שגיאה: {str(e)}"

    def delete_task_reminders(self, task_id: int) -> Tuple[bool, str]:
        """מחיקת כל התזכורות של משימה"""
        reminders = self.get_all_reminders()
        count = 0

        for r in reminders:
            if r.task_id == task_id:
                self.db.delete_reminder(r.id)
                count += 1

        return True, f"✅ נמחקו {count} תזכורות"

    def get_all_reminders(self, active_only: bool = True) -> List[Reminder]:
        """קבלת כל התזכורות"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("""
                    SELECT r.*, t.title as task_title
                    FROM reminders r
                    LEFT JOIN tasks t ON r.task_id = t.id
                    WHERE r.is_active = 1
                    ORDER BY r.remind_at ASC
                """)
            else:
                cursor.execute("""
                    SELECT r.*, t.title as task_title
                    FROM reminders r
                    LEFT JOIN tasks t ON r.task_id = t.id
                    ORDER BY r.remind_at ASC
                """)
            return [Reminder.from_dict(dict(row)) for row in cursor.fetchall()]

    # ========== התראות דדליין - Deadline Alerts ==========

    def check_deadlines(self) -> List[Dict[str, Any]]:
        """
        בדיקת דדליינים קרובים ויצירת התראות

        Returns:
            רשימת התראות
        """
        alerts = []
        today = datetime.now().date()

        # קבלת משימות עם דדליינים
        deadlines = self.db.get_upcoming_deadlines(days=7)

        for task_data in deadlines:
            task = Task.from_dict(task_data)

            if not task.due_date:
                continue

            try:
                due = datetime.strptime(task.due_date, DATE_FORMAT).date()
                days_until = (due - today).days

                alert = {
                    'task_id': task.id,
                    'task_title': task.title,
                    'due_date': task.due_date,
                    'days_until': days_until,
                    'priority': task.priority,
                    'course_name': task.course_name
                }

                if days_until < 0:
                    alert['type'] = 'overdue'
                    alert['message'] = MESSAGES['deadline_passed'].format(task.title)
                    alert['urgency'] = 'critical'
                elif days_until == 0:
                    alert['type'] = 'today'
                    alert['message'] = MESSAGES['deadline_today'].format(task.title)
                    alert['urgency'] = 'high'
                elif days_until <= 3:
                    alert['type'] = 'approaching'
                    alert['message'] = MESSAGES['deadline_warning'].format(days_until, task.title)
                    alert['urgency'] = 'medium'
                else:
                    alert['type'] = 'upcoming'
                    alert['message'] = f"📅 {task.title} - עוד {days_until} ימים"
                    alert['urgency'] = 'low'

                alerts.append(alert)

            except ValueError:
                continue

        # מיון לפי דחיפות
        urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        alerts.sort(key=lambda x: (urgency_order.get(x.get('urgency', 'low'), 4), x.get('days_until', 999)))

        return alerts

    def get_daily_briefing(self) -> Dict[str, Any]:
        """
        קבלת תדריך יומי

        Returns:
            תדריך עם כל המידע הרלוונטי להיום
        """
        today = datetime.now()
        today_str = today.strftime(DATE_FORMAT)

        briefing = {
            'date': today_str,
            'day_name': WEEKDAYS_HE[today.weekday()],
            'tasks_today': [],
            'deadlines_today': [],
            'overdue_tasks': [],
            'reminders_today': [],
            'upcoming_deadlines': [],
            'summary': {}
        }

        # משימות להיום
        today_tasks = self.db.get_all_tasks({
            'due_date_from': today_str,
            'due_date_to': today_str,
            'exclude_completed': True
        })
        briefing['tasks_today'] = [Task.from_dict(t) for t in today_tasks]

        # דדליינים להיום
        briefing['deadlines_today'] = [
            t for t in briefing['tasks_today']
            if t.due_date == today_str
        ]

        # משימות באיחור
        overdue = self.db.get_all_tasks({'exclude_completed': True})
        briefing['overdue_tasks'] = [
            Task.from_dict(t) for t in overdue
            if t.get('due_date') and t['due_date'] < today_str
        ]

        # תזכורות להיום
        tomorrow = (today + timedelta(days=1)).strftime(DATE_FORMAT)
        reminders = self.get_upcoming_reminders(24)
        briefing['reminders_today'] = reminders

        # דדליינים קרובים (שבוע הבא)
        upcoming = self.db.get_upcoming_deadlines(7)
        briefing['upcoming_deadlines'] = [Task.from_dict(t) for t in upcoming]

        # סיכום
        briefing['summary'] = {
            'tasks_count': len(briefing['tasks_today']),
            'deadlines_count': len(briefing['deadlines_today']),
            'overdue_count': len(briefing['overdue_tasks']),
            'reminders_count': len(briefing['reminders_today']),
            'upcoming_count': len(briefing['upcoming_deadlines'])
        }

        return briefing

    # ========== תזמון רקע - Background Scheduling ==========

    def set_notification_callback(self, callback: Callable[[Reminder], None]):
        """
        הגדרת פונקציית callback להתראות

        Args:
            callback: פונקציה שתיקרא כאשר מגיעה תזכורת
        """
        self._notification_callback = callback

    def start_scheduler(self):
        """התחלת שירות התזמון ברקע"""
        if self._running:
            return

        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def stop_scheduler(self):
        """עצירת שירות התזמון"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)

    def _scheduler_loop(self):
        """לולאת התזמון הראשית"""
        while self._running:
            try:
                self._check_and_trigger_reminders()
            except Exception as e:
                print(f"שגיאה בתזמון: {e}")

            time.sleep(self._check_interval)

    def _check_and_trigger_reminders(self):
        """בדיקה והפעלת תזכורות"""
        pending = self.get_pending_reminders()

        for reminder in pending:
            # סימון כהופעל
            self.db.mark_reminder_triggered(reminder.id)

            # קריאה ל-callback אם קיים
            if self._notification_callback:
                try:
                    self._notification_callback(reminder)
                except Exception as e:
                    print(f"שגיאה בהתראה: {e}")

            # טיפול בתזכורות חוזרות
            if reminder.repeat_type and reminder.repeat_type != 'none':
                self._schedule_next_repeat(reminder)

    def _schedule_next_repeat(self, reminder: Reminder):
        """תזמון החזרה הבאה של תזכורת"""
        try:
            current = datetime.strptime(reminder.remind_at, DATETIME_FORMAT)
            next_time = None

            if reminder.repeat_type == 'daily':
                next_time = current + timedelta(days=reminder.repeat_interval or 1)
            elif reminder.repeat_type == 'weekly':
                next_time = current + timedelta(weeks=reminder.repeat_interval or 1)
            elif reminder.repeat_type == 'monthly':
                # הוספת חודש
                month = current.month + (reminder.repeat_interval or 1)
                year = current.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                next_time = current.replace(year=year, month=month)

            if next_time:
                self.create_reminder(
                    title=reminder.title,
                    remind_at=next_time.strftime(DATETIME_FORMAT),
                    message=reminder.message,
                    task_id=reminder.task_id,
                    repeat_type=reminder.repeat_type,
                    repeat_interval=reminder.repeat_interval
                )

        except Exception as e:
            print(f"שגיאה בתזמון חזרה: {e}")

    # ========== תזכורות מהירות - Quick Reminders ==========

    def remind_in_minutes(
        self,
        title: str,
        minutes: int,
        message: str = None,
        task_id: int = None
    ) -> Tuple[bool, str, Optional[Reminder]]:
        """
        יצירת תזכורת בעוד X דקות

        Args:
            title: כותרת
            minutes: מספר דקות
            message: הודעה
            task_id: מזהה משימה

        Returns:
            (success, message, reminder)
        """
        remind_at = (datetime.now() + timedelta(minutes=minutes)).strftime(DATETIME_FORMAT)
        return self.create_reminder(title, remind_at, message, task_id)

    def remind_in_hours(
        self,
        title: str,
        hours: int,
        message: str = None,
        task_id: int = None
    ) -> Tuple[bool, str, Optional[Reminder]]:
        """
        יצירת תזכורת בעוד X שעות

        Args:
            title: כותרת
            hours: מספר שעות
            message: הודעה
            task_id: מזהה משימה

        Returns:
            (success, message, reminder)
        """
        remind_at = (datetime.now() + timedelta(hours=hours)).strftime(DATETIME_FORMAT)
        return self.create_reminder(title, remind_at, message, task_id)

    def remind_tomorrow(
        self,
        title: str,
        time_str: str = "09:00",
        message: str = None,
        task_id: int = None
    ) -> Tuple[bool, str, Optional[Reminder]]:
        """
        יצירת תזכורת למחר

        Args:
            title: כותרת
            time_str: שעה (HH:MM)
            message: הודעה
            task_id: מזהה משימה

        Returns:
            (success, message, reminder)
        """
        tomorrow = datetime.now() + timedelta(days=1)
        try:
            hour, minute = map(int, time_str.split(':'))
            remind_dt = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return self.create_reminder(title, remind_dt.strftime(DATETIME_FORMAT), message, task_id)
        except ValueError:
            return False, MESSAGES['invalid_time'], None

    # ========== ייצוא תזכורות - Export Reminders ==========

    def export_reminders_to_json(self, filepath: str) -> Tuple[bool, str]:
        """ייצוא תזכורות לקובץ JSON"""
        try:
            reminders = self.get_all_reminders(active_only=False)
            data = [
                {
                    'id': r.id,
                    'title': r.title,
                    'message': r.message,
                    'remind_at': r.remind_at,
                    'task_id': r.task_id,
                    'repeat_type': r.repeat_type,
                    'is_active': r.is_active,
                    'is_triggered': r.is_triggered
                }
                for r in reminders
            ]

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True, f"✅ יוצאו {len(data)} תזכורות"
        except Exception as e:
            return False, f"❌ שגיאה בייצוא: {str(e)}"
