from services.config.workout_config import PROMPT

class LLMCoach:
    def __init__(self, groq_client):
        self.client = groq_client
        self.history = []
        self.system_prompt = PROMPT

    def give_feedback(self, event, issue=None, metrics=None):
        prompt = f"Event: {event}"

        if issue:
            prompt += f"\nForm Issue: {issue}"

        if metrics:
            prompt += f"\nWorkout Results: {metrics}"

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            *self.history[-10:],
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.4
        )

        feedback = response.choices[0].message.content.strip()

        self.history.append({
            "role": "user",
            "content": prompt
        })

        self.history.append({
            "role": "assistant",
            "content": feedback
        })

        return feedback