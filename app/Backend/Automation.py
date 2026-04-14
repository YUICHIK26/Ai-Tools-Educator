#Automation.py
try:
    from AppOpener import close, open as appopen  # type: ignore
except Exception:  # pragma: no cover
    close = None
    appopen = None

try:
    from Backend.SystemControls import (
        toggle_bluetooth, toggle_wifi, toggle_hotspot,
        lock_screen, sleep_pc, shutdown_pc, restart_pc, cancel_shutdown
    )  # type: ignore
except Exception:
    try:
        from SystemControls import (
            toggle_bluetooth, toggle_wifi, toggle_hotspot,
            lock_screen, sleep_pc, shutdown_pc, restart_pc, cancel_shutdown
        )  # type: ignore
    except Exception:
        toggle_bluetooth = toggle_wifi = toggle_hotspot = None
        lock_screen = sleep_pc = shutdown_pc = restart_pc = cancel_shutdown = None

from webbrowser import open as webopen

# pywhatkit is optional; provide URL-based fallbacks when missing.
try:
    from pywhatkit import search as pk_search, playonyt as pk_playonyt, sendwhatmsg as pk_sendwhatmsg  # type: ignore
except Exception:  # pragma: no cover
    pk_search = None
    pk_playonyt = None
    pk_sendwhatmsg = None
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print

# groq is optional (only needed for AI content-writing features)
try:
    from groq import Groq  # type: ignore
except Exception:  # pragma: no cover
    Groq = None

import webbrowser
import subprocess
import requests

# Optional deps (not required for open/search features)
try:
    import keyboard  # type: ignore
except Exception:  # pragma: no cover
    keyboard = None

import asyncio
import os
import time

try:
    import screen_brightness_control as sbc  # type: ignore
except Exception:  # pragma: no cover
    sbc = None

try:
    import pyautogui  # type: ignore
except Exception:  # pragma: no cover
    pyautogui = None

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None

import platform
from datetime import datetime, timedelta
import threading
import re

try:
    import pythoncom  # type: ignore
    from win32com.client import Dispatch  # type: ignore
except Exception:  # pragma: no cover
    pythoncom = None
    Dispatch = None

from urllib.parse import quote_plus

# Screen monitoring imports are optional
try:
    from Backend.ScreenMonitor import screen_monitor  # type: ignore
    from Backend.ScreenAnalysis import screen_analyzer  # type: ignore
except Exception:  # pragma: no cover
    screen_monitor = None
    screen_analyzer = None

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

classes = ["zCubwf", "hgKELc", "LTKOO SY7ric", "ZOLcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta",
           "IZ6rdc", "05uR6d LTKOO", "vlzY6d", "webanswers-webanswers_table_webanswers-table", "dDoNo ikb4Bb gsrt", "sXLa0e", 
           "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"]

useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

# Initialize Groq client only if API key exists and SDK is installed
client = None
if GroqAPIKey and Groq is not None:
    client = Groq(api_key=GroqAPIKey)

professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need—don't hesitate to ask.",
]

messages = []

SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ.get('Username', 'User')}, a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems, etc."}]

# Dictionary to store active timers and alarms
active_timers = {}
active_alarms = {}

def GoogleSearch(topic):
    # Prefer pywhatkit when available.
    if pk_search is not None:
        try:
            pk_search(topic)
            return True
        except Exception as e:
            print(f"pywhatkit.search failed: {e}")

    # Fallback: open a Google search URL in the default browser.
    topic_q = quote_plus(str(topic or '').strip())
    webbrowser.open_new_tab(f"https://www.google.com/search?q={topic_q}")
    return True

