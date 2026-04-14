# AgentNarrator.py — Non-blocking, serialised voice narration for the Teaching Agent
from __future__ import annotations

import threading
import time

# Re-use the updated TTS pipeline (now thread-safe with its own _mixer_lock)
try:
    from Backend.TextToSpeech import TTS  # type: ignore
    _HAS_TTS = True
except Exception:
    try:
        from app.Backend.TextToSpeech import TTS  # type: ignore
        _HAS_TTS = True
    except Exception:
        _HAS_TTS = False


class AgentNarrator:
    """
    Speaks agent step narrations via the existing EdgeTTS/pygame pipeline.

    Key guarantees
    ──────────────
    • Non-blocking: each narrate() call returns immediately.
    • Serialised: the new narration only starts AFTER the previous one has
      finished (or been stopped), so pygame never has two instances fighting
      over the audio device.
    • Safe stop: calling stop() signals the current speech to end; the worker
      thread exits cleanly and the temp file is deleted by TextToSpeech.
    """

    def __init__(self):
        self._thread: threading.Thread | None = None
        self._thread_lock = threading.Lock()  # protects _thread
        self._stop_event = threading.Event()
        self.enabled = True

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    def narrate(self, text: str) -> None:
        """Fire-and-forget narration. Stops any in-progress speech first."""
        if not self.enabled or not text.strip():
            return
        self._stop_and_join(timeout=0.5)   # abort previous, wait max 0.5 s
        self._start(text)

    def narrate_sync(self, text: str) -> None:
        """Blocking narration (for tests or final summary)."""
        if not self.enabled or not text.strip():
            return
        self._stop_and_join(timeout=1.0)
        self._start(text)
        with self._thread_lock:
            t = self._thread
        if t:
            t.join()

    def stop(self) -> None:
        """Signal the current narration to stop and wait briefly."""
        self._stop_and_join(timeout=0.5)

    def toggle(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            self.stop()

    # ──────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────

    def _start(self, text: str) -> None:
        event = threading.Event()
        self._stop_event = event  # replace with fresh event

        def _run():
            try:
                if _HAS_TTS:
                    # Pass a func that lets TTS check if it should keep going
                    TTS(text, func=lambda r=None: not event.is_set())
            except Exception as e:
                print(f"[AgentNarrator] TTS error: {e}")

        t = threading.Thread(target=_run, daemon=True, name="AgentNarrator-TTS")
        with self._thread_lock:
            self._thread = t
        t.start()

    def _stop_and_join(self, timeout: float = 0.5) -> None:
        """Signal stop and wait for the running thread to finish."""
        self._stop_event.set()
        with self._thread_lock:
            t = self._thread
        if t and t.is_alive():
            t.join(timeout=timeout)
        with self._thread_lock:
            self._thread = None

    def __del__(self):
        try:
            self._stop_and_join(timeout=0.2)
        except Exception:
            pass


# Module-level singleton
agent_narrator = AgentNarrator()
