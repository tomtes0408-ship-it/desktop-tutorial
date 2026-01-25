"""
מודלים - Data Models
מחלקות לייצוג נתונים במערכת העוזר האישי
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional, List
from enum import Enum

from .config import PRIORITIES, STATUSES, DATETIME_FORMAT, DATE_FORMAT, TIME_FORMAT


class TaskStatus(Enum):
    """סטטוס משימה"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

    @property
    def hebrew(self) -> str:
        """שם בעברית"""
        return STATUSES.get(self.value, self.value)


class Priority(Enum):
    """עדיפות משימה"""
    URGENT_HIGH = 1
    URGENT = 2
    NORMAL = 3
    LOW = 4
    NOT_URGENT = 5

    @property
    def hebrew(self) -> str:
        """שם בעברית"""
        return PRIORITIES.get(self.value, {}).get('name', str(self.value))

    @property
    def color(self) -> str:
        """צבע"""
        return PRIORITIES.get(self.value, {}).get('color', 'white')

    @property
    def emoji(self) -> str:
        """אימוג'י"""
        return PRIORITIES.get(self.value, {}).get('emoji', '⚪')


class RepeatType(Enum):
    """סוג חזרה לתזכורת"""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class AssignmentType(Enum):
    """סוג הגשה"""
    HOMEWORK = "homework"
    PROJECT = "project"
    EXAM = "exam"
    QUIZ = "quiz"
    PAPER = "paper"
    PRESENTATION = "presentation"
    LAB = "lab"
    OTHER = "other"

    @property
    def hebrew(self) -> str:
        """שם בעברית"""
        names = {
            "homework": "שיעורי בית",
            "project": "פרויקט",
            "exam": "מבחן",
            "quiz": "בוחן",
            "paper": "עבודה",
            "presentation": "מצגת",
            "lab": "מעבדה",
            "other": "אחר"
        }
        return names.get(self.value, self.value)


class SessionStatus(Enum):
    """סטטוס סשן לימוד"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class Category:
    """קטגוריה"""
    id: Optional[int] = None
    name: str = ""
    name_he: str = ""
    color: str = "blue"
    icon: str = "📁"
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Category':
        """יצירה מדיקשנרי"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            name_he=data.get('name_he', ''),
            color=data.get('color', 'blue'),
            icon=data.get('icon', '📁'),
            created_at=cls._parse_datetime(data.get('created_at'))
        )

    @staticmethod
    def _parse_datetime(value) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, DATETIME_FORMAT)
            except ValueError:
                return None
        return None


@dataclass
class Task:
    """משימה"""
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    priority: int = 3
    status: str = "pending"
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    estimated_duration: Optional[int] = None  # בדקות
    actual_duration: Optional[int] = None
    parent_task_id: Optional[int] = None
    course_name: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    subtasks: List['Task'] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """יצירה מדיקשנרי"""
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            description=data.get('description'),
            category_id=data.get('category_id'),
            category_name=data.get('category_name'),
            priority=data.get('priority', 3),
            status=data.get('status', 'pending'),
            due_date=data.get('due_date'),
            due_time=data.get('due_time'),
            estimated_duration=data.get('estimated_duration'),
            actual_duration=data.get('actual_duration'),
            parent_task_id=data.get('parent_task_id'),
            course_name=data.get('course_name'),
            tags=data.get('tags'),
            notes=data.get('notes'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            completed_at=data.get('completed_at')
        )

    def to_dict(self) -> dict:
        """המרה לדיקשנרי"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'priority': self.priority,
            'status': self.status,
            'due_date': self.due_date,
            'due_time': self.due_time,
            'estimated_duration': self.estimated_duration,
            'actual_duration': self.actual_duration,
            'parent_task_id': self.parent_task_id,
            'course_name': self.course_name,
            'tags': self.tags,
            'notes': self.notes
        }

    @property
    def priority_info(self) -> dict:
        """מידע על עדיפות"""
        return PRIORITIES.get(self.priority, PRIORITIES[3])

    @property
    def status_hebrew(self) -> str:
        """סטטוס בעברית"""
        return STATUSES.get(self.status, self.status)

    @property
    def is_overdue(self) -> bool:
        """האם באיחור"""
        if not self.due_date or self.status == 'completed':
            return False
        try:
            due = datetime.strptime(self.due_date, DATE_FORMAT).date()
            return due < date.today()
        except ValueError:
            return False

    @property
    def days_until_due(self) -> Optional[int]:
        """ימים עד הדדליין"""
        if not self.due_date:
            return None
        try:
            due = datetime.strptime(self.due_date, DATE_FORMAT).date()
            return (due - date.today()).days
        except ValueError:
            return None

    def get_display_title(self) -> str:
        """כותרת להצגה עם אימוג'י עדיפות"""
        emoji = self.priority_info.get('emoji', '⚪')
        return f"{emoji} {self.title}"


@dataclass
class Reminder:
    """תזכורת"""
    id: Optional[int] = None
    task_id: Optional[int] = None
    task_title: Optional[str] = None
    title: str = ""
    message: Optional[str] = None
    remind_at: str = ""
    repeat_type: Optional[str] = None
    repeat_interval: Optional[int] = None
    is_active: bool = True
    is_triggered: bool = False
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Reminder':
        """יצירה מדיקשנרי"""
        return cls(
            id=data.get('id'),
            task_id=data.get('task_id'),
            task_title=data.get('task_title'),
            title=data.get('title', ''),
            message=data.get('message'),
            remind_at=data.get('remind_at', ''),
            repeat_type=data.get('repeat_type'),
            repeat_interval=data.get('repeat_interval'),
            is_active=bool(data.get('is_active', True)),
            is_triggered=bool(data.get('is_triggered', False)),
            created_at=data.get('created_at')
        )

    def to_dict(self) -> dict:
        """המרה לדיקשנרי"""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'message': self.message,
            'remind_at': self.remind_at,
            'repeat_type': self.repeat_type,
            'repeat_interval': self.repeat_interval,
            'is_active': 1 if self.is_active else 0
        }


