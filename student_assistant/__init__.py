"""
עוזר אישי לסטודנט - Student Assistant
מערכת ניהול משימות, לו"ז ותזכורות לסטודנטים

A comprehensive task management, scheduling, and reminder system for university students.
All interface and messages are in Hebrew.
"""

__version__ = "1.0.0"
__author__ = "Student Assistant"

from .database import DatabaseManager
from .models import Task, Reminder, Assignment, StudySession, Category
from .task_manager import TaskManager
from .scheduler import SchedulerManager
from .planner import StudyPlanner
from .proactive import ProactiveAssistant
from .ui import StudentAssistantUI

__all__ = [
    'DatabaseManager',
    'Task',
    'Reminder',
    'Assignment',
    'StudySession',
    'Category',
    'TaskManager',
    'SchedulerManager',
    'StudyPlanner',
    'ProactiveAssistant',
    'StudentAssistantUI'
]