def Content(topic):
    def OpenWord(content, filename):
        try:
            if pythoncom is None or Dispatch is None:
                raise RuntimeError('pythoncom/win32com not installed')

            # Initialize COM for Word
            pythoncom.CoInitialize()

            # Try to open with Microsoft Word using COM
            word = Dispatch('Word.Application')
            word.Visible = True
            
            # Create a new document
            doc = word.Documents.Add()
            
            # Add content to the document
            doc.Content.Text = content
            
            # Save the document to the specified location
            data_dir = "C:\\python\\jarvis final\\jarvis-ai-light theme\\Data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            full_path = os.path.join(data_dir, filename)
            doc.SaveAs(full_path)
            
            print(f"Content written to: {full_path}")
            return True
            
        except Exception as e:
            print(f"Error opening Word: {e}")
            # Fallback to notepad
            return OpenNotepad(content, filename)
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    def OpenNotepad(content, filename):
        try:
            # Create Data directory if it doesn't exist
            data_dir = "C:\\python\\jarvis final\\jarvis-ai-light theme\\Data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Change .docx to .txt for notepad
            txt_filename = filename.replace('.docx', '.txt')
            full_path = os.path.join(data_dir, txt_filename)
            
            # Write content to text file
            with open(full_path, "w", encoding="utf-8") as file:
                file.write(content)
            
            print(f"Content written to: {full_path}")
            
            # Open with notepad
            subprocess.Popen(['notepad.exe', full_path])
            return True
        except Exception as e:
            print(f"Error opening notepad: {e}")
            return False

    def ContentWriterAI(prompt):
        if not client:
            print("Error: Groq API key not found. Please check your .env file.")
            return "Error: Unable to generate content - API key missing."
        
        try:
            messages.append({"role": "user", "content": f"{prompt}"})

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=SystemChatBot + messages,
                max_tokens=2048,
                temperature=0.7,
                top_p=1,
                stream=True,
                stop=None
            )

            answer = ""

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    answer += chunk.choices[0].delta.content

            answer = answer.replace("</s>", "")
            messages.append({"role": "assistant", "content": answer})
            return answer
        except Exception as e:
            print(f"Error generating content: {e}")
            return f"Error: Unable to generate content - {str(e)}"

    # Extract the actual topic (remove "content" prefix)
    topic = topic.replace("content", "").strip()
    
    # Generate content using AI
    content_by_ai = ContentWriterAI(topic)
    
    # Create filename from topic - clean it up first
    # Remove special characters and replace spaces with underscores
    clean_topic = re.sub(r'[^a-zA-Z0-9\s]', '', topic)
    filename = f"{clean_topic.lower().replace(' ', '_')}.docx"
    
    # Try to open in Word, fallback to Notepad if it fails
    return OpenWord(content_by_ai, filename)

def YouTubeSearch(topic):
    # Use quote_plus so spaces become '+' and the URL is always valid.
    topic_q = quote_plus(str(topic or '').strip())
    url = f"https://www.youtube.com/results?search_query={topic_q}"
    webbrowser.open(url)
    return True


def ChromeSearch(topic: str) -> bool:
    """Search Google in Chrome explicitly.

    We can't rely on pywhatkit.search() here because it uses the OS default browser.
    """
    topic_q = quote_plus(str(topic or '').strip())
    url = f"https://www.google.com/search?q={topic_q}"

    # Prefer launching Chrome explicitly on Windows.
    try:
        if platform.system() == 'Windows':
            # "start" is a cmd built-in -> requires shell=True
            subprocess.Popen(f'start chrome "{url}"', shell=True)
            return True
    except Exception as e:
        print(f"Error launching Chrome via start: {e}")

    # Fallback: attempt to locate chrome through webbrowser
    try:
        browser = webbrowser.get('chrome')
        browser.open_new_tab(url)
        return True
    except Exception:
        # Last fallback: open in default browser
        webbrowser.open_new_tab(url)
        return True

def PlayYoutube(query):
    # Prefer pywhatkit when available.
    if pk_playonyt is not None:
        try:
            pk_playonyt(query)
            return True
        except Exception as e:
            print(f"pywhatkit.playonyt failed: {e}")

    # Fallback: open YouTube search results.
    return YouTubeSearch(query)


