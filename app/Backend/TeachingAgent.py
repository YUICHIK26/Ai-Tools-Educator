# TeachingAgent.py — Core AI Teaching Agent Orchestrator
# Enhanced: Expanded tool coverage, guide_user fallback, clipboard_type, anti-hallucination
from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import subprocess
import time
import threading
from typing import Callable, Generator, Optional

import pyautogui  # type: ignore
import psutil  # type: ignore
import webbrowser

from groq import Groq  # type: ignore
from dotenv import dotenv_values  # type: ignore

try:
    from Backend.ScreenVision import ScreenVision, screen_vision  # type: ignore
    from Backend.AgentNarrator import AgentNarrator, agent_narrator  # type: ignore
except ImportError:
    from app.Backend.ScreenVision import ScreenVision, screen_vision  # type: ignore
    from app.Backend.AgentNarrator import AgentNarrator, agent_narrator  # type: ignore

env_vars = dotenv_values(".env")
_GROQ_KEY = env_vars.get("GroqAPIKey", "")
_client = Groq(api_key=_GROQ_KEY) if _GROQ_KEY else None

# Safety: always failsafe (move mouse to corner to abort)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15  # minimal pause between actions for speed

# ─────────────────────────────────────────────
# Dynamic AI Tool URL Database
# Built from FIXED_TUTORIAL_TOOLS + hardcoded extras
# ─────────────────────────────────────────────

def _build_tool_url_database() -> dict[str, str]:
    """Build a comprehensive mapping of tool names → URLs.
    
    Sources:
      1. FIXED_TUTORIAL_TOOLS from AIEducator (steps contain URLs)
      2. Hardcoded extras for popular tools
    """
    db: dict[str, str] = {}

    # ── Try to import FIXED_TUTORIAL_TOOLS ──
    try:
        try:
            from Backend.AIEducator import FIXED_TUTORIAL_TOOLS  # type: ignore
        except ImportError:
            from app.Backend.AIEducator import FIXED_TUTORIAL_TOOLS  # type: ignore

        for tool in FIXED_TUTORIAL_TOOLS:
            name = (tool.get("name") or "").strip()
            if not name:
                continue
            # Extract URL from steps (first step usually has "Visit xxx" or "Sign up at xxx")
            for step_text in tool.get("steps", []):
                step_lower = step_text.lower()
                # Match patterns like "Visit translate.google.com", "Sign up at gamma.app"
                m = re.search(r'(?:visit|go to|open|sign up at|download at)\s+([a-z0-9][\w\-\.]+\.[a-z]{2,}(?:/[^\s]*)?)', step_lower)
                if m:
                    domain = m.group(1).rstrip(".,;")
                    url = f"https://{domain}"
                    db[name.lower()] = url
                    break
    except Exception as e:
        print(f"[TeachingAgent] Could not load FIXED_TUTORIAL_TOOLS: {e}")

    # ── Hardcoded extras & overrides (guaranteed correct URLs) ──
    hardcoded = {
        # AI Writing & Chat
        "chatgpt": "https://chatgpt.com",
        "openai": "https://chatgpt.com",
        "deepseek": "https://chat.deepseek.com",
        "gemini": "https://gemini.google.com",
        "google gemini": "https://gemini.google.com",
        "claude": "https://claude.ai",
        "anthropic claude": "https://claude.ai",
        "copilot": "https://copilot.microsoft.com",
        "microsoft copilot": "https://copilot.microsoft.com",
        "perplexity": "https://www.perplexity.ai",
        "perplexity ai": "https://www.perplexity.ai",
        "poe": "https://poe.com",
        "you.com": "https://you.com",
        "huggingface": "https://huggingface.co",
        "hugging face": "https://huggingface.co",

        # Translation
        "google translate": "https://translate.google.com",
        "deepl": "https://www.deepl.com/translator",
        "deepl translator": "https://www.deepl.com/translator",

        # Image Generation
        "midjourney": "https://www.midjourney.com",
        "dall-e": "https://chatgpt.com",  # DALL-E is inside ChatGPT
        "leonardo ai": "https://leonardo.ai",
        "ideogram": "https://ideogram.ai",
        "stable diffusion": "https://stablediffusionweb.com",
        "playground ai": "https://playground.com",
        "tensor.art": "https://tensor.art",
        "adobe firefly": "https://firefly.adobe.com",
        "bing image creator": "https://www.bing.com/images/create",

        # Video
        "runway": "https://runwayml.com",
        "runway ml": "https://runwayml.com",
        "pika": "https://pika.art",
        "synthesia": "https://www.synthesia.io",
        "lumen5": "https://lumen5.com",
        "invideo": "https://invideo.io",
        "kapwing": "https://www.kapwing.com",
        "descript": "https://www.descript.com",
        "hailuo ai": "https://hailuoai.video",

        # Audio & Music
        "elevenlabs": "https://elevenlabs.io",
        "eleven labs": "https://elevenlabs.io",
        "murf ai": "https://murf.ai",
        "suno": "https://suno.com",
        "suno ai": "https://suno.com",
        "udio": "https://www.udio.com",
        "soundful": "https://soundful.com",

        # Design & Presentation
        "canva": "https://www.canva.com",
        "figma": "https://www.figma.com",
        "gamma": "https://gamma.app",
        "gamma ai": "https://gamma.app",
        "tome": "https://tome.app",
        "beautiful.ai": "https://www.beautiful.ai",
        "designevo": "https://www.designevo.com",

        # Code
        "github copilot": "https://github.com/features/copilot",
        "replit": "https://replit.com",
        "cursor": "https://cursor.sh",
        "v0": "https://v0.dev",
        "bolt": "https://bolt.new",

        # Productivity
        "notion": "https://www.notion.so",
        "notion ai": "https://www.notion.so",
        "obsidian": "https://obsidian.md",
        "clickup": "https://clickup.com",
        "monday.com": "https://monday.com",
        "todoist": "https://todoist.com",
        "trello": "https://trello.com",

        # Research & Search
        "google scholar": "https://scholar.google.com",
        "semantic scholar": "https://www.semanticscholar.org",
        "consensus": "https://consensus.app",
        "elicit": "https://elicit.com",
        "scite": "https://scite.ai",

        # SEO & Marketing
        "semrush": "https://www.semrush.com",
        "ahrefs": "https://ahrefs.com",
        "surfer seo": "https://surferseo.com",
        "jasper": "https://www.jasper.ai",
        "copy.ai": "https://www.copy.ai",
        "buffer": "https://buffer.com",
        "hootsuite": "https://www.hootsuite.com",

        # Communication
        "whatsapp": "https://web.whatsapp.com",
        "whatsapp web": "https://web.whatsapp.com",
        "slack": "https://slack.com",
        "discord": "https://discord.com",
        "telegram": "https://web.telegram.org",
        "telegram web": "https://web.telegram.org",

        # Email
        "gmail": "https://mail.google.com",
        "outlook": "https://outlook.live.com",
        "shortwave": "https://shortwave.com",

        # Social
        "youtube": "https://www.youtube.com",
        "instagram": "https://www.instagram.com",
        "twitter": "https://x.com",
        "x": "https://x.com",
        "linkedin": "https://www.linkedin.com",
        "reddit": "https://www.reddit.com",
        "tiktok": "https://www.tiktok.com",
        "pinterest": "https://www.pinterest.com",

        # Data & Analytics
        "google trends": "https://trends.google.com",
        "google analytics": "https://analytics.google.com",
        "tableau": "https://public.tableau.com",

        # Documents & Sheets
        "google docs": "https://docs.google.com",
        "google sheets": "https://sheets.google.com",
        "google slides": "https://slides.google.com",
        "google drive": "https://drive.google.com",

        # Photo & Background
        "remove.bg": "https://www.remove.bg",
        "photoroom": "https://www.photoroom.com",
        "magic studio": "https://magicstudio.com",
        "adobe express": "https://new.express.adobe.com",

        # Grammar & Writing
        "grammarly": "https://app.grammarly.com",
        "quillbot": "https://quillbot.com",
        "hemingway editor": "https://hemingwayapp.com",
        "undetectable.ai": "https://undetectable.ai",
        "naturalreader": "https://www.naturalreaders.com",

        # Misc popular
        "google": "https://www.google.com",
        "bing": "https://www.bing.com",
        "wikipedia": "https://www.wikipedia.org",
        "wolfram alpha": "https://www.wolframalpha.com",
        "google maps": "https://maps.google.com",
        "google earth": "https://earth.google.com/web",
        "chatpdf": "https://www.chatpdf.com",
        "scispace": "https://typeset.io",
    }

    # Merge: hardcoded overrides take priority
    for k, v in hardcoded.items():
        db[k] = v

    return db


