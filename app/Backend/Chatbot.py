#Chatbot.py:
import json  # Ensure the import is used
from json import load, dump
from dotenv import dotenv_values
import requests
import datetime
# groq is optional; without it the chatbot can't generate LLM responses.
try:
    from groq import Groq  # type: ignore
except Exception:  # pragma: no cover
    Groq = None

env_vars = dotenv_values(".env")

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey) if (Groq is not None and GroqAPIKey) else None

messages = []

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname}.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***

FORMATTING RULES (IMPORTANT):
- When you write code, ALWAYS format it in Markdown fenced code blocks using triple backticks.
- Always include the language after the opening backticks, e.g. ```python, ```html, ```css, ```javascript, ```json.
- Do NOT use single-line inline code for multi-line code.

Example:
```python
def add(a, b):
    return a + b
```
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
except json.JSONDecodeError:
    print("ChatLog.json is empty or corrupted. Initializing with an empty list.")
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

def RealtimeInformation():
    # Keep this short to avoid adding lots of tokens on every call.
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")

    return (
        "Real-time info (use only if needed):\n"
        f"Day: {day}\nDate: {date} {month} {year}\n"
        f"Time: {hour}:{minute}\n"
    )

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def ChatBot(Query):
    """Send the user's query to the chatbot and return the AI's response."""

    if client is None:
        return "Chatbot is unavailable because Groq API is not configured/installed."

    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)

        messages.append({"role": "user", "content": f"{Query}"})

        # Keep only the latest N messages to reduce latency + token usage
        # (Groq models get noticeably slower with long chat history)
        MAX_HISTORY = int(env_vars.get('CHAT_MAX_HISTORY', '12'))
        if len(messages) > MAX_HISTORY:
            messages = messages[-MAX_HISTORY:]

        # Use Groq's compound-beta for advanced tool-aware chatbot responses
        model_name = env_vars.get('CHAT_MODEL', 'compound-beta')

        # Only attach realtime info when the user is actually asking about time/date
        q_low = (Query or '').lower()
        include_realtime = any(k in q_low for k in ['time', 'date', 'day', 'today', 'month', 'year'])

        completion = client.chat.completions.create(
            model=model_name,
            messages=(SystemChatBot + ([{"role": "system", "content": RealtimeInformation()}] if include_realtime else []) + messages),
            max_tokens=int(env_vars.get('CHAT_MAX_TOKENS', '1024')),
            temperature=float(env_vars.get('CHAT_TEMPERATURE', '0.4')),
            top_p=1,
            stream=True,
            stop=None,
        )

        Answer = ""

        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")

        # Safety net: if the user asked for code and the model forgot code fences,
        # wrap the response so the UI can syntax-highlight it.
        ql = (Query or '').lower()
        if '```' not in Answer and any(k in ql for k in ['code', 'script', 'program', 'function', 'python', 'javascript', 'html', 'css']):
            if '\n' in Answer and any(sym in Answer for sym in ['{', '}', ';', 'def ', 'class ', 'import ', '#include', 'console.log', '<html', '</']):
                Answer = f"```\n{Answer.strip()}\n```"

        messages.append({"role": "assistant", "content": Answer})

        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return Answer  # Return the answer to the main function

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return "Connection error, please try again."
    except Exception as e:
        print(f"Error: {e}")
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return "An error occurred, please try again."

if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        response = ChatBot(user_input)
        print(response)  # Print the response to the user