def NotepadWrite(text: str) -> bool:
    """Open Notepad and write EXACT provided text.

    Implementation: write to a .txt file and open it in notepad.
    This avoids unreliable keystroke automation and avoids opening Word.
    """
    try:
        data_dir = os.path.join(os.getcwd(), 'Data')
        os.makedirs(data_dir, exist_ok=True)
        filename = os.path.join(data_dir, 'notepad_write.txt')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(text or ''))
        subprocess.Popen(['notepad.exe', filename])
        return True
    except Exception as e:
        print(f"Error in NotepadWrite: {e}")
        return False


def WordWrite(text: str) -> bool:
    """Open Word and write EXACT provided text into a single document.

    Avoids creating multiple Word instances and avoids AI paraphrasing.
    """
    if pythoncom is None or Dispatch is None:
        print('pythoncom/win32com not installed; cannot automate Word')
        return False

    try:
        pythoncom.CoInitialize()

        # Reuse existing Word instance if present; otherwise create.
        # Dispatch() may create a new invisible instance depending on COM state.
        word = None
        try:
            # GetActiveObject is more reliable for reusing the current instance.
            word = pythoncom.GetActiveObject('Word.Application')
        except Exception:
            try:
                word = Dispatch('Word.Application')
            except Exception:
                word = Dispatch('Word.Application')

        word.Visible = True

        # Prefer active document; otherwise create exactly one new doc.
        doc = None
        try:
            doc = word.ActiveDocument
        except Exception:
            doc = None

        if doc is None:
            doc = word.Documents.Add()

        # Ensure the doc is the active window/document to avoid writing into a different instance.
        try:
            doc.Activate()
        except Exception:
            pass

        # Write exactly what user said.
        doc.Content.Text = str(text or '')
        return True

    except Exception as e:
        print(f"Error in WordWrite: {e}")
        return False
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

def OpenApp(app, sess=requests.session()):
    # Prefer AppOpener when available.
    if appopen is not None:
        try:
            appopen(app, match_closest=True, output=True, throw_error=True)
            return True
        except Exception as e:
            print(f"Error opening {app} with AppOpener: {e}")

    # Fallback to system start menu search (Windows).
    try:
        subprocess.Popen(f'start {app}', shell=True)
        return True
    except Exception as e2:
        print(f"Error opening {app} with system command: {e2}")
        return False

def CloseApp(app):
    # Map common names to process names
    app_process_map = {
        "word": "WINWORD.EXE",
        "microsoft word": "WINWORD.EXE",
        "powerpoint": "POWERPNT.EXE",
        "microsoft powerpoint": "POWERPNT.EXE",
        "command line": "cmd.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe"
    }
    
    # Get the process name from the map, or use the original app name
    process_name = app_process_map.get(app.lower(), app)
    
    try:
        # First try to close using taskkill
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/f", "/im", process_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Closed {app} using taskkill")
            return True
    except:
        pass
    
    if close is not None:
        try:
            close(app, match_closest=True, output=True, throw_error=True)
            print(f"Closed {app} using AppOpener")
            return True
        except Exception as e:
            print(f"Error closing {app}: {e}")
            return False

    return False

