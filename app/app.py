# app/app.py
from flask import Flask, render_template, request, jsonify, send_from_directory

import os
import sys

# Allow running as a module (python -m app.app) or as a script (python app.py)
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

try:
    from Backend.Model import FirstLayerDMM
except Exception as e:  # pragma: no cover
    # Allow the web app to run even if optional LLM routing deps aren't installed.
    print(f"[WARN] Failed to import Decision Model (Backend.Model): {e}")
    
    def FirstLayerDMM(prompt: str):
        # Safe fallback: route everything to general chat.
        return [f"general {prompt}"]
try:
    from Backend.RealtimeSearchEngine import RealtimeSearchEngine
except Exception as e:  # pragma: no cover
    print(f"[WARN] Failed to import RealtimeSearchEngine: {e}")

    def RealtimeSearchEngine(prompt: str) -> str:
        return "Realtime search is unavailable because required dependencies are missing."
from Backend.Automation import Automation
from Backend.AutomationSummary import summarize_automation
try:
    from Backend.SpeechToText import SpeechRecognition
except Exception as e:  # pragma: no cover
    print(f"[WARN] Failed to import SpeechToText: {e}")

    def SpeechRecognition():
        raise RuntimeError('Speech recognition is unavailable because dependencies are missing')
from Backend.Chatbot import ChatBot
from Backend.ConversationStore import ConversationStore
try:
    from Backend.TextToSpeech import TextToSpeech
except Exception as e:  # pragma: no cover
    print(f"[WARN] Failed to import TextToSpeech: {e}")

    def TextToSpeech(text: str):
        # No-op fallback
        return None
try:
    from Backend.AIEducator import AIEducator, FIXED_TUTORIAL_TOOLS
except Exception as e:  # pragma: no cover
    print(f"[WARN] Failed to import AIEducator: {e}")

    AIEducator = None  # type: ignore
    FIXED_TUTORIAL_TOOLS = []
try:
    from Backend.TeachingAgent import TeachingAgent, is_teach_request  # type: ignore
except Exception as e:  # pragma: no cover
    print(f"[WARN] Failed to import TeachingAgent: {e}")
    TeachingAgent = None  # type: ignore
    def is_teach_request(q): return False
from Backend.SystemControls import parse_brightness_volume_query, execute_parsed_control, toggle_hotspot, toggle_bluetooth
from dotenv import dotenv_values
from flask import Response, stream_with_context
import asyncio
import threading
import json
import os
import subprocess
import re


def _speak_async(text: str) -> None:
    """Run TextToSpeech in a background thread so HTTP responses aren't blocked."""
    try:
        t = threading.Thread(target=TextToSpeech, args=(text,), daemon=True)
        t.start()
    except Exception as e:
        print(f"Error starting async TTS: {e}")

app = Flask(__name__)

# Persistent multi-chat store
conv_store = ConversationStore()

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = "AI Educator"

# Navbar menu items
navbar_menu = [
    {"name": "Dashboard", "url": "/"},
    {"name": "Chat", "url": "/chat"},
    {"name": "Features", "url": "/features"},
    {"name": "About", "url": "/about"},
    {"name": "Contact", "url": "/contact"}
]

# Welcome message
DefaultMessage = f"""You: Hello
AI Educator: Welcome to AI Educator! I can help you with AI tools recommendations, automation tasks, and much more. Ask me about AI tools for any specific task!"""

# Functions list including AI educator commands
functions = ["open", "close", "play", "system", "content", "google search", "youtube search", 
             "create file", "create folder", "set timer", "set alarm", "whatsapp", "analyze screen",
             "monitor for text", "get screen context", "take screenshot", "ai tools", "ai educator",
             "recommend ai", "find ai tool", "ai for", "best ai", "free ai tools"]
subprocess_list = []

# Global agent state (one agent at a time)
_active_agent: "TeachingAgent | None" = None
_agent_lock = threading.Lock()

# Initialize chat history
chat_history = []

