import time
import streamlit as st

class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0

    def _find_form_issue(self, exercise, metrics):
        if not metrics:
            return None

        if "issue" in metrics:
            return metrics["issue"]

        if exercise == "Squats":
            if metrics.get("depth_status") == "TOO HIGH":
                return "Your squat is not deep enough. Bend your knees further."

            angle = metrics.get("back_angle", 180)
            if isinstance(angle, (int, float)) and angle < 130:
                return "Keep your back straight."

        elif exercise == "Push-ups":
            if metrics.get("body_alignment") == "Poor Form":
                return "Keep your body straight."

            if metrics.get("hip_status") == "SAGGING":
                return "Your hips are sagging."

            if metrics.get("hip_status") == "PIKED UP":
                return "Lower your hips."

        elif exercise == "Biceps Curls (Dumbbell)":
            if metrics.get("swing_status") == "SWINGING":
                return "Avoid swinging your body."

            if metrics.get("shoulder_status") == "ELBOW DRIFTING":
                return "Keep your elbows close to your body."

        elif exercise == "Shoulder Press":
            if metrics.get("back_arch_status") == "Excessive Arch":
                return "Avoid arching your lower back. Tighten your core."

            if metrics.get("back_arch_status") == "Slight Arch":
                return "Brace your core."

        elif exercise == "Lunges":
            if metrics.get("balance_status") == "OFF BALANCE":
                return "Maintain your balance."

        return None

    def process_event(self, event, exercise, metrics=None):
        print("\n========== VOICE PIPELINE ==========")
        print("EVENT:", event)
        print("EXERCISE:", exercise)

        if metrics is None:
            metrics = {}

        issue = self._find_form_issue(exercise, metrics)
        now = time.time()

        print("FORM ISSUE:", issue)

        priority_events = [
            "workout_started",
            "set_completed",
            "workout_completed"
        ]

        if event not in priority_events:
            if event == "ongoing_form_check" and not issue:
                print("SKIPPED: No form issue detected.")
                return None

            if event not in ["no_pose_detected", "ongoing_form_check"]:
                print("SKIPPED: Unknown event.")
                return None

            if now - self.last_spoken_at < 5:
                print("SKIPPED: Voice cooldown active.")
                return None

        try:
            print("REQUESTING LLM FEEDBACK...")

            text = self.llm.give_feedback(
                event,
                issue,
                metrics
            )

            print("LLM RESPONSE:", text)

            if not text:
                print("FAILED: Empty LLM response.")
                return None

            print("GENERATING AUDIO...")

            audio = self.tts.speak(text)

            if not audio:
                print("FAILED: TTS returned no audio.")
                return None

            self.last_spoken_at = time.time()

            print("SUCCESS: AUDIO GENERATED")
            print("AUDIO SIZE:", len(audio), "bytes")

            return audio, text

        except Exception as e:
            print("VOICE PIPELINE ERROR:", repr(e))
            return None


def autoplay_audio(audio_bytes):
    if audio_bytes:
        st.audio(
            audio_bytes,
            format="audio/mp3",
            autoplay=False
        )