def System(command: str):
    """Execute a system command.

    Supported (legacy):
      mute | unmute | volume up | volume down | brightness up | brightness down

    Extended:
      volume up <n> | volume down <n>
      brightness up <n> | brightness down <n>
      volume max | volume 0
      brightness max | brightness 0

    For volume, numeric changes are best-effort via keypress repetition.
    For brightness, absolute and delta control uses screen_brightness_control.
    """

    def _press(key: str, times: int = 1):
        if keyboard is None:
            raise RuntimeError('keyboard module not installed')
        for _ in range(max(1, int(times))):
            keyboard.press_and_release(key)

    def _set_brightness_abs(v: int) -> bool:
        try:
            v = max(0, min(100, int(v)))
            if sbc is None:
                raise RuntimeError('screen_brightness_control not installed')
            sbc.set_brightness(v)
            return True
        except Exception as e:
            print(f"Error setting brightness: {e}")
            return False

    def _brightness_delta(delta: int) -> bool:
        try:
            current = int(sbc.get_brightness()[0])
            return _set_brightness_abs(current + int(delta))
        except Exception as e:
            print(f"Error changing brightness: {e}")
            return False

    cmd = (command or '').strip().lower()

    try:
        # extremes
        if cmd in {"volume max", "max volume", "volume maximum"}:
            _press("volume up", 60)
            return True
        if cmd in {"volume 0", "volume zero", "volume min", "min volume", "mute volume"}:
            _press("volume down", 60)
            return True
        if cmd in {"brightness max", "max brightness", "brightness maximum"}:
            return _set_brightness_abs(100)
        if cmd in {"brightness 0", "brightness zero", "brightness min", "min brightness"}:
            return _set_brightness_abs(0)

        # numeric patterns
        m = re.match(r"^(volume up|volume down)\s+(\d{1,3})$", cmd)
        if m:
            base = m.group(1)
            n = int(m.group(2))
            _press("volume up" if base == "volume up" else "volume down", n)
            return True

        m = re.match(r"^(brightness up|brightness down)\s+(\d{1,3})$", cmd)
        if m:
            base = m.group(1)
            n = int(m.group(2))
            return _brightness_delta(n if base == "brightness up" else -n)

        # legacy
        if cmd == "mute":
            _press("volume mute", 1)
            return True
        if cmd == "unmute":
            _press("volume mute", 1)
            return True
        if cmd == "volume up":
            _press("volume up", 1)
            return True
        if cmd == "volume down":
            _press("volume down", 1)
            return True
        if cmd == "brightness up":
            return _brightness_delta(10)
        if cmd == "brightness down":
            return _brightness_delta(-10)

        print(f"Unknown system command: {command}")
        return False

    except Exception as e:
        print(f"Error executing system command {command}: {e}")
        return False

def CreateFile(filename):
    try:
        with open(filename, 'w') as f:
            f.write('')
        print(f"Created file: {filename}")
        return True
    except Exception as e:
        print(f"Error creating file: {e}")
        return False

def CreateFolder(foldername):
    try:
        os.makedirs(foldername, exist_ok=True)
        print(f"Created folder: {foldername}")
        return True
    except Exception as e:
        print(f"Error creating folder: {e}")
        return False

def SetTimer(duration, message):
    try:
        def timer_callback():
            time.sleep(duration)
            print(f"Timer: {message}")
            # You can add notification or sound here
        
        timer_thread = threading.Thread(target=timer_callback)
        timer_thread.daemon = True
        timer_thread.start()
        
        active_timers[message] = timer_thread
        return True
    except Exception as e:
        print(f"Error setting timer: {e}")
        return False

def SetAlarm(time_str, message):
    try:
        alarm_time = datetime.strptime(time_str, "%H:%M")
        now = datetime.now()
        alarm_datetime = datetime(now.year, now.month, now.day, alarm_time.hour, alarm_time.minute)
        
        if alarm_datetime < now:
            alarm_datetime += timedelta(days=1)
        
        delay = (alarm_datetime - now).total_seconds()
        
        def alarm_callback():
            time.sleep(delay)
            print(f"Alarm: {message}")
            # You can add notification or sound here
        
        alarm_thread = threading.Thread(target=alarm_callback)
        alarm_thread.daemon = True
        alarm_thread.start()
        
        active_alarms[message] = alarm_thread
        return True
    except Exception as e:
        print(f"Error setting alarm: {e}")
        return False

def SendWhatsAppMessage(phone, message):
    """Send a WhatsApp message.

    Requires pywhatkit for actual sending. If pywhatkit isn't installed, we fall back
    to opening WhatsApp Web with a prefilled message (user still needs to press Send).
    """
    phone = str(phone or '').strip()
    message = str(message or '').strip()

    if pk_sendwhatmsg is not None:
        try:
            # Get current time and add 2 minutes
            now = datetime.now()
            send_time = now + timedelta(minutes=2)
            pk_sendwhatmsg(phone, message, send_time.hour, send_time.minute)
            return True
        except Exception as e:
            print(f"pywhatkit.sendwhatmsg failed: {e}")

    # Fallback: open WhatsApp Web with prefilled message
    try:
        msg_q = quote_plus(message)
        phone_digits = re.sub(r'\D', '', phone)
        if phone_digits:
            webbrowser.open_new_tab(f"https://wa.me/{phone_digits}?text={msg_q}")
        else:
            webbrowser.open_new_tab(f"https://web.whatsapp.com/send?text={msg_q}")
        return True
    except Exception as e:
        print(f"Error opening WhatsApp Web fallback: {e}")
        return False

