
import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import time
import uuid
import pandas as pd
from groq import Groq
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db, get_users_exercises
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline

def initialize_voice_pipeline():
    if st.session_state.get("voice_pipeline") is not None:
        return
    try:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            try:
                api_key = st.secrets.get("GROQ_API_KEY", "")
            except Exception:
                api_key = ""
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing.")
        groq_client = Groq(api_key=api_key)
        llm_coach = LLMCoach(groq_client)
        tts = TextToSpeech()
        st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
        st.session_state.voice_error = None
    except Exception as e:
        st.session_state.voice_pipeline = None
        st.session_state.voice_error = str(e)

def save_voice_result(result):
    if result:
        audio, feedback = result
        if audio:
            st.session_state.audio_to_play = audio
            st.session_state.coach_feedback = feedback

def play_audio_automatically(audio):
    if not audio:
        return
    audio_base64 = base64.b64encode(audio).decode("utf-8")
    audio_html = f"""
    <audio id="coach-audio" autoplay controls style="width:100%;">
        <source src="data:audio/mpeg;base64,{audio_base64}" type="audio/mpeg">
        Your browser does not support audio playback.
    </audio>
    <script>
        const audio = document.getElementById("coach-audio");
        audio.play().catch(error => {{
            console.log("Browser blocked autoplay:", error);
        }});
    </script>
    """
    components.html(audio_html, height=80)

def get_workout_results():
    return {
        "exercise": st.session_state.get("exercise_type", "Unknown"),
        "total_reps": st.session_state.get("reps", 0),
        "sets_completed": st.session_state.get("sets_completed", 0),
        "target_sets": st.session_state.get("target_sets", 0),
        "reps_per_set": st.session_state.get("reps_per_set", 0)
    }