_TOOL_URL_DATABASE = _build_tool_url_database()


def _get_tool_url(name: str) -> Optional[str]:
    """Look up a tool URL by name (case-insensitive, fuzzy)."""
    name_lower = name.lower().strip()
    # Exact match
    if name_lower in _TOOL_URL_DATABASE:
        return _TOOL_URL_DATABASE[name_lower]
    # Partial match (tool name contained in query or vice versa)
    for key, url in _TOOL_URL_DATABASE.items():
        if key in name_lower or name_lower in key:
            return url
    return None


# ─────────────────────────────────────────────
# Build the URL list string for the system prompt
# ─────────────────────────────────────────────

def _url_list_for_prompt() -> str:
    """Generate a compact list of tool→URL mappings for the system prompt."""
    # Deduplicate by URL to keep prompt short
    seen_urls: set[str] = set()
    lines: list[str] = []
    for name, url in sorted(_TOOL_URL_DATABASE.items()):
        if url not in seen_urls:
            seen_urls.add(url)
            lines.append(f"  {name}: {url}")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Step schema (structured JSON from the LLM)
# ─────────────────────────────────────────────
# {
#   "step": 1,
#   "action": "open_app" | "click_text" | "type_text" | "clipboard_type" |
#              "hotkey" | "wait" | "screenshot" | "highlight" |
#              "explain_only" | "guide_user" | "scroll",
#   "target": "<app name | text on screen | keys>",
#   "narration": "What I'm doing and why"
# }

