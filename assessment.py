from utils import Severity

class MentalHealthAssessment:
    def __init__(self, questions):
        self.questions = questions

    def get_current_question(self, index):
        return self.questions[index] if 0 <= index < len(self.questions) else None
