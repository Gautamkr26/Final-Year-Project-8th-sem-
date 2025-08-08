import pyttsx3
import threading

_engine = pyttsx3.init()

def _speak(text):
    try:
        _engine.say(text)
        _engine.runAndWait()
    except Exception:
        pass

def threaded_speak(text):
    threading.Thread(target=_speak, args=(text,), daemon=True).start()
