"""
מנהל משימות - Task Manager
ניהול מלא של משימות עם פונקציונליות CRUD
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from .database import DatabaseManager
from .models import Task, Category, Assignment
from .config import (
    MESSAGES, PRIORITIES, STATUSES, DATE_FORMAT, DATETIME_FORMAT,
    DEFAULT_CATEGORIES
)


class TaskManager:
    """
    מנהל משימות - Task Manager
    מספק ממשק עילי לניהול משימות, קטגוריות והגשות
    """

    def __init__(self, db: Optional[DatabaseManager] = None):
        """אתחול מנהל המשימות"""
        self.db = db or DatabaseManager()

    # ========== ניהול משימות - Task Management ==========

    def create_task(
        self,
        title: str,
        description: str = None,
        category: str = None,
        priority: int = 3,
        due_date: str = None,
        due_time: str = None,
        estimated_duration: int = None,
        course_name: str = None,
        tags: str = None,
        notes: str = None,
        parent_task_id: int = None
    ) -> Tuple[bool, str, Optional[Task]]:
        """
        יצירת משימה חדשה

        Args:
            title: כותרת המשימה
            description: תיאור
            category: קטגוריה (שם)
            priority: עדיפות (1-5)
            due_date: תאריך יעד (DD/MM/YYYY)
            due_time: שעת יעד (HH:MM)
            estimated_duration: משך משוער בדקות
            course_name: שם הקורס
            tags: תגיות (מופרדות בפסיק)
            notes: הערות
            parent_task_id: מזהה משימת אב (לתת-משימה)

        Returns:
            (success, message, task)
        """
        # ולידציה
        if not title or not title.strip():
            return False, "❌ חובה להזין כותרת למשימה", None

        if priority < 1 or priority > 5:
            return False, "❌ עדיפות חייבת להיות בין 1 ל-5", None

        # מציאת קטגוריה
        category_id = None
        if category:
            cat = self.db.get_category_by_name(category)
            if cat:
                category_id = cat['id']

        # ולידציית תאריך
        if due_date:
            try:
                datetime.strptime(due_date, DATE_FORMAT)
            except ValueError:
                return False, MESSAGES['invalid_date'], None

        # יצירת המשימה
        task_data = {
            'title': title.strip(),
            'description': description,
            'category_id': category_id,
            'priority': priority,
            'status': 'pending',
            'due_date': due_date,
            'due_time': due_time,
            'estimated_duration': estimated_duration,
            'parent_task_id': parent_task_id,
            'course_name': course_name,
            'tags': tags,
            'notes': notes
        }

        try:
            task_id = self.db.create_task(task_data)
            task = self.get_task(task_id)
            return True, MESSAGES['task_created'], task
        except Exception as e:
            return False, f"❌ שגיאה ביצירת משימה: {str(e)}", None

    def get_task(self, task_id: int) -> Optional[Task]:
        """קבלת משימה לפי מזהה"""
        data = self.db.get_task(task_id)
        if data:
            task = Task.from_dict(data)
            # טעינת תתי-משימות
            subtasks_data = self.db.get_subtasks(task_id)
            task.subtasks = [Task.from_dict(st) for st in subtasks_data]
            return task
        return None

    def get_all_tasks(
        self,
        status: str = None,
        category: str = None,
        priority: int = None,
        course_name: str = None,
        due_date_from: str = None,
        due_date_to: str = None,
        exclude_completed: bool = False,
        only_parent_tasks: bool = False
    ) -> List[Task]:
        """
        קבלת כל המשימות עם סינון

        Args:
            status: סינון לפי סטטוס
            category: סינון לפי קטגוריה
            priority: סינון לפי עדיפות
            course_name: סינון לפי קורס
            due_date_from: תאריך התחלה
            due_date_to: תאריך סיום
            exclude_completed: לא לכלול הושלמו
            only_parent_tasks: רק משימות ראשיות (לא תת-משימות)

        Returns:
            רשימת משימות
        """
        filters = {}

        if status:
            filters['status'] = status
        if priority:
            filters['priority'] = priority
        if course_name:
            filters['course_name'] = course_name
        if due_date_from:
            filters['due_date_from'] = due_date_from
        if due_date_to:
            filters['due_date_to'] = due_date_to
        if exclude_completed:
            filters['exclude_completed'] = True

        # קבלת קטגוריה לפי שם
        if category:
            cat = self.db.get_category_by_name(category)
            if cat:
                filters['category_id'] = cat['id']

        tasks_data = self.db.get_all_tasks(filters)
        tasks = [Task.from_dict(t) for t in tasks_data]

        # סינון משימות ראשיות בלבד
        if only_parent_tasks:
            tasks = [t for t in tasks if t.parent_task_id is None]

        return tasks

    def update_task(
        self,
        task_id: int,
        title: str = None,
        description: str = None,
        category: str = None,
        priority: int = None,
        due_date: str = None,
        due_time: str = None,
        estimated_duration: int = None,
        course_name: str = None,
        tags: str = None,
        notes: str = None,
        status: str = None
    ) -> Tuple[bool, str]:
        """
        עדכון משימה

        Args:
            task_id: מזהה המשימה
            ... שאר הפרמטרים - ערכים לעדכון

        Returns:
            (success, message)
        """
        # בדיקה שהמשימה קיימת
        task = self.get_task(task_id)
        if not task:
            return False, MESSAGES['task_not_found']

        # בניית נתונים לעדכון
        update_data = {}

        if title is not None:
            if not title.strip():
                return False, "❌ כותרת לא יכולה להיות ריקה"
            update_data['title'] = title.strip()

        if description is not None:
            update_data['description'] = description

        if category is not None:
            cat = self.db.get_category_by_name(category)
            update_data['category_id'] = cat['id'] if cat else None

        if priority is not None:
            if priority < 1 or priority > 5:
                return False, "❌ עדיפות חייבת להיות בין 1 ל-5"
            update_data['priority'] = priority

        if due_date is not None:
            if due_date:  # אם לא ריק
                try:
                    datetime.strptime(due_date, DATE_FORMAT)
                except ValueError:
                    return False, MESSAGES['invalid_date']
            update_data['due_date'] = due_date if due_date else None

        if due_time is not None:
            update_data['due_time'] = due_time if due_time else None

        if estimated_duration is not None:
            update_data['estimated_duration'] = estimated_duration

        if course_name is not None:
            update_data['course_name'] = course_name if course_name else None

        if tags is not None:
            update_data['tags'] = tags if tags else None

        if notes is not None:
            update_data['notes'] = notes if notes else None

        if status is not None:
            if status not in STATUSES:
                return False, f"❌ סטטוס לא תקין. אפשרויות: {', '.join(STATUSES.values())}"
            update_data['status'] = status

        if not update_data:
            return False, "❌ לא הוזנו נתונים לעדכון"

        try:
            self.db.update_task(task_id, update_data)
            return True, MESSAGES['task_updated']
        except Exception as e:
            return False, f"❌ שגיאה בעדכון משימה: {str(e)}"

    def complete_task(self, task_id: int) -> Tuple[bool, str]:
        """
        סימון משימה כהושלמה

        Args:
            task_id: מזהה המשימה

        Returns:
            (success, message)
        """
        task = self.get_task(task_id)
        if not task:
            return False, MESSAGES['task_not_found']

        if task.status == 'completed':
            return False, "❌ המשימה כבר הושלמה"

        try:
            self.db.complete_task(task_id)

            # השלמת תתי-משימות גם כן
            if task.subtasks:
                for subtask in task.subtasks:
                    if subtask.status != 'completed':
                        self.db.complete_task(subtask.id)

            return True, MESSAGES['task_completed']
        except Exception as e:
            return False, f"❌ שגיאה בהשלמת משימה: {str(e)}"

    def delete_task(self, task_id: int) -> Tuple[bool, str]:
        """
        מחיקת משימה

        Args:
            task_id: מזהה המשימה

        Returns:
            (success, message)
        """
        task = self.get_task(task_id)
        if not task:
            return False, MESSAGES['task_not_found']

        try:
            self.db.delete_task(task_id)
            return True, MESSAGES['task_deleted']
        except Exception as e:
            return False, f"❌ שגיאה במחיקת משימה: {str(e)}"

    def start_task(self, task_id: int) -> Tuple[bool, str]:
        """התחלת עבודה על משימה"""
        task = self.get_task(task_id)
        if not task:
            return False, MESSAGES['task_not_found']

        if task.status == 'completed':
            return False, "❌ לא ניתן להתחיל משימה שהושלמה"

        return self.update_task(task_id, status='in_progress')

    # ========== ניהול תתי-משימות - Subtask Management ==========

    def create_subtask(
        self,
        parent_task_id: int,
        title: str,
        due_date: str = None,
        estimated_duration: int = None,
        notes: str = None
    ) -> Tuple[bool, str, Optional[Task]]:
        """
        יצירת תת-משימה

        Args:
            parent_task_id: מזהה משימת האב
            title: כותרת
            due_date: תאריך יעד
            estimated_duration: משך משוער
            notes: הערות

        Returns:
            (success, message, subtask)
        """
        # בדיקה שמשימת האב קיימת
        parent = self.get_task(parent_task_id)
        if not parent:
            return False, MESSAGES['task_not_found'], None

        # יצירת תת-משימה עם הגדרות מהאב
        return self.create_task(
            title=title,
            category=parent.category_name,
            priority=parent.priority,
            due_date=due_date or parent.due_date,
            estimated_duration=estimated_duration,
            course_name=parent.course_name,
            notes=notes,
            parent_task_id=parent_task_id
        )

    def break_task_into_subtasks(
        self,
        task_id: int,
        subtask_titles: List[str],
        distribute_dates: bool = True
    ) -> Tuple[bool, str, List[Task]]:
        """
        פירוק משימה לתתי-משימות

        Args:
            task_id: מזהה המשימה
            subtask_titles: רשימת כותרות לתתי-משימות
            distribute_dates: חלוקת תאריכים שווה

        Returns:
            (success, message, subtasks)
        """
        parent = self.get_task(task_id)
        if not parent:
            return False, MESSAGES['task_not_found'], []

        if not subtask_titles:
            return False, "❌ יש להזין לפחות תת-משימה אחת", []

        subtasks = []
        due_dates = []

        # חישוב תאריכי יעד אם מבוקש
        if distribute_dates and parent.due_date:
            try:
                due = datetime.strptime(parent.due_date, DATE_FORMAT)
                today = datetime.now()
                days_available = (due - today).days

                if days_available > 0:
                    interval = days_available // len(subtask_titles)
                    for i in range(len(subtask_titles)):
                        subtask_due = today + timedelta(days=interval * (i + 1))
                        if subtask_due > due:
                            subtask_due = due
                        due_dates.append(subtask_due.strftime(DATE_FORMAT))
                else:
                    due_dates = [parent.due_date] * len(subtask_titles)
            except ValueError:
                due_dates = [None] * len(subtask_titles)
        else:
            due_dates = [parent.due_date] * len(subtask_titles)

        # יצירת תתי-המשימות
        for i, title in enumerate(subtask_titles):
            success, msg, subtask = self.create_subtask(
                parent_task_id=task_id,
                title=title,
                due_date=due_dates[i] if i < len(due_dates) else None
            )
            if success and subtask:
                subtasks.append(subtask)

        if subtasks:
            return True, f"✅ נוצרו {len(subtasks)} תתי-משימות בהצלחה!", subtasks
        else:
            return False, "❌ לא הצלחתי ליצור תתי-משימות", []

    # ========== ניהול קטגוריות - Category Management ==========

    def get_categories(self) -> List[Category]:
        """קבלת כל הקטגוריות"""
        categories_data = self.db.get_categories()
        return [Category.from_dict(c) for c in categories_data]

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """קבלת קטגוריה לפי שם"""
        data = self.db.get_category_by_name(name)
        return Category.from_dict(data) if data else None

    # ========== ניהול הגשות - Assignment Management ==========

    def create_assignment(
        self,
        title: str,
        course_name: str,
        assignment_type: str,
        due_date: str,
        due_time: str = None,
        weight: float = None,
        submission_link: str = None,
        description: str = None
    ) -> Tuple[bool, str, Optional[Assignment]]:
        """
        יצירת הגשה חדשה

        Args:
            title: כותרת ההגשה
            course_name: שם הקורס
            assignment_type: סוג ההגשה
            due_date: תאריך הגשה
            due_time: שעת הגשה
            weight: משקל בציון
            submission_link: קישור להגשה
            description: תיאור

        Returns:
            (success, message, assignment)
        """
        # יצירת משימה קשורה
        success, msg, task = self.create_task(
            title=title,
            description=description,
            category='submission',
            priority=2,  # דחוף
            due_date=due_date,
            due_time=due_time,
            course_name=course_name
        )

        if not success or not task:
            return False, msg, None

        # יצירת ההגשה
        assignment_data = {
            'task_id': task.id,
            'course_name': course_name,
            'assignment_type': assignment_type,
            'weight': weight,
            'submission_link': submission_link
        }

        try:
            assignment_id = self.db.create_assignment(assignment_data)
            assignments = self.db.get_assignments()
            for a in assignments:
                if a['id'] == assignment_id:
                    return True, "✅ הגשה נוצרה בהצלחה!", Assignment.from_dict(a)
            return True, "✅ הגשה נוצרה בהצלחה!", None
        except Exception as e:
            return False, f"❌ שגיאה ביצירת הגשה: {str(e)}", None

    def get_assignments(self, course_name: str = None) -> List[Assignment]:
        """קבלת הגשות"""
        assignments_data = self.db.get_assignments(course_name)
        return [Assignment.from_dict(a) for a in assignments_data]

    def update_assignment_grade(
        self,
        assignment_id: int,
        grade: float,
        feedback: str = None
    ) -> Tuple[bool, str]:
        """עדכון ציון להגשה"""
        try:
            self.db.update_assignment_grade(assignment_id, grade, feedback)
            return True, f"✅ ציון עודכן: {grade}"
        except Exception as e:
            return False, f"❌ שגיאה בעדכון ציון: {str(e)}"

    # ========== סטטיסטיקות ודוחות - Statistics & Reports ==========

    def get_task_statistics(self) -> Dict[str, Any]:
        """קבלת סטטיסטיקות משימות"""
        return self.db.get_task_statistics()

    def get_upcoming_deadlines(self, days: int = 7) -> List[Task]:
        """קבלת דדליינים קרובים"""
        deadlines_data = self.db.get_upcoming_deadlines(days)
        return [Task.from_dict(d) for d in deadlines_data]

    def get_overdue_tasks(self) -> List[Task]:
        """קבלת משימות באיחור"""
        tasks = self.get_all_tasks(exclude_completed=True)
        return [t for t in tasks if t.is_overdue]

    def get_tasks_by_priority(self) -> Dict[int, List[Task]]:
        """קבלת משימות מקובצות לפי עדיפות"""
        tasks = self.get_all_tasks(exclude_completed=True)
        by_priority = {i: [] for i in range(1, 6)}

        for task in tasks:
            if task.priority in by_priority:
                by_priority[task.priority].append(task)

        return by_priority

    def get_today_tasks(self) -> List[Task]:
        """קבלת משימות להיום"""
        today = datetime.now().strftime(DATE_FORMAT)
        return self.get_all_tasks(
            due_date_from=today,
            due_date_to=today,
            exclude_completed=True
        )

    def get_this_week_tasks(self) -> List[Task]:
        """קבלת משימות לשבוע הקרוב"""
        today = datetime.now()
        week_end = (today + timedelta(days=7)).strftime(DATE_FORMAT)
        return self.get_all_tasks(
            due_date_from=today.strftime(DATE_FORMAT),
            due_date_to=week_end,
            exclude_completed=True
        )

    # ========== חיפוש - Search ==========

    def search_tasks(self, query: str) -> List[Task]:
        """
        חיפוש משימות

        Args:
            query: מחרוזת חיפוש

        Returns:
            רשימת משימות תואמות
        """
        all_tasks = self.get_all_tasks()
        query_lower = query.lower()

        results = []
        for task in all_tasks:
            # חיפוש בכותרת, תיאור, קורס, תגיות והערות
            searchable = ' '.join(filter(None, [
                task.title,
                task.description,
                task.course_name,
                task.tags,
                task.notes
            ])).lower()

            if query_lower in searchable:
                results.append(task)

        return results

    # ========== פעולות אצווה - Batch Operations ==========

    def complete_multiple_tasks(self, task_ids: List[int]) -> Tuple[int, int]:
        """
        השלמת מספר משימות

        Args:
            task_ids: רשימת מזהי משימות

        Returns:
            (הצליחו, נכשלו)
        """
        success_count = 0
        fail_count = 0

        for task_id in task_ids:
            success, _ = self.complete_task(task_id)
            if success:
                success_count += 1
            else:
                fail_count += 1

        return success_count, fail_count

    def delete_completed_tasks(self) -> int:
        """מחיקת כל המשימות שהושלמו"""
        completed = self.get_all_tasks(status='completed')
        count = 0

        for task in completed:
            success, _ = self.delete_task(task.id)
            if success:
                count += 1

        return count

    def reschedule_overdue_tasks(self, new_date: str) -> int:
        """
        תזמון מחדש של משימות באיחור

        Args:
            new_date: תאריך יעד חדש

        Returns:
            מספר משימות שעודכנו
        """
        overdue = self.get_overdue_tasks()
        count = 0

        for task in overdue:
            success, _ = self.update_task(task.id, due_date=new_date)
            if success:
                count += 1

        return count
