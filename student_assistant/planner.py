"""
מתכנן לימודים - Study Planner
ניהול לוח זמנים, סשני לימוד ותכנון אוטומטי
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import random

from .database import DatabaseManager
from .models import Task, StudySession, Course, WeeklyScheduleEntry
from .config import (
    MESSAGES, DATE_FORMAT, DATETIME_FORMAT, TIME_FORMAT,
    WEEKDAYS_HE, MONTHS_HE, STUDY_TIPS, REMINDER_DEFAULTS
)


class StudyPlanner:
    """
    מתכנן לימודים - Study Planner
    מספק כלים לתכנון לימודים, סשנים ולוח זמנים
    """

    def __init__(self, db: Optional[DatabaseManager] = None):
        """אתחול המתכנן"""
        self.db = db or DatabaseManager()

    # ========== ניהול קורסים - Course Management ==========

    def create_course(
        self,
        name: str,
        code: str = None,
        lecturer: str = None,
        credits: float = None,
        color: str = "blue",
        semester: str = None,
        year: int = None,
        notes: str = None
    ) -> Tuple[bool, str, Optional[Course]]:
        """
        יצירת קורס חדש

        Args:
            name: שם הקורס
            code: קוד הקורס
            lecturer: שם המרצה
            credits: נקודות זכות
            color: צבע
            semester: סמסטר
            year: שנה
            notes: הערות

        Returns:
            (success, message, course)
        """
        if not name or not name.strip():
            return False, "❌ חובה להזין שם לקורס", None

        course_data = {
            'name': name.strip(),
            'code': code,
            'lecturer': lecturer,
            'credits': credits,
            'color': color,
            'semester': semester,
            'year': year,
            'notes': notes
        }

        try:
            course_id = self.db.create_course(course_data)
            course = self.get_course(course_id)
            return True, "✅ קורס נוצר בהצלחה!", course
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                return False, "❌ קורס עם שם זה כבר קיים", None
            return False, f"❌ שגיאה ביצירת קורס: {str(e)}", None

    def get_course(self, course_id: int) -> Optional[Course]:
        """קבלת קורס לפי מזהה"""
        data = self.db.get_course(course_id)
        return Course.from_dict(data) if data else None

    def get_all_courses(self) -> List[Course]:
        """קבלת כל הקורסים"""
        courses_data = self.db.get_courses()
        return [Course.from_dict(c) for c in courses_data]

    # ========== ניהול סשני לימוד - Study Session Management ==========

    def create_study_session(
        self,
        planned_start: str,
        duration_minutes: int,
        course_name: str = None,
        topic: str = None,
        task_id: int = None,
        notes: str = None
    ) -> Tuple[bool, str, Optional[StudySession]]:
        """
        יצירת סשן לימוד

        Args:
            planned_start: זמן התחלה מתוכנן (DD/MM/YYYY HH:MM)
            duration_minutes: משך בדקות
            course_name: שם הקורס
            topic: נושא הלימוד
            task_id: מזהה משימה מקושרת
            notes: הערות

        Returns:
            (success, message, session)
        """
        # ולידציית זמן התחלה
        try:
            start_dt = datetime.strptime(planned_start, DATETIME_FORMAT)
        except ValueError:
            return False, "❌ פורמט זמן לא תקין. השתמש בפורמט DD/MM/YYYY HH:MM", None

        # חישוב זמן סיום
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        session_data = {
            'task_id': task_id,
            'course_name': course_name,
            'topic': topic,
            'planned_start': planned_start,
            'planned_end': end_dt.strftime(DATETIME_FORMAT),
            'status': 'planned',
            'notes': notes
        }

        try:
            session_id = self.db.create_study_session(session_data)
            sessions = self.get_study_sessions()
            for s in sessions:
                if s.id == session_id:
                    return True, "✅ סשן לימוד נוצר בהצלחה!", s
            return True, "✅ סשן לימוד נוצר בהצלחה!", None
        except Exception as e:
            return False, f"❌ שגיאה ביצירת סשן לימוד: {str(e)}", None

    def get_study_sessions(
        self,
        date_from: str = None,
        date_to: str = None
    ) -> List[StudySession]:
        """קבלת סשני לימוד"""
        sessions_data = self.db.get_study_sessions(date_from, date_to)
        return [StudySession.from_dict(s) for s in sessions_data]

    def start_study_session(self, session_id: int) -> Tuple[bool, str]:
        """התחלת סשן לימוד"""
        try:
            self.db.start_study_session(session_id)
            return True, "📖 סשן לימוד התחיל! בהצלחה!"
        except Exception as e:
            return False, f"❌ שגיאה: {str(e)}"

    def end_study_session(
        self,
        session_id: int,
        productivity_rating: int = None
    ) -> Tuple[bool, str]:
        """
        סיום סשן לימוד

        Args:
            session_id: מזהה הסשן
            productivity_rating: דירוג פרודוקטיביות (1-5)

        Returns:
            (success, message)
        """
        if productivity_rating and (productivity_rating < 1 or productivity_rating > 5):
            return False, "❌ דירוג חייב להיות בין 1 ל-5"

        try:
            self.db.end_study_session(session_id, productivity_rating)
            msg = "✅ סשן לימוד הסתיים!"
            if productivity_rating:
                msg += f" דירוג: {'⭐' * productivity_rating}"
            return True, msg
        except Exception as e:
            return False, f"❌ שגיאה: {str(e)}"

    def get_today_sessions(self) -> List[StudySession]:
        """קבלת סשני לימוד להיום"""
        today = datetime.now().strftime(DATE_FORMAT)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime(DATE_FORMAT)
        return self.get_study_sessions(
            date_from=f"{today} 00:00",
            date_to=f"{tomorrow} 00:00"
        )

    # ========== תכנון אוטומטי - Auto Planning ==========

    def auto_plan_study_schedule(
        self,
        tasks: List[Task],
        start_date: str,
        end_date: str,
        daily_study_hours: int = 4,
        preferred_start_time: str = "09:00",
        break_duration: int = 15,
        session_duration: int = 45
    ) -> Tuple[bool, str, List[StudySession]]:
        """
        תכנון אוטומטי של לוח לימודים

        Args:
            tasks: רשימת משימות לתכנון
            start_date: תאריך התחלה
            end_date: תאריך סיום
            daily_study_hours: שעות לימוד ביום
            preferred_start_time: שעת התחלה מועדפת
            break_duration: משך הפסקה בדקות
            session_duration: משך סשן בדקות

        Returns:
            (success, message, sessions)
        """
        if not tasks:
            return False, "❌ אין משימות לתכנון", []

        try:
            start_dt = datetime.strptime(start_date, DATE_FORMAT)
            end_dt = datetime.strptime(end_date, DATE_FORMAT)
            start_time = datetime.strptime(preferred_start_time, TIME_FORMAT)
        except ValueError:
            return False, "❌ פורמט תאריך או שעה לא תקין", []

        # מיון משימות לפי עדיפות ודדליין
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (t.priority, t.due_date or "9999-99-99")
        )

        sessions = []
        current_date = start_dt
        daily_minutes = daily_study_hours * 60
        minutes_per_block = session_duration + break_duration

        task_index = 0

        while current_date <= end_dt and task_index < len(sorted_tasks):
            # חישוב מספר סשנים ביום
            sessions_per_day = daily_minutes // minutes_per_block

            current_time = datetime.combine(
                current_date.date(),
                start_time.time()
            )

            for _ in range(sessions_per_day):
                if task_index >= len(sorted_tasks):
                    break

                task = sorted_tasks[task_index]

                # יצירת סשן
                success, msg, session = self.create_study_session(
                    planned_start=current_time.strftime(DATETIME_FORMAT),
                    duration_minutes=session_duration,
                    course_name=task.course_name,
                    topic=task.title,
                    task_id=task.id
                )

                if success and session:
                    sessions.append(session)

                # קידום הזמן
                current_time += timedelta(minutes=minutes_per_block)

                # אם הסשן קשור למשימה שלמה, עבור למשימה הבאה
                if task.estimated_duration:
                    remaining = task.estimated_duration - session_duration
                    if remaining <= 0:
                        task_index += 1
                else:
                    task_index += 1

            current_date += timedelta(days=1)

        if sessions:
            return True, f"✅ נוצרו {len(sessions)} סשני לימוד!", sessions
        else:
            return False, "❌ לא הצלחתי ליצור סשני לימוד", []

    def suggest_study_plan(
        self,
        task: Task,
        available_hours_per_day: int = 2
    ) -> Dict[str, Any]:
        """
        הצעת תכנית לימוד למשימה

        Args:
            task: המשימה
            available_hours_per_day: שעות זמינות ביום

        Returns:
            תכנית מוצעת
        """
        plan = {
            'task_title': task.title,
            'total_estimated_hours': None,
            'suggested_sessions': [],
            'tips': []
        }

        # חישוב זמן נדרש
        if task.estimated_duration:
            hours = task.estimated_duration / 60
            plan['total_estimated_hours'] = hours

            # חישוב מספר ימים נדרש
            days_needed = int(hours / available_hours_per_day) + 1

            if task.due_date:
                try:
                    due = datetime.strptime(task.due_date, DATE_FORMAT)
                    days_available = (due - datetime.now()).days

                    if days_available < days_needed:
                        plan['warning'] = f"⚠️ אין מספיק זמן! נדרשים {days_needed} ימים אבל יש רק {days_available}"
                    else:
                        plan['days_to_start_by'] = days_available - days_needed
                except ValueError:
                    pass

            # הצעת סשנים
            session_duration = REMINDER_DEFAULTS['study_session_duration']
            sessions_per_day = (available_hours_per_day * 60) // session_duration

            for day in range(days_needed):
                for session in range(sessions_per_day):
                    plan['suggested_sessions'].append({
                        'day': day + 1,
                        'session': session + 1,
                        'duration': session_duration
                    })

        # הוספת טיפים
        plan['tips'] = random.sample(STUDY_TIPS, min(3, len(STUDY_TIPS)))

        return plan

    # ========== ניתוח וסטטיסטיקות - Analysis & Statistics ==========

    def get_weekly_study_summary(self) -> Dict[str, Any]:
        """קבלת סיכום שבועי של לימודים"""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=7)

        sessions = self.get_study_sessions(
            date_from=week_start.strftime(DATETIME_FORMAT),
            date_to=week_end.strftime(DATETIME_FORMAT)
        )

        total_planned_minutes = 0
        total_actual_minutes = 0
        completed_sessions = 0
        by_course = {}

        for session in sessions:
            if session.duration_minutes:
                total_planned_minutes += session.duration_minutes

            if session.status == 'completed':
                completed_sessions += 1
                if session.actual_start and session.actual_end:
                    try:
                        start = datetime.strptime(session.actual_start, DATETIME_FORMAT)
                        end = datetime.strptime(session.actual_end, DATETIME_FORMAT)
                        actual = (end - start).total_seconds() / 60
                        total_actual_minutes += actual
                    except ValueError:
                        pass

            # סיכום לפי קורס
            course = session.course_name or "כללי"
            if course not in by_course:
                by_course[course] = {'planned': 0, 'completed': 0}

            if session.duration_minutes:
                by_course[course]['planned'] += session.duration_minutes

            if session.status == 'completed':
                by_course[course]['completed'] += 1

        return {
            'week_start': week_start.strftime(DATE_FORMAT),
            'week_end': week_end.strftime(DATE_FORMAT),
            'total_sessions': len(sessions),
            'completed_sessions': completed_sessions,
            'total_planned_hours': round(total_planned_minutes / 60, 1),
            'total_actual_hours': round(total_actual_minutes / 60, 1),
            'by_course': by_course,
            'completion_rate': round(
                (completed_sessions / len(sessions) * 100) if sessions else 0, 1
            )
        }

    def get_productivity_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """קבלת מגמת פרודוקטיביות"""
        trend = []
        today = datetime.now()

        for i in range(days):
            day = today - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0)
            day_end = day.replace(hour=23, minute=59, second=59)

            sessions = self.get_study_sessions(
                date_from=day_start.strftime(DATETIME_FORMAT),
                date_to=day_end.strftime(DATETIME_FORMAT)
            )

            completed = [s for s in sessions if s.status == 'completed']
            avg_rating = 0
            if completed:
                ratings = [s.productivity_rating for s in completed if s.productivity_rating]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0

            trend.append({
                'date': day.strftime(DATE_FORMAT),
                'day_name': WEEKDAYS_HE[day.weekday()],
                'sessions_planned': len(sessions),
                'sessions_completed': len(completed),
                'avg_productivity': round(avg_rating, 1)
            })

        return list(reversed(trend))

    # ========== עזרים - Helpers ==========

    def format_date_hebrew(self, date_str: str) -> str:
        """פורמט תאריך בעברית"""
        try:
            dt = datetime.strptime(date_str, DATE_FORMAT)
            day_name = WEEKDAYS_HE[dt.weekday()]
            month_name = MONTHS_HE[dt.month]
            return f"{day_name}, {dt.day} ב{month_name} {dt.year}"
        except ValueError:
            return date_str

    def get_random_study_tip(self) -> str:
        """קבלת טיפ אקראי ללימוד"""
        return random.choice(STUDY_TIPS)

    def calculate_workload(
        self,
        tasks: List[Task],
        days: int = 7
    ) -> Dict[str, Any]:
        """
        חישוב עומס עבודה

        Args:
            tasks: רשימת משימות
            days: מספר ימים לתכנון

        Returns:
            ניתוח עומס עבודה
        """
        total_hours = 0
        urgent_hours = 0
        by_course = {}

        for task in tasks:
            if task.estimated_duration:
                hours = task.estimated_duration / 60
                total_hours += hours

                if task.priority <= 2:
                    urgent_hours += hours

                course = task.course_name or "כללי"
                by_course[course] = by_course.get(course, 0) + hours

        hours_per_day = total_hours / days if days > 0 else total_hours

        return {
            'total_hours': round(total_hours, 1),
            'urgent_hours': round(urgent_hours, 1),
            'hours_per_day': round(hours_per_day, 1),
            'by_course': {k: round(v, 1) for k, v in by_course.items()},
            'workload_level': self._assess_workload(hours_per_day)
        }

    def _assess_workload(self, hours_per_day: float) -> Dict[str, str]:
        """הערכת רמת עומס"""
        if hours_per_day <= 2:
            return {'level': 'קל', 'color': 'green', 'emoji': '😊'}
        elif hours_per_day <= 4:
            return {'level': 'בינוני', 'color': 'yellow', 'emoji': '😐'}
        elif hours_per_day <= 6:
            return {'level': 'גבוה', 'color': 'orange', 'emoji': '😓'}
        else:
            return {'level': 'כבד מאוד', 'color': 'red', 'emoji': '😰'}
