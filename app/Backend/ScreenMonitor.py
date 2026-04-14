# ScreenMonitor.py
import pyautogui
import cv2
import numpy as np
import pytesseract
from PIL import Image
import time
import os
from dotenv import dotenv_values

# Set Tesseract path (update this to your Tesseract installation path)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ScreenMonitor:
    def __init__(self):
        self.screenshot_dir = "Data/Screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
    def capture_screen(self, region=None, save=False, filename=None):
        """
        Capture the entire screen or a specific region
        region: (left, top, width, height) tuple
        save: whether to save the screenshot
        filename: name for the saved file
        """
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            if save:
                if not filename:
                    timestamp = int(time.time())
                    filename = f"screenshot_{timestamp}.png"
                
                filepath = os.path.join(self.screenshot_dir, filename)
                screenshot.save(filepath)
                print(f"Screenshot saved: {filepath}")
            
            return np.array(screenshot)
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def extract_text_from_screen(self, region=None, preprocess=True):
        """
        Extract text from screen or region
        """
        try:
            # Capture screen
            screen = self.capture_screen(region=region)
            if screen is None:
                return ""
            
            # Convert to grayscale
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            
            # Preprocess if needed
            if preprocess:
                # Apply threshold to get image with only black and white
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            
            # Perform OCR
            text = pytesseract.image_to_string(gray)
            return text.strip()
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
    
    def find_element_on_screen(self, image_path, confidence=0.8):
        """
        Find an element/image on screen
        """
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            return location
        except Exception as e:
            print(f"Error finding element: {e}")
            return None
    
    def get_screen_info(self):
        """
        Get basic screen information
        """
        screen_width, screen_height = pyautogui.size()
        current_x, current_y = pyautogui.position()
        
        return {
            "width": screen_width,
            "height": screen_height,
            "cursor_position": (current_x, current_y),
            "timestamp": time.time()
        }
    
    def monitor_for_text(self, target_text, timeout=30, check_interval=2, region=None):
        """
        Monitor screen for specific text
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            extracted_text = self.extract_text_from_screen(region=region)
            if target_text.lower() in extracted_text.lower():
                return True, extracted_text
            time.sleep(check_interval)
        
        return False, ""
    
    def monitor_for_element(self, image_path, timeout=30, check_interval=2, confidence=0.8):
        """
        Monitor screen for specific element/image
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            location = self.find_element_on_screen(image_path, confidence=confidence)
            if location:
                return True, location
            time.sleep(check_interval)
        
        return False, None

# Global instance
screen_monitor = ScreenMonitor()