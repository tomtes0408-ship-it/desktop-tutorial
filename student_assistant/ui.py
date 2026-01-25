"""
ממשק משתמש - User Interface
ממשק שורת פקודה בעברית לעוזר האישי
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable

# תמיכה בעברית - Hebrew Support
# רוב הטרמינלים המודרניים תומכים בעברית RTL באופן טבעי

def heb(text: str) -> str:
    """
    פונקציית עזר לתצוגת עברית
    ברירת מחדל: ללא המרה (מתאים לטרמינלים מודרניים כמו Windows Terminal)
    """
    return text if text else ""

from .database import DatabaseManager
from .task_manager import TaskManager
from .planner import StudyPlanner
from .scheduler import SchedulerManager
from .models import Task, Reminder, StudySession, Course, Assignment
from .config import (
    MESSAGES, PRIORITIES, STATUSES, DATE_FORMAT, DATETIME_FORMAT,
    WEEKDAYS_HE, MONTHS_HE, STUDY_TIPS
)


class Colors:
    """צבעים לטרמינל"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

    @classmethod
    def disable(cls):
        """ביטול צבעים"""
        cls.RESET = ''
        cls.BOLD = ''
        cls.RED = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.BLUE = ''
        cls.PURPLE = ''
        cls.CYAN = ''
        cls.WHITE = ''
        cls.GRAY = ''


