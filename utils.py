from enum import Enum

# Severity levels
class Severity(Enum):
    MINIMAL = 0
    MILD = 1
    MODERATE = 2
    SEVERE = 3

# Score to severity mapping
def score_to_severity(score):
    if score <= 13:
        return Severity.MINIMAL
    elif score <= 19:
        return Severity.MILD
    elif score <= 28:
        return Severity.MODERATE
    else:
        return Severity.SEVERE

# Severity messages
def severity_message(severity):
    if severity == Severity.MINIMAL:
        return "Your score suggests minimal or no depression."
    elif severity == Severity.MILD:
        return "Your score suggests mild depression. Consider self-help strategies and monitoring your mood."
    elif severity == Severity.MODERATE:
        return "Your score suggests moderate depression. It's advisable to consult a mental health professional."
    elif severity == Severity.SEVERE:
        return "Your score suggests severe depression. Please seek professional help immediately."
    return ""

# Crisis message
def crisis_message():
    return "⚠️ If you are experiencing suicidal thoughts or are in crisis, please seek immediate help from local crisis services or helplines."
