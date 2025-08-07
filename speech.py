import pyttsx3
import threading

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def threaded_speak(text):
    threading.Thread(target=speak, args=(text,), daemon=True).start()