def parse_whatsapp_intent(query):
    """
    Parses a natural language string to extract a Contact Name and Message.
    Example: "on whatsapp tell kashif hi" -> ("kashif", "hi")
    """
    q_lower = query.lower().strip()
    wa_name, wa_msg = None, None

    # Check if WhatsApp is mentioned
    if any(k in q_lower for k in ["whatsapp", "whatsaap", "whatsap", "whats app"]):
        # 1. Normalize the trigger
        q_clean = re.sub(r'(?:on\s+)?(?:whats\s*app|whatsaap|whatsap|whatsapp)', 'WASPLIT', q_lower)
        parts = re.split('WASPLIT', q_clean, maxsplit=1)
        content = (parts[0] + " " + parts[1]).strip()

        # Remove filler words
        content = re.sub(r'\b(and|with|on|to)\b', ' ', content)
        content = " ".join(content.split())

        # 2. Split Name and Message using indicators
        msg_indicators = [r'\btell\b', r'\bsay\b', r'\bmessage\b', r'\bwrite\b', r'\bsend\b', r'\bthat\b', r'\bsaying\b']
        best_split = -1
        best_ind_len = 0

        for ind_p in msg_indicators:
            match = re.search(ind_p, content)
            if match and match.start() > 2:
                best_split = match.start()
                best_ind_len = match.end() - match.start()
        if best_split != -1:
            wa_name = content[:best_split].strip()
            wa_msg = content[best_split + best_ind_len:].strip()
        else:
            # Fallback for simple "whatsapp name message"
            words = content.split()
            if len(words) > 1:
                wa_name = words[0]
                wa_msg = " ".join(words[1:])
            else:
                wa_name = content
                wa_msg = "Hello"
        # 3. Clean the name
        prefixes = [r'^(to|search|find|open|message|chat|the|a|send)\s+']
        suffixes = [r'\s+(chat|contact|send)$']
        for _ in range(3):
            for p in prefixes: wa_name = re.sub(p, '', wa_name).strip()
            for s in suffixes: wa_name = re.sub(s, '', wa_name).strip()

        # Exclusion filter
        if wa_name and wa_name.lower() in ["close", "open", "exit", "stop", "launch"]:
            wa_name = None

    return wa_name, wa_msg or "Hello"


def WhatsAppByName(name: str, message: str) -> bool:
    """Automate WhatsApp Desktop to send a message to a contact by name.

    Uses keyboard shortcuts (Ctrl+F) and pyautogui to search for a contact,
    select the top result, type the message, and send it.
    """
    try:
        import pyautogui
        # Failsafe allows you to move mouse to corner of screen to abort
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
    except ImportError:
        print("Please run: pip install pyautogui")
        return False

    # 1. Launch/Focus WhatsApp Desktop
    try:
        print(f"[Automation] Launching WhatsApp protocol for: {name}")
        subprocess.Popen('start whatsapp:', shell=True)
        # Give the app a full 5 seconds to load UI elements
        time.sleep(5.0)
    except Exception as e:
        print(f"Error launching WhatsApp: {e}")
        return False

    # 2. The Keyboard Sequence
    try:
        # Clear any existing view state
        pyautogui.press('escape')
        time.sleep(0.5)

        # Trigger Search (Standard WhatsApp Desktop Shortcut)
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(1.0)

        # Type contact name slowly so results can filter
        pyautogui.typewrite(name, interval=0.1)
        time.sleep(3.0)

        # Select the TOP result
        pyautogui.press('enter')
        time.sleep(2.0)

        # Type and send the content
        pyautogui.typewrite(message, interval=0.08)
        time.sleep(1.0)
        pyautogui.press('enter')

        print(f"Message sent to {name}!")
        return True
    except Exception as e:
        print(f"Automation sequence failed: {e}")
        return False


