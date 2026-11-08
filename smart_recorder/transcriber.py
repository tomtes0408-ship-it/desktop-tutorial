"""
תמלול אוטומטי מדויק באמצעות Whisper (faster-whisper) - רץ מקומית, ללא שליחת אודיו לענן.

ברירת המחדל היא המודל large-v3 - המדויק ביותר, כולל לעברית.
אפשר לשנות דרך משתני הסביבה:
    WHISPER_MODEL   (tiny / base / small / medium / large-v3 / turbo)
    WHISPER_DEVICE  (auto / cpu / cuda)
    WHISPER_COMPUTE (auto / int8 / float16 / int8_float16)
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, asdict, field

DEFAULT_MODEL = os.environ.get("WHISPER_MODEL", "large-v3")
DEFAULT_DEVICE = os.environ.get("WHISPER_DEVICE", "auto")
DEFAULT_COMPUTE = os.environ.get("WHISPER_COMPUTE", "auto")


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    language: str
    language_probability: float
    duration: float
    segments: list[Segment] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(s.text for s in self.segments).strip()

    def timestamped_text(self) -> str:
        return "\n".join(f"[{fmt_time(s.start)}] {s.text}" for s in self.segments)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["text"] = self.text
        return d


def fmt_time(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class Transcriber:
    """עוטף את faster-whisper; המודל נטען פעם אחת בלבד (טעינה עצלה ובטוחה לתהליכונים)."""

    def __init__(self, model_size: str = DEFAULT_MODEL, device: str = DEFAULT_DEVICE,
                 compute_type: str = DEFAULT_COMPUTE):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is None:
                from faster_whisper import WhisperModel

                compute = self.compute_type
                if compute == "auto":
                    compute = "default"
                self._model = WhisperModel(self.model_size, device=self.device, compute_type=compute)
        return self._model

    def transcribe(self, audio_path: str, language: str | None = None,
                   on_progress=None) -> Transcript:
        """
        מתמלל קובץ אודיו/וידאו (כל פורמט ש-ffmpeg תומך בו).

        language: קוד שפה ('he', 'en', ...) או None לזיהוי אוטומטי.
        on_progress: פונקציה אופציונלית שמקבלת אחוז התקדמות (0-100).
        """
        model = self._load()
        segments_iter, info = model.transcribe(
            audio_path,
            language=language or None,
            beam_size=5,                       # חיפוש רחב יותר = דיוק גבוה יותר
            vad_filter=True,                   # מסנן שקטים ומונע "הזיות" בקטעים ריקים
            vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=True,   # שומר על הקשר בין משפטים
            temperature=[0.0, 0.2, 0.4, 0.6], # נסיגה הדרגתית במקרה של פענוח כושל
        )

        result = Transcript(
            language=info.language,
            language_probability=round(info.language_probability, 3),
            duration=round(info.duration, 2),
        )
        for seg in segments_iter:
            text = seg.text.strip()
            if text:
                result.segments.append(Segment(round(seg.start, 2), round(seg.end, 2), text))
            if on_progress and info.duration:
                on_progress(min(100, int(seg.end / info.duration * 100)))
        if on_progress:
            on_progress(100)
        return result
