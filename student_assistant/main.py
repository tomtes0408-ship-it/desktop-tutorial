#!/usr/bin/env python3
"""
עוזר אישי לסטודנט - Student Assistant
נקודת הכניסה הראשית לאפליקציה

הפעלה:
    python -m student_assistant.main
    או:
    python student_assistant/main.py
"""

import sys
import argparse
from pathlib import Path

# הוספת תיקיית הפרויקט ל-path
sys.path.insert(0, str(Path(__file__).parent.parent))

from student_assistant.ui import StudentAssistantUI
from student_assistant.database import DatabaseManager
from student_assistant.task_manager import TaskManager
from student_assistant.scheduler import SchedulerManager
from student_assistant.planner import StudyPlanner
from student_assistant.proactive import ProactiveAssistant


def main():
    """נקודת הכניסה הראשית"""
    parser = argparse.ArgumentParser(
        description='עוזר אישי לסטודנט - מערכת ניהול משימות ולוח זמנים',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
דוגמאות שימוש:
  python -m student_assistant.main              # הפעלה רגילה
  python -m student_assistant.main --quick      # תדריך מהיר
  python -m student_assistant.main --add-task   # הוספת משימה מהירה
        """
    )

    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='הצג תדריך יומי מהיר'
    )

    parser.add_argument(
        '--add-task', '-a',
        action='store_true',
        help='הוסף משימה חדשה'
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='הצג רשימת משימות פעילות'
    )

    parser.add_argument(
        '--deadlines', '-d',
        action='store_true',
        help='הצג דדליינים קרובים'
    )

    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help='הצג סטטיסטיקות'
    )

    args = parser.parse_args()

    # אתחול
    db = DatabaseManager()
    ui = StudentAssistantUI()

    # טיפול בפקודות מהירות
    if args.quick:
        _show_quick_briefing(db, ui)
    elif args.add_task:
        _quick_add_task(db, ui)
    elif args.list:
        _show_task_list(db, ui)
    elif args.deadlines:
        _show_deadlines(db, ui)
    elif args.stats:
        _show_stats(db, ui)
    else:
        # הפעלה מלאה
        ui.run()


def _show_quick_briefing(db: DatabaseManager, ui: StudentAssistantUI):
    """הצגת תדריך מהיר"""
    scheduler = SchedulerManager(db)
    proactive = ProactiveAssistant(db)

    # ברכה
    recommendations = proactive.get_daily_recommendations()
    print(f"\n{recommendations['greeting']}")
    print()

    # תדריך
    briefing = scheduler.get_daily_briefing()

    # אזהרות
    if recommendations['warnings']:
        print("⚠️  אזהרות:")
        for warning in recommendations['warnings']:
            print(f"   {warning['message']}")
        print()

    # משימות בעדיפות
    if recommendations['priority_tasks']:
        print("🔴 משימות דחופות:")
        for task in recommendations['priority_tasks'][:3]:
            print(f"   • {task.title}")
        print()

    # סיכום
    summary = briefing['summary']
    print(f"📊 סיכום: {summary['tasks_count']} משימות להיום, "
          f"{summary['overdue_count']} באיחור, "
          f"{summary['reminders_count']} תזכורות")
    print()

    # טיפ
    print(f"💡 טיפ: {recommendations['study_tip']}")
    print()


def _quick_add_task(db: DatabaseManager, ui: StudentAssistantUI):
    """הוספת משימה מהירה"""
    task_manager = TaskManager(db)

    print("\n📝 הוספת משימה מהירה\n")

    title = input("כותרת: ").strip()
    if not title:
        print("❌ חובה להזין כותרת")
        return

    due_date = input("תאריך יעד (DD/MM/YYYY, השאר ריק לדילוג): ").strip()
    priority = input("עדיפות (1-5, ברירת מחדל 3): ").strip()

    try:
        priority = int(priority) if priority else 3
        priority = max(1, min(5, priority))
    except ValueError:
        priority = 3

    success, message, task = task_manager.create_task(
        title=title,
        due_date=due_date if due_date else None,
        priority=priority
    )

    print(f"\n{message}")
    if success and task:
        print(f"   מזהה: {task.id}")


def _show_task_list(db: DatabaseManager, ui: StudentAssistantUI):
    """הצגת רשימת משימות"""
    task_manager = TaskManager(db)
    tasks = task_manager.get_all_tasks(exclude_completed=True, only_parent_tasks=True)

    print("\n📋 משימות פעילות:\n")

    if not tasks:
        print("   אין משימות פעילות 🎉")
    else:
        from student_assistant.config import PRIORITIES
        for task in tasks:
            emoji = PRIORITIES.get(task.priority, {}).get('emoji', '⚪')
            due = f" ({task.due_date})" if task.due_date else ""
            overdue = " ❗" if task.is_overdue else ""
            print(f"   {emoji} [{task.id}] {task.title}{due}{overdue}")

    print()


def _show_deadlines(db: DatabaseManager, ui: StudentAssistantUI):
    """הצגת דדליינים"""
    scheduler = SchedulerManager(db)
    alerts = scheduler.check_deadlines()

    print("\n📅 דדליינים קרובים:\n")

    if not alerts:
        print("   אין דדליינים קרובים 🎉")
    else:
        for alert in alerts[:10]:
            print(f"   {alert['message']}")

    print()


def _show_stats(db: DatabaseManager, ui: StudentAssistantUI):
    """הצגת סטטיסטיקות"""
    task_manager = TaskManager(db)
    stats = task_manager.get_task_statistics()

    print("\n📊 סטטיסטיקות:\n")
    print(f"   סה\"כ משימות: {stats['total']}")
    print(f"   הושלמו השבוע: {stats['completed_this_week']}")
    print(f"   באיחור: {stats['overdue']}")
    print()

    from student_assistant.config import STATUSES
    print("   לפי סטטוס:")
    for status, count in stats['by_status'].items():
        status_name = STATUSES.get(status, status)
        print(f"      {status_name}: {count}")

    print()


if __name__ == '__main__':
    main()