async def execute_whatsapp_command(name, message):
    """Bridge between the parser and the automation."""
    if name:
        print(f"Routing to WhatsApp: {name} -> {message}")
        # Run the automation in a separate thread so it doesn't block the main loop
        result = await asyncio.to_thread(WhatsAppByName, name, message)
        return result
    return False


# Screen Monitoring Functions
def AnalyzeScreen():
    """
    Analyze the current screen and provide insights
    """
    try:
        response = screen_analyzer.analyze_and_respond()
        return response
    except Exception as e:
        print(f"Error analyzing screen: {e}")
        return f"Error analyzing screen: {str(e)}"

def MonitorForText(text_to_find, timeout=30):
    """
    Monitor screen for specific text
    """
    try:
        found, extracted_text = screen_monitor.monitor_for_text(text_to_find, timeout=timeout)
        if found:
            return f"Found text '{text_to_find}' on screen. Context: {extracted_text[:100]}..."
        else:
            return f"Text '{text_to_find}' not found within {timeout} seconds."
    except Exception as e:
        print(f"Error monitoring for text: {e}")
        return f"Error monitoring for text: {str(e)}"

def GetScreenContext():
    """
    Get context from the current screen
    """
    try:
        context = screen_analyzer.get_screen_context()
        return f"Screen context: {context}"
    except Exception as e:
        print(f"Error getting screen context: {e}")
        return f"Error getting screen context: {str(e)}"

def TakeScreenshot(filename=None):
    """
    Take a screenshot
    """
    try:
        screen_monitor.capture_screen(save=True, filename=filename)
        return "Screenshot taken successfully."
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return f"Error taking screenshot: {str(e)}"

def parse_timer_command(command):
    """Parse timer command like 'set timer 5 seconds for tea'"""
    try:
        # Extract duration and message
        pattern = r'set timer (\d+) (second|minute|hour)s? for (.+)'
        match = re.search(pattern, command)
        
        if match:
            duration = int(match.group(1))
            unit = match.group(2)
            message = match.group(3)
            
            # Convert to seconds
            if unit == "minute":
                duration *= 60
            elif unit == "hour":
                duration *= 3600
                
            return duration, message
        return None, None
    except Exception as e:
        print(f"Error parsing timer command: {e}")
        return None, None

def parse_alarm_command(command):
    """Parse alarm command like 'set alarm 07:00 for wake up'"""
    try:
        # Extract time and message
        pattern = r'set alarm (\d{1,2}:\d{2}) for (.+)'
        match = re.search(pattern, command)
        
        if match:
            time_str = match.group(1)
            message = match.group(2)
            return time_str, message
        return None, None
    except Exception as e:
        print(f"Error parsing alarm command: {e}")
        return None, None

def parse_whatsapp_command(command):
    """Parse WhatsApp command like 'whatsapp hello to +1234567890'"""
    try:
        # Extract message and phone number
        pattern = r'whatsapp (.+) to (.+)'
        match = re.search(pattern, command)
        
        if match:
            message = match.group(1)
            phone = match.group(2)
            return message, phone
        return None, None
    except Exception as e:
        print(f"Error parsing WhatsApp command: {e}")
        return None, None

def parse_monitor_command(command):
    """Parse monitor command like 'monitor for error messages for 30 seconds'"""
    try:
        pattern = r'monitor for (.+) for (\d+) seconds'
        match = re.search(pattern, command)
        
        if match:
            text_to_find = match.group(1).strip()
            timeout = int(match.group(2))
            return text_to_find, timeout
        return None, None
    except Exception as e:
        print(f"Error parsing monitor command: {e}")
        return None, None