@dataclass
class Assignment:
    """הגשה/מטלה"""
    id: Optional[int] = None
    task_id: int = 0
    course_name: str = ""
    assignment_type: str = "homework"
    weight: Optional[float] = None  # משקל בציון
    submission_link: Optional[str] = None
    grade: Optional[float] = None
    feedback: Optional[str] = None
    submitted_at: Optional[str] = None
    created_at: Optional[str] = None
    # מידע מהמשימה המקושרת
    title: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Assignment':
        """יצירה מדיקשנרי"""
        return cls(
            id=data.get('id'),
            task_id=data.get('task_id', 0),
            course_name=data.get('course_name', ''),
            assignment_type=data.get('assignment_type', 'homework'),
            weight=data.get('weight'),
            submission_link=data.get('submission_link'),
            grade=data.get('grade'),
            feedback=data.get('feedback'),
            submitted_at=data.get('submitted_at'),
            created_at=data.get('created_at'),
            title=data.get('title'),
            due_date=data.get('due_date'),
            status=data.get('status')
        )

    def to_dict(self) -> dict:
        """המרה לדיקשנרי"""
        return {
            'task_id': self.task_id,
            'course_name': self.course_name,
            'assignment_type': self.assignment_type,
            'weight': self.weight,
            'submission_link': self.submission_link
        }

    @property
    def type_hebrew(self) -> str:
        """סוג בעברית"""
        try:
            return AssignmentType(self.assignment_type).hebrew
        except ValueError:
            return self.assignment_type


@dataclass
class StudySession:
    """סשן לימוד"""
    id: Optional[int] = None
    task_id: Optional[int] = None
    course_name: Optional[str] = None
    topic: Optional[str] = None
    planned_start: str = ""
    planned_end: str = ""
    actual_start: Optional[str] = None
    actual_end: Optional[str] = None
    status: str = "planned"
    notes: Optional[str] = None
    productivity_rating: Optional[int] = None  # 1-5
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'StudySession':
        """יצירה מדיקשנרי"""
        return cls(
            id=data.get('id'),
            task_id=data.get('task_id'),
            course_name=data.get('course_name'),
            topic=data.get('topic'),
            planned_start=data.get('planned_start', ''),
            planned_end=data.get('planned_end', ''),
            actual_start=data.get('actual_start'),
            actual_end=data.get('actual_end'),
            status=data.get('status', 'planned'),
            notes=data.get('notes'),
            productivity_rating=data.get('productivity_rating'),
            created_at=data.get('created_at')
        )

    def to_dict(self) -> dict:
        """המרה לדיקשנרי"""
        return {
            'task_id': self.task_id,
            'course_name': self.course_name,
            'topic': self.topic,
            'planned_start': self.planned_start,
            'planned_end': self.planned_end,
            'status': self.status,
            'notes': self.notes
        }

    @property
    def duration_minutes(self) -> Optional[int]:
        """משך בדקות"""
        try:
            start = datetime.strptime(self.planned_start, DATETIME_FORMAT)
            end = datetime.strptime(self.planned_end, DATETIME_FORMAT)
            return int((end - start).total_seconds() / 60)
        except ValueError:
            return None


@dataclass
class Course:
    """קורס"""
    id: Optional[int] = None
    name: str = ""
    code: Optional[str] = None
    lecturer: Optional[str] = None
    credits: Optional[float] = None
    color: str = "blue"
    semester: Optional[str] = None
    year: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Course':
        """יצירה מדיקשנרי"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            code=data.get('code'),
            lecturer=data.get('lecturer'),
            credits=data.get('credits'),
            color=data.get('color', 'blue'),
            semester=data.get('semester'),
            year=data.get('year'),
            notes=data.get('notes'),
            created_at=data.get('created_at')
        )

    def to_dict(self) -> dict:
        """המרה לדיקשנרי"""
        return {
            'name': self.name,
            'code': self.code,
            'lecturer': self.lecturer,
            'credits': self.credits,
            'color': self.color,
            'semester': self.semester,
            'year': self.year,
            'notes': self.notes
        }


@dataclass
class WeeklyScheduleEntry:
    """רשומה בלוח זמנים שבועי"""
    id: Optional[int] = None
    course_id: Optional[int] = None
    day_of_week: int = 0  # 0=ראשון, 6=שבת
    start_time: str = ""
    end_time: str = ""
    room: Optional[str] = None
    schedule_type: str = "lecture"  # lecture, tutorial, lab
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'WeeklyScheduleEntry':
        """יצירה מדיקשנרי"""
        return cls(
            id=data.get('id'),
            course_id=data.get('course_id'),
            day_of_week=data.get('day_of_week', 0),
            start_time=data.get('start_time', ''),
            end_time=data.get('end_time', ''),
            room=data.get('room'),
            schedule_type=data.get('schedule_type', 'lecture'),
            created_at=data.get('created_at')
        )

    @property
    def type_hebrew(self) -> str:
        """סוג בעברית"""
        types = {
            "lecture": "הרצאה",
            "tutorial": "תרגול",
            "lab": "מעבדה",
            "seminar": "סמינר"
        }
        return types.get(self.schedule_type, self.schedule_type)