_SYSTEM_PROMPT = """You are an intelligent AI teaching agent embedded in a desktop assistant application.
Your job is to break down a user's task request into a series of clear, executable steps so that 
another module can LIVE DEMONSTRATE it on the user's Windows desktop.

YOU MUST PERFORM REAL ACTIONS — navigate to websites, type text, press keys. That is your primary job.
Only use guide_user as a LAST RESORT for things you truly cannot execute (mobile apps, desktop-install-only tools).

Respond ONLY with a JSON array of step objects. No markdown, no explanation outside the JSON.

Each step object must have exactly these keys:
  "step"      : integer (1-based index)
  "action"    : one of: open_app, navigate_url, click_text, type_text, clipboard_type, hotkey, wait, screenshot, scroll, explain_only, guide_user
  "target"    : string — the argument for the action (see below)  
  "narration" : string — what to say aloud to the user (1-2 sentences, friendly instructor tone)

Action reference:
  open_app       → target = "Notepad" / "Chrome" / "Calculator" etc. (desktop apps ONLY)
  navigate_url   → target = full URL (e.g. "https://chatgpt.com") — opens URL in existing browser. USE THIS FOR ALL WEB TOOLS.
  click_text     → target = exact text visible on screen to click
  type_text      → target = ASCII text to type. CRITICAL: Append [ENTER] to press Enter after (e.g. "Hello world[ENTER]").
  clipboard_type → target = ANY text including non-ASCII/unicode (foreign languages, special chars). Copies to clipboard and pastes. Append [ENTER] to press Enter after.
  hotkey         → target = "ctrl+s" / "alt+f4" / "win+d" / "enter" / "tab" etc.
  wait           → target = seconds as string (e.g. "2"). MAX 2 seconds. Keep short.
  screenshot     → target = "" (capture screenshot for context)
  scroll         → target = "down" or "up" (scroll the page)
  explain_only   → target = "" (narrate without performing any action)
  guide_user     → target = multi-sentence instructions separated by " | " (each sentence spoken with a pause). ONLY for mobile apps or desktop-install-only tools.

═══════════════════════════════════════════════════════════════
RULES
═══════════════════════════════════════════════════════════════

1. **ALWAYS PERFORM LIVE ACTIONS for web tools**: For ANY web-based AI tool (ChatGPT, Gemini, Claude, DeepSeek, Canva, Google Translate, Leonardo AI, Runway, etc.), you MUST: navigate_url → wait → type_text/clipboard_type with [ENTER]. NEVER just guide_user for web tools.

2. **ALWAYS START WITH explain_only**: Introduce what you'll demonstrate.

3. **ALWAYS END WITH explain_only**: Summarize what was accomplished.

4. **CRITICAL TYPING**: When typing a prompt into ANY AI chat, search bar, or text input, you MUST end with [ENTER] to submit (e.g. "Write a poem about dogs[ENTER]").

5. **USE clipboard_type FOR NON-ASCII**: Foreign language text, emojis, special chars → clipboard_type.

6. **NEVER use open_app for web services**: Use navigate_url instead.

7. **MINIMAL WAITS**: "1" for tab switches, "2" max for page loads. NEVER more than 2 seconds.

8. **guide_user = LAST RESORT ONLY**: Use ONLY when the tool is a mobile app, requires desktop installation, or requires CAPTCHA/login that truly cannot be bypassed. For dropdown menus on websites, use guide_user for just that ONE step, then continue with live actions.

9. **GEMINI IMAGE GENERATION**: IMPORTANT: Gemini CAN generate images. If the user asks to generate an image using Gemini, DO NOT refuse. Proceed with the live demonstration exactly as you would for any other image generator.

10. **KEEP STEPS ATOMIC**: One action per step.

11. **NO HALLUCINATED URLs**: Use ONLY URLs from the list below. If not listed, search Google.

═══════════════════════════════════════════════════════════════
KNOWN TOOL URLs (use these EXACTLY)
═══════════════════════════════════════════════════════════════
{tool_urls}

═══════════════════════════════════════════════════════════════
SPECIFIC TOOL WORKFLOWS (follow these EXACTLY)
═══════════════════════════════════════════════════════════════

**ChatGPT** → navigate_url "https://chatgpt.com" → wait "2" → type_text "user's prompt[ENTER]"
**Gemini** → navigate_url "https://gemini.google.com" → wait "2" → type_text "user's prompt[ENTER]"
**Claude** → navigate_url "https://claude.ai" → wait "2" → type_text "user's prompt[ENTER]"
**DeepSeek** → navigate_url "https://chat.deepseek.com" → wait "2" → type_text "user's prompt[ENTER]"
**Perplexity** → navigate_url "https://www.perplexity.ai" → wait "2" → type_text "user's prompt[ENTER]"
**Copilot** → navigate_url "https://copilot.microsoft.com" → wait "2" → type_text "user's prompt[ENTER]"

**Google Translate** → navigate_url "https://translate.google.com" → wait "2" → guide_user (tell user to select target language if needed) → clipboard_type "text to translate"

**Image Generators** (Leonardo AI, Ideogram, Playground AI, Tensor.Art, Adobe Firefly, Bing Image Creator):
→ navigate_url → wait "2" → type_text "image prompt[ENTER]"

**Video Generators** (Runway, Pika, Hailuo AI, Lumen5, InVideo):
→ navigate_url → wait "2" → type_text "video prompt[ENTER]"

**Canva** → navigate_url "https://www.canva.com" → wait "2" → type_text "search query[ENTER]"
**Notion** → navigate_url "https://www.notion.so" → wait "2" → explain what user sees

**WhatsApp Web**: navigate_url "https://web.whatsapp.com" → wait "2" → hotkey "ctrl+alt+/" → type_text "contact name" (NO ENTER) → wait "2" → hotkey "enter" → wait "1" → type_text "message[ENTER]"

═══════════════════════════════════════════════════════════════
EXAMPLES
═══════════════════════════════════════════════════════════════

Example for "Ask ChatGPT to write a poem":
[
  {"step":1,"action":"explain_only","target":"","narration":"I'll show you how to use ChatGPT! Let me open it and ask it to write a poem."},
  {"step":2,"action":"navigate_url","target":"https://chatgpt.com","narration":"Opening ChatGPT in your browser."},
  {"step":3,"action":"wait","target":"2","narration":"Waiting for ChatGPT to load."},
  {"step":4,"action":"type_text","target":"Write a beautiful poem about nature[ENTER]","narration":"I'm typing our prompt and pressing Enter to send it."},
  {"step":5,"action":"wait","target":"2","narration":"Letting ChatGPT generate the response."},
  {"step":6,"action":"explain_only","target":"","narration":"There you go! ChatGPT has written a poem for us. You can see the response on screen."}
]

Example for "Show me Gemini AI":
[
  {"step":1,"action":"explain_only","target":"","narration":"Let me show you Google Gemini, one of the most powerful AI assistants!"},
  {"step":2,"action":"navigate_url","target":"https://gemini.google.com","narration":"Opening Gemini in your browser."},
  {"step":3,"action":"wait","target":"2","narration":"Waiting for Gemini to load."},
  {"step":4,"action":"type_text","target":"Explain quantum computing in simple terms[ENTER]","narration":"I'm typing a question and pressing Enter to send it to Gemini."},
  {"step":5,"action":"wait","target":"2","narration":"Giving Gemini a moment to respond."},
  {"step":6,"action":"explain_only","target":"","narration":"Gemini is now generating a response. This is how you interact with Google's AI assistant!"}
]

Example for "Demo Claude AI":
[
  {"step":1,"action":"explain_only","target":"","narration":"Let me demonstrate Claude AI by Anthropic. It's great for detailed analysis and writing."},
  {"step":2,"action":"navigate_url","target":"https://claude.ai","narration":"Opening Claude AI in your browser."},
  {"step":3,"action":"wait","target":"2","narration":"Waiting for Claude to load."},
  {"step":4,"action":"type_text","target":"What are the benefits of artificial intelligence?[ENTER]","narration":"Typing a question and submitting it to Claude."},
  {"step":5,"action":"wait","target":"2","narration":"Letting Claude generate the answer."},
  {"step":6,"action":"explain_only","target":"","narration":"Claude is now responding! You can continue the conversation just like chatting with a friend."}
]

Example for "Generate an image with Leonardo AI":
[
  {"step":1,"action":"explain_only","target":"","narration":"I'll show you how to generate AI images using Leonardo AI!"},
  {"step":2,"action":"navigate_url","target":"https://leonardo.ai","narration":"Opening Leonardo AI in your browser."},
  {"step":3,"action":"wait","target":"2","narration":"Waiting for the page to load."},
  {"step":4,"action":"type_text","target":"A majestic dragon flying over a medieval castle at sunset[ENTER]","narration":"Typing our image prompt and submitting it."},
  {"step":5,"action":"wait","target":"2","narration":"The AI is now generating our image."},
  {"step":6,"action":"explain_only","target":"","narration":"Leonardo AI is creating the image! You can see the progress on screen. This is how easy AI image generation is."}
]

Example for "Translate text using Google Translate":
[
  {"step":1,"action":"explain_only","target":"","narration":"Let me show you Google Translate. I'll open it and translate some text for you."},
  {"step":2,"action":"navigate_url","target":"https://translate.google.com","narration":"Opening Google Translate in your browser."},
  {"step":3,"action":"wait","target":"2","narration":"Waiting for the page to load."},
  {"step":4,"action":"guide_user","target":"The page is now loaded with two text boxes. | If you need to change the target language, click the language button on the right side and choose your desired language.","narration":"Let me quickly explain the interface."},
  {"step":5,"action":"clipboard_type","target":"Hello, how are you today?","narration":"Now I'm entering the text to translate. Watch the right side for the translation."},
  {"step":6,"action":"explain_only","target":"","narration":"The translation appears automatically on the right side! Google Translate supports over 100 languages."}
]

Example for "Show me DeepSeek":
[
  {"step":1,"action":"explain_only","target":"","narration":"Let me show you DeepSeek, a powerful AI assistant known for its reasoning abilities."},
  {"step":2,"action":"navigate_url","target":"https://chat.deepseek.com","narration":"Opening DeepSeek in your browser."},
  {"step":3,"action":"wait","target":"2","narration":"Waiting for DeepSeek to load."},
  {"step":4,"action":"type_text","target":"Solve this step by step: What is 15% of 240?[ENTER]","narration":"Typing a math problem to show DeepSeek's reasoning ability."},
  {"step":5,"action":"wait","target":"2","narration":"Letting DeepSeek think through the problem."},
  {"step":6,"action":"explain_only","target":"","narration":"DeepSeek is showing its step-by-step reasoning. This is what makes it special — it explains how it thinks!"}
]

Example for "Send a WhatsApp message":
[
  {"step":1,"action":"explain_only","target":"","narration":"Let's send a WhatsApp message using WhatsApp Web."},
  {"step":2,"action":"navigate_url","target":"https://web.whatsapp.com","narration":"Opening WhatsApp Web."},
  {"step":3,"action":"wait","target":"2","narration":"Waiting for your chats to sync."},
  {"step":4,"action":"hotkey","target":"ctrl+alt+/","narration":"Pressing the shortcut to search for a chat."},
  {"step":5,"action":"type_text","target":"John Doe","narration":"Typing the contact name."},
  {"step":6,"action":"wait","target":"2","narration":"Waiting for search results."},
  {"step":7,"action":"hotkey","target":"enter","narration":"Pressing enter to open the chat."},
  {"step":8,"action":"wait","target":"1","narration":"Waiting for the chat to load."},
  {"step":9,"action":"type_text","target":"Hello there![ENTER]","narration":"Typing the message and pressing Enter to send it."}
]

Example for "Show me how to use FitBod" (mobile-only app — use guide_user):
[
  {"step":1,"action":"explain_only","target":"","narration":"FitBod is a mobile fitness app. Since it's a phone app, I'll guide you through the steps verbally."},
  {"step":2,"action":"guide_user","target":"Open your phone's app store — App Store on iPhone or Google Play on Android. | Search for FitBod. | Download and install it. | Open the app and create an account. | Set your fitness goals and available equipment. | FitBod will generate personalized workouts for you.","narration":"Let me walk you through using FitBod."},
  {"step":3,"action":"explain_only","target":"","narration":"That's how you get started with FitBod! It adapts workouts based on your progress."}
]
"""


