class MentalHealthAssessment:
    def __init__(self, questions):
        self.questions = questions
        self.score = 0
        self.index = 0

    def get_current_question(self):
        if self.index < len(self.questions):
            return self.questions[self.index]
        return None

    def record_answer(self, selected_index):
        self.score += selected_index
        self.index += 1

    def get_feedback(self):
        if self.score <= 13:
            return self.score, (
                "🟢 Minimal depression.\n\nYou're doing well, but don't ignore your mental well-being. "
                "Keep engaging in physical activity, maintain a good sleep schedule, and talk with loved ones."
            )
        elif 14 <= self.score <= 19:
            return self.score, (
                "🟡 Mild depression.\n\nTry journaling your thoughts, practicing mindfulness, and staying socially connected. "
                "Avoid isolation and adopt a structured daily routine."
            )
        elif 20 <= self.score <= 28:
            return self.score, (
                "🟠 Moderate depression.\n\nIt’s a good time to talk to a counselor or mental health expert. "
                "Start doing light exercises like walking or yoga. You're not alone—help is available."
            )
        else:
            return self.score, (
                "🔴 Severe depression.\n\nPlease seek immediate support from a licensed mental health professional. "
                "Talk to someone you trust and don’t delay therapy or consultation."
            )
