import streamlit as st
import time
from services.config.workout_config import METRICS_FIELDS
from services.persistence.exercise_repository import add_exercise


def save_voice_result(result):
    if result is None:
        return

    audio, feedback = result

    if audio:
        st.session_state.audio_to_play = audio
        st.session_state.coach_feedback = feedback


def sync_metrics_update(context):
    if context is None or not hasattr(context, "state") or not context.state.playing:
        return

    processor = getattr(context, "video_processor", None)
    if processor is None:
        return

    exercise = st.session_state.get("exercise_type")
    if not exercise:
        return

    processor.set_exercise(exercise)
    latest_metrics = processor.get_latest_metrics()

    if not latest_metrics:
        return

    # Update repetition count
    reps = latest_metrics.get("reps")
    reps = int(reps) if reps is not None else 0
    st.session_state.reps = reps

    # Update exercise metrics
    fields = METRICS_FIELDS.get(exercise, {})
    if not fields:
        return

    for key, default in fields.items():
        value = latest_metrics.get(key)
        st.session_state[key] = default if value is None else value

    # Calculate sets and repetitions
    reps_per_set = int(st.session_state.get("reps_per_set") or 0)
    target_sets = int(st.session_state.get("target_sets") or 0)

    if reps_per_set > 0 and target_sets > 0:
        sets_completed = min(reps // reps_per_set, target_sets)
        current_set_reps = reps % reps_per_set
        workout_completed = sets_completed >= target_sets
    else:
        sets_completed = 0
        current_set_reps = 0
        workout_completed = False

    st.session_state.sets_completed = sets_completed
    st.session_state.current_set_reps = current_set_reps
    st.session_state.workout_completed = workout_completed

    pipeline = st.session_state.get("voice_pipeline")

    # Prepare workout summary for AI feedback
    workout_results = {
        "exercise": exercise,
        "total_reps": reps,
        "sets_completed": sets_completed,
        "target_sets": target_sets,
        "reps_per_set": reps_per_set
    }

    # Check pose detection
    pose_detected = latest_metrics.get("pose_detected", True)

    if not pose_detected:
        if pipeline:
            result = pipeline.process_event(
                event="no_pose_detected",
                exercise=exercise,
                metrics={
                    "issue": "No pose detected! Please step into the camera frame."
                }
            )
            save_voice_result(result)
        return

    # Save completed sets
    last_saved_sets = st.session_state.get("last_saved_sets_completed", 0) or 0

    if sets_completed > last_saved_sets:
        newly_completed = sets_completed - last_saved_sets
        now_ts = time.time()
        started_at = st.session_state.get("set_cycle_started_at") or now_ts
        time_taken = max(0, now_ts - started_at)

        user_id = st.session_state.get("user_id")

        if user_id is not None:
            add_exercise(
                user_id,
                exercise,
                newly_completed * reps_per_set,
                newly_completed,
                time_taken
            )

        st.session_state.set_cycle_started_at = now_ts
        st.session_state.last_saved_sets_completed = sets_completed

        # Announce completed set or workout
        if pipeline:
            if workout_completed:
                if not st.session_state.get("last_notified_workout_complete", False):
                    st.session_state.last_notified_workout_complete = True

                    result = pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics=workout_results
                    )
                    save_voice_result(result)

            else:
                result = pipeline.process_event(
                    event="set_completed",
                    exercise=exercise,
                    metrics=workout_results
                )
                save_voice_result(result)

    # Handle workout completion
    if workout_completed and not st.session_state.get("last_notified_workout_complete", False):
        st.session_state.last_notified_workout_complete = True

        if pipeline:
            result = pipeline.process_event(
                event="workout_completed",
                exercise=exercise,
                metrics=workout_results
            )
            save_voice_result(result)

        return

    # Real-time form correction
    if pipeline and not workout_completed:
        result = pipeline.process_event(
            event="ongoing_form_check",
            exercise=exercise,
            metrics=latest_metrics
        )
        save_voice_result(result)