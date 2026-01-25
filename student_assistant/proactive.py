"""
עוזר פרואקטיבי - Proactive Assistant
מודול להצעות אוטומטיות, אזהרות ותכנון חכם
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import random

from .database import DatabaseManager
from .models import Task, Reminder, StudySession
from .config import (
    MESSAGES, DATE_FORMAT, DATETIME_FORMAT, STUDY_TIPS,
    PRIORITIES, WEEKDAYS_HE, REMINDER_DEFAULTS
)


class ProactiveAssistant:
    """
    עוזר פרואקטיבי - Proactive Assistant
    מספק הצעות, אזהרות ועזרה יזומה לסטודנט
    """

    def __init__(self, db: Optional[DatabaseManager] = None):
        """אתחול העוזר הפרואקטיבי"""
        self.db = db or DatabaseManager()

    # ========== ניתוח משימות - Task Analysis ==========

    def analyze_task_complexity(self, task: Task) -> Dict[str, Any]:
        """
        ניתוח מורכבות משימה

        Args:
            task: המשימה לניתוח

        Returns:
            ניתוח מפורט
        """
        analysis = {
            'task_id': task.id,
            'title': task.title,
            'complexity': 'רגילה',
            'suggestions': [],
            'warnings': [],
            'recommended_actions': []
        }

        # בדיקת משך משוער
        if task.estimated_duration:
            if task.estimated_duration > 180:  # יותר מ-3 שעות
                analysis['complexity'] = 'גבוהה'
                analysis['suggestions'].append(
                    MESSAGES['suggestion_break_task'].format(task.title)
                )
                analysis['recommended_actions'].append({
                    'action': 'break_into_subtasks',
                    'description': 'פירוק לתתי-משימות'
                })
            elif task.estimated_duration > 60:
                analysis['complexity'] = 'בינונית'

        # בדיקת דדליין
        if task.due_date:
            days_until = task.days_until_due
            if days_until is not None:
                if days_until < 0:
                    analysis['warnings'].append(
                        MESSAGES['deadline_passed'].format(task.title)
                    )
                    analysis['recommended_actions'].append({
                        'action': 'reschedule',
                        'description': 'תזמון מחדש דחוף'
                    })
                elif days_until == 0:
                    analysis['warnings'].append(
                        MESSAGES['deadline_today'].format(task.title)
                    )
                    analysis['recommended_actions'].append({
                        'action': 'prioritize',
                        'description': 'יש להתחיל מיד'
                    })
                elif days_until <= 3:
                    analysis['warnings'].append(
                        MESSAGES['deadline_warning'].format(days_until, task.title)
                    )

                # בדיקה אם יש מספיק זמן
                if task.estimated_duration and days_until > 0:
                    hours_available = days_until * 4  # הנחה של 4 שעות ביום
                    hours_needed = task.estimated_duration / 60

                    if hours_needed > hours_available:
                        analysis['warnings'].append(
                            f"⚠️ ייתכן שאין מספיק זמן! נדרשות {hours_needed:.1f} שעות, זמינות {hours_available} שעות"
                        )
                        analysis['recommended_actions'].append({
                            'action': 'plan_intensively',
                            'description': 'תכנון אינטנסיבי נדרש'
                        })

        # בדיקת עדיפות
        if task.priority == 1:
            analysis['suggestions'].append(
                "💡 משימה דחופה מאוד - מומלץ להתחיל מיד"
            )
        elif task.priority == 2:
            analysis['suggestions'].append(
                "💡 משימה דחופה - כדאי לתעדף"
            )

        return analysis

    def suggest_task_breakdown(
        self,
        task: Task,
        num_parts: int = None
    ) -> List[Dict[str, Any]]:
        """
        הצעת פירוק משימה לחלקים

        Args:
            task: המשימה לפירוק
            num_parts: מספר חלקים רצוי (אופציונלי)

        Returns:
            רשימת תתי-משימות מוצעות
        """
        suggested_subtasks = []

        if task.estimated_duration:
            # חישוב מספר חלקים אופטימלי
            if num_parts is None:
                # כל חלק כ-45 דקות
                num_parts = max(2, task.estimated_duration // 45)

            part_duration = task.estimated_duration // num_parts

            # יצירת הצעות
            for i in range(num_parts):
                subtask = {
                    'title': f"{task.title} - חלק {i + 1}",
                    'estimated_duration': part_duration,
                    'order': i + 1
                }

                # חישוב תאריך יעד אם יש דדליין
                if task.due_date and task.days_until_due:
                    days_available = task.days_until_due
                    if days_available > 0:
                        interval = days_available / num_parts
                        subtask_due = datetime.now() + timedelta(days=interval * (i + 1))
                        if subtask_due.strftime(DATE_FORMAT) <= task.due_date:
                            subtask['suggested_due_date'] = subtask_due.strftime(DATE_FORMAT)
                        else:
                            subtask['suggested_due_date'] = task.due_date

                suggested_subtasks.append(subtask)

        else:
            # הצעה גנרית ל-3 חלקים
            phases = ["הכנה ומחקר", "ביצוע עיקרי", "סיכום ובדיקה"]
            for i, phase in enumerate(phases):
                suggested_subtasks.append({
                    'title': f"{task.title} - {phase}",
                    'order': i + 1
                })

        return suggested_subtasks

    # ========== הצעות תכנון - Planning Suggestions ==========

    def get_daily_recommendations(self) -> Dict[str, Any]:
        """
        קבלת המלצות יומיות

        Returns:
            המלצות מותאמות אישית
        """
        recommendations = {
            'date': datetime.now().strftime(DATE_FORMAT),
            'greeting': self._get_time_based_greeting(),
            'priority_tasks': [],
            'warnings': [],
            'suggestions': [],
            'study_tip': random.choice(STUDY_TIPS)
        }

        # קבלת משימות פעילות
        all_tasks = self.db.get_all_tasks({'exclude_completed': True})
        tasks = [Task.from_dict(t) for t in all_tasks]

        # משימות בעדיפות גבוהה
        priority_tasks = [t for t in tasks if t.priority <= 2]
        recommendations['priority_tasks'] = priority_tasks[:5]

        # אזהרות על דדליינים
        for task in tasks:
            if task.due_date:
                days = task.days_until_due
                if days is not None:
                    if days < 0:
                        recommendations['warnings'].append({
                            'type': 'overdue',
                            'task': task,
                            'message': MESSAGES['deadline_passed'].format(task.title)
                        })
                    elif days == 0:
                        recommendations['warnings'].append({
                            'type': 'today',
                            'task': task,
                            'message': MESSAGES['deadline_today'].format(task.title)
                        })
                    elif days <= 3:
                        recommendations['warnings'].append({
                            'type': 'approaching',
                            'task': task,
                            'message': MESSAGES['deadline_warning'].format(days, task.title)
                        })

        # הצעות כלליות
        if len(tasks) > 10:
            recommendations['suggestions'].append(
                "💡 יש לך הרבה משימות פתוחות. כדאי לסקור ולארגן"
            )

        overdue_count = len([t for t in tasks if t.is_overdue])
        if overdue_count > 0:
            recommendations['suggestions'].append(
                f"💡 יש לך {overdue_count} משימות באיחור. כדאי לטפל בהן או לתזמן מחדש"
            )

        # הצעה לתכנון אם אין משימות להיום
        today = datetime.now().strftime(DATE_FORMAT)
        today_tasks = [t for t in tasks if t.due_date == today]
        if not today_tasks and tasks:
            recommendations['suggestions'].append(
                "💡 אין לך משימות מתוזמנות להיום. זה הזמן לקדם משימות!"
            )

        return recommendations

    def suggest_optimal_schedule(
        self,
        tasks: List[Task],
        available_hours: Dict[str, float] = None
    ) -> Dict[str, List[Task]]:
        """
        הצעת לוח זמנים אופטימלי

        Args:
            tasks: רשימת משימות
            available_hours: שעות זמינות לכל יום

        Returns:
            לוח זמנים מוצע
        """
        if available_hours is None:
            available_hours = {str(i): 4.0 for i in range(7)}  # 4 שעות ביום

        schedule = {}
        remaining_tasks = sorted(
            tasks,
            key=lambda t: (t.priority, t.due_date or "9999-99-99")
        )

        current_date = datetime.now()

        for day_offset in range(14):  # תכנון ל-2 שבועות
            date = current_date + timedelta(days=day_offset)
            date_str = date.strftime(DATE_FORMAT)
            day_of_week = str(date.weekday())

            hours_available = available_hours.get(day_of_week, 4.0)
            hours_used = 0
            day_tasks = []

            for task in remaining_tasks[:]:
                if task.estimated_duration:
                    task_hours = task.estimated_duration / 60
                    if hours_used + task_hours <= hours_available:
                        day_tasks.append(task)
                        hours_used += task_hours
                        remaining_tasks.remove(task)
                else:
                    # משימות ללא משך - הנחה של שעה
                    if hours_used + 1 <= hours_available:
                        day_tasks.append(task)
                        hours_used += 1
                        remaining_tasks.remove(task)

            if day_tasks:
                schedule[date_str] = day_tasks

            if not remaining_tasks:
                break

        return schedule

    def identify_bottlenecks(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """
        זיהוי צווארי בקבוק

        Args:
            tasks: רשימת משימות

        Returns:
            רשימת בעיות ופתרונות מוצעים
        """
        bottlenecks = []

        # ניתוח לפי תאריך
        by_date = {}
        for task in tasks:
            if task.due_date:
                if task.due_date not in by_date:
                    by_date[task.due_date] = []
                by_date[task.due_date].append(task)

        # זיהוי ימים עמוסים
        for date, date_tasks in by_date.items():
            total_hours = sum((t.estimated_duration or 60) / 60 for t in date_tasks)
            if total_hours > 6:
                bottlenecks.append({
                    'type': 'overloaded_day',
                    'date': date,
                    'tasks_count': len(date_tasks),
                    'total_hours': total_hours,
                    'message': f"⚠️ היום {date} עמוס מאוד ({total_hours:.1f} שעות)",
                    'suggestion': "כדאי לפזר משימות לימים אחרים"
                })

        # זיהוי משימות גדולות ללא פירוק
        for task in tasks:
            if task.estimated_duration and task.estimated_duration > 180:
                if not self.db.get_subtasks(task.id):
                    bottlenecks.append({
                        'type': 'large_task',
                        'task': task,
                        'message': f"⚠️ המשימה '{task.title}' גדולה ({task.estimated_duration} דקות)",
                        'suggestion': "מומלץ לפרק לתתי-משימות"
                    })

        # זיהוי משימות ללא תאריך
        no_date = [t for t in tasks if not t.due_date]
        if no_date:
            bottlenecks.append({
                'type': 'no_deadline',
                'tasks_count': len(no_date),
                'message': f"⚠️ יש {len(no_date)} משימות ללא תאריך יעד",
                'suggestion': "כדאי להגדיר תאריכי יעד לניהול טוב יותר"
            })

        return bottlenecks

    # ========== הצעות ללימוד - Study Suggestions ==========

    def suggest_study_strategy(self, task: Task) -> Dict[str, Any]:
        """
        הצעת אסטרטגיית לימוד למשימה

        Args:
            task: המשימה

        Returns:
            אסטרטגיה מוצעת
        """
        strategy = {
            'task_title': task.title,
            'approach': '',
            'steps': [],
            'time_management': [],
            'tips': []
        }

        # זיהוי סוג המשימה לפי קטגוריה או כותרת
        title_lower = task.title.lower() if task.title else ''
        category = task.category_name or ''

        if 'מבחן' in title_lower or 'exam' in category.lower():
            strategy['approach'] = 'הכנה למבחן'
            strategy['steps'] = [
                "1. סקירת כל החומר והסילבוס",
                "2. סיכום נקודות עיקריות",
                "3. פתירת מבחנים קודמים",
                "4. חזרה על נושאים קשים",
                "5. חזרה אחרונה יום לפני"
            ]
            strategy['time_management'] = [
                "התחל לפחות שבוע לפני",
                "חלק את החומר לימים",
                "הקדש זמן לפתירת בחינות"
            ]

        elif 'פרויקט' in title_lower or 'project' in category.lower():
            strategy['approach'] = 'ביצוע פרויקט'
            strategy['steps'] = [
                "1. הבנת הדרישות והיעדים",
                "2. תכנון ופירוק לשלבים",
                "3. מחקר והכנה",
                "4. ביצוע בשלבים",
                "5. בדיקה ושיפורים",
                "6. הכנה להגשה"
            ]
            strategy['time_management'] = [
                "הקדש 20% לתכנון",
                "60% לביצוע",
                "20% לבדיקות ותיקונים"
            ]

        elif 'עבודה' in title_lower or 'paper' in category.lower():
            strategy['approach'] = 'כתיבת עבודה'
            strategy['steps'] = [
                "1. בחירת נושא וגיבוש תיזה",
                "2. איסוף מקורות",
                "3. כתיבת מתווה",
                "4. כתיבת טיוטה ראשונה",
                "5. עריכה ושכתוב",
                "6. בדיקה סופית"
            ]

        else:
            strategy['approach'] = 'גישה כללית'
            strategy['steps'] = [
                "1. הבנת המטרה",
                "2. פירוק לשלבים",
                "3. התחלה מהקל לקשה",
                "4. התקדמות הדרגתית",
                "5. בדיקה וסיכום"
            ]

        # טיפים רלוונטיים
        strategy['tips'] = random.sample(STUDY_TIPS, min(3, len(STUDY_TIPS)))

        return strategy

    def get_focus_recommendation(self) -> Dict[str, Any]:
        """
        המלצה על מה להתמקד עכשיו

        Returns:
            המלצת פוקוס
        """
        now = datetime.now()
        hour = now.hour

        recommendation = {
            'time_of_day': '',
            'focus_level': '',
            'recommended_task_type': '',
            'suggestion': ''
        }

        # המלצות לפי שעה ביום
        if 6 <= hour < 10:
            recommendation['time_of_day'] = 'בוקר מוקדם'
            recommendation['focus_level'] = 'גבוה'
            recommendation['recommended_task_type'] = 'משימות מורכבות'
            recommendation['suggestion'] = 'זה הזמן האידיאלי למשימות שדורשות ריכוז מקסימלי'

        elif 10 <= hour < 12:
            recommendation['time_of_day'] = 'בוקר'
            recommendation['focus_level'] = 'גבוה מאוד'
            recommendation['recommended_task_type'] = 'לימוד מעמיק'
            recommendation['suggestion'] = 'שיא הריכוז - מושלם ללימוד חומר חדש'

        elif 12 <= hour < 14:
            recommendation['time_of_day'] = 'צהריים'
            recommendation['focus_level'] = 'בינוני'
            recommendation['recommended_task_type'] = 'משימות קלות'
            recommendation['suggestion'] = 'אחרי האוכל הריכוז יורד - מתאים למשימות פשוטות'

        elif 14 <= hour < 17:
            recommendation['time_of_day'] = 'אחר הצהריים'
            recommendation['focus_level'] = 'בינוני-גבוה'
            recommendation['recommended_task_type'] = 'עבודה יצירתית'
            recommendation['suggestion'] = 'זמן טוב לפרויקטים ועבודות'

        elif 17 <= hour < 20:
            recommendation['time_of_day'] = 'ערב מוקדם'
            recommendation['focus_level'] = 'בינוני'
            recommendation['recommended_task_type'] = 'חזרות וסיכומים'
            recommendation['suggestion'] = 'מתאים לחזור על חומר שלמדת'

        elif 20 <= hour < 23:
            recommendation['time_of_day'] = 'ערב'
            recommendation['focus_level'] = 'יורד'
            recommendation['recommended_task_type'] = 'תכנון מחר'
            recommendation['suggestion'] = 'זמן טוב לתכנון ומשימות קלות'

        else:
            recommendation['time_of_day'] = 'לילה'
            recommendation['focus_level'] = 'נמוך'
            recommendation['recommended_task_type'] = 'מנוחה'
            recommendation['suggestion'] = 'שינה חשובה ללמידה - מומלץ לנוח'

        return recommendation

    # ========== פונקציות עזר - Helper Functions ==========

    def _get_time_based_greeting(self) -> str:
        """ברכה לפי שעה"""
        hour = datetime.now().hour

        if 5 <= hour < 12:
            return "בוקר טוב! ☀️"
        elif 12 <= hour < 17:
            return "צהריים טובים! 🌤️"
        elif 17 <= hour < 21:
            return "ערב טוב! 🌅"
        else:
            return "לילה טוב! 🌙"

    def generate_weekly_plan(
        self,
        tasks: List[Task],
        preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        יצירת תכנית שבועית

        Args:
            tasks: רשימת משימות
            preferences: העדפות משתמש

        Returns:
            תכנית שבועית מפורטת
        """
        if preferences is None:
            preferences = {
                'study_hours_per_day': 4,
                'preferred_start_time': '09:00',
                'break_duration': 15,
                'session_length': 45,
                'free_days': [5, 6]  # שישי-שבת
            }

        plan = {
            'week_start': datetime.now().strftime(DATE_FORMAT),
            'days': {},
            'summary': {
                'total_tasks': len(tasks),
                'total_hours': 0,
                'distribution': {}
            }
        }

        # מיון משימות לפי דחיפות
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (t.priority, t.due_date or "9999-99-99")
        )

        # חלוקה לימים
        current_date = datetime.now()
        remaining = list(sorted_tasks)

        for day_offset in range(7):
            date = current_date + timedelta(days=day_offset)
            day_of_week = date.weekday()
            date_str = date.strftime(DATE_FORMAT)
            day_name = WEEKDAYS_HE[day_of_week]

            if day_of_week in preferences.get('free_days', []):
                plan['days'][date_str] = {
                    'day_name': day_name,
                    'is_free_day': True,
                    'tasks': [],
                    'sessions': []
                }
                continue

            daily_hours = preferences['study_hours_per_day']
            daily_minutes = daily_hours * 60
            minutes_used = 0
            day_tasks = []
            sessions = []

            session_start = datetime.strptime(
                f"{date_str} {preferences['preferred_start_time']}",
                DATETIME_FORMAT
            )

            for task in remaining[:]:
                task_minutes = task.estimated_duration or 60

                if minutes_used + task_minutes <= daily_minutes:
                    day_tasks.append(task)
                    minutes_used += task_minutes
                    remaining.remove(task)

                    # יצירת סשנים
                    while task_minutes > 0:
                        session_length = min(
                            task_minutes,
                            preferences['session_length']
                        )
                        sessions.append({
                            'task': task.title,
                            'start': session_start.strftime('%H:%M'),
                            'duration': session_length
                        })
                        task_minutes -= session_length
                        session_start += timedelta(
                            minutes=session_length + preferences['break_duration']
                        )

            plan['days'][date_str] = {
                'day_name': day_name,
                'is_free_day': False,
                'tasks': day_tasks,
                'sessions': sessions,
                'total_minutes': minutes_used
            }

            plan['summary']['total_hours'] += minutes_used / 60

        plan['summary']['unscheduled_tasks'] = len(remaining)

        return plan
