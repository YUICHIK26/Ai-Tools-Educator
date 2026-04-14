# ScreenAnalysis.py
from groq import Groq
from dotenv import dotenv_values
from Backend.ScreenMonitor import screen_monitor
import base64
import json
import os

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey) if GroqAPIKey else None

class ScreenAnalyzer:
    def __init__(self):
        self.system_prompt = """You are a screen analysis AI. You will receive screenshots and text extracted from screens.
        Your task is to:
        1. Analyze what's on the screen
        2. Understand the context
        3. Provide appropriate responses or actions
        4. Help users with what they're seeing
        
        Be concise, helpful, and focus on what's visible on screen."""
    
    def analyze_screen_with_ai(self, screenshot_path=None, extracted_text=""):
        """
        Analyze screen content using AI
        """
        if not client:
            return "Error: Groq API key not configured for screen analysis."
        
        try:
            # Prepare the message
            user_message = f"I see the following on screen:\n{extracted_text}\n\nWhat should I do with this?"
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                top_p=1
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            return f"Error analyzing screen: {str(e)}"
    
    def analyze_and_respond(self, region=None):
        """
        Comprehensive screen analysis and response
        """
        # Capture screen
        screenshot = screen_monitor.capture_screen(region=region, save=True)
        if screenshot is None:
            return "Failed to capture screen."
        
        # Extract text
        extracted_text = screen_monitor.extract_text_from_screen(region=region)
        
        # Analyze with AI
        response = self.analyze_screen_with_ai(None, extracted_text)
        return response
    
    def get_screen_context(self):
        """
        Get context from screen for better task execution
        """
        extracted_text = screen_monitor.extract_text_from_screen()
        screen_info = screen_monitor.get_screen_info()
        
        context = {
            "screen_text": extracted_text,
            "screen_resolution": f"{screen_info['width']}x{screen_info['height']}",
            "cursor_position": screen_info['cursor_position'],
            "active_applications": self._get_active_applications_context(extracted_text)
        }
        
        return context
    
    def _get_active_applications_context(self, extracted_text):
        """
        Try to identify active applications from screen text
        """
        applications = []
        
        # Common application identifiers
        app_indicators = {
            "chrome": ["chrome", "google", "www.", "http"],
            "word": ["microsoft word", "document", "docx"],
            "excel": ["microsoft excel", "spreadsheet", "xlsx"],
            "powerpoint": ["microsoft powerpoint", "presentation", "pptx"],
            "vscode": ["visual studio code", "vscode", "python", "javascript"],
            "browser": ["browser", "search", "website"],
            "file_explorer": ["file explorer", "folder", "directory"]
        }
        
        text_lower = extracted_text.lower()
        
        for app, indicators in app_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                applications.append(app)
        
        return applications if applications else ["unknown"]

# Global instance
screen_analyzer = ScreenAnalyzer()