async def TranslateAndExecute(commands: list[str]):
    funcs = []

    for command in commands:
        print(f"Processing command: {command}")
        
        if command.startswith("open "):
            app_name = command.removeprefix("open ").strip()
            fun = asyncio.to_thread(OpenApp, app_name)
            funcs.append(fun)
        elif command.startswith("close "):
            app_name = command.removeprefix("close ").strip()
            fun = asyncio.to_thread(CloseApp, app_name)
            funcs.append(fun)
        elif command.startswith("play "):
            query = command.removeprefix("play ").strip()
            fun = asyncio.to_thread(PlayYoutube, query)
            funcs.append(fun)
        elif command.startswith("content "):
            topic = command.removeprefix("content ").strip()
            fun = asyncio.to_thread(Content, topic)
            funcs.append(fun)
        elif command.startswith("google search "):
            query = command.removeprefix("google search ").strip()
            fun = asyncio.to_thread(GoogleSearch, query)
            funcs.append(fun)
        elif command.startswith("youtube search "):
            query = command.removeprefix("youtube search ").strip()
            fun = asyncio.to_thread(YouTubeSearch, query)
            funcs.append(fun)
        elif command.startswith("chrome search "):
            query = command.removeprefix("chrome search ").strip()
            fun = asyncio.to_thread(ChromeSearch, query)
            funcs.append(fun)
        elif command.startswith("notepad write "):
            text = command.removeprefix("notepad write ").strip()
            fun = asyncio.to_thread(NotepadWrite, text)
            funcs.append(fun)
        elif command.startswith("word write "):
            text = command.removeprefix("word write ").strip()
            fun = asyncio.to_thread(WordWrite, text)
            funcs.append(fun)
        elif command.startswith("system "):
            sys_command = command.removeprefix("system ").strip()
            fun = asyncio.to_thread(System, sys_command)
            funcs.append(fun)
        elif command.startswith("create file "):
            filename = command.removeprefix("create file ").strip()
            fun = asyncio.to_thread(CreateFile, filename)
            funcs.append(fun)
        elif command.startswith("create folder "):
            foldername = command.removeprefix("create folder ").strip()
            fun = asyncio.to_thread(CreateFolder, foldername)
            funcs.append(fun)
        elif "set timer" in command:
            duration, message = parse_timer_command(command)
            if duration is not None and message is not None:
                fun = asyncio.to_thread(SetTimer, duration, message)
                funcs.append(fun)
            else:
                print(f"Invalid timer command format: {command}")
        elif "set alarm" in command:
            time_str, message = parse_alarm_command(command)
            if time_str is not None and message is not None:
                fun = asyncio.to_thread(SetAlarm, time_str, message)
                funcs.append(fun)
            else:
                print(f"Invalid alarm command format: {command}")
        elif command.startswith("whatsapp "):
            # Try name-based intent first (e.g. "whatsapp tell kashif hi")
            wa_name, wa_msg = parse_whatsapp_intent(command)
            if wa_name:
                fun = asyncio.to_thread(WhatsAppByName, wa_name, wa_msg)
                funcs.append(fun)
            else:
                # Fallback to phone-number format (e.g. "whatsapp hello to +1234567890")
                message, phone = parse_whatsapp_command(command)
                if message is not None and phone is not None:
                    fun = asyncio.to_thread(SendWhatsAppMessage, phone, message)
                    funcs.append(fun)
                else:
                    print(f"Invalid WhatsApp command format: {command}")
        # Screen monitoring commands
        elif command.startswith("analyze screen"):
            fun = asyncio.to_thread(AnalyzeScreen)
            funcs.append(fun)
        elif command.startswith("monitor for text"):
            text_to_find, timeout = parse_monitor_command(command)
            if text_to_find is not None and timeout is not None:
                fun = asyncio.to_thread(MonitorForText, text_to_find, timeout)
                funcs.append(fun)
            else:
                print(f"Invalid monitor command format: {command}")
        elif command.startswith("get screen context"):
            fun = asyncio.to_thread(GetScreenContext)
            funcs.append(fun)
        elif command.startswith("take screenshot"):
            filename = command.removeprefix("take screenshot").strip()
            filename = filename if filename else None
            fun = asyncio.to_thread(TakeScreenshot, filename)
            funcs.append(fun)
        elif command.startswith("bluetooth "):
            if "pair" in command or "connect" in command:
                # Expected format: "bluetooth pair device_name"
                device_name = command.replace("bluetooth", "").replace("pair", "").replace("connect", "").replace("with", "").replace("to", "").strip()
                if device_name:
                    import subprocess as _sp
                    import sys as _sys
                    cmd_to_run = [_sys.executable, 'Backend/BluetoothManager.py', 'pair', device_name]
                    fun = asyncio.to_thread(_sp.run, cmd_to_run, capture_output=True)
                    funcs.append(fun)
                else:
                    if toggle_bluetooth:
                        fun = asyncio.to_thread(toggle_bluetooth, "on" in command)
                        funcs.append(fun)
            else:
                if toggle_bluetooth:
                    fun = asyncio.to_thread(toggle_bluetooth, "on" in command)
                    funcs.append(fun)
        # ── NEW SYSTEM CONTROLS ──
        elif command in ("bluetooth on", "turn on bluetooth", "enable bluetooth"):
            if toggle_bluetooth:
                fun = asyncio.to_thread(toggle_bluetooth, True)
                funcs.append(fun)
        elif command in ("bluetooth off", "turn off bluetooth", "disable bluetooth"):
            if toggle_bluetooth:
                fun = asyncio.to_thread(toggle_bluetooth, False)
                funcs.append(fun)
        elif command in ("wifi on", "turn on wifi", "enable wifi", "wi-fi on", "enable wi-fi"):
            if toggle_wifi:
                fun = asyncio.to_thread(toggle_wifi, True)
                funcs.append(fun)
        elif command in ("wifi off", "turn off wifi", "disable wifi", "wi-fi off", "disable wi-fi"):
            if toggle_wifi:
                fun = asyncio.to_thread(toggle_wifi, False)
                funcs.append(fun)
        elif command in ("hotspot on", "turn on hotspot", "enable hotspot", "start hotspot", "mobile hotspot on"):
            if toggle_hotspot:
                fun = asyncio.to_thread(toggle_hotspot, True)
                funcs.append(fun)
        elif command in ("hotspot off", "turn off hotspot", "disable hotspot", "stop hotspot", "mobile hotspot off"):
            if toggle_hotspot:
                fun = asyncio.to_thread(toggle_hotspot, False)
                funcs.append(fun)
        elif command in ("lock screen", "lock my screen", "lock computer", "lock pc"):
            if lock_screen:
                fun = asyncio.to_thread(lock_screen)
                funcs.append(fun)
        elif command in ("sleep", "sleep pc", "sleep computer", "pc sleep"):
            if sleep_pc:
                fun = asyncio.to_thread(sleep_pc)
                funcs.append(fun)
        elif command.startswith("shutdown"):
            if shutdown_pc:
                rest = command.removeprefix("shutdown").strip()
                try:
                    delay = int(rest) if rest.isdigit() else 0
                except Exception:
                    delay = 0
                fun = asyncio.to_thread(shutdown_pc, delay)
                funcs.append(fun)
        elif command.startswith("restart"):
            if restart_pc:
                rest = command.removeprefix("restart").strip()
                try:
                    delay = int(rest) if rest.isdigit() else 0
                except Exception:
                    delay = 0
                fun = asyncio.to_thread(restart_pc, delay)
                funcs.append(fun)
        elif command in ("cancel shutdown", "abort shutdown", "cancel restart"):
            if cancel_shutdown:
                fun = asyncio.to_thread(cancel_shutdown)
                funcs.append(fun)
        else:
            print(f"No function found for command: {command}")

    if funcs:
        results = await asyncio.gather(*funcs, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Command {i+1} failed with exception: {result}")
            else:
                print(f"Command {i+1} result: {result}")
            yield result
    else:
        print("No valid commands to execute")

async def Automation(commands: list[str]):
    """Execute commands and return a list of per-command results.

    Each element corresponds to the yielded result of TranslateAndExecute in order.
    Typically booleans or strings (for screen/context functions), or an Exception.
    """
    print(f"Starting automation with commands: {commands}")
    results = []
    async for result in TranslateAndExecute(commands):
        results.append(result)
    print(f"Automation completed. Results: {results}")
    return results