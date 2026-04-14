# Model.py
import cohere
from rich import print
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
CohereAPIKey = env_vars["CohereAPIKey"]

co = cohere.Client(api_key=CohereAPIKey)

funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "reminder", "create file", "create folder",
    "set timer", "set alarm", "whatsapp", "analyze screen",
    "monitor for text", "get screen context", "take screenshot"
]

messages = []

preamble = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write a application and open it in notepad'
*** Do not answer any query, just decide what kind of query is given to you. ***
-> Respond with 'general ( query )' if a query can be answered by a llm model (conversational ai chatbot) and doesn't require any up to date information like if the query is 'who was akbar?' respond with 'general who was akbar?', if the query is 'how can i study more effectively?' respond with 'general how can i study more effectively?', if the query is 'can you help me with this math problem?' respond with 'general can you help me with this math problem?', if the query is 'Thanks, i really liked it.' respond with 'general thanks, i really liked it.' , if the query is 'what is python programming language?' respond with 'general what is python programming language?', etc. Respond with 'general (query)' if a query doesn't have a proper noun or is incomplete like if the query is 'who is he?' respond with 'general who is he?', if the query is 'what's his networth?' respond with 'general what's his networth?', if the query is 'tell me more about him.' respond with 'general tell me more about him.', and so on even if it require up-to-date information to answer. Respond with 'general (query)' if the query is asking about time, day, date, month, year, etc like if the query is 'what's the time?' respond with 'general what's the time?'.
-> Respond with 'realtime ( query )' if a query can not be answered by a llm model (because they don't have realtime data) and requires up to date information like if the query is 'who is indian prime minister' respond with 'realtime who is indian prime minister', if the query is 'tell me about facebook's recent update.' respond with 'realtime tell me about facebook's recent update.', if the query is 'tell me news about coronavirus.' respond with 'realtime tell me news about coronavirus.', etc and if the query is asking about any individual or thing like if the query is 'who is akshay kumar' respond with 'realtime who is akshay kumar', if the query is 'what is today's news?' respond with 'realtime what is today's news?', if the query is 'what is today's headline?' respond with 'realtime what is today's headline?', etc.
-> Respond with 'open (application name or website name)' if a query is asking to open any application like 'open facebook', 'open telegram', etc. but if the query is asking to open multiple applications, respond with 'open 1st application name, open 2nd application name' and so on.
-> Respond with 'close (application name)' if a query is asking to close any application like 'close notepad', 'close facebook', etc. but if the query is asking to close multiple applications or websites, respond with 'close 1st application name, close 2nd application name' and so on.
-> Respond with 'play (song name)' if a query is asking to play any song like 'play afsanay by ys', 'play let her go', etc. but if the query is asking to play multiple songs, respond with 'play 1st song name, play 2nd song name' and so on.
-> Respond with 'generate image (image prompt)' if a query is requesting to generate a image with given prompt like 'generate image of a lion', 'generate image of a cat', etc. but if the query is asking to generate multiple images, respond with 'generate image 1st image prompt, generate image 2nd image prompt' and so on.
-> Respond with 'reminder (datetime with message)' if a query is requesting to set a reminder like 'set a reminder at 9:00pm on 25th june for my business meeting.' respond with 'reminder 9:00pm 25th june business meeting'.
-> Respond with 'system (task name)' if a query is asking to control volume/brightness or other system settings.
   Examples:
     - "mute" -> system mute
     - "increase volume" -> system volume up
     - "increase volume by 5" -> system volume up 5
     - "decrease volume by 3" -> system volume down 3
     - "max the volume" -> system volume max
     - "set volume to 0" -> system volume 0
     - "increase brightness" -> system brightness up
     - "increase brightness by 4" -> system brightness up 4
     - "decrease brightness by 2" -> system brightness down 2
     - "max brightness" -> system brightness max
     - "set brightness to 0" -> system brightness 0
   If the query asks multiple tasks, respond with multiple system commands.
-> Respond with 'content (topic)' if a query is asking to write any type of content like application, codes, emails or anything else about a specific topic but if the query is asking to write multiple types of content, respond with 'content 1st topic, content 2nd topic' and so on.
-> Respond with 'google search (topic)' if a query is asking to search a specific topic on google but if the query is asking to search multiple topics on google, respond with 'google search 1st topic, google search 2nd topic' and so on.
-> Respond with 'youtube search (topic)' if a query is asking to search a specific topic on youtube but if the query is asking to search multiple topics on youtube, respond with 'youtube search 1st topic, youtube search 2nd topic' and so on.
-> Respond with 'create file (filename)' if a query is asking to create a file like 'create file notes.txt' respond with 'create file notes.txt'.
-> Respond with 'create folder (foldername)' if a query is asking to create a folder like 'create folder documents' respond with 'create folder documents'.
-> Respond with 'set timer (duration for message)' if a query is asking to set a timer like 'set timer 5 minutes for tea' respond with 'set timer 5 minutes for tea'.
-> Respond with 'set alarm (time for message)' if a query is asking to set an alarm like 'set alarm 07:00 for wake up' respond with 'set alarm 07:00 for wake up'.
-> Respond with 'whatsapp (message to phone)' if a query is asking to send a WhatsApp message like 'whatsapp hello to +1234567890' respond with 'whatsapp hello to +1234567890'.
-> Respond with 'analyze screen' if a query is asking to analyze what's on the screen like 'what do you see on my screen?' or 'analyze my screen'.
-> Respond with 'monitor for text (text to find) for (timeout) seconds' if a query is asking to monitor the screen for specific text like 'monitor for error messages for 30 seconds'.
-> Respond with 'get screen context' if a query is asking to get context from the current screen like 'what's on my screen right now?'.
-> Respond with 'take screenshot (filename)' if a query is asking to take a screenshot like 'take a screenshot' or 'capture my screen'.
*** If the query is asking to perform multiple tasks like 'open facebook, telegram and close whatsapp' respond with 'open facebook, open telegram, close whatsapp' ***
*** If the user is saying goodbye or wants to end the conversation like 'bye agent.' respond with 'exit'.***
*** Respond with 'general (query)' if you can't decide the kind of query or if a query is asking to perform a task which is not mentioned above. ***
"""

ChatHistory = [
    {"role": "User", "message": "how are you ?"},
    {"role": "Chatbot", "message": "general how are you ?"},
    {"role": "User", "message": "do you like pizza ?"},
    {"role": "Chatbot", "message": "general do you like pizza ?"},
    {"role": "User", "message": "how are you ?"},
    {"role": "User", "message": "open chrome and tell me about mahatma gandhi."},
    {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi."},
    {"role": "User", "message": "open chrome and firefox"},
    {"role": "Chatbot", "message": "open chrome, open firefox"},
    {"role": "User", "message": "what is today's date and by the way remind me that i have a dancing performance on 5th at 11pm "},
    {"role": "Chatbot", "message": "general what is today's date, reminder 11:00pm 5th aug dancing performance"},
    {"role": "User", "message": "create file notes.txt"},
    {"role": "Chatbot", "message": "create file notes.txt"},
    {"role": "User", "message": "set timer 5 minutes for tea"},
    {"role": "Chatbot", "message": "set timer 5 minutes for tea"},
    {"role": "User", "message": "set alarm 07:00 for wake up"},
    {"role": "Chatbot", "message": "set alarm 07:00 for wake up"},
    {"role": "User", "message": "whatsapp hello to +1234567890"},
    {"role": "Chatbot", "message": "whatsapp hello to +1234567890"},
    {"role": "User", "message": "chat with me."},
    {"role": "Chatbot", "message": "general chat with me."},
    {"role": "User", "message": "analyze my screen"},
    {"role": "Chatbot", "message": "analyze screen"},
    {"role": "User", "message": "what's on my screen right now?"},
    {"role": "Chatbot", "message": "get screen context"},
    {"role": "User", "message": "monitor for error messages for 30 seconds"},
    {"role": "Chatbot", "message": "monitor for text error messages for 30 seconds"},
    {"role": "User", "message": "take a screenshot"},
    {"role": "Chatbot", "message": "take screenshot"}
]

def FirstLayerDMM(prompt: str = "test"):
    messages.append({"role": "user", "content": f"{prompt}"})

    stream = co.chat(
        model='command-a-03-2025',  # Latest Cohere model — best intent classification
        message=prompt,
        temperature=0.7,
        chat_history=ChatHistory,
        prompt_truncation='OFF',
        connectors=[],
        preamble=preamble
    )

    response = ""

    for event in stream:
        # Print the event to see its structure
        if event[0] == 'text':
            response = event[1] # Get the text response
        
        if hasattr(event, 'event_type') and event.event_type == "text-generation":
            response += event.text

    response = response.replace("\n", "")
    response = response.split(",")

    response = [i.strip() for i in response]

    temp = []

    for task in response:
        for func in funcs:
            if task.startswith(func):
                temp.append(task)
    
    response = temp

    if "(query)" in response:
        newresponse = FirstLayerDMM(prompt=prompt)
        return newresponse
    else:
        return response

    
if __name__ == "__main__":
    while True:
        print(FirstLayerDMM(input(">>>")))