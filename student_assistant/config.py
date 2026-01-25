"""
הגדרות תצורה - Configuration Settings
קובץ הגדרות עבור העוזר האישי לסטודנט
"""

import os
from pathlib import Path
from datetime import timedelta

# נתיבי קבצים - File Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "student_assistant.db"

# יצירת תיקיית נתונים אם לא קיימת
DATA_DIR.mkdir(exist_ok=True)

# הגדרות שפה - Language Settings
LANGUAGE = "he"  # Hebrew

# הגדרות תזכורות - Reminder Settings
REMINDER_DEFAULTS = {
    "deadline_warning_days": [7, 3, 1, 0],  # ימים לפני דדליין להתראה
    "study_session_duration": 45,  # דקות
    "break_duration": 15,  # דקות
}

# קטגוריות ברירת מחדל - Default Categories
DEFAULT_CATEGORIES = {
    "homework": "שיעורי בית",
    "exam": "מבחנים",
    "project": "פרויקטים",
    "reading": "קריאה",
    "submission": "הגשות",
    "meeting": "פגישות",
    "personal": "אישי",
    "study": "לימודים",
}

# עדיפויות - Priorities
PRIORITIES = {
    1: {"name": "דחוף מאוד", "color": "red", "emoji": "🔴"},
    2: {"name": "דחוף", "color": "orange", "emoji": "🟠"},
    3: {"name": "רגיל", "color": "yellow", "emoji": "🟡"},
    4: {"name": "נמוך", "color": "green", "emoji": "🟢"},
    5: {"name": "לא דחוף", "color": "blue", "emoji": "🔵"},
}

# סטטוסים - Statuses
STATUSES = {
    "pending": "ממתין",
    "in_progress": "בביצוע",
    "completed": "הושלם",
    "cancelled": "בוטל",
    "overdue": "באיחור",
}

# הודעות מערכת בעברית - Hebrew System Messages
MESSAGES = {
    # הודעות כלליות
    "welcome": "ברוך הבא לעוזר האישי שלך! 📚",
    "goodbye": "להתראות! בהצלחה בלימודים! 🎓",
    "help": "עזרה",

    # משימות
    "task_created": "✅ משימה נוצרה בהצלחה!",
    "task_updated": "📝 משימה עודכנה בהצלחה!",
    "task_deleted": "🗑️ משימה נמחקה בהצלחה!",
    "task_completed": "🎉 כל הכבוד! המשימה הושלמה!",
    "task_not_found": "❌ משימה לא נמצאה",
    "no_tasks": "📭 אין משימות פעילות",

    # תזכורות
    "reminder_set": "⏰ תזכורת הוגדרה בהצלחה!",
    "reminder_triggered": "🔔 תזכורת: {}",
    "deadline_warning": "⚠️ אזהרה: {} ימים לדדליין של '{}'",
    "deadline_today": "🚨 היום הדדליין של '{}'!",
    "deadline_passed": "❗ עבר הדדליין של '{}'!",

    # לוח זמנים
    "schedule_created": "📅 לוח זמנים נוצר בהצלחה!",
    "study_session_start": "📖 זמן ללמוד! התחל סשן לימודים",
    "break_time": "☕ הגיע זמן הפסקה!",

    # ניתוח וסיכום
    "weekly_summary": "📊 סיכום שבועי",
    "productivity_tip": "💡 טיפ: {}",

    # שגיאות
    "invalid_input": "❌ קלט לא תקין. נסה שוב.",
    "invalid_date": "❌ תאריך לא תקין. השתמש בפורמט DD/MM/YYYY",
    "invalid_time": "❌ שעה לא תקינה. השתמש בפורמט HH:MM",

    # פרואקטיביות
    "suggestion_break_task": "💡 הצעה: המשימה '{}' גדולה. האם תרצה לפרק אותה לשלבים קטנים יותר?",
    "suggestion_schedule": "💡 הצעה: יש לך {} משימות השבוע. האם תרצה שאעזור לך לתכנן את הזמן?",
    "no_upcoming": "✨ אין אירועים קרובים. זה הזמן לקדם משימות!",
}

# טיפים ללימוד - Study Tips
STUDY_TIPS = [
    "קח הפסקה קצרה כל 45 דקות לשמירה על ריכוז",
    "חלק משימות גדולות לחלקים קטנים וניתנים לניהול",
    "למד בשעות שבהן אתה הכי ערני",
    "סקור חומר ישן לפני שתלמד חומר חדש",
    "השתמש בטכניקת פומודורו: 25 דקות לימוד, 5 דקות הפסקה",
    "שמור על סביבת לימוד נקייה ומסודרת",
    "הימנע מריבוי משימות - התמקד בדבר אחד בכל פעם",
    "ישן מספיק - שינה חיונית לזיכרון ולמידה",
    "תרגל בעיות במקום רק לקרוא - למידה אקטיבית יעילה יותר",
    "לימוד קבוצתי יכול לעזור להבין נושאים קשים",
]

# פורמט תאריך ושעה - Date/Time Format
DATE_FORMAT = "%d/%m/%Y"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = "%d/%m/%Y %H:%M"

# ימי השבוע בעברית - Hebrew Weekdays
WEEKDAYS_HE = {
    0: "יום ראשון",
    1: "יום שני",
    2: "יום שלישי",
    3: "יום רביעי",
    4: "יום חמישי",
    5: "יום שישי",
    6: "יום שבת",
}

# חודשים בעברית - Hebrew Months
MONTHS_HE = {
    1: "ינואר",
    2: "פברואר",
    3: "מרץ",
    4: "אפריל",
    5: "מאי",
    6: "יוני",
    7: "יולי",
    8: "אוגוסט",
    9: "ספטמבר",
    10: "אוקטובר",
    11: "נובמבר",
    12: "דצמבר",
}
