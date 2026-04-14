import pygame
import random
import asyncio
import edge_tts
import os
import threading
import uuid
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural")

# ──────────────────────────────────────────────────────────────────────
# Global serialisation: only ONE pygame mixer session at a time.
# This prevents WinError 32 (file-in-use) and "Invalid audio device ID"
# when AgentNarrator fires rapid back-to-back TTS calls.
# ──────────────────────────────────────────────────────────────────────
_mixer_lock = threading.Lock()

# ── Data dir ──────────────────────────────────────────────────────────
_DATA_DIR = "Data"
os.makedirs(_DATA_DIR, exist_ok=True)


async def TextToAudioFile(text, file_path) -> bool:
    """Generate an MP3 at *file_path* from *text* using edge-tts."""
    # Remove stale file if it exists and we own it (no lock needed — caller
    # is already holding _mixer_lock, so no other thread can be here)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass  # another process has the file; we'll overwrite below

    try:
        communicate = edge_tts.Communicate(text, AssistantVoice,
                                           pitch='+0Hz', rate='+0%')
        await communicate.save(file_path)
        return True
    except Exception as e:
        print(f"EdgeTTS API Error: {e}")
        return False


def TTS(Text, func=lambda r=None: True):
    """
    Convert Text to speech and play it.
    Uses a unique temp filename per call to avoid cross-thread file collisions,
    and serialises all mixer operations through _mixer_lock.
    """
    # Each call gets its own unique audio file so concurrent calls never share
    # the same path (even if _mixer_lock blocks them sequentially, the temp
    # file won't be deleted by a racing thread).
    session_id = uuid.uuid4().hex[:8]
    file_path = os.path.join(_DATA_DIR, f"speech_{session_id}.mp3")

    max_retries = 3
    attempts = 0

    while attempts < max_retries:
        with _mixer_lock:
            try:
                # Generate audio
                success = asyncio.run(TextToAudioFile(Text, file_path))

                if not success or not os.path.exists(file_path):
                    attempts += 1
                    continue

                # Play audio
                pygame.mixer.init()
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()

                clock = pygame.time.Clock()
                while pygame.mixer.music.get_busy():
                    if not func():
                        break
                    clock.tick(10)

                return True

            except Exception as e:
                print(f"Error in TTS: {e}")
                attempts += 1

            finally:
                try:
                    func(False)
                except Exception:
                    pass
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                except Exception as e:
                    print(f"Error closing mixer: {e}")
                # Clean up the unique temp file
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except OSError:
                    pass  # another process may still have a handle; ignore

    print("TTS failed after maximum retries.")
    return False


def TextToSpeech(Text, func=lambda r=None: True):
    Data = str(Text).split(".")

    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see."
    ]

    # If text is very long, speak first 2 sentences then the fallback message
    if len(Data) > 4 and len(Text) >= 250:
        TTS(" ".join(Text.split(".")[0:2]) + ". " + random.choice(responses), func)
    else:
        TTS(Text, func)


if __name__ == "__main__":
    while True:
        TextToSpeech(input("Enter the text : "))