class StudentAssistantUI:
    """
    ממשק המשתמש הראשי - Main User Interface
    ממשק שורת פקודה אינטראקטיבי בעברית
    """

    def __init__(self):
        """אתחול הממשק"""
        self.db = DatabaseManager()
        self.task_manager = TaskManager(self.db)
        self.planner = StudyPlanner(self.db)
        self.scheduler = SchedulerManager(self.db)

        # בדיקה אם הטרמינל תומך בצבעים
        if not sys.stdout.isatty():
            Colors.disable()

    # ========== פונקציות עזר להצגה - Display Helpers ==========

    def clear_screen(self):
        """ניקוי המסך"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title: str):
        """הדפסת כותרת"""
        width = 60
        print()
        print(f"{Colors.CYAN}{'═' * width}{Colors.RESET}")
        print(f"{Colors.CYAN}║{Colors.BOLD} {heb(title):^56} {Colors.RESET}{Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.CYAN}{'═' * width}{Colors.RESET}")
        print()

    def print_subheader(self, title: str):
        """הדפסת כותרת משנית"""
        print(f"\n{Colors.YELLOW}── {heb(title)} ──{Colors.RESET}\n")

    def print_success(self, message: str):
        """הדפסת הודעת הצלחה"""
        print(f"{Colors.GREEN}{heb(message)}{Colors.RESET}")

    def print_error(self, message: str):
        """הדפסת הודעת שגיאה"""
        print(f"{Colors.RED}{heb(message)}{Colors.RESET}")

    def print_warning(self, message: str):
        """הדפסת אזהרה"""
        print(f"{Colors.YELLOW}{heb(message)}{Colors.RESET}")

    def print_info(self, message: str):
        """הדפסת מידע"""
        print(f"{Colors.BLUE}{heb(message)}{Colors.RESET}")

    def get_input(self, prompt: str, default: str = None) -> str:
        """קבלת קלט מהמשתמש"""
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "

        try:
            value = input(f"{Colors.WHITE}{prompt}{Colors.RESET}").strip()
            return value if value else (default or "")
        except (EOFError, KeyboardInterrupt):
            print()
            return default or ""

    def get_int_input(self, prompt: str, default: int = None, min_val: int = None, max_val: int = None) -> Optional[int]:
        """קבלת מספר שלם מהמשתמש"""
        value = self.get_input(prompt, str(default) if default else None)
        if not value:
            return default

        try:
            num = int(value)
            if min_val is not None and num < min_val:
                self.print_error(f"הערך חייב להיות לפחות {min_val}")
                return None
            if max_val is not None and num > max_val:
                self.print_error(f"הערך חייב להיות לכל היותר {max_val}")
                return None
            return num
        except ValueError:
            self.print_error("יש להזין מספר")
            return None

    def get_date_input(self, prompt: str, default: str = None) -> Optional[str]:
        """קבלת תאריך מהמשתמש"""
        value = self.get_input(f"{prompt} (DD/MM/YYYY)", default)
        if not value:
            return default

        try:
            datetime.strptime(value, DATE_FORMAT)
            return value
        except ValueError:
            self.print_error(MESSAGES['invalid_date'])
            return None

    def get_time_input(self, prompt: str, default: str = None) -> Optional[str]:
        """קבלת שעה מהמשתמש"""
        value = self.get_input(f"{prompt} (HH:MM)", default)
        if not value:
            return default

        try:
            datetime.strptime(value, "%H:%M")
            return value
        except ValueError:
            self.print_error(MESSAGES['invalid_time'])
            return None

    def confirm(self, message: str) -> bool:
        """בקשת אישור מהמשתמש"""
        response = self.get_input(f"{message} (כ/ל)", "ל")
        return response.lower() in ['כ', 'כן', 'y', 'yes']

    def select_from_list(self, items: List[Any], prompt: str, display_func: Callable = str) -> Optional[Any]:
        """בחירה מרשימה"""
        if not items:
            self.print_info("הרשימה ריקה")
            return None

        print()
        for i, item in enumerate(items, 1):
            print(f"  {Colors.CYAN}{i}.{Colors.RESET} {display_func(item)}")
        print()

        choice = self.get_int_input(prompt, min_val=1, max_val=len(items))
        if choice:
            return items[choice - 1]
        return None

    # ========== הצגת משימות - Task Display ==========

    def display_task(self, task: Task, detailed: bool = False):
        """הצגת משימה"""
        # צבע לפי עדיפות
        priority_colors = {
            1: Colors.RED,
            2: Colors.YELLOW,
            3: Colors.WHITE,
            4: Colors.GREEN,
            5: Colors.BLUE
        }
        color = priority_colors.get(task.priority, Colors.WHITE)

        # סימון סטטוס
        status_symbols = {
            'pending': '○',
            'in_progress': '◐',
            'completed': '●',
            'cancelled': '✗',
            'overdue': '!'
        }
        symbol = status_symbols.get(task.status, '○')

        # בדיקת איחור
        if task.is_overdue and task.status not in ['completed', 'cancelled']:
            symbol = '!'
            color = Colors.RED

        # הצגה בסיסית
        print(f"  {color}{symbol} [{task.id}] {task.get_display_title()}{Colors.RESET}", end="")

        if task.due_date:
            days = task.days_until_due
            if days is not None:
                if days < 0:
                    print(f" {Colors.RED}(איחור: {abs(days)} ימים){Colors.RESET}", end="")
                elif days == 0:
                    print(f" {Colors.RED}(היום!){Colors.RESET}", end="")
                elif days == 1:
                    print(f" {Colors.YELLOW}(מחר){Colors.RESET}", end="")
                else:
                    print(f" {Colors.GRAY}({task.due_date}){Colors.RESET}", end="")

        if task.course_name:
            print(f" {Colors.PURPLE}[{task.course_name}]{Colors.RESET}", end="")

        print()

        # פרטים נוספים
        if detailed:
            if task.description:
                print(f"      {Colors.GRAY}תיאור: {task.description}{Colors.RESET}")
            if task.category_name:
                print(f"      {Colors.GRAY}קטגוריה: {task.category_name}{Colors.RESET}")
            if task.estimated_duration:
                print(f"      {Colors.GRAY}משך משוער: {task.estimated_duration} דקות{Colors.RESET}")
            if task.tags:
                print(f"      {Colors.GRAY}תגיות: {task.tags}{Colors.RESET}")
            if task.notes:
                print(f"      {Colors.GRAY}הערות: {task.notes}{Colors.RESET}")

            # תתי-משימות
            if task.subtasks:
                print(f"      {Colors.CYAN}תתי-משימות:{Colors.RESET}")
                for subtask in task.subtasks:
                    st_symbol = '●' if subtask.status == 'completed' else '○'
                    print(f"        {st_symbol} {subtask.title}")

    def display_task_list(self, tasks: List[Task], title: str = "משימות"):
        """הצגת רשימת משימות"""
        self.print_subheader(title)

        if not tasks:
            print(f"  {Colors.GRAY}אין משימות להצגה{Colors.RESET}")
            return

        for task in tasks:
            self.display_task(task)

    # ========== הצגת תזכורות - Reminder Display ==========

    def display_reminder(self, reminder: Reminder):
        """הצגת תזכורת"""
        status = "🔔" if reminder.is_active else "🔕"
        print(f"  {status} [{reminder.id}] {reminder.title}")
        print(f"      {Colors.GRAY}זמן: {reminder.remind_at}{Colors.RESET}")
        if reminder.message:
            print(f"      {Colors.GRAY}הודעה: {reminder.message}{Colors.RESET}")
        if reminder.task_title:
            print(f"      {Colors.GRAY}משימה: {reminder.task_title}{Colors.RESET}")

    def display_reminder_list(self, reminders: List[Reminder], title: str = "תזכורות"):
        """הצגת רשימת תזכורות"""
        self.print_subheader(title)

        if not reminders:
            print(f"  {Colors.GRAY}אין תזכורות להצגה{Colors.RESET}")
            return

        for reminder in reminders:
            self.display_reminder(reminder)

    # ========== תפריטים - Menus ==========

    def show_main_menu(self) -> str:
        """הצגת התפריט הראשי"""
        self.print_header("🎓 עוזר אישי לסטודנט")

        # הצגת תדריך יומי מקוצר
        self._show_quick_briefing()

        print(f"\n{Colors.BOLD}תפריט ראשי:{Colors.RESET}")
        print(f"  {Colors.CYAN}1.{Colors.RESET} 📝 ניהול משימות")
        print(f"  {Colors.CYAN}2.{Colors.RESET} ⏰ תזכורות")
        print(f"  {Colors.CYAN}3.{Colors.RESET} 📅 תכנון לימודים")
        print(f"  {Colors.CYAN}4.{Colors.RESET} 📚 קורסים והגשות")
        print(f"  {Colors.CYAN}5.{Colors.RESET} 📊 סטטיסטיקות ודוחות")
        print(f"  {Colors.CYAN}6.{Colors.RESET} 🔍 חיפוש")
        print(f"  {Colors.CYAN}7.{Colors.RESET} ⚙️  הגדרות")
        print(f"  {Colors.CYAN}0.{Colors.RESET} 🚪 יציאה")
        print()

        return self.get_input("בחר אפשרות", "0")

    def _show_quick_briefing(self):
        """הצגת תדריך מהיר"""
        briefing = self.scheduler.get_daily_briefing()

        today = datetime.now()
        day_name = WEEKDAYS_HE[today.weekday()]
        date_str = f"{today.day}/{today.month}/{today.year}"

        print(f"\n{Colors.BOLD}📅 {day_name}, {date_str}{Colors.RESET}")

        summary = briefing['summary']
        alerts = []

        if summary['overdue_count'] > 0:
            alerts.append(f"{Colors.RED}❗ {summary['overdue_count']} משימות באיחור{Colors.RESET}")

        if summary['deadlines_count'] > 0:
            alerts.append(f"{Colors.YELLOW}⚠️ {summary['deadlines_count']} דדליינים היום{Colors.RESET}")

        if summary['tasks_count'] > 0:
            alerts.append(f"📋 {summary['tasks_count']} משימות להיום")

        if summary['reminders_count'] > 0:
            alerts.append(f"🔔 {summary['reminders_count']} תזכורות")

        if alerts:
            for alert in alerts:
                print(f"  {alert}")
        else:
            print(f"  {Colors.GREEN}✨ אין משימות דחופות להיום!{Colors.RESET}")

    # ========== תפריט משימות - Tasks Menu ==========

    def show_tasks_menu(self):
        """תפריט ניהול משימות"""
        while True:
            self.print_header("📝 ניהול משימות")

            print(f"  {Colors.CYAN}1.{Colors.RESET} הצג את כל המשימות")
            print(f"  {Colors.CYAN}2.{Colors.RESET} משימות להיום")
            print(f"  {Colors.CYAN}3.{Colors.RESET} משימות לשבוע הקרוב")
            print(f"  {Colors.CYAN}4.{Colors.RESET} משימות באיחור")
            print(f"  {Colors.CYAN}5.{Colors.RESET} צור משימה חדשה")
            print(f"  {Colors.CYAN}6.{Colors.RESET} עדכן משימה")
            print(f"  {Colors.CYAN}7.{Colors.RESET} סמן משימה כהושלמה")
            print(f"  {Colors.CYAN}8.{Colors.RESET} מחק משימה")
            print(f"  {Colors.CYAN}9.{Colors.RESET} פרק משימה לתתי-משימות")
            print(f"  {Colors.CYAN}0.{Colors.RESET} חזרה לתפריט הראשי")
            print()

            choice = self.get_input("בחר אפשרות", "0")

            if choice == "1":
                self._show_all_tasks()
            elif choice == "2":
                self._show_today_tasks()
            elif choice == "3":
                self._show_week_tasks()
            elif choice == "4":
                self._show_overdue_tasks()
            elif choice == "5":
                self._create_task()
            elif choice == "6":
                self._update_task()
            elif choice == "7":
                self._complete_task()
            elif choice == "8":
                self._delete_task()
            elif choice == "9":
                self._break_task()
            elif choice == "0":
                break

    def _show_all_tasks(self):
        """הצגת כל המשימות"""
        tasks = self.task_manager.get_all_tasks(exclude_completed=True, only_parent_tasks=True)
        self.display_task_list(tasks, "כל המשימות הפעילות")
        self.get_input("\nלחץ Enter להמשך")

    def _show_today_tasks(self):
        """הצגת משימות להיום"""
        tasks = self.task_manager.get_today_tasks()
        self.display_task_list(tasks, "משימות להיום")
        self.get_input("\nלחץ Enter להמשך")

    def _show_week_tasks(self):
        """הצגת משימות לשבוע"""
        tasks = self.task_manager.get_this_week_tasks()
        self.display_task_list(tasks, "משימות לשבוע הקרוב")
        self.get_input("\nלחץ Enter להמשך")

    def _show_overdue_tasks(self):
        """הצגת משימות באיחור"""
        tasks = self.task_manager.get_overdue_tasks()
        self.display_task_list(tasks, "משימות באיחור")

        if tasks and self.confirm("\nהאם לתזמן מחדש את המשימות?"):
            new_date = self.get_date_input("תאריך יעד חדש")
            if new_date:
                count = self.task_manager.reschedule_overdue_tasks(new_date)
                self.print_success(f"✅ תוזמנו מחדש {count} משימות")

        self.get_input("\nלחץ Enter להמשך")

    def _create_task(self):
        """יצירת משימה חדשה"""
        self.print_subheader("יצירת משימה חדשה")

        title = self.get_input("כותרת המשימה")
        if not title:
            self.print_error("חובה להזין כותרת")
            return

        description = self.get_input("תיאור (אופציונלי)")

        # בחירת קטגוריה
        categories = self.task_manager.get_categories()
        print("\nקטגוריות:")
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat.icon} {cat.name_he}")
        cat_choice = self.get_int_input("בחר קטגוריה", min_val=1, max_val=len(categories))
        category = categories[cat_choice - 1].name if cat_choice else None

        # עדיפות
        print("\nעדיפות:")
        for p, info in PRIORITIES.items():
            print(f"  {p}. {info['emoji']} {info['name']}")
        priority = self.get_int_input("בחר עדיפות", default=3, min_val=1, max_val=5) or 3

        due_date = self.get_date_input("תאריך יעד (אופציונלי)")
        due_time = self.get_time_input("שעת יעד (אופציונלי)") if due_date else None

        estimated = self.get_int_input("משך משוער בדקות (אופציונלי)")
        course_name = self.get_input("שם קורס (אופציונלי)")
        tags = self.get_input("תגיות - מופרדות בפסיק (אופציונלי)")
        notes = self.get_input("הערות (אופציונלי)")

        success, message, task = self.task_manager.create_task(
            title=title,
            description=description,
            category=category,
            priority=priority,
            due_date=due_date,
            due_time=due_time,
            estimated_duration=estimated,
            course_name=course_name,
            tags=tags,
            notes=notes
        )

        if success:
            self.print_success(message)

            # הצעה ליצור תזכורות
            if due_date and self.confirm("האם ליצור תזכורות לדדליין?"):
                s, m, reminders = self.scheduler.create_deadline_reminders(task.id)
                if s:
                    self.print_success(m)

            # הצעה לפרק למשימות קטנות
            if estimated and estimated > 120:
                self.print_info(MESSAGES['suggestion_break_task'].format(title))
        else:
            self.print_error(message)

        self.get_input("\nלחץ Enter להמשך")

    def _update_task(self):
        """עדכון משימה"""
        tasks = self.task_manager.get_all_tasks(exclude_completed=True)
        if not tasks:
            self.print_info("אין משימות פעילות")
            return

        self.display_task_list(tasks)
        task_id = self.get_int_input("הזן מספר משימה לעדכון")
        if not task_id:
            return

        task = self.task_manager.get_task(task_id)
        if not task:
            self.print_error(MESSAGES['task_not_found'])
            return

        self.print_subheader(f"עדכון: {task.title}")
        print("(השאר ריק לשמירת הערך הנוכחי)")

        title = self.get_input("כותרת", task.title)
        description = self.get_input("תיאור", task.description or "")
        priority = self.get_int_input("עדיפות (1-5)", task.priority, 1, 5)
        due_date = self.get_date_input("תאריך יעד", task.due_date)

        success, message = self.task_manager.update_task(
            task_id=task_id,
            title=title if title != task.title else None,
            description=description if description != task.description else None,
            priority=priority if priority != task.priority else None,
            due_date=due_date if due_date != task.due_date else None
        )

        if success:
            self.print_success(message)
        else:
            self.print_error(message)

        self.get_input("\nלחץ Enter להמשך")

    def _complete_task(self):
        """סימון משימה כהושלמה"""
        tasks = self.task_manager.get_all_tasks(exclude_completed=True)
        if not tasks:
            self.print_info("אין משימות פעילות")
            return

        self.display_task_list(tasks)
        task_id = self.get_int_input("הזן מספר משימה להשלמה")
        if not task_id:
            return

        success, message = self.task_manager.complete_task(task_id)
        if success:
            self.print_success(message)
        else:
            self.print_error(message)

        self.get_input("\nלחץ Enter להמשך")

    def _delete_task(self):
        """מחיקת משימה"""
        tasks = self.task_manager.get_all_tasks()
        if not tasks:
            self.print_info("אין משימות")
            return

        self.display_task_list(tasks)
        task_id = self.get_int_input("הזן מספר משימה למחיקה")
        if not task_id:
            return

        if self.confirm("האם אתה בטוח שברצונך למחוק את המשימה?"):
            success, message = self.task_manager.delete_task(task_id)
            if success:
                self.print_success(message)
            else:
                self.print_error(message)

        self.get_input("\nלחץ Enter להמשך")

    def _break_task(self):
        """פירוק משימה לתתי-משימות"""
        tasks = self.task_manager.get_all_tasks(exclude_completed=True, only_parent_tasks=True)
        if not tasks:
            self.print_info("אין משימות פעילות")
            return

        self.display_task_list(tasks)
        task_id = self.get_int_input("הזן מספר משימה לפירוק")
        if not task_id:
            return

        task = self.task_manager.get_task(task_id)
        if not task:
            self.print_error(MESSAGES['task_not_found'])
            return

        self.print_subheader(f"פירוק: {task.title}")
        print("הזן כותרות לתתי-משימות (שורה ריקה לסיום):")

        subtask_titles = []
        while True:
            title = self.get_input(f"  תת-משימה {len(subtask_titles) + 1}")
            if not title:
                break
            subtask_titles.append(title)

        if not subtask_titles:
            self.print_info("לא הוזנו תתי-משימות")
            return

        distribute = self.confirm("האם לחלק תאריכים באופן שווה?")

        success, message, subtasks = self.task_manager.break_task_into_subtasks(
            task_id, subtask_titles, distribute
        )

        if success:
            self.print_success(message)
            for st in subtasks:
                print(f"  ✓ {st.title} ({st.due_date or 'ללא תאריך'})")
        else:
            self.print_error(message)

        self.get_input("\nלחץ Enter להמשך")

    # ========== תפריט תזכורות - Reminders Menu ==========

    def show_reminders_menu(self):
        """תפריט תזכורות"""
        while True:
            self.print_header("⏰ תזכורות")

            print(f"  {Colors.CYAN}1.{Colors.RESET} הצג תזכורות פעילות")
            print(f"  {Colors.CYAN}2.{Colors.RESET} תזכורות ל-24 שעות הקרובות")
            print(f"  {Colors.CYAN}3.{Colors.RESET} צור תזכורת חדשה")
            print(f"  {Colors.CYAN}4.{Colors.RESET} תזכורת מהירה (בעוד X דקות)")
            print(f"  {Colors.CYAN}5.{Colors.RESET} תזכורת למחר")
            print(f"  {Colors.CYAN}6.{Colors.RESET} צור תזכורות דדליין למשימה")
            print(f"  {Colors.CYAN}7.{Colors.RESET} מחק תזכורת")
            print(f"  {Colors.CYAN}0.{Colors.RESET} חזרה לתפריט הראשי")
            print()

            choice = self.get_input("בחר אפשרות", "0")

            if choice == "1":
                self._show_active_reminders()
            elif choice == "2":
                self._show_upcoming_reminders()
            elif choice == "3":
                self._create_reminder()
            elif choice == "4":
                self._create_quick_reminder()
            elif choice == "5":
                self._create_tomorrow_reminder()
            elif choice == "6":
                self._create_deadline_reminders()
            elif choice == "7":
                self._delete_reminder()
            elif choice == "0":
                break

    def _show_active_reminders(self):
        """הצגת תזכורות פעילות"""
        reminders = self.scheduler.get_all_reminders()
        self.display_reminder_list(reminders, "תזכורות פעילות")
        self.get_input("\nלחץ Enter להמשך")

    def _show_upcoming_reminders(self):
        """הצגת תזכורות קרובות"""
        reminders = self.scheduler.get_upcoming_reminders(24)
        self.display_reminder_list(reminders, "תזכורות ל-24 שעות הקרובות")
        self.get_input("\nלחץ Enter להמשך")

    def _create_reminder(self):
        """יצירת תזכורת"""
        self.print_subheader("יצירת תזכורת חדשה")

        title = self.get_input("כותרת התזכורת")
        if not title:
            self.print_error("חובה להזין כותרת")
            return

        date = self.get_date_input("תאריך")
        if not date:
            return

        time = self.get_time_input("שעה")
        if not time:
            return

        message = self.get_input("הודעה (אופציונלי)")

        remind_at = f"{date} {time}"
        success, msg, reminder = self.scheduler.create_reminder(
            title=title,
            remind_at=remind_at,
            message=message
        )

        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    def _create_quick_reminder(self):
        """יצירת תזכורת מהירה"""
        title = self.get_input("כותרת התזכורת")
        if not title:
            return

        minutes = self.get_int_input("בעוד כמה דקות?", min_val=1)
        if not minutes:
            return

        success, msg, reminder = self.scheduler.remind_in_minutes(title, minutes)
        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    def _create_tomorrow_reminder(self):
        """יצירת תזכורת למחר"""
        title = self.get_input("כותרת התזכורת")
        if not title:
            return

        time = self.get_time_input("באיזו שעה?", "09:00")
        if not time:
            return

        success, msg, reminder = self.scheduler.remind_tomorrow(title, time)
        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    def _create_deadline_reminders(self):
        """יצירת תזכורות דדליין"""
        tasks = self.task_manager.get_all_tasks(exclude_completed=True)
        tasks_with_deadline = [t for t in tasks if t.due_date]

        if not tasks_with_deadline:
            self.print_info("אין משימות עם תאריך יעד")
            return

        self.display_task_list(tasks_with_deadline)
        task_id = self.get_int_input("בחר משימה")
        if not task_id:
            return

        success, msg, reminders = self.scheduler.create_deadline_reminders(task_id)
        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    def _delete_reminder(self):
        """מחיקת תזכורת"""
        reminders = self.scheduler.get_all_reminders()
        if not reminders:
            self.print_info("אין תזכורות")
            return

        self.display_reminder_list(reminders)
        reminder_id = self.get_int_input("הזן מספר תזכורת למחיקה")
        if not reminder_id:
            return

        success, msg = self.scheduler.delete_reminder(reminder_id)
        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    # ========== תפריט תכנון - Planning Menu ==========

    def show_planning_menu(self):
        """תפריט תכנון לימודים"""
        while True:
            self.print_header("📅 תכנון לימודים")

            print(f"  {Colors.CYAN}1.{Colors.RESET} צור סשן לימוד")
            print(f"  {Colors.CYAN}2.{Colors.RESET} סשני לימוד להיום")
            print(f"  {Colors.CYAN}3.{Colors.RESET} התחל סשן לימוד")
            print(f"  {Colors.CYAN}4.{Colors.RESET} סיים סשן לימוד")
            print(f"  {Colors.CYAN}5.{Colors.RESET} תכנון אוטומטי")
            print(f"  {Colors.CYAN}6.{Colors.RESET} סיכום שבועי")
            print(f"  {Colors.CYAN}7.{Colors.RESET} חישוב עומס עבודה")
            print(f"  {Colors.CYAN}8.{Colors.RESET} טיפ ללימוד")
            print(f"  {Colors.CYAN}0.{Colors.RESET} חזרה לתפריט הראשי")
            print()

            choice = self.get_input("בחר אפשרות", "0")

            if choice == "1":
                self._create_study_session()
            elif choice == "2":
                self._show_today_sessions()
            elif choice == "3":
                self._start_study_session()
            elif choice == "4":
                self._end_study_session()
            elif choice == "5":
                self._auto_plan()
            elif choice == "6":
                self._show_weekly_summary()
            elif choice == "7":
                self._calculate_workload()
            elif choice == "8":
                self._show_study_tip()
            elif choice == "0":
                break

    def _create_study_session(self):
        """יצירת סשן לימוד"""
        self.print_subheader("יצירת סשן לימוד")

        date = self.get_date_input("תאריך")
        if not date:
            return

        time = self.get_time_input("שעת התחלה")
        if not time:
            return

        duration = self.get_int_input("משך בדקות", default=45, min_val=15)
        course = self.get_input("קורס (אופציונלי)")
        topic = self.get_input("נושא (אופציונלי)")

        planned_start = f"{date} {time}"
        success, msg, session = self.planner.create_study_session(
            planned_start=planned_start,
            duration_minutes=duration,
            course_name=course if course else None,
            topic=topic if topic else None
        )

        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    def _show_today_sessions(self):
        """הצגת סשני לימוד להיום"""
        sessions = self.planner.get_today_sessions()
        self.print_subheader("סשני לימוד להיום")

        if not sessions:
            self.print_info("אין סשני לימוד מתוכננים להיום")
        else:
            for session in sessions:
                status_icon = "✓" if session.status == 'completed' else "○"
                print(f"  {status_icon} [{session.id}] {session.planned_start} - {session.planned_end}")
                if session.course_name:
                    print(f"      קורס: {session.course_name}")
                if session.topic:
                    print(f"      נושא: {session.topic}")

        self.get_input("\nלחץ Enter להמשך")

    def _start_study_session(self):
        """התחלת סשן לימוד"""
        sessions = self.planner.get_today_sessions()
        planned = [s for s in sessions if s.status == 'planned']

        if not planned:
            self.print_info("אין סשנים מתוכננים להתחיל")
            return

        for session in planned:
            print(f"  [{session.id}] {session.planned_start} - {session.topic or session.course_name or 'לימוד'}")

        session_id = self.get_int_input("בחר סשן להתחלה")
        if not session_id:
            return

        success, msg = self.planner.start_study_session(session_id)
        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    def _end_study_session(self):
        """סיום סשן לימוד"""
        sessions = self.planner.get_today_sessions()
        in_progress = [s for s in sessions if s.status == 'in_progress']

        if not in_progress:
            self.print_info("אין סשנים פעילים")
            return

        for session in in_progress:
            print(f"  [{session.id}] {session.topic or session.course_name or 'לימוד'}")

        session_id = self.get_int_input("בחר סשן לסיום")
        if not session_id:
            return

        rating = self.get_int_input("דרג את הפרודוקטיביות (1-5)", min_val=1, max_val=5)

        success, msg = self.planner.end_study_session(session_id, rating)
        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    def _auto_plan(self):
        """תכנון אוטומטי"""
        tasks = self.task_manager.get_all_tasks(exclude_completed=True)
        if not tasks:
            self.print_info("אין משימות לתכנון")
            return

        self.print_subheader("תכנון אוטומטי")

        start_date = self.get_date_input("תאריך התחלה", datetime.now().strftime(DATE_FORMAT))
        end_date = self.get_date_input("תאריך סיום")
        if not end_date:
            return

        hours_per_day = self.get_int_input("שעות לימוד ביום", default=4, min_val=1, max_val=12)
        start_time = self.get_time_input("שעת התחלה מועדפת", "09:00")

        success, msg, sessions = self.planner.auto_plan_study_schedule(
            tasks=tasks,
            start_date=start_date,
            end_date=end_date,
            daily_study_hours=hours_per_day,
            preferred_start_time=start_time
        )

        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    def _show_weekly_summary(self):
        """הצגת סיכום שבועי"""
        summary = self.planner.get_weekly_study_summary()
        self.print_subheader(f"סיכום שבועי ({summary['week_start']} - {summary['week_end']})")

        print(f"  סה\"כ סשנים: {summary['total_sessions']}")
        print(f"  סשנים שהושלמו: {summary['completed_sessions']}")
        print(f"  שעות מתוכננות: {summary['total_planned_hours']}")
        print(f"  שעות בפועל: {summary['total_actual_hours']}")
        print(f"  אחוז השלמה: {summary['completion_rate']}%")

        if summary['by_course']:
            print(f"\n  לפי קורס:")
            for course, data in summary['by_course'].items():
                print(f"    {course}: {data['planned']} דקות, {data['completed']} סשנים")

        self.get_input("\nלחץ Enter להמשך")

    def _calculate_workload(self):
        """חישוב עומס עבודה"""
        tasks = self.task_manager.get_all_tasks(exclude_completed=True)

        if not tasks:
            self.print_info("אין משימות פעילות")
            return

        days = self.get_int_input("לכמה ימים לחשב?", default=7, min_val=1)

        workload = self.planner.calculate_workload(tasks, days)

        self.print_subheader("ניתוח עומס עבודה")
        print(f"  סה\"כ שעות: {workload['total_hours']}")
        print(f"  שעות דחופות: {workload['urgent_hours']}")
        print(f"  שעות ליום: {workload['hours_per_day']}")

        level = workload['workload_level']
        print(f"  רמת עומס: {level['emoji']} {level['level']}")

        if workload['by_course']:
            print(f"\n  לפי קורס:")
            for course, hours in workload['by_course'].items():
                print(f"    {course}: {hours} שעות")

        self.get_input("\nלחץ Enter להמשך")

    def _show_study_tip(self):
        """הצגת טיפ ללימוד"""
        tip = self.planner.get_random_study_tip()
        self.print_subheader("💡 טיפ ללימוד")
        print(f"  {tip}")
        self.get_input("\nלחץ Enter להמשך")

    # ========== תפריט קורסים - Courses Menu ==========

    def show_courses_menu(self):
        """תפריט קורסים והגשות"""
        while True:
            self.print_header("📚 קורסים והגשות")

            print(f"  {Colors.CYAN}1.{Colors.RESET} הצג קורסים")
            print(f"  {Colors.CYAN}2.{Colors.RESET} הוסף קורס")
            print(f"  {Colors.CYAN}3.{Colors.RESET} הצג הגשות")
            print(f"  {Colors.CYAN}4.{Colors.RESET} צור הגשה חדשה")
            print(f"  {Colors.CYAN}5.{Colors.RESET} עדכן ציון")
            print(f"  {Colors.CYAN}0.{Colors.RESET} חזרה לתפריט הראשי")
            print()

            choice = self.get_input("בחר אפשרות", "0")

            if choice == "1":
                self._show_courses()
            elif choice == "2":
                self._add_course()
            elif choice == "3":
                self._show_assignments()
            elif choice == "4":
                self._create_assignment()
            elif choice == "5":
                self._update_grade()
            elif choice == "0":
                break

    def _show_courses(self):
        """הצגת קורסים"""
        courses = self.planner.get_all_courses()
        self.print_subheader("קורסים")

        if not courses:
            self.print_info("אין קורסים רשומים")
        else:
            for course in courses:
                print(f"  [{course.id}] {course.name}")
                if course.code:
                    print(f"      קוד: {course.code}")
                if course.lecturer:
                    print(f"      מרצה: {course.lecturer}")
                if course.credits:
                    print(f"      נ\"ז: {course.credits}")

        self.get_input("\nלחץ Enter להמשך")

    def _add_course(self):
        """הוספת קורס"""
        self.print_subheader("הוספת קורס חדש")

        name = self.get_input("שם הקורס")
        if not name:
            return

        code = self.get_input("קוד הקורס (אופציונלי)")
        lecturer = self.get_input("שם המרצה (אופציונלי)")
        credits = self.get_int_input("נקודות זכות (אופציונלי)")

        success, msg, course = self.planner.create_course(
            name=name,
            code=code if code else None,
            lecturer=lecturer if lecturer else None,
            credits=credits
        )

        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    def _show_assignments(self):
        """הצגת הגשות"""
        assignments = self.task_manager.get_assignments()
        self.print_subheader("הגשות")

        if not assignments:
            self.print_info("אין הגשות רשומות")
        else:
            for a in assignments:
                status = "✓" if a.status == 'completed' else "○"
                grade = f" | ציון: {a.grade}" if a.grade else ""
                print(f"  {status} [{a.id}] {a.title} - {a.course_name}")
                print(f"      סוג: {a.type_hebrew} | תאריך: {a.due_date or 'לא נקבע'}{grade}")

        self.get_input("\nלחץ Enter להמשך")

    def _create_assignment(self):
        """יצירת הגשה"""
        self.print_subheader("יצירת הגשה חדשה")

        title = self.get_input("כותרת ההגשה")
        if not title:
            return

        course = self.get_input("שם הקורס")
        if not course:
            return

        print("\nסוג הגשה:")
        types = ["homework", "project", "exam", "quiz", "paper", "presentation", "lab", "other"]
        type_names = ["שיעורי בית", "פרויקט", "מבחן", "בוחן", "עבודה", "מצגת", "מעבדה", "אחר"]
        for i, (t, n) in enumerate(zip(types, type_names), 1):
            print(f"  {i}. {n}")
        type_choice = self.get_int_input("בחר סוג", min_val=1, max_val=len(types))
        assignment_type = types[type_choice - 1] if type_choice else "homework"

        due_date = self.get_date_input("תאריך הגשה")
        if not due_date:
            return

        due_time = self.get_time_input("שעת הגשה (אופציונלי)")
        weight = self.get_int_input("משקל בציון באחוזים (אופציונלי)")
        link = self.get_input("קישור להגשה (אופציונלי)")

        success, msg, assignment = self.task_manager.create_assignment(
            title=title,
            course_name=course,
            assignment_type=assignment_type,
            due_date=due_date,
            due_time=due_time,
            weight=weight,
            submission_link=link if link else None
        )

        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    def _update_grade(self):
        """עדכון ציון"""
        assignments = self.task_manager.get_assignments()
        if not assignments:
            self.print_info("אין הגשות")
            return

        for a in assignments:
            grade = f" | ציון: {a.grade}" if a.grade else ""
            print(f"  [{a.id}] {a.title}{grade}")

        assignment_id = self.get_int_input("בחר הגשה לעדכון ציון")
        if not assignment_id:
            return

        grade = self.get_int_input("ציון", min_val=0, max_val=100)
        if grade is None:
            return

        feedback = self.get_input("משוב (אופציונלי)")

        success, msg = self.task_manager.update_assignment_grade(
            assignment_id, grade, feedback if feedback else None
        )

        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)

        self.get_input("\nלחץ Enter להמשך")

    # ========== תפריט סטטיסטיקות - Statistics Menu ==========

    def show_statistics_menu(self):
        """תפריט סטטיסטיקות"""
        while True:
            self.print_header("📊 סטטיסטיקות ודוחות")

            print(f"  {Colors.CYAN}1.{Colors.RESET} סטטיסטיקות משימות")
            print(f"  {Colors.CYAN}2.{Colors.RESET} תדריך יומי מפורט")
            print(f"  {Colors.CYAN}3.{Colors.RESET} דדליינים קרובים")
            print(f"  {Colors.CYAN}4.{Colors.RESET} מגמת פרודוקטיביות")
            print(f"  {Colors.CYAN}5.{Colors.RESET} יומן פעילות")
            print(f"  {Colors.CYAN}0.{Colors.RESET} חזרה לתפריט הראשי")
            print()

            choice = self.get_input("בחר אפשרות", "0")

            if choice == "1":
                self._show_task_statistics()
            elif choice == "2":
                self._show_detailed_briefing()
            elif choice == "3":
                self._show_deadlines()
            elif choice == "4":
                self._show_productivity_trend()
            elif choice == "5":
                self._show_activity_log()
            elif choice == "0":
                break

    def _show_task_statistics(self):
        """הצגת סטטיסטיקות משימות"""
        stats = self.task_manager.get_task_statistics()
        self.print_subheader("סטטיסטיקות משימות")

        print(f"  סה\"כ משימות: {stats['total']}")
        print(f"  הושלמו השבוע: {stats['completed_this_week']}")
        print(f"  באיחור: {stats['overdue']}")

        print(f"\n  לפי סטטוס:")
        for status, count in stats['by_status'].items():
            status_name = STATUSES.get(status, status)
            print(f"    {status_name}: {count}")

        print(f"\n  לפי עדיפות:")
        for priority, count in stats['by_priority'].items():
            priority_info = PRIORITIES.get(priority, {})
            name = priority_info.get('name', str(priority))
            emoji = priority_info.get('emoji', '')
            print(f"    {emoji} {name}: {count}")

        self.get_input("\nלחץ Enter להמשך")

    def _show_detailed_briefing(self):
        """הצגת תדריך יומי מפורט"""
        briefing = self.scheduler.get_daily_briefing()
        self.print_subheader(f"תדריך יומי - {briefing['day_name']}, {briefing['date']}")

        # משימות באיחור
        if briefing['overdue_tasks']:
            print(f"\n{Colors.RED}❗ משימות באיחור:{Colors.RESET}")
            for task in briefing['overdue_tasks']:
                print(f"  • {task.title} (מ-{task.due_date})")

        # דדליינים להיום
        if briefing['deadlines_today']:
            print(f"\n{Colors.YELLOW}⚠️ דדליינים להיום:{Colors.RESET}")
            for task in briefing['deadlines_today']:
                print(f"  • {task.title}")

        # משימות להיום
        if briefing['tasks_today']:
            print(f"\n📋 משימות להיום:")
            for task in briefing['tasks_today']:
                print(f"  • {task.title}")

        # תזכורות
        if briefing['reminders_today']:
            print(f"\n🔔 תזכורות:")
            for reminder in briefing['reminders_today']:
                print(f"  • {reminder.remind_at} - {reminder.title}")

        # דדליינים קרובים
        if briefing['upcoming_deadlines']:
            print(f"\n📅 דדליינים קרובים:")
            for task in briefing['upcoming_deadlines'][:5]:
                days = task.days_until_due
                print(f"  • {task.title} - {task.due_date} (עוד {days} ימים)")

        self.get_input("\nלחץ Enter להמשך")

    def _show_deadlines(self):
        """הצגת דדליינים"""
        alerts = self.scheduler.check_deadlines()
        self.print_subheader("דדליינים קרובים")

        if not alerts:
            self.print_success("אין דדליינים קרובים!")
        else:
            for alert in alerts:
                if alert['urgency'] == 'critical':
                    color = Colors.RED
                elif alert['urgency'] == 'high':
                    color = Colors.YELLOW
                else:
                    color = Colors.WHITE
                print(f"  {color}{alert['message']}{Colors.RESET}")

        self.get_input("\nלחץ Enter להמשך")

    def _show_productivity_trend(self):
        """הצגת מגמת פרודוקטיביות"""
        trend = self.planner.get_productivity_trend(7)
        self.print_subheader("מגמת פרודוקטיביות - 7 ימים אחרונים")

        for day in trend:
            stars = '⭐' * int(day['avg_productivity']) if day['avg_productivity'] else '-'
            print(f"  {day['day_name']} ({day['date']}): {day['sessions_completed']}/{day['sessions_planned']} סשנים | {stars}")

        self.get_input("\nלחץ Enter להמשך")

    def _show_activity_log(self):
        """הצגת יומן פעילות"""
        log = self.db.get_activity_log(20)
        self.print_subheader("יומן פעילות אחרון")

        if not log:
            self.print_info("אין פעילות רשומה")
        else:
            for entry in log:
                print(f"  {entry['created_at']} - {entry['description']}")

        self.get_input("\nלחץ Enter להמשך")

    # ========== חיפוש - Search ==========

    def show_search(self):
        """חיפוש"""
        self.print_header("🔍 חיפוש")

        query = self.get_input("הזן מילות חיפוש")
        if not query:
            return

        tasks = self.task_manager.search_tasks(query)

        if tasks:
            self.display_task_list(tasks, f"תוצאות חיפוש: '{query}'")
        else:
            self.print_info("לא נמצאו תוצאות")

        self.get_input("\nלחץ Enter להמשך")

    # ========== הגדרות - Settings ==========

    def show_settings_menu(self):
        """תפריט הגדרות"""
        while True:
            self.print_header("⚙️ הגדרות")

            print(f"  {Colors.CYAN}1.{Colors.RESET} מחק משימות שהושלמו")
            print(f"  {Colors.CYAN}2.{Colors.RESET} ייצא תזכורות")
            print(f"  {Colors.CYAN}3.{Colors.RESET} אודות")
            print(f"  {Colors.CYAN}0.{Colors.RESET} חזרה לתפריט הראשי")
            print()

            choice = self.get_input("בחר אפשרות", "0")

            if choice == "1":
                self._delete_completed_tasks()
            elif choice == "2":
                self._export_reminders()
            elif choice == "3":
                self._show_about()
            elif choice == "0":
                break

    def _delete_completed_tasks(self):
        """מחיקת משימות שהושלמו"""
        if self.confirm("האם למחוק את כל המשימות שהושלמו?"):
            count = self.task_manager.delete_completed_tasks()
            self.print_success(f"נמחקו {count} משימות")
        self.get_input("\nלחץ Enter להמשך")

    def _export_reminders(self):
        """ייצוא תזכורות"""
        filepath = self.get_input("נתיב לשמירת הקובץ", "reminders.json")
        success, msg = self.scheduler.export_reminders_to_json(filepath)
        if success:
            self.print_success(msg)
        else:
            self.print_error(msg)
        self.get_input("\nלחץ Enter להמשך")

    def _show_about(self):
        """אודות"""
        self.print_subheader("אודות")
        print("  🎓 עוזר אישי לסטודנט")
        print("  גרסה: 1.0.0")
        print()
        print("  מערכת לניהול משימות, תזכורות ולוח זמנים")
        print("  מותאמת במיוחד לסטודנטים")
        print()
        print("  תכונות עיקריות:")
        print("  • ניהול משימות מלא")
        print("  • תזכורות ודדליינים")
        print("  • תכנון לימודים אוטומטי")
        print("  • מעקב אחר הגשות וציונים")
        print("  • סטטיסטיקות ודוחות")
        self.get_input("\nלחץ Enter להמשך")

    # ========== לולאה ראשית - Main Loop ==========

    def run(self):
        """הרצת האפליקציה"""
        # הפעלת שירות התזכורות ברקע
        self.scheduler.set_notification_callback(self._handle_notification)
        self.scheduler.start_scheduler()

        print(MESSAGES['welcome'])

        try:
            while True:
                self.clear_screen()
                choice = self.show_main_menu()

                if choice == "1":
                    self.show_tasks_menu()
                elif choice == "2":
                    self.show_reminders_menu()
                elif choice == "3":
                    self.show_planning_menu()
                elif choice == "4":
                    self.show_courses_menu()
                elif choice == "5":
                    self.show_statistics_menu()
                elif choice == "6":
                    self.show_search()
                elif choice == "7":
                    self.show_settings_menu()
                elif choice == "0":
                    if self.confirm("האם לצאת מהתוכנית?"):
                        break

        except KeyboardInterrupt:
            pass
        finally:
            self.scheduler.stop_scheduler()
            print(f"\n{MESSAGES['goodbye']}")

    def _handle_notification(self, reminder: Reminder):
        """טיפול בהתראה"""
        print(f"\n{Colors.YELLOW}🔔 תזכורת: {reminder.title}{Colors.RESET}")
        if reminder.message:
            print(f"   {reminder.message}")
        print()