# AI tools query keywords
# - A small fixed list of generic phrases
# - PLUS dynamically loaded tool names/categories from the up-to-date database
AI_KEYWORDS_BASE = [
    'ai tool', 'ai tools', 'ai for', 'recommend ai', 'find ai', 'ai educator',
    'ai tools for', 'best ai', 'free ai', 'ai app', 'ai software', 'ai platform',
    'tool for', 'application for', 'software for', 'website for',
    'tutorial', 'tutorials', 'video tutorial', 'show me tutorials', 'available tutorials'
]

def _load_dynamic_ai_keywords():
    """Load dynamic AI keywords so AI-tools queries are detected reliably.

    Sources:
      1) Base generic phrases (AI_KEYWORDS_BASE)
      2) Data/ai_tools_database.json categories + tool names (dynamic / user-maintained)
      3) FIXED_TUTORIAL_TOOLS names (always supported because local tutorial videos exist)
      4) Local Tutorial Videos folder (auto-detect tool names from filenames)

    Note: This keyword list is only for *query detection* (routing to AI Educator).
    Actual recommendations are still produced by AIEducator.search_tools().
    """
    keywords = set(k.lower() for k in AI_KEYWORDS_BASE)

    def _add_name(name: str) -> None:
        name = (name or '').strip().lower()
        if not name:
            return
        keywords.add(name)
        keywords.add(name.replace('.', '').replace('-', ' '))

    try:
        tools_file = os.path.join('Data', 'ai_tools_database.json')
        if os.path.exists(tools_file):
            with open(tools_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for category in data.get('categories', []):
                _add_name(category.get('name') or '')
                for tool in category.get('tools', []):
                    _add_name(tool.get('name') or '')

        # Include all fixed tutorial tools (even if JSON is missing them)
        for t in FIXED_TUTORIAL_TOOLS:
            _add_name(t.get('name') or '')

        # Auto-detect tool names from Tutorial Videos/*/*.mp4
        tutorials_base = os.path.join(os.getcwd(), 'Tutorial Videos')
        if os.path.isdir(tutorials_base):
            for root, _, files in os.walk(tutorials_base):
                for fn in files:
                    if not fn.lower().endswith(('.mp4', '.mkv', '.mov', '.avi')):
                        continue
                    tool_name = os.path.splitext(fn)[0]
                    # Strip leading numbers like "52 OpusClip - free"
                    tool_name = re.sub(r'^\s*\d+\s*[\.\-_:]*\s*', '', tool_name)
                    _add_name(tool_name)

    except Exception as e:
        print(f"[AI Educator] Failed to load dynamic AI keywords: {e}")

    return list(keywords)

AI_KEYWORDS = _load_dynamic_ai_keywords()

# Helper functions
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ['how', 'what', 'who', 'where', 'when', 'why', 'which', 'whom',
                      'can you', "what's", "where's", "how's"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + '.'
        else:
            new_query += '.'

    return new_query.capitalize()

def TempDirectoryPath(Filename):
    current_dir = os.getcwd()
    TempDirPath = rf"{current_dir}\Frontend\Files"
    path = rf'{TempDirPath}\{Filename}'
    return path

def SetAsssistantStatus(Status):
    with open(TempDirectoryPath('Status.data'), 'w', encoding='utf-8') as file:
        file.write(Status)

def GetAssistantStatus():
    try:
        with open(TempDirectoryPath('Status.data'), 'r', encoding='utf-8') as file:
            Status = file.read()
        return Status
    except FileNotFoundError:
        return "Available..."

def is_ai_tools_query(query: str) -> bool:
    """Check if query is asking about AI tools.

    This powers routing to AIEducator (which is the only path that appends the
    <!--TUTORIALS_START--> marker used to show saved tutorial videos).

    The previous implementation only checked substring membership against a keyword list.
    That misses very common queries like:
      - "ai writing tools"
      - "ai image gen tools"
      - "ai tools for video editing"

    We keep the keyword list, but add a small, safe heuristic:
    if the query contains "ai" and "tool/tools" in any order (or "tools for"),
    we treat it as an AI-tools query.
    """
    query_lower = (query or '').lower()

    # Fast keyword list check (keeps existing behavior)
    if any(keyword in query_lower for keyword in AI_KEYWORDS):
        return True

    # Heuristic: match common phrases even when they don't contain "ai tools" as a literal substring.
    # Examples matched:
    #   "ai writing tools" (ai ... tools)
    #   "tools for ai writing" (tools ... ai)
    #   "best tools for ai video" (tools for ai)
    if re.search(r'\bai\b', query_lower) and re.search(r'\btools?\b', query_lower):
        return True

    if re.search(r'\btools?\s+for\s+ai\b', query_lower):
        return True

    # NEW: Catch any request for a "video" or "youtube tutorial" broadly
    if re.search(r'\b(video|tutorial|youtube|yt|how\s+to\s+use)\b', query_lower):
        return True

    return False

# Routes
@app.route('/')
def home():
    return render_template('index.html',
                           assistant_name=Assistantname,
                           navbar_menu=navbar_menu)

@app.route('/chat')
def chat():
    return render_template('chat.html',
                           assistant_name=Assistantname,
                           username="You",
                           navbar_menu=navbar_menu)

@app.route('/features')
def features():
    return render_template('features.html',
                           assistant_name=Assistantname,
                           navbar_menu=navbar_menu)

@app.route('/about')
def about():
    return render_template('about.html',
                           assistant_name=Assistantname,
                           navbar_menu=navbar_menu)

@app.route('/contact')
def contact():
    return render_template('contact.html',
                           assistant_name=Assistantname,
                           navbar_menu=navbar_menu)

@app.route('/login')
def login():
    return render_template('app.html',
                           assistant_name=Assistantname,
                           navbar_menu=navbar_menu,
                           start_page='login')

@app.route('/get_ai_tools', methods=['POST'])
def get_ai_tools():
    """Endpoint for AI tool recommendations"""
    data = request.json
    query = data.get('query', '')
    category = data.get('category', '')

    try:
        ai_educator = AIEducator()
        if category:
            tools = ai_educator.get_tools_by_category(category)
        else:
            tools = ai_educator.search_tools(query)

        return jsonify({'tools': tools})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_ai_categories', methods=['GET'])
def get_ai_categories():
    """Get all AI categories"""
    try:
        ai_educator = AIEducator()
        categories = ai_educator.get_categories()
        return jsonify({'categories': categories})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────────────────────────
#  TUTORIAL VIDEO SERVING  — FIXED
#
#  Flask's <path:filename> converter already URL-decodes the path,
#  so `filename` arrives as a plain string such as:
#      "1. AI Writing Generation/ChatGPT - Free.mp4"
#
#  The OLD code used send_from_directory(tutorials_path, full_path)
#  where full_path = os.path.join(category_dir, video_file).
#  On Windows os.path.join uses backslashes which Flask/Werkzeug
#  does NOT accept as a safe sub-path — it raises NotFound.
#
#  FIX: pass the category sub-folder as the *directory* argument
#  and the bare filename as the *path* argument, so Werkzeug only
#  has to locate a file inside a flat folder (no sub-path joining).
# ─────────────────────────────────────────────────────────────────
@app.route('/speech.mp3')
def serve_speech():
    # Serve latest TTS output
    return send_from_directory(os.path.join(os.getcwd(), 'Data'), 'speech.mp3', as_attachment=False)


@app.route('/tutorials/<path:filename>')
def serve_tutorials(filename):
    """Serve tutorial video files from the 'Tutorial Videos' folder tree."""
    try:
        # Root of all tutorial videos
        tutorials_base = os.path.join(os.getcwd(), 'Tutorial Videos')

        # Normalize and split — Flask already URL-decoded the path
        parts = filename.replace('\\', '/').split('/')
        parts = [p for p in parts if p]  # drop empty segments

        if len(parts) >= 2:
            # e.g. ["1. AI Writing Generation", "ChatGPT - Free.mp4"]
            # Build the sub-directory from all parts except the last
            sub_dir   = os.path.join(tutorials_base, *parts[:-1])
            video_file = parts[-1]
        else:
            # File sits directly in Tutorial Videos/
            sub_dir    = tutorials_base
            video_file = parts[0] if parts else filename

        print(f"[AI Educator] Serving: {os.path.join(sub_dir, video_file)}")
        return send_from_directory(sub_dir, video_file)

    except Exception as e:
        print(f"[AI Educator] Error serving tutorial '{filename}': {e}")
        return jsonify({'error': str(e)}), 404

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json or {}
    message = data.get('message')
    conversation_id = data.get('conversation_id')
    is_voice = data.get('is_voice', False)
    active_models = data.get('active_models', {})
    voice_response = data.get('voice_response', True)
    attachments = data.get('attachments') or []

    if not conversation_id:
        # create a new conversation if frontend didn't provide one
        conv = conv_store.create_conversation('New Chat')
        conversation_id = conv['id']

    query = message
    if is_voice:
        SetAsssistantStatus("Listening...")

    # Persist user message (with attachments metadata)
    conv_store.append_message(conversation_id, 'user', query, attachments=attachments)

    # Process the query
    response = process_query(query, active_models, voice_response)

    # Persist assistant response
    conv_store.append_message(conversation_id, 'assistant', response)

    # Keep legacy in-memory history (used by existing features)
    chat_history.append({'sender': 'user', 'message': query})
    chat_history.append({'sender': 'assistant', 'message': response})

    return jsonify({'response': response, 'conversation_id': conversation_id})

@app.route('/start_voice', methods=['POST'])
def start_voice():
    SetAsssistantStatus("Listening...")
    return jsonify({'status': 'listening'})

@app.route('/stop_voice', methods=['POST'])
def stop_voice():
    SetAsssistantStatus("Available...")
    return jsonify({'status': 'stopped'})

@app.route('/get_status', methods=['GET'])
def get_status():
    status = GetAssistantStatus()
    return jsonify({'status': status})

# ─────────────────────────────────────────
# Conversations API (multi-chat persistence)
# ─────────────────────────────────────────
@app.route('/api/conversations', methods=['GET', 'POST'])
def api_conversations():
    if request.method == 'GET':
        return jsonify({'conversations': conv_store.list_conversations()})

    # POST create
    data = request.json or {}
    title = data.get('title') or 'New Chat'
    conv = conv_store.create_conversation(title)
    return jsonify({'conversation': {
        'id': conv['id'],
        'title': conv.get('title') or 'New Chat',
        'pinned': bool(conv.get('pinned')),
        'created_at': conv.get('created_at'),
        'updated_at': conv.get('updated_at'),
        'message_count': len(conv.get('messages') or []),
    }})


from Backend.Uploads import UPLOAD_BASE, save_attachments

@app.route('/uploads/<path:subpath>')
def serve_upload(subpath):
    # Serve uploaded attachments from Data/uploads
    base = os.path.abspath(UPLOAD_BASE)
    # send_from_directory safely joins paths
    return send_from_directory(base, subpath, as_attachment=False)


@app.route('/api/upload', methods=['POST'])
def api_upload():
    """Upload one or more attachments for a conversation."""
    conversation_id = request.form.get('conversation_id') or ''
    if not conversation_id:
        conv = conv_store.create_conversation('New Chat')
        conversation_id = conv['id']

    files = request.files.getlist('files')
    attachments = save_attachments(conversation_id, files)

    # Also persist a system message noting the upload (optional but helps history)
    if attachments:
        conv_store.append_message(
            conversation_id,
            'system',
            f"Uploaded {len(attachments)} attachment(s).",
            attachments=attachments,
        )

    return jsonify({'conversation_id': conversation_id, 'attachments': attachments})


@app.route('/api/conversations/<conv_id>', methods=['GET', 'PATCH', 'DELETE'])
def api_conversation(conv_id):
    if request.method == 'GET':
        conv = conv_store.get_conversation(conv_id)
        if not conv:
            return jsonify({'error': 'not_found'}), 404
        # Ensure messages always have expected keys for frontend
        conv.setdefault('messages', [])
        for m in conv['messages']:
            m.setdefault('attachments', [])
        return jsonify({'conversation': conv})

    if request.method == 'PATCH':
        data = request.json or {}
        title = data.get('title') if 'title' in data else None
        pinned = data.get('pinned') if 'pinned' in data else None
        conv = conv_store.update_conversation(conv_id, title=title, pinned=pinned)
        if not conv:
            return jsonify({'error': 'not_found'}), 404
        return jsonify({'conversation': {
            'id': conv['id'],
            'title': conv.get('title') or 'New Chat',
            'pinned': bool(conv.get('pinned')),
            'created_at': conv.get('created_at'),
            'updated_at': conv.get('updated_at'),
            'message_count': len(conv.get('messages') or []),
        }})

    # DELETE
    ok = conv_store.delete_conversation(conv_id)
    return jsonify({'deleted': ok})


# ─────────────────────────────────────────────────────────────────
# TEACHING AGENT API
# ─────────────────────────────────────────────────────────────────

@app.route('/api/teach', methods=['POST'])
def api_teach():
    """SSE endpoint: streams agent steps as JSON events."""
    global _active_agent

    if TeachingAgent is None:
        return jsonify({'error': 'TeachingAgent not available'}), 503

    data = request.json or {}
    task = data.get('task', '').strip()
    voice = bool(data.get('voice', True))

    if not task:
        return jsonify({'error': 'task is required'}), 400

    def generate():
        global _active_agent
        agent = TeachingAgent(voice=voice)
        with _agent_lock:
            _active_agent = agent
        try:
            for event in agent.teach(task):
                payload = json.dumps(event)
                yield f"data: {payload}\n\n"
        except Exception as e:
            err = json.dumps({'step': 0, 'status': 'error', 'narration': str(e), 'screenshot_b64': ''})
            yield f"data: {err}\n\n"
        finally:
            with _agent_lock:
                _active_agent = None
            yield "data: {\"done\": true}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


@app.route('/api/agent_screenshot', methods=['GET'])
def api_agent_screenshot():
    """Return the latest annotated screenshot PNG from the active agent."""
    global _active_agent
    with _agent_lock:
        agent = _active_agent
    if agent:
        png_bytes = agent.get_latest_screenshot_bytes()
        if png_bytes:
            return Response(png_bytes, mimetype='image/png')
    # Fallback: take a fresh screenshot
    try:
        from Backend.ScreenVision import screen_vision  # type: ignore
        img = screen_vision.capture()
        import io
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return Response(buf.getvalue(), mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agent_stop', methods=['POST'])
def api_agent_stop():
    """Signal the running agent to stop."""
    global _active_agent
    with _agent_lock:
        agent = _active_agent
    if agent:
        agent.stop()
        return jsonify({'status': 'stopping'})
    return jsonify({'status': 'no_agent_running'})

def process_query(query, active_models, voice_response):
    try:
        # PRIORITY 0: explicit "open ... and search ..." shortcuts.
        # These were historically expected to work even when the decision model
        # output varied (e.g. "open yt and search hello").
        q_raw = (query or '').strip()
        q = q_raw.lower().strip()

        def _run_automation(cmds: list[str]) -> str:
            results = asyncio.run(Automation(list(cmds)))
            summary = summarize_automation(list(cmds), results)
            if voice_response:
                _speak_async(summary)
            return summary

        # youtube / yt
        m = re.search(r'\b(?:open|launch|start)\s+(?:yt|youtube)\b\s*(?:and\s*)?(?:search|find|look\s*up)\s+(.+)$', q, flags=re.IGNORECASE)
        if m:
            topic = m.group(1).strip(' .')
            return _run_automation([f"youtube search {topic}"])

        # chrome
        m = re.search(r'\b(?:open|launch|start)\s+chrome\b\s*(?:and\s*)?(?:search|find|look\s*up)\s+(.+)$', q, flags=re.IGNORECASE)
        if m:
            topic = m.group(1).strip(' .')
            return _run_automation([f"chrome search {topic}"])

        # notepad write (write EXACT text; do not use AI content generator)
        m = re.search(r'\b(?:open|launch|start)\s+notepad\b\s*(?:and\s*)?(?:write|type)\s+(.+)$', q, flags=re.IGNORECASE)
        if m:
            text = m.group(1).strip()
            return _run_automation([f"notepad write {text}"])

        # word write (write EXACT text; do not use AI content generator)
        m = re.search(r'\b(?:open|launch|start)\s+(?:word|ms\s*word|microsoft\s+word)\b\s*(?:and\s*)?(?:write|type)\s+(.+)$', q, flags=re.IGNORECASE)
        if m:
            text = m.group(1).strip()
            return _run_automation([f"word write {text}"])

        # PRIORITY 1: explicit system controls (brightness/volume) from natural language
        parsed = parse_brightness_volume_query(query)
        if parsed:
            res = execute_parsed_control(parsed)
            if voice_response:
                _speak_async(res.summary)
            return res.summary

        # PRIORITY: Bluetooth pairing / connect / toggle
        if "bluetooth" in q:
            # Pairing or connecting to a specific device
            if any(k in q for k in ["pair", "connect"]):
                target = q
                for word in ["pair", "connect", "with", "to", "bluetooth", "my", "the", "device"]:
                    target = target.replace(word, "")
                target = target.strip()
                if target:
                    return _run_automation([f"bluetooth pair {target}"])
                else:
                    return _run_automation(["bluetooth on"])
            
            # Generic Bluetooth toggle (off verbs)
            if any(k in q for k in ["off", "disable", "stop", "turn off", "switch off", "close"]):
                return _run_automation(["bluetooth off"])
            # Default to turning ON for any other bluetooth query ("bluetooth", "open bluetooth", "start bluetooth")
            else:
                return _run_automation(["bluetooth on"])

        # PRIORITY: Hotspot toggle
        if re.search(r'\b(turn\s+on|enable|start|create|on)\s+(hotspot|mobile\s+hotspot|personal\s+hotspot)\b', q):
            res = toggle_hotspot(True)
            if voice_response:
                _speak_async(res.summary)
            return res.summary

        if re.search(r'\b(turn\s+off|disable|stop|off)\s+(hotspot|mobile\s+hotspot|personal\s+hotspot)\b', q):
            res = toggle_hotspot(False)
            if voice_response:
                _speak_async(res.summary)
            return res.summary

        if re.search(r'\b(hotspot|mobile\s+hotspot|personal\s+hotspot)\s+(on|enable|start|turn\s+on)\b', q):
            res = toggle_hotspot(True)
            if voice_response:
                _speak_async(res.summary)
            return res.summary

        if re.search(r'\b(hotspot|mobile\s+hotspot|personal\s+hotspot)\s+(off|disable|stop|turn\s+off)\b', q):
            res = toggle_hotspot(False)
            if voice_response:
                _speak_async(res.summary)
            return res.summary

        # PRIORITY 1: AI tools / YouTube Search (Dynamic Tutorials)
        if is_ai_tools_query(query):
            print(f"[AI Educator] Routing to AIEducator/YouTube for query: {query!r}")
            SetAsssistantStatus("Searching YouTube...")
            if AIEducator is None:
                response = "AI educator feature is unavailable because dependencies are missing."
            else:
                ai_educator = AIEducator()
                response = ai_educator.process_ai_query(query)
            SetAsssistantStatus("Answering...")

            # Strip tutorial JSON marker before TTS
            if voice_response:
                clean_response = re.sub(
                    r'<!--TUTORIALS_START-->.*?<!--TUTORIALS_END-->',
                    '', response, flags=re.DOTALL
                )
                _speak_async(clean_response)

            return response

        # PRIORITY 2: Teaching Agent — detect "show me / teach me" intent (only if not a video request)
        if is_teach_request(query) and TeachingAgent is not None:
            print(f"[TeachingAgent] Routing to TeachingAgent for query: {query!r}")
            SetAsssistantStatus("Teaching...")
            response = (
                f"🤖 **Live Teaching Agent Activated!**\n\n"
                f"I'll guide you step-by-step for: *{query}*\n\n"
                f"👉 Head over to the **Agent** tab in the navigation to watch me perform this live on your screen with voice guidance!"
            )
            if voice_response:
                _speak_async("Opening the live teaching agent for your task. Please switch to the Agent tab to see the demonstration!")
            SetAsssistantStatus("Available...")
            return response

        # Active model overrides
        if active_models.get('note', False):
            note_content = query.replace("create note", "").strip()
            with open(TempDirectoryPath('note.txt'), 'w') as note_file:
                note_file.write(note_content)
            response = "Note created successfully!"
            if voice_response:
                _speak_async(response)
            return response

        if active_models.get('calendar', False):
            response = f"Event '{query}' scheduled successfully!"
            if voice_response:
                _speak_async(response)
            return response

        if active_models.get('music', False):
            response = f"Playing music: {query}"
            if voice_response:
                _speak_async(response)
            return response

        # Normal DMM processing
        TaskExecution = False
        ImageExecution = False
        ImageGenerationQuery = ""

        SetAsssistantStatus("Thinking...")
        Decision = FirstLayerDMM(query)

        print(f"\nDecision: {Decision}\n")
        print(f"Active Models: {active_models}\n")
        print(f"Voice Response: {voice_response}\n")

        if active_models.get('search', False):
            Decision = (["realtime " + query]
                        if not any("realtime" in d for d in Decision)
                        else Decision)

        G = any(i for i in Decision if i.startswith("general"))
        R = any(i for i in Decision if i.startswith("realtime"))

        Merged_query = " and ".join(
            [" ".join(i.split()[1:])
             for i in Decision
             if i.startswith("general") or i.startswith("realtime")]
        )

        for queries in Decision:
            if "generate" in queries:
                ImageGenerationQuery = str(queries)
                ImageExecution = True

        for queries in Decision:
            if not TaskExecution:
                if any(queries.startswith(func) for func in functions):
                    results = asyncio.run(Automation(list(Decision)))
                    TaskExecution = True
                    # Return a user-visible summary for side-effect tasks (open/search/system etc.)
                    summary = summarize_automation(list(Decision), results)
                    if voice_response:
                        _speak_async(summary)
                    return summary

        if ImageExecution:
            with open(TempDirectoryPath('ImageGeneration.data'), "w") as file:
                file.write(f"{ImageGenerationQuery},True")
            try:
                p1 = subprocess.Popen(
                    ['python', "Backend/ImageGeneration.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    shell=False,
                )
                subprocess_list.append(p1)
            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")

        if G and R or R:
            SetAsssistantStatus("Searching...")
            Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
            SetAsssistantStatus("Answering...")
            if not Answer.startswith("⚡ AGENT:"):
                Answer = f"⚡ AGENT: {Answer}"
            if voice_response:
                _speak_async(Answer)
            return Answer
        else:
            for queries in Decision:
                if "general" in queries:
                    SetAsssistantStatus("Thinking...")
                    QueryFinal = queries.replace("general", "")
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    SetAsssistantStatus("Answering...")
                    if voice_response:
                        _speak_async(Answer)
                    return Answer
                elif "realtime" in queries:
                    SetAsssistantStatus("Searching...")
                    QueryFinal = queries.replace("realtime", "")
                    Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                    SetAsssistantStatus("Answering...")
                    if voice_response:
                        _speak_async(Answer)
                    return Answer
                elif "exit" in queries:
                    QueryFinal = "Okay, Bye!"
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    SetAsssistantStatus("Answering...")
                    if voice_response:
                        _speak_async(Answer)
                    return Answer

    except Exception as e:
        print(f"Error in process_query: {e}")
        return "Sorry, I encountered an error processing your request."

if __name__ == '__main__':
    if not os.path.exists(TempDirectoryPath('')):
        os.makedirs(TempDirectoryPath(''))

    # Create Tutorial Videos directory if it doesn't exist
    tutorials_dir = os.path.join(os.getcwd(), 'Tutorial Videos')
    if not os.path.exists(tutorials_dir):
        os.makedirs(tutorials_dir)

    SetAsssistantStatus("Available...")

    port = 5000
    print(f"Starting AI Educator Flask server on port {port}...")
    print(f"Web interface: http://localhost:{port}")
    print(f"Chat interface: http://localhost:{port}/chat")

    app.run(debug=True, host='0.0.0.0', port=port)