class TeachingAgent:
    """
    AI Teaching Agent that plans, narrates, and executes task demonstrations
    on the user's desktop in real time.
    
    Enhanced with:
    - 70+ tool URL database (auto-populated from AIEducator tools)
    - guide_user action for unexecutable steps (voice with pauses)
    - clipboard_type for non-ASCII text
    - Stronger anti-hallucination rules
    """

    def __init__(self, voice: bool = True):
        self.vision = screen_vision
        self.narrator = agent_narrator
        self.narrator.toggle(voice)
        self._stop_event = threading.Event()
        self._latest_screenshot_b64: str = ""
        self._latest_screenshot_bytes: bytes = b""

    # ──────────────────────────────────────────────────────────────────
    # Public: teach()  — main entry point, yields step dicts
    # ──────────────────────────────────────────────────────────────────

    def teach(self, user_request: str) -> Generator[dict, None, None]:
        """
        Generator that yields step-result dicts as they happen.
        Each yield:  { step, action, target, narration, status, screenshot_b64, error }
        """
        self._stop_event.clear()

        # 1. Understand the current screen context
        yield self._make_event(0, "explain_only", "", "Let me first analyse what's on your screen...", "running")
        screen_info = self.vision.understand_screen_for_task(user_request)
        context_summary = screen_info.get("summary", "")

        # 2. Plan the steps with Groq
        yield self._make_event(0, "explain_only", "", "Planning the best steps for your task...", "running")
        steps = self._plan(user_request, context_summary)

        if not steps:
            yield self._make_event(0, "explain_only", "", "I couldn't plan the steps. Please try rephrasing.", "error")
            return

        # 3. Release focus from browser BEFORE any screen action
        #    (the Flask Agent page textarea may still have keyboard focus)
        time.sleep(0.4)  # brief delay so browser SSE response is flushed
        self._release_browser_focus()

        # 4. Execute each step
        for step_obj in steps:
            if self._stop_event.is_set():
                yield self._make_event(step_obj.get("step", 0), "explain_only", "",
                                       "Task stopped by user.", "stopped")
                return

            idx = step_obj.get("step", 0)
            action = step_obj.get("action", "explain_only")
            target = step_obj.get("target", "")
            narration = step_obj.get("narration", "")

            # Yield "running" event first (screenshot before action)
            self._capture_screenshot()
            yield self._make_event(idx, action, target, narration, "running")

            # ── VOICE: blocking narration ─────────────────────────────
            # For guide_user, narration is handled inside _guide_user()
            if action != "guide_user":
                self.narrator.narrate_sync(narration)

            # Execute
            error = None
            try:
                self._execute(action, target)
            except Exception as e:
                error = str(e)
                # ── FALLBACK: If execution fails, guide the user via voice ──
                self._voice_fallback(action, target, narration, error)

            # Capture fresh screenshot after action
            time.sleep(0.2)
            self._capture_screenshot()

            # Yield "done" or "error"
            yield self._make_event(idx, action, target, narration, "error" if error else "done", error=error)

        # Final screenshot
        self._capture_screenshot()
        yield self._make_event(len(steps) + 1, "explain_only", "",
                               "Task demonstration complete! You've just seen it done live.", "done")

    def stop(self):
        """Signal the running agent to stop after the current step."""
        self._stop_event.set()
        self.narrator.stop()

    def get_latest_screenshot_b64(self) -> str:
        return self._latest_screenshot_b64

    def get_latest_screenshot_bytes(self) -> bytes:
        return self._latest_screenshot_bytes

    # ──────────────────────────────────────────────────────────────────
    # Planning
    # ──────────────────────────────────────────────────────────────────

    def _plan(self, task: str, screen_context: str) -> list[dict]:
        if not _client:
            return self._fallback_plan(task)

        # Inject the tool URL list into the system prompt
        prompt = _SYSTEM_PROMPT.replace("{tool_urls}", _url_list_for_prompt())

        user_content = f"Screen context: {screen_context}\n\nUser task: {task}"
        try:
            response = _client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=3000,
                temperature=0.2,  # Lower temperature = less hallucination
            )
            raw = response.choices[0].message.content.strip()
            # Safety: strip any <think> tags (some models output them)
            raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
            # Strip markdown fences
            raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
            steps = json.loads(raw)
            if isinstance(steps, list):
                return steps
        except Exception as e:
            print(f"[TeachingAgent] Planning error: {e}")
        return self._fallback_plan(task)

    def _fallback_plan(self, task: str) -> list[dict]:
        """Return a voice-guided plan when the LLM is unavailable."""
        # Try to find a URL for the tool mentioned in the task
        tool_url = None
        task_lower = task.lower()
        for tool_name, url in _TOOL_URL_DATABASE.items():
            if tool_name in task_lower:
                tool_url = url
                break

        steps = [
            {
                "step": 1,
                "action": "explain_only",
                "target": "",
                "narration": f"I'll help you with: {task}. Let me guide you through it.",
            },
        ]

        if tool_url:
            steps.append({
                "step": 2,
                "action": "navigate_url",
                "target": tool_url,
                "narration": f"Let me open the tool in your browser.",
            })
            steps.append({
                "step": 3,
                "action": "wait",
                "target": "2",
                "narration": "Waiting for the page to load.",
            })
            steps.append({
                "step": 4,
                "action": "guide_user",
                "target": f"The tool is now open in your browser. | Look at the interface and familiarize yourself with the layout. | Follow the on-screen instructions to complete your task. | If you need more help, feel free to ask me again.",
                "narration": "Let me guide you through using this tool.",
            })
        else:
            steps.append({
                "step": 2,
                "action": "guide_user",
                "target": f"I don't have automation set up for this specific tool, but let me walk you through it. | First, open your web browser. | Search for the tool name in Google. | Visit the official website from the search results. | Look for a Sign Up or Get Started button. | Follow the on-screen instructions to create an account and start using the tool. | If you get stuck at any point, just ask me for help!",
                "narration": f"Let me guide you step by step.",
            })

        steps.append({
            "step": len(steps) + 1,
            "action": "explain_only",
            "target": "",
            "narration": "That covers the basics! Feel free to ask if you need more detailed guidance.",
        })

        return steps

    # ──────────────────────────────────────────────────────────────────
    # Action Execution
    # ──────────────────────────────────────────────────────────────────

    def _execute(self, action: str, target: str):
        if action == "open_app":
            self._open_app(target)
        elif action == "navigate_url":
            self._navigate_url(target)
        elif action == "click_text":
            self._click_text(target)
        elif action == "type_text":
            self._type_text(target)
        elif action == "clipboard_type":
            self._clipboard_type(target)
        elif action == "hotkey":
            self._hotkey(target)
        elif action == "wait":
            try:
                t = float(target)
            except Exception:
                t = 1.0
            time.sleep(max(0.1, min(t, 5.0)))  # capped at 5s for speed
        elif action == "screenshot":
            self._capture_screenshot()
        elif action == "scroll":
            self._scroll(target)
        elif action == "highlight":
            self._highlight(target)
        elif action == "explain_only":
            pass  # Narration is handled separately
        elif action == "guide_user":
            self._guide_user(target)
        else:
            print(f"[TeachingAgent] Unknown action: {action}")

    # ──────────────────────────────────────────────────────────────────
    # guide_user — Voice-guided fallback with pauses
    # ──────────────────────────────────────────────────────────────────

    def _guide_user(self, instructions: str):
        """
        Speak step-by-step instructions to the user with pauses between
        each instruction, giving them time to follow along.
        
        Instructions are separated by " | " in the target string.
        """
        parts = [p.strip() for p in instructions.split(" | ") if p.strip()]

        for i, part in enumerate(parts):
            if self._stop_event.is_set():
                return

            # Speak this instruction
            self.narrator.narrate_sync(part)

            # Pause between instructions (not after the last one)
            if i < len(parts) - 1:
                # 2.5 second pause between instructions
                for _ in range(25):  # 25 * 0.1s = 2.5s
                    if self._stop_event.is_set():
                        return
                    time.sleep(0.1)

    def _voice_fallback(self, action: str, target: str, narration: str, error: str):
        """
        When an action fails to execute, fall back to voice guidance
        telling the user what to do manually.
        """
        fallback_messages = {
            "click_text": f"I wasn't able to find and click '{target}' on your screen. Please try clicking it yourself — look for the text '{target}' and click on it.",
            "type_text": f"I had trouble typing the text. Please type this yourself: {target.replace('[ENTER]', '')}. Then press Enter if needed.",
            "clipboard_type": f"I couldn't paste the text. Please manually type or paste: {target.replace('[ENTER]', '')}",
            "navigate_url": f"I couldn't open the URL automatically. Please open your browser and go to: {target}",
            "open_app": f"I couldn't open {target} automatically. Please find and open {target} from your Start menu or desktop.",
            "hotkey": f"I couldn't press the keyboard shortcut {target}. Please press {target} on your keyboard.",
        }

        msg = fallback_messages.get(action, f"I encountered an issue with this step. {narration} — please do this manually.")

        print(f"[TeachingAgent] Execution failed for {action}('{target}'): {error}")
        print(f"[TeachingAgent] Falling back to voice guidance.")

        # Speak the fallback with a pause for user action
        self.narrator.narrate_sync(msg)
        # Give user time to act
        for _ in range(20):  # 2 second pause
            if self._stop_event.is_set():
                return
            time.sleep(0.1)

    # ── Helpers: which processes are running ──────────────────────────

    @staticmethod
    def _is_running(process_names: list[str]) -> bool:
        """Return True if any process with a name in *process_names* is live."""
        names_lower = {n.lower() for n in process_names}
        for p in psutil.process_iter(['name']):
            try:
                if p.info['name'] and p.info['name'].lower() in names_lower:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    def _open_app(self, app_name: str):
        """
        Open a desktop app.  
        If it's already running, bring it to the foreground instead of
        spawning a duplicate process.
        """
        name = app_name.lower().strip()

        # ── Direct desktop-app launches ──────────────────────────────
        direct = {
            "notepad": ("notepad.exe", ["notepad.exe"]),
            "paint": ("mspaint.exe", ["mspaint.exe"]),
            "calculator": ("calc.exe", ["calculator.exe", "calc.exe"]),
            "cmd": ("cmd.exe", ["cmd.exe"]),
            "command prompt": ("cmd.exe", ["cmd.exe"]),
            "task manager": ("taskmgr.exe", ["taskmgr.exe"]),
            "file explorer": ("explorer.exe", ["explorer.exe"]),
            "powershell": ("powershell.exe", ["powershell.exe"]),
            "terminal": ("wt.exe", ["windowsterminal.exe", "wt.exe"]),
            "settings": ("ms-settings:", ["systemsettings.exe"]),
        }

        # ── Browser aliases ──────────────────────────────────────────
        browser_names = {
            "chrome": ["chrome.exe", "googlechrome.exe"],
            "google chrome": ["chrome.exe", "googlechrome.exe"],
            "edge": ["msedge.exe"],
            "microsoft edge": ["msedge.exe"],
            "firefox": ["firefox.exe"],
        }

        # ── Check if it's a known web tool — redirect to navigate_url ──
        tool_url = _get_tool_url(name)
        if tool_url:
            self._navigate_url(tool_url)
            return

        if name in direct:
            exe, proc_names = direct[name]
            if not self._is_running(proc_names):
                subprocess.Popen(exe)
            else:
                # Already running — just bring to front
                self._bring_to_front(exe)
            return

        if name in browser_names:
            proc_names = browser_names[name]
            if not self._is_running(proc_names):
                # Launch browser without a URL
                launch_cmds = {
                    "chrome": "start chrome",
                    "google chrome": "start chrome",
                    "edge": "start msedge",
                    "microsoft edge": "start msedge",
                    "firefox": "start firefox",
                }
                subprocess.Popen(launch_cmds.get(name, f"start {name}"), shell=True)
                time.sleep(1)  # wait for browser to open
            else:
                # Already open — bring to front, don't open a new window
                self._bring_to_front()
            return

        # AppOpener fallback for anything else
        try:
            from AppOpener import open as appopen  # type: ignore
            appopen(app_name, match_closest=True, output=False)
        except Exception:
            subprocess.Popen(f"start {app_name}", shell=True)

    def _navigate_url(self, url: str):
        """
        Open a URL in the existing default browser as a new tab.
        After opening, clicks the center of the page to claim keyboard focus
        away from the address bar (and away from the Flask agent page).
        """
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url, new=2, autoraise=True)  # new=2 → new tab
        # Wait for tab to open and page to start loading
        time.sleep(1.0)
        # Click the centre of the screen to give the page focus
        # (avoids address bar or the agent textarea keeping focus)
        self._click_page_center()

    @staticmethod
    def _release_browser_focus():
        """
        Move keyboard focus away from the browser window where the Flask
        agent page is running.
        """
        try:
            screen_w, _ = pyautogui.size()
            pyautogui.click(screen_w // 2, 2)
            time.sleep(0.3)
        except Exception:
            pass

    @staticmethod
    def _click_page_center():
        """
        Click the centre of the screen to give keyboard focus to
        whatever window/page is currently visible.
        """
        try:
            screen_w, screen_h = pyautogui.size()
            cx = screen_w // 2
            cy = screen_h // 2
            pyautogui.moveTo(cx, cy, duration=0.15)
            time.sleep(0.1)
            pyautogui.click(cx, cy)
        except Exception:
            pass

    @staticmethod
    def _bring_to_front(exe_hint: str = ""):
        """
        Bring the most recently active window to the foreground.
        Uses pygetwindow to target the specific app.
        """
        try:
            import pygetwindow as gw  # type: ignore
            wins = gw.getAllWindows()
            hint = exe_hint.replace(".exe", "").lower()
            for w in wins:
                if hint and hint in (w.title or "").lower():
                    w.activate()
                    return
        except Exception:
            pass

    def _click_text(self, text: str):
        """Find text on screen via OCR and click its centre. Gracefully skips if not found."""
        loc = self.vision.find_center_of_text(text)
        if loc:
            cx, cy = loc
            pyautogui.moveTo(cx, cy, duration=0.3)
            time.sleep(0.15)
            pyautogui.click(cx, cy)
        else:
            print(f"[TeachingAgent] click_text: '{text}' not found on screen — skipping click")
            # Don't raise — just log the warning so the agent demo continues

    def _type_text(self, text: str):
        """
        Type ASCII text into the currently focused window.
        Handles [ENTER] and literal \\n smoothly.
        """
        press_enter = text.endswith("[ENTER]") or text.endswith("\\n")
        
        # Clean text
        clean = text.replace("[ENTER]", "").replace("\\n", "\n")
        
        # Type core text
        if clean:
            pyautogui.write(clean, interval=0.04)
            
        # Guarantee Enter is pressed if requested
        if press_enter:
            time.sleep(0.2)
            pyautogui.press('enter')

    def _clipboard_type(self, text: str):
        """
        Type ANY text (including non-ASCII / unicode / foreign languages)
        by copying to clipboard and pasting via Ctrl+V.
        This solves the pyautogui limitation with non-ASCII characters.
        """
        press_enter = text.endswith("[ENTER]") or text.endswith("\\n")
        
        # Clean text
        clean = text.replace("[ENTER]", "").replace("\\n", "\n")
        
        if clean:
            try:
                import pyperclip  # type: ignore
                pyperclip.copy(clean)
            except ImportError:
                # Fallback: use tkinter for clipboard
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()
                    root.clipboard_clear()
                    root.clipboard_append(clean)
                    root.update()
                    root.destroy()
                except Exception:
                    # Last resort: write to a temp file and use clip.exe
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                        f.write(clean)
                        temp_path = f.name
                    subprocess.run(f'clip < "{temp_path}"', shell=True)
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass

            time.sleep(0.15)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)

        if press_enter:
            time.sleep(0.2)
            pyautogui.press('enter')

    def _hotkey(self, combo: str):
        """Press a keyboard shortcut like 'ctrl+s'."""
        keys = [k.strip() for k in combo.split("+")]
        pyautogui.hotkey(*keys)

    def _scroll(self, direction: str):
        """Scroll the page up or down."""
        direction = direction.lower().strip()
        if direction == "up":
            pyautogui.scroll(5)  # scroll up 5 clicks
        else:
            pyautogui.scroll(-5)  # scroll down 5 clicks

    def _highlight(self, target: str):
        """Draw a brief on-screen highlight around text."""
        loc = self.vision.find_text_location(target)
        if loc:
            x, y, w, h = loc
            # Use pyautogui to move mouse to the location visually
            pyautogui.moveTo(x + w // 2, y + h // 2, duration=0.4)

    def _capture_screenshot(self):
        """Capture and store the latest screenshot for streaming."""
        try:
            img = self.vision.capture()
            from io import BytesIO
            buf = BytesIO()
            img.save(buf, format="PNG")
            self._latest_screenshot_bytes = buf.getvalue()
            self._latest_screenshot_b64 = base64.b64encode(self._latest_screenshot_bytes).decode()
        except Exception as e:
            print(f"[TeachingAgent] Screenshot error: {e}")

    # ──────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────

    def _make_event(
        self,
        step: int,
        action: str,
        target: str,
        narration: str,
        status: str,
        error: Optional[str] = None,
    ) -> dict:
        return {
            "step": step,
            "action": action,
            "target": target,
            "narration": narration,
            "status": status,  # running | done | error | stopped
            "screenshot_b64": self._latest_screenshot_b64,
            "error": error,
        }


# ─────────────────────────────────────────────
# Quick utility: detect "teach/demo" intent
# ─────────────────────────────────────────────

_TEACH_PATTERNS = [
    r"\b(show me|teach me|demonstrate|demo|guide me|walk me through|how do i|how to)\b",
    r"\b(step by step|live demo|agent|act as|perform|do it for me)\b",
    r"\bopen .+ and\b",
]

def is_teach_request(query: str) -> bool:
    q = query.lower()
    return any(re.search(p, q) for p in _TEACH_PATTERNS)