def main():
    st.set_page_config(
        page_icon="🏋️‍♀️",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="centered"
    )
    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")
    init_db()
    if not render_login_wall():
        return
    initial_session_defaults()
    defaults = {
        "audio_to_play": None,
        "coach_feedback": None,
        "voice_pipeline": None,
        "voice_error": None,
        "audio_playback_until": 0
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    initialize_voice_pipeline()
    workout_started = st.session_state.get("workout_started", False)
    with st.sidebar:
        st.title("🏋️‍♂️ Apna AI Coach")
        username = st.session_state.get("username")
        if username:
            st.caption(f"👤 Login as {username}")
        st.divider()
        st.subheader("Workout Plan")
        if not workout_started:
            plan_exercise = st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")
            plan_sets = st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)
            plan_reps = st.number_input("Reps per Set", min_value=0, max_value=50, key="plan_reps", step=1)
            start_session_button = st.button("Start Workout", width="stretch", key="start_session_button")
            if start_session_button:
                if plan_sets <= 0 or plan_reps <= 0:
                    st.warning("Please select at least 1 set and 1 rep.")
                else:
                    st.session_state.exercise_type = plan_exercise
                    st.session_state.target_sets = int(plan_sets)
                    st.session_state.reps_per_set = int(plan_reps)
                    st.session_state.reps = 0
                    st.session_state.current_set_reps = 0
                    st.session_state.sets_completed = 0
                    st.session_state.workout_started = True
                    st.session_state.workout_completed = False
                    st.session_state.webrtc_session_id = uuid.uuid4().hex
                    st.session_state.set_cycle_started_at = time.time()
                    st.session_state.last_saved_sets_completed = 0
                    st.session_state.last_notified_sets_completed = 0
                    st.session_state.last_notified_workout_complete = False
                    st.session_state.audio_to_play = None
                    st.session_state.coach_feedback = None
                    st.session_state.audio_playback_until = 0
                    pipeline = st.session_state.get("voice_pipeline")
                    if pipeline:
                        result = pipeline.process_event("workout_started", plan_exercise, {})
                        save_voice_result(result)
                    st.rerun()
        else:
            exercise = st.session_state.get("exercise_type", "Unknown")
            sets = st.session_state.get("target_sets", 0)
            reps = st.session_state.get("reps_per_set", 0)
            st.info(f"**{exercise}** -- {sets} Sets / {reps} Reps")
            end_session_button = st.button("End Workout", key="end_session_button", width="stretch")
            if end_session_button:
                pipeline = st.session_state.get("voice_pipeline")
                if pipeline and not st.session_state.get("last_notified_workout_complete", False):
                    result = pipeline.process_event("workout_completed", exercise, get_workout_results())
                    save_voice_result(result)
                st.session_state.last_notified_workout_complete = True
                st.session_state.workout_started = False
                st.rerun()
        if workout_started:
            st.divider()
            exercise = st.session_state.get("exercise_type", "Unknown")
            total_reps = st.session_state.get("reps", 0)
            current_set_reps = st.session_state.get("current_set_reps", 0)
            reps_per_set = st.session_state.get("reps_per_set", 0)
            sets_completed = st.session_state.get("sets_completed", 0)
            target_sets = st.session_state.get("target_sets", 0)
            st.subheader("Progress")
            st.metric("Total Reps", total_reps)
            st.metric("Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed} / {target_sets}")
            st.divider()
            if exercise == "Squats":
                st.subheader("Squat Metrics")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Depth Status", st.session_state.depth_status)
            elif exercise == "Push-ups":
                st.subheader("Push-up Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)
            elif exercise == "Biceps Curls (Dumbbell)":
                st.subheader("Curl Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Stability", st.session_state.shoulder_status)
                st.metric("Swing Detection", st.session_state.swing_status)
            elif exercise == "Shoulder Press":
                st.subheader("Shoulder Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Arm Extension", st.session_state.extension_status)
                st.metric("Back Arch", st.session_state.back_arch_status)
            elif exercise == "Lunges":
                st.subheader("Lunge Metrics")
                st.metric("Front Knee Angle", f"{st.session_state.front_knee_angle}°")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Balance Status", st.session_state.balance_status)
    st.title("AI Real-time GYM Coach")
    st.markdown("#### Real-time pose detection with proactive AI voice coaching")
    context = None
    if not workout_started:
        st.markdown(
            """
            <div style="border:10px dashed #444;border-radius:0px;padding:48px 32px;text-align:center;color:#888;margin-top:32px;margin-bottom:32px;">
                <h2 style="color:#ccc;margin-bottom:8px;">👈 Set your workout plan</h2>
                <p style="font-size:1.05rem;">Choose your exercise, sets and reps in the sidebar,<br>then click <strong>Start Workout</strong> to activate the camera and AI coach.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        if "webrtc_session_id" not in st.session_state:
            st.session_state.webrtc_session_id = uuid.uuid4().hex
        context = webrtc_streamer(
            key=f"exercise-analysis-{st.session_state.webrtc_session_id}",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={
                "iceServers": [
                    {
                        "urls": ["stun:stun.l.google.com:19302"]
                    },
                    {
                        "urls": st.secrets["turn"]["urls"],
                        "username": st.secrets["turn"]["username"],
                        "credential": st.secrets["turn"]["credential"]
                    }
                ]
            },
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True
        )
    if context is not None:
        st.write("WebRTC playing:", context.state.playing)
        st.write("Video processor:", context.video_processor)
        if context.video_processor is not None:
            metrics = context.video_processor.get_latest_metrics()
            st.write("Latest metrics:", metrics)
        sync_metrics_update(context)
    if st.session_state.get("workout_completed", False):
        st.session_state.workout_started = False
    inject_webrtc_styles()
    audio = st.session_state.get("audio_to_play")
    if audio:
        st.markdown("### 🔊 AI Voice Coach")
        play_audio_automatically(audio)
        st.session_state.audio_playback_until = time.time() + max(5, min(20, len(audio) * 8 / 24000))
        st.session_state.audio_to_play = None
    feedback = st.session_state.get("coach_feedback")
    if feedback:
        st.success(f"🤖 Coach: {feedback}", icon="🤖")
    if st.session_state.get("voice_error"):
        st.warning(f"Voice initialization failed: {st.session_state.voice_error}")
    st.divider()
    st.markdown("#### Workout History")
    user_id = st.session_state.get("user_id")
    if user_id is not None:
        history_rows = get_users_exercises(user_id)
        arr = [
            {
                "Exercise": row["exercise_name"],
                "Reps": row["reps"],
                "Sets": row["sets"],
                "Time (sec)": row["time"],
                "Date": row["created_at"]
            }
            for row in history_rows
        ]
        df = pd.DataFrame(arr)
        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            agg_df = df.groupby(["Exercise", "Date"]).agg({
                "Reps": "sum",
                "Sets": "sum",
                "Time (sec)": "sum"
            }).reset_index()
            agg_df.index += 1
            agg_df.index.name = "S.No"
            st.table(agg_df, border="horizontal")
        else:
            st.info("No workout history found.")
    else:
        st.warning("Please log in to view your workout history.")
    if context is not None and context.state.playing:
        playback_remaining = st.session_state.audio_playback_until - time.time()
        if playback_remaining > 0:
            time.sleep(playback_remaining)
        time.sleep(0.25)
        st.rerun()

if __name__ == "__main__":
    main()
