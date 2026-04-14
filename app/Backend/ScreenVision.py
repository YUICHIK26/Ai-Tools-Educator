# ScreenVision.py — Enhanced screen capture and Groq Vision analysis
from __future__ import annotations

import base64
import io
import os
import time
from typing import Optional

import pyautogui
from PIL import Image, ImageDraw, ImageFont

try:
    import pytesseract  # type: ignore
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    _HAS_TESSERACT = True
except Exception:
    _HAS_TESSERACT = False

from groq import Groq
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
_GROQ_KEY = env_vars.get("GroqAPIKey", "")
_client = Groq(api_key=_GROQ_KEY) if _GROQ_KEY else None

# Colour palette for step annotations
_PALETTE = [
    "#FF5F6D", "#FFC371", "#2AF598", "#08AEEA",
    "#DA22FF", "#FF6E7F", "#43E97B", "#38F9D7",
]

SCREENSHOTS_DIR = os.path.join("Data", "Screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


class ScreenVision:
    """Computer Vision wrapper: capture, encode, annotate, and AI-describe the screen."""

    # ──────────────────────────────────────────────────────────────────
    # Capture helpers
    # ──────────────────────────────────────────────────────────────────

    def capture(self, region=None) -> Image.Image:
        """Capture full screen (or a region) and return a PIL Image."""
        try:
            if region:
                return pyautogui.screenshot(region=region)
            return pyautogui.screenshot()
        except Exception as e:
            # Return a blank grey image so the rest of the pipeline can continue
            img = Image.new("RGB", (1280, 720), color=(30, 30, 30))
            return img

    def capture_and_encode(self, region=None) -> str:
        """Capture screen and return base64-encoded PNG string."""
        img = self.capture(region=region)
        return self._img_to_b64(img)

    def save_screenshot(self, filename: Optional[str] = None) -> str:
        """Save a screenshot and return its file path."""
        if not filename:
            filename = f"screenshot_{int(time.time())}.png"
        path = os.path.join(SCREENSHOTS_DIR, filename)
        img = self.capture()
        img.save(path)
        return path

    # ──────────────────────────────────────────────────────────────────
    # OCR helpers
    # ──────────────────────────────────────────────────────────────────

    def extract_text(self, region=None) -> str:
        """Extract visible text from the screen via OCR."""
        if not _HAS_TESSERACT:
            return ""
        try:
            img = self.capture(region=region)
            text = pytesseract.image_to_string(img)
            return text.strip() if text else ""
        except Exception:
            return ""

    def find_text_location(self, text: str):
        """
        Find the first on-screen bounding box for *text* using OCR.
        Returns (x, y, w, h) or None.
        """
        if not _HAS_TESSERACT:
            return None
        try:
            img = self.capture()
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            # Make Pyre happy by typing the dict arrays from tesseract
            texts: list[str] = data.get("text", [])
            lefts: list[int] = data.get("left", [])
            tops: list[int] = data.get("top", [])
            widths: list[int] = data.get("width", [])
            heights: list[int] = data.get("height", [])
            
            needles = text.lower().split()
            texts_str = [str(t) for t in texts]
            for i, word in enumerate(texts_str):
                if word.lower() in needles[0]:
                    x = int(lefts[i])
                    y = int(tops[i])
                    w = int(widths[i])
                    h = int(heights[i])
                    if w > 0 and h > 0:
                        return (x, y, w, h)
        except Exception:
            pass
        return None

    def find_center_of_text(self, text: str):
        """Return the (cx, cy) screen coordinate of the named text, or None."""
        loc = self.find_text_location(text)
        if loc:
            x, y, w, h = loc
            return (x + w // 2, y + h // 2)
        return None

    # ──────────────────────────────────────────────────────────────────
    # Annotation helpers
    # ──────────────────────────────────────────────────────────────────

    def annotate(
        self,
        boxes: list[tuple],  # list of (x, y, w, h)
        labels: list[str],
        highlight_box: Optional[tuple] = None,
    ) -> tuple[bytes, str]:
        """
        Draw coloured rectangles + labels on a screenshot.
        Returns (png_bytes, base64_str).
        """
        img = self.capture().convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for idx, (box, label) in enumerate(zip(boxes, labels)):
            colour = _PALETTE[idx % len(_PALETTE)]
            rgb = self._hex_to_rgba(colour, alpha=90)
            border = self._hex_to_rgba(colour, alpha=220)
            x, y, w, h = (int(v) for v in box)
            draw.rectangle([x, y, x + w, y + h], fill=rgb, outline=border, width=3)
            # Label badge
            draw.rectangle([x, y - 22, x + 120, y], fill=border)
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except Exception:
                font = ImageFont.load_default()
            label_str = str(label) if label else ""
            draw.text((x + 4, y - 20), label_str[:18], fill="white", font=font)

        # Optional pulsing highlight box
        if highlight_box:
            hx, hy, hw, hh = (int(v) for v in highlight_box)
            bright = self._hex_to_rgba("#FFFFFF", alpha=50)
            draw.rectangle([hx - 6, hy - 6, hx + hw + 6, hy + hh + 6],
                           fill=None, outline=bright, width=5)

        combined = Image.alpha_composite(img, overlay).convert("RGB")
        png_bytes = self._img_to_bytes(combined)
        return png_bytes, base64.b64encode(png_bytes).decode()

    # ──────────────────────────────────────────────────────────────────
    # Groq Vision AI
    # ──────────────────────────────────────────────────────────────────

    def describe_screen(self, question: str = "What application is open and what can I do here?") -> str:
        """
        Send a screenshot to Groq Vision and get an AI description/answer.
        Returns a plain-text description.
        """
        if not _client:
            return "Screen vision unavailable: Groq API key not configured."

        try:
            b64 = self.capture_and_encode()
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64}"
                            },
                        },
                        {
                            "type": "text",
                            "text": question,
                        },
                    ],
                }
            ]
            response = _client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=messages,
                max_tokens=512,
                temperature=0.3,
            )
            return str(response.choices[0].message.content).strip()
        except Exception as e:
            # Fallback: use OCR-based description
            try:
                ext_text = self.extract_text()
                text = str(ext_text)[:400] if ext_text else ""
                return f"Screen contains: {text}" if text else f"Screen analysis failed: {e}"
            except Exception:
                return f"Screen analysis failed: {e}"

    def understand_screen_for_task(self, task: str) -> dict:
        """
        Analyse the screen in context of a task.
        Returns dict with keys: summary, app_visible, suggested_first_action
        """
        if not _client:
            ext_text = self.extract_text()
            text = str(ext_text)[:300] if ext_text else ""
            return {
                "summary": text or "Screen content unavailable",
                "app_visible": "unknown",
                "suggested_first_action": "Proceed with task",
            }

        prompt = f"""You are a computer vision assistant analysing a screenshot to help an AI agent perform a task.
Task: "{task}"

Analyse the screenshot and respond ONLY with valid JSON (no markdown):
{{
  "summary": "brief description of what's visible on screen",
  "app_visible": "name of the primary app/window visible or 'desktop'",
  "suggested_first_action": "the single most sensible first action to start the task"
}}"""
        try:
            b64 = self.capture_and_encode()
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            raw_response = _client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=messages,
                max_tokens=300,
                temperature=0.2,
            )
            raw = str(raw_response.choices[0].message.content).strip()

            import json, re
            # Strip markdown fences if present
            raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
            return json.loads(raw)
        except Exception as e:
            return {
                "summary": f"Could not analyse screen: {e}",
                "app_visible": "unknown",
                "suggested_first_action": "Proceed with task",
            }

    # ──────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _img_to_b64(img: Image.Image) -> str:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    @staticmethod
    def _img_to_bytes(img: Image.Image) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b, alpha)


# Module-level singleton
screen_vision = ScreenVision()
