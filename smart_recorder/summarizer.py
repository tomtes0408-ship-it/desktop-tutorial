"""
סיכום חכם ונקודות מפתח באמצעות Claude.

מקבל תמליל עם חותמות זמן ומחזיר אובייקט מובנה (JSON מאומת לפי סכמה):
כותרת, תקציר מנהלים, סיכום מפורט, נקודות מפתח עם זמנים, משימות לביצוע,
החלטות, שאלות פתוחות ונושאים.

דורש ANTHROPIC_API_KEY (או פרופיל `ant auth login`).
"""

from __future__ import annotations

import json
import os

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("CLAUDE_EFFORT", "high")

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "executive_summary": {"type": "string"},
        "detailed_summary": {"type": "array", "items": {"type": "string"}},
        "key_points": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "point": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "importance": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["point", "timestamp", "importance"],
                "additionalProperties": False,
            },
        },
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "owner": {"type": "string"},
                    "due": {"type": "string"},
                },
                "required": ["task", "owner", "due"],
                "additionalProperties": False,
            },
        },
        "decisions": {"type": "array", "items": {"type": "string"}},
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "topics": {"type": "array", "items": {"type": "string"}},
        "sentiment": {"type": "string"},
    },
    "required": [
        "title", "executive_summary", "detailed_summary", "key_points",
        "action_items", "decisions", "open_questions", "topics", "sentiment",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You analyze transcripts of recordings (meetings, lectures, interviews, calls, voice notes) \
and produce a precise, useful summary.

The transcript comes from automatic speech recognition, so it may contain misheard words, missing \
punctuation, or names spelled inconsistently. Infer the intended meaning from context, but never invent \
facts, numbers, names, or commitments that are not supported by the transcript.

Guidelines for each field:
- title: a short, specific title for the recording.
- executive_summary: 2-4 sentences a busy reader can rely on without reading anything else.
- detailed_summary: a few paragraphs following the flow of the recording, one paragraph per main section.
- key_points: the most important facts, insights, and conclusions, in the order they occurred. \
`timestamp` is the [mm:ss] or [hh:mm:ss] marker of the line where the point is made (without brackets). \
Mark `importance` honestly - not everything is high.
- action_items: concrete tasks someone committed to or was asked to do. Use an empty string for owner or \
due when the transcript does not say. Return an empty list if there are none.
- decisions: decisions that were actually made. Empty list if none.
- open_questions: questions or issues left unresolved. Empty list if none.
- topics: 3-8 short topic tags.
- sentiment: one short phrase describing the overall tone.

Write every field in the output language specified by the user."""

LANGUAGE_NAMES = {
    "he": "Hebrew", "en": "English", "ar": "Arabic", "ru": "Russian", "fr": "French",
    "es": "Spanish", "de": "German", "it": "Italian", "pt": "Portuguese", "am": "Amharic",
}


class SummaryError(RuntimeError):
    pass


class Summarizer:
    def __init__(self, model: str = MODEL, effort: str = EFFORT):
        self.model = model
        self.effort = effort
        self._client: anthropic.Anthropic | None = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def summarize(self, timestamped_transcript: str, output_language: str = "he",
                  context: str = "") -> dict:
        if not timestamped_transcript.strip():
            raise SummaryError("התמליל ריק - אין מה לסכם.")

        lang_name = LANGUAGE_NAMES.get(output_language, output_language)
        user_content = (
            f"Output language: {lang_name}\n"
            + (f"Context from the user about this recording: {context}\n" if context else "")
            + f"\n<transcript>\n{timestamped_transcript}\n</transcript>"
        )

        try:
            # סטרימינג מונע timeout בתמלילים ארוכים; fallbacks="default" מנתב
            # בקשה שנדחתה ע"י מסווגי הבטיחות למודל חלופי בצד השרת.
            with self.client.beta.messages.stream(
                model=self.model,
                max_tokens=32000,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=SYSTEM_PROMPT,
                output_config={
                    "effort": self.effort,
                    "format": {"type": "json_schema", "schema": SUMMARY_SCHEMA},
                },
                messages=[{"role": "user", "content": user_content}],
            ) as stream:
                response = stream.get_final_message()
        except anthropic.AuthenticationError as e:
            raise SummaryError("מפתח ה-API של Anthropic חסר או שגוי (ANTHROPIC_API_KEY).") from e
        except anthropic.RateLimitError as e:
            raise SummaryError("חריגה ממגבלת קצב הבקשות - נסו שוב בעוד דקה.") from e
        except anthropic.APIStatusError as e:
            raise SummaryError(f"שגיאת API ({e.status_code}): {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise SummaryError("אין חיבור לשרתי Anthropic - בדקו את חיבור האינטרנט.") from e

        if response.stop_reason == "refusal":
            raise SummaryError("המודל סירב לסכם את התוכן הזה.")
        if response.stop_reason == "max_tokens":
            raise SummaryError("הסיכום נקטע (חריגה מאורך מקסימלי).")

        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise SummaryError("התקבלה תשובה לא תקינה מהמודל.") from e


def summary_to_markdown(summary: dict, transcript_text: str | None = None) -> str:
    """ממיר סיכום (ותמליל אופציונלי) למסמך Markdown לייצוא."""
    imp = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    out = [f"# {summary.get('title', 'סיכום הקלטה')}", ""]
    out += ["## תקציר", summary.get("executive_summary", ""), ""]
    if summary.get("detailed_summary"):
        out += ["## סיכום מפורט"] + [p + "\n" for p in summary["detailed_summary"]]
    if summary.get("key_points"):
        out.append("## נקודות מפתח")
        for kp in summary["key_points"]:
            ts = f" `[{kp['timestamp']}]`" if kp.get("timestamp") else ""
            out.append(f"- {imp.get(kp.get('importance'), '•')} {kp['point']}{ts}")
        out.append("")
    if summary.get("action_items"):
        out.append("## משימות לביצוע")
        for a in summary["action_items"]:
            extra = " — ".join(x for x in [a.get("owner"), a.get("due")] if x)
            out.append(f"- [ ] {a['task']}" + (f" ({extra})" if extra else ""))
        out.append("")
    for key, heading in [("decisions", "החלטות"), ("open_questions", "שאלות פתוחות")]:
        if summary.get(key):
            out += [f"## {heading}"] + [f"- {x}" for x in summary[key]] + [""]
    if summary.get("topics"):
        out += ["**נושאים:** " + ", ".join(summary["topics"]), ""]
    if transcript_text:
        out += ["---", "## תמליל מלא", "", transcript_text]
    return "\n".